import logging, json, os
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

from ollama import Client
from modules.services.chatService import ChatService
from modules.services.sessionService import SessionService
from modules.database.qdrantClient import QdrantClient
from modules.database.mem0Client import Mem0Client
from modules.utils.session_utils import normalize_session_id
from qdrant_client.models import PointStruct, Distance, Filter, FieldCondition, MatchValue

# 设置日志
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/prompt",
    tags=["AI prompt generate result"],
    responses={404: {"description": "未找到"}},
)

# 初始化聊天服务
chat_service = ChatService()

# 初始化会话服务
_session_service: Optional[SessionService] = None

async def get_session_service() -> SessionService:
    """获取会话服务实例（懒加载）"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
        await _session_service.initialize()
    return _session_service

# 初始化 Qdrant 客户端
qdrant_client = QdrantClient()

# 初始化 Mem0 客户端
mem0_client = Mem0Client()

# 聊天记录集合名称
CHAT_COLLECTION_NAME = "chat_records"

# 向量维度（需要与 embedding 模型匹配，默认使用 nomic-embed-text 的 768 维）
VECTOR_SIZE = 768


def get_user_id(request: Request, user_id: Optional[str] = None) -> str:
    """获取用户ID，优先级：参数 > X-User 请求头 > 默认值 bigboom"""
    if user_id:
        return user_id
    
    x_user = request.headers.get("X-User", "")
    if x_user:
        return x_user
    
    return "bigboom"


class ContentRequest(BaseModel):
    fromSystem: Optional[str] = "你是一个有用的AI助手。"  # 系统提示词，默认为通用助手
    fromUser: Optional[str] = ""  # 用户消息，默认为空
    model: Optional[str] = None  # 模型名称，默认使用环境变量或 "qwen3"
    images: Optional[List[str]] = None  # 图片列表
    user_id: Optional[str] = None  # 用户ID，用于存储聊天记录
    conversation_id: Optional[str] = None  # 会话ID，用于关联多轮对话
    save_chat: bool = True  # 是否保存聊天记录
    use_memory: bool = True  # 是否使用 Mem0 记忆检索
    memory_limit: int = 5  # 记忆检索数量限制
    use_vector_search: bool = True  # 是否使用 Qdrant 向量检索
    vector_search_limit: int = 5  # 向量检索数量限制


class ChatQueryRequest(BaseModel):
    query: str  # 搜索关键词
    user_id: Optional[str] = None
    limit: int = 10


class ChatUpdateRequest(BaseModel):
    messages: List[dict]
    metadata: Optional[dict] = None


async def save_chat_to_qdrant(
    user_id: str,
    conversation_id: Optional[str],
    messages: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """保存聊天记录到 Qdrant 的辅助函数"""
    try:
        # 如果没有 conversation_id，创建新的会话
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # 规范化 conversation_id：如果是 URL 格式，则进行 MD5 处理
        conversation_id = normalize_session_id(conversation_id)
        
        # 获取 Ollama 配置用于生成 embedding
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        ollama_auth = os.getenv("OLLAMA_AUTH", "")
        embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        
        # 创建 Ollama 客户端用于生成 embedding
        if ollama_auth:
            if ':' in ollama_auth:
                username, password = ollama_auth.split(':', 1)
            else:
                username = ollama_auth
                password = ""
            ollama_client = Client(host=ollama_url, auth=(username, password))
        else:
            ollama_client = Client(host=ollama_url)
        
        # 合并所有消息内容用于生成 embedding
        text_content = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        # 验证输入内容不为空
        if not text_content or not text_content.strip():
            raise ValueError("无法生成 embedding：消息内容为空")
        
        # 生成 embedding
        try:
            # Ollama embed API 需要 input 参数为列表
            embedding_response = ollama_client.embed(
                model=embedding_model,
                input=[text_content]  # 改为列表格式
            )
            
            # 添加调试日志
            logger.debug(f"Embedding 响应类型: {type(embedding_response)}")
            logger.debug(f"Embedding 响应内容: {embedding_response}")
            
            # 处理响应：Ollama 可能返回不同的格式
            vector = None
            
            # 方法1: 检查是否是 dict 类型
            if isinstance(embedding_response, dict):
                # 可能是 {"embeddings": [[...]], ...} 或 {"embedding": [...]}
                if "embeddings" in embedding_response:
                    embeddings = embedding_response["embeddings"]
                    if isinstance(embeddings, list) and len(embeddings) > 0:
                        vector = embeddings[0] if isinstance(embeddings[0], list) else embeddings
                elif "embedding" in embedding_response:
                    vector = embedding_response["embedding"]
            
            # 方法2: 检查是否有 embeddings 属性（对象类型）
            elif hasattr(embedding_response, 'embeddings'):
                embeddings = embedding_response.embeddings
                if isinstance(embeddings, list) and len(embeddings) > 0:
                    vector = embeddings[0] if isinstance(embeddings[0], list) else embeddings
                elif not isinstance(embeddings, list):
                    vector = list(embeddings) if hasattr(embeddings, '__iter__') else None
            
            # 方法3: 检查是否有 embedding 属性（单数）
            elif hasattr(embedding_response, 'embedding'):
                vector = embedding_response.embedding
                if not isinstance(vector, list):
                    vector = list(vector) if hasattr(vector, '__iter__') else None
            
            # 方法4: 直接是列表
            elif isinstance(embedding_response, list):
                if len(embedding_response) > 0:
                    vector = embedding_response[0] if isinstance(embedding_response[0], list) else embedding_response
            
            # 验证向量
            if not vector or not isinstance(vector, list) or len(vector) == 0:
                error_msg = f"生成的向量为空，请检查 embedding 模型 {embedding_model} 是否可用。"
                error_msg += f"\n响应类型: {type(embedding_response)}"
                error_msg += f"\n响应内容: {str(embedding_response)[:500]}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 确保向量是数字列表
            if not all(isinstance(x, (int, float)) for x in vector):
                error_msg = f"向量包含非数字元素，请检查 embedding 模型 {embedding_model}。"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 获取实际向量维度
            actual_vector_size = len(vector)
            logger.info(f"成功生成向量，维度: {actual_vector_size} (模型: {embedding_model})")
            
        except ValueError:
            # 重新抛出 ValueError
            raise
        except Exception as e:
            error_msg = f"生成 embedding 失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(f"{error_msg}。请确保 embedding 模型 {embedding_model} 已下载并可用（可通过 'ollama pull {embedding_model}' 下载）。")
        
        # 使用实际向量维度创建或验证集合
        try:
            qdrant_client.create_collection(
                collection_name=CHAT_COLLECTION_NAME,
                vector_size=actual_vector_size,  # 使用实际向量维度
                distance=Distance.COSINE
            )
        except Exception as e:
            # 如果集合已存在但维度不匹配，记录警告但继续尝试保存
            logger.warning(f"集合创建/验证失败: {str(e)}。尝试使用现有集合。")
        
        # 生成文档 ID
        doc_id = str(uuid.uuid4())
        
        # 构建 Qdrant Point
        point = PointStruct(
            id=doc_id,
            vector=vector,
            payload={
                "conversation_id": conversation_id,
                "user_id": user_id,
                "messages": messages,
                "message_count": len(messages),
                "created_time": datetime.now(timezone.utc).isoformat(),
                "updated_time": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
                "text_content": text_content  # 保存原始文本用于检索
            }
        )
        
        # 保存到 Qdrant
        qdrant_client.upsert_points(
            collection_name=CHAT_COLLECTION_NAME,
            points=[point]
        )
        
        result = {
            "id": doc_id,
            "conversation_id": conversation_id,
            "success": True,
            "vector_size": len(vector)
        }
        
        logger.info(f"聊天记录已保存到 Qdrant: doc_id={doc_id}, conversation_id={conversation_id}")
        return result
        
    except Exception as e:
        logger.error(f"保存聊天记录到 Qdrant 失败: {str(e)}", exc_info=True)
        raise


async def stream_ollama_response(request: ContentRequest, chat_service: ChatService, http_request: Request):
    """生成流式响应，并保存聊天记录"""
    assistant_content = ""
    conversation_id = request.conversation_id
    
    # 规范化 conversation_id：如果是 URL 格式，则进行 MD5 处理
    if conversation_id:
        conversation_id = normalize_session_id(conversation_id)
    
    # 获取用户ID（从参数、X-User 或默认值）
    user_id = get_user_id(http_request, request.user_id)
    
    try:
        # 初始化聊天服务
        await chat_service.initialize()
        
        # 创建Ollama客户端
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        model_name = request.model if request.model else "qwen3"
        
        # 获取认证信息
        ollama_auth = os.getenv("OLLAMA_AUTH", "")
        
        # 配置客户端
        if ollama_auth:
            if ':' in ollama_auth:
                username, password = ollama_auth.split(':', 1)
            else:
                username = ollama_auth
                password = ""
            client = Client(host=ollama_url, auth=(username, password))
        else:
            client = Client(host=ollama_url)
        
        # 增强系统提示：添加检索到的相关记忆和聊天记录
        enhanced_system_prompt = request.fromSystem
        relevant_context = []
        context_info = {"memories_count": 0, "chats_count": 0}
        memories = []
        search_results = []
        
        # 1. 使用 Mem0 检索相关记忆
        if request.use_memory and mem0_client.is_available() and user_id and request.fromUser:
            try:
                memories = mem0_client.search_memories(
                    query=request.fromUser,
                    user_id=user_id,
                    limit=request.memory_limit
                )
                if memories:
                    memory_texts = []
                    memory_details = []
                    for mem in memories:
                        mem_content = mem.get("memory", "")
                        if mem_content:
                            memory_texts.append(f"- {mem_content}")
                            # 保存详细信息用于前端展示
                            memory_details.append({
                                "memory": mem_content,
                                "content": mem_content,  # 兼容字段
                                "score": mem.get("score"),
                                "id": mem.get("id"),
                                "metadata": mem.get("metadata", {})
                            })
                    if memory_texts:
                        relevant_context.append(f"相关记忆：\n" + "\n".join(memory_texts))
                        context_info["memories_count"] = len(memories)
                        context_info["memories"] = memory_details
                        logger.info(f"检索到 {len(memories)} 条相关记忆")
            except Exception as e:
                logger.warning(f"Mem0 记忆检索失败: {str(e)}")
        
        # 2. 使用 Qdrant 检索相关聊天记录（如果 Mem0 不可用或需要更直接的检索）
        if request.use_vector_search and user_id and request.fromUser:
            try:
                # 生成用户查询的 embedding（重用已创建的 client）
                embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
                embedding_response = client.embed(
                    model=embedding_model,
                    input=[request.fromUser]
                )
                
                # 提取向量
                query_vector = None
                if isinstance(embedding_response, dict):
                    if "embeddings" in embedding_response:
                        embeddings = embedding_response["embeddings"]
                        query_vector = embeddings[0] if isinstance(embeddings, list) and len(embeddings) > 0 else embeddings
                    elif "embedding" in embedding_response:
                        query_vector = embedding_response["embedding"]
                elif hasattr(embedding_response, 'embeddings'):
                    embeddings = embedding_response.embeddings
                    query_vector = embeddings[0] if isinstance(embeddings, list) and len(embeddings) > 0 else embeddings
                elif hasattr(embedding_response, 'embedding'):
                    query_vector = embedding_response.embedding
                elif isinstance(embedding_response, list):
                    query_vector = embedding_response[0] if len(embedding_response) > 0 else None
                
                # 在 Qdrant 中搜索相关聊天记录
                # 优先检索同一会话的聊天记录，如果结果不够再检索用户的所有记录
                if query_vector:
                    search_results = []
                    
                    # 策略1：如果有 conversation_id，优先检索同一会话的记录
                    if conversation_id and user_id:
                        try:
                            filter_conditions = [
                                FieldCondition(
                                    key="user_id",
                                    match=MatchValue(value=user_id)
                                ),
                                FieldCondition(
                                    key="conversation_id",
                                    match=MatchValue(value=conversation_id)
                                )
                            ]
                            
                            session_results = qdrant_client.search(
                                collection_name=CHAT_COLLECTION_NAME,
                                query_vector=query_vector,
                                limit=request.vector_search_limit,
                                filter=Filter(must=filter_conditions),
                                score_threshold=0.7
                            )
                            
                            if session_results:
                                search_results = session_results
                                logger.info(f"从当前会话 {conversation_id} 检索到 {len(session_results)} 条相关记录")
                        except Exception as e:
                            logger.warning(f"检索会话记录失败: {str(e)}")
                    
                    # 策略2：如果同一会话记录不够，补充检索用户的其他会话记录
                    if len(search_results) < request.vector_search_limit:
                        try:
                            filter_conditions = []
                            if user_id:
                                filter_conditions.append(
                                    FieldCondition(
                                        key="user_id",
                                        match=MatchValue(value=user_id)
                                    )
                                )
                            # 如果有会话 ID，排除当前会话已检索的记录（使用 should 而不是 must）
                            if conversation_id:
                                # 这里不排除，允许跨会话的相似内容作为补充上下文
                                pass
                            
                            # 检索更多记录以补足限制
                            remaining_limit = request.vector_search_limit - len(search_results)
                            if remaining_limit > 0:
                                additional_results = qdrant_client.search(
                                    collection_name=CHAT_COLLECTION_NAME,
                                    query_vector=query_vector,
                                    limit=remaining_limit * 2,  # 多检索一些，然后过滤
                                    filter=Filter(must=filter_conditions) if filter_conditions else None,
                                    score_threshold=0.7
                                )
                                
                                # 过滤掉已经在 search_results 中的记录（按 ID）
                                existing_ids = {r.get("id") for r in search_results}
                                additional_results = [r for r in additional_results if r.get("id") not in existing_ids]
                                
                                # 合并结果
                                search_results.extend(additional_results[:remaining_limit])
                                logger.info(f"补充检索到 {len(additional_results[:remaining_limit])} 条跨会话相关记录")
                        except Exception as e:
                            logger.warning(f"补充检索记录失败: {str(e)}")
                    
                    # 如果没有会话 ID，直接检索用户的所有记录
                    if not search_results and user_id:
                        filter_conditions = [
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=user_id)
                            )
                        ]
                        
                        search_results = qdrant_client.search(
                            collection_name=CHAT_COLLECTION_NAME,
                            query_vector=query_vector,
                            limit=request.vector_search_limit,
                            filter=Filter(must=filter_conditions),
                            score_threshold=0.7
                        )
                    
                    if search_results:
                        chat_texts = []
                        chat_details = []
                        for result in search_results:
                            payload = result.get("payload", {})
                            text_content = payload.get("text_content", "")
                            if text_content and len(text_content) > 0:
                                # 截断过长的内容用于系统提示
                                display_text = text_content[:200] + "..." if len(text_content) > 200 else text_content
                                chat_texts.append(f"- {display_text}")
                                # 保存详细信息用于前端展示
                                chat_details.append({
                                    "text_content": text_content,
                                    "score": result.get("score"),
                                    "id": result.get("id"),
                                    "payload": payload
                                })
                        if chat_texts:
                            relevant_context.append(f"相关聊天记录：\n" + "\n".join(chat_texts))
                            context_info["chats_count"] = len(search_results)
                            context_info["chats"] = chat_details
                            logger.info(f"检索到 {len(search_results)} 条相关聊天记录")
            except Exception as e:
                logger.warning(f"Qdrant 向量检索失败: {str(e)}")
        
        # 3. 如果有相关上下文，添加到系统提示中
        if relevant_context:
            context_section = "\n\n" + "=" * 50 + "\n相关上下文信息（请参考这些信息来更好地回答用户的问题）：\n" + "=" * 50 + "\n"
            context_section += "\n\n".join(relevant_context)
            enhanced_system_prompt = request.fromSystem + context_section
        
        # 发送上下文信息到前端
        if context_info["memories_count"] > 0 or context_info["chats_count"] > 0:
            context_notification = json.dumps({
                "type": "context_info",
                "data": context_info
            }, ensure_ascii=False)
            yield f"data: {context_notification}\n\n"
        
        # 准备消息
        if request.images and len(request.images) > 0:
            content = []
            content.append({"type": "text", "text": request.fromUser})
            for img in request.images:
                content.append({"type": "image_url", "image_url": {"url": img}})
            messages = [
                {"role": "system", "content": enhanced_system_prompt},
                {"role": "user", "content": content}
            ]
        else:
            messages = [
                {"role": "system", "content": enhanced_system_prompt},
                {"role": "user", "content": request.fromUser}
            ]
        
        # 4. 如果有会话ID，获取历史消息构建完整的对话上下文
        if conversation_id and user_id:
            try:
                # 获取会话的所有历史消息（限制最多 20 条记录，每条记录包含一对消息）
                history_chats = await chat_service.get_chats_by_conversation(
                    conversation_id=conversation_id,
                    limit=20
                )
                
                # 将历史消息添加到 messages 中（按时间正序，最新的在前面）
                history_messages = []
                for chat in reversed(history_chats):
                    chat_messages = chat.get("messages", [])
                    if chat_messages:
                        # 合并历史消息
                        history_messages.extend(chat_messages)
                
                # 如果历史消息过多，只保留最近的（保留最后 30 条消息，约 15 轮对话）
                if len(history_messages) > 30:
                    history_messages = history_messages[-30:]
                    logger.info(f"会话 {conversation_id} 历史消息过多，仅保留最近 30 条")
                
                # 构建完整的消息列表：历史消息 + 当前系统提示 + 当前用户消息
                if history_messages:
                    messages = history_messages.copy()
                    # 在历史消息后添加当前的系统提示和用户消息
                    messages.append({"role": "system", "content": enhanced_system_prompt})
                    messages.append({"role": "user", "content": request.fromUser if not request.images else content})
                    logger.info(f"已加载会话 {conversation_id} 的 {len(history_messages)} 条历史消息")
                else:
                    logger.debug(f"会话 {conversation_id} 暂无历史消息")
            except Exception as e:
                logger.warning(f"获取历史消息失败: {str(e)}")
        
        # 调用Ollama流式API
        try:
            stream = client.chat(
                model=model_name, 
                messages=messages,
                stream=True
            )
            
            # 流式返回响应
            for chunk in stream:
                # 转换 chunk 为字典
                if hasattr(chunk, 'model_dump'):
                    chunk_dict = chunk.model_dump()
                elif hasattr(chunk, 'dict'):
                    chunk_dict = chunk.dict()
                elif hasattr(chunk, '__dict__'):
                    chunk_dict = chunk.__dict__
                else:
                    chunk_dict = {
                        'message': chunk.message.dict() if hasattr(chunk.message, 'dict') else str(chunk.message),
                        'done': chunk.done if hasattr(chunk, 'done') else False,
                        'total_duration': getattr(chunk, 'total_duration', None),
                        'load_duration': getattr(chunk, 'load_duration', None),
                        'prompt_eval_count': getattr(chunk, 'prompt_eval_count', None),
                        'prompt_eval_duration': getattr(chunk, 'prompt_eval_duration', None),
                        'eval_count': getattr(chunk, 'eval_count', None),
                        'eval_duration': getattr(chunk, 'eval_duration', None)
                    }
                
                # 累积助手回复内容
                if chunk_dict.get('message') and chunk_dict['message'].get('content'):
                    assistant_content += chunk_dict['message']['content']
                
                chunk_data = json.dumps(chunk_dict, ensure_ascii=False)
                yield f"data: {chunk_data}\n\n"
            
            # 保存聊天记录到 Qdrant
            if request.save_chat and user_id and assistant_content and request.fromUser:
                try:
                    chat_messages = [
                        {"role": "user", "content": request.fromUser},
                        {"role": "assistant", "content": assistant_content}
                    ]
                    
                    result = await save_chat_to_qdrant(
                        user_id=user_id,
                        conversation_id=conversation_id,
                        messages=chat_messages,
                        metadata={
                            "model": model_name,
                            "has_images": bool(request.images and len(request.images) > 0)
                        }
                    )
                    conversation_id = result.get("conversation_id")
                    
                    # 发送保存成功的通知
                    save_notification = json.dumps({
                        "type": "chat_saved",
                        "conversation_id": conversation_id,
                        "doc_id": result.get("id")
                    }, ensure_ascii=False)
                    yield f"data: {save_notification}\n\n"
                    
                    # 自动保存会话到 SessionService
                    try:
                        # 获取会话服务
                        session_service = await get_session_service()
                        
                        # 收集当前会话的所有消息（包括历史消息和当前消息）
                        all_messages = []
                        
                        # 如果有历史消息，先添加历史消息（但不包括 system 消息）
                        if conversation_id and user_id:
                            try:
                                history_chats = await chat_service.get_chats_by_conversation(
                                    conversation_id=conversation_id,
                                    limit=100  # 获取更多历史消息以构建完整会话
                                )
                                
                                # 反转列表，使最老的消息在前（因为get_chats_by_conversation返回的是倒序）
                                history_chats = list(reversed(history_chats))
                                
                                for chat in history_chats:
                                    chat_messages_list = chat.get("messages", [])
                                    # 只添加用户和助手消息，排除系统消息
                                    for msg in chat_messages_list:
                                        role = msg.get("role", "")
                                        if role in ["user", "assistant"]:
                                            all_messages.append({
                                                "role": role,
                                                "content": msg.get("content", "")
                                            })
                            except Exception as e:
                                logger.warning(f"获取历史消息用于会话保存失败: {str(e)}")
                        
                        # 添加当前消息
                        all_messages.extend(chat_messages)
                        
                        # 如果没有消息，跳过保存
                        if not all_messages:
                            logger.debug("没有消息可保存到会话")
                        else:
                            # 构建会话数据
                            # 如果 conversation_id 是 URL 格式，使用它作为会话 URL
                            session_url = None
                            if conversation_id and (conversation_id.startswith("http://") or conversation_id.startswith("https://")):
                                session_url = conversation_id
                            elif request.conversation_id and (request.conversation_id.startswith("http://") or request.conversation_id.startswith("https://")):
                                session_url = request.conversation_id
                            
                            session_data = {
                                "id": conversation_id,  # 使用 conversation_id 作为会话 ID
                                "url": session_url or "",
                                "title": request.fromUser[:100] if request.fromUser else "",  # 使用用户消息的前100字符作为标题
                                "messages": all_messages,
                                "updatedAt": int(datetime.now(timezone.utc).timestamp() * 1000),
                                "lastAccessTime": int(datetime.now(timezone.utc).timestamp() * 1000)
                            }
                            
                            # 如果 conversation_id 存在，尝试获取现有会话以保留其他字段
                            if conversation_id:
                                try:
                                    existing_session = await session_service.get_session(conversation_id, user_id=user_id)
                                    if existing_session:
                                        # 保留现有会话的字段
                                        session_data["url"] = existing_session.get("url", session_data["url"])
                                        session_data["title"] = existing_session.get("title", session_data["title"])
                                        session_data["pageTitle"] = existing_session.get("pageTitle", "")
                                        session_data["pageDescription"] = existing_session.get("pageDescription", "")
                                        session_data["pageContent"] = existing_session.get("pageContent", "")
                                        session_data["createdAt"] = existing_session.get("createdAt")
                                except Exception as e:
                                    logger.debug(f"获取现有会话信息失败（可能是新会话）: {str(e)}")
                            
                            # 保存会话
                            session_result = await session_service.save_session(session_data, user_id=user_id)
                            
                            # 发送会话保存成功的通知
                            session_notification = json.dumps({
                                "type": "session_saved",
                                "session_id": session_result.get("session_id"),
                                "is_new": session_result.get("is_new", False)
                            }, ensure_ascii=False)
                            yield f"data: {session_notification}\n\n"
                            
                            logger.info(f"会话已自动保存: session_id={session_result.get('session_id')}, is_new={session_result.get('is_new')}")
                    except Exception as e:
                        logger.error(f"自动保存会话失败: {str(e)}", exc_info=True)
                        # 不抛出异常，避免影响主流程
                except Exception as e:
                    logger.error(f"保存聊天记录失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"Ollama调用失败: {str(e)}")
            error_data = json.dumps({
                "type": "error",
                "data": f"AI服务调用失败: {str(e)}"
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
            
    except Exception as e:
        logger.error(f"流式处理错误: {str(e)}", exc_info=True)
        error_data = json.dumps({
            "type": "error",
            "data": f"处理失败: {str(e)}"
        }, ensure_ascii=False)
        yield f"data: {error_data}\n\n"


@router.post("/")
async def generate_role_ai_json(request: ContentRequest, http_request: Request):
    """处理 /prompt/ 路由，支持流式响应和聊天记录存储
    
    所有参数都是可选的，如果未提供将使用默认值：
    - fromSystem: 默认 "你是一个有用的AI助手。"
    - fromUser: 默认为空字符串（如果为空，可能无法正常对话）
    - model: 默认使用环境变量或 "qwen3"
    - images: 默认为 None
    - user_id: 默认从 X-User 请求头获取，或使用 "bigboom"
    - conversation_id: 默认为 None，会自动生成新的会话ID
    - save_chat: 默认 True
    - use_memory: 默认 True
    - memory_limit: 默认 5
    - use_vector_search: 默认 True
    - vector_search_limit: 默认 5
    """
    # 确保 fromSystem 和 fromUser 有默认值
    if not request.fromSystem:
        request.fromSystem = "你是一个有用的AI助手。"
    if request.fromUser is None:
        request.fromUser = ""
    
    return StreamingResponse(
        stream_ollama_response(request, chat_service, http_request),
        media_type="text/event-stream"
    )


@router.post("/save")
async def save_chat(
    http_request: Request,
    user_id: Optional[str] = None,
    messages: List[dict] = None,
    conversation_id: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """保存聊天记录到 Qdrant"""
    try:
        user_id = get_user_id(http_request, user_id)
        messages = messages or []
        
        if not messages:
            raise HTTPException(status_code=400, detail="消息列表不能为空")
        
        # 使用辅助函数保存到 Qdrant
        result = await save_chat_to_qdrant(
            user_id=user_id,
            conversation_id=conversation_id,
            messages=messages,
            metadata=metadata
        )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存聊天记录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{doc_id}")
async def get_chat(doc_id: str):
    """根据ID获取聊天记录"""
    try:
        await chat_service.initialize()
        chat = await chat_service.get_chat_by_id(doc_id)
        if not chat:
            raise HTTPException(status_code=404, detail="聊天记录未找到")
        return JSONResponse(content=chat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/conversation/{conversation_id}")
async def get_chats_by_conversation(
    conversation_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    skip: int = Query(default=0, ge=0)
):
    """根据会话ID获取所有聊天记录"""
    try:
        # 规范化 conversation_id：如果是 URL 格式，则进行 MD5 处理
        conversation_id = normalize_session_id(conversation_id)
        
        await chat_service.initialize()
        chats = await chat_service.get_chats_by_conversation(
            conversation_id=conversation_id,
            limit=limit,
            skip=skip
        )
        return JSONResponse(content={
            "conversation_id": conversation_id,
            "count": len(chats),
            "chats": chats
        })
    except Exception as e:
        logger.error(f"获取会话聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/user/{user_id}")
async def get_chats_by_user(
    user_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    skip: int = Query(default=0, ge=0)
):
    """根据用户ID获取所有聊天记录"""
    try:
        await chat_service.initialize()
        chats = await chat_service.get_chats_by_user(
            user_id=user_id,
            limit=limit,
            skip=skip
        )
        return JSONResponse(content={
            "user_id": user_id,
            "count": len(chats),
            "chats": chats
        })
    except Exception as e:
        logger.error(f"获取用户聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/search")
async def search_chats(request: ChatQueryRequest, http_request: Request):
    """语义搜索聊天记录"""
    try:
        await chat_service.initialize()
        user_id = get_user_id(http_request, request.user_id)
        results = await chat_service.search_chats(
            query=request.query,
            user_id=user_id,
            limit=request.limit
        )
        return JSONResponse(content={
            "query": request.query,
            "count": len(results),
            "results": results
        })
    except Exception as e:
        logger.error(f"搜索聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/chat/{doc_id}")
async def update_chat(
    doc_id: str,
    request: ChatUpdateRequest
):
    """更新聊天记录"""
    try:
        await chat_service.initialize()
        success = await chat_service.update_chat(
            doc_id=doc_id,
            messages=request.messages,
            metadata=request.metadata
        )
        if not success:
            raise HTTPException(status_code=404, detail="聊天记录未找到或更新失败")
        return JSONResponse(content={"success": True, "doc_id": doc_id})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/{doc_id}")
async def delete_chat(doc_id: str):
    """删除聊天记录"""
    try:
        await chat_service.initialize()
        success = await chat_service.delete_chat(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="聊天记录未找到或删除失败")
        return JSONResponse(content={"success": True, "doc_id": doc_id})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """删除整个会话的所有聊天记录"""
    try:
        # 规范化 conversation_id：如果是 URL 格式，则进行 MD5 处理
        conversation_id = normalize_session_id(conversation_id)
        
        await chat_service.initialize()
        deleted_count = await chat_service.delete_conversation(conversation_id)
        return JSONResponse(content={
            "success": True,
            "conversation_id": conversation_id,
            "deleted_count": deleted_count
        })
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_service_status():
    """获取服务状态（Mem0 和 Qdrant）"""
    try:
        qdrant_status = {
            "available": False,
            "message": "未检查"
        }
        mem0_status = {
            "available": mem0_client.is_available(),
            "message": "Mem0 服务可用" if mem0_client.is_available() else "Mem0 服务不可用"
        }
        
        # 检查 Qdrant 状态
        try:
            collections = qdrant_client.client.get_collections()
            qdrant_status = {
                "available": True,
                "collections_count": len(collections.collections),
                "message": f"Qdrant 服务可用，共有 {len(collections.collections)} 个集合"
            }
        except Exception as e:
            qdrant_status = {
                "available": False,
                "message": f"Qdrant 服务不可用: {str(e)}"
            }
        
        return JSONResponse(content={
            "success": True,
            "qdrant": qdrant_status,
            "mem0": mem0_status
        })
    except Exception as e:
        logger.error(f"获取服务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取服务状态失败: {str(e)}")
