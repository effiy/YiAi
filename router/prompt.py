import logging, json, os
import uuid
from typing import Optional, List

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

from ollama import Client
from modules.services.chatService import ChatService
from modules.utils.session_utils import normalize_session_id

# 设置日志
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/prompt",
    tags=["AI prompt generate result"],
    responses={404: {"description": "未找到"}},
)

# 初始化聊天服务
chat_service = ChatService()


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



class ChatQueryRequest(BaseModel):
    query: str  # 搜索关键词
    user_id: Optional[str] = None
    limit: int = 10


class ChatUpdateRequest(BaseModel):
    messages: List[dict]
    metadata: Optional[dict] = None


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
        
        # 使用系统提示
        enhanced_system_prompt = request.fromSystem
        
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
    """保存聊天记录"""
    try:
        user_id = get_user_id(http_request, user_id)
        messages = messages or []
        
        if not messages:
            raise HTTPException(status_code=400, detail="消息列表不能为空")
        
        # 如果没有 conversation_id，创建新的会话
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # 规范化 conversation_id：如果是 URL 格式，则进行 MD5 处理
        conversation_id = normalize_session_id(conversation_id)
        
        # 使用聊天服务保存记录
        await chat_service.initialize()
        result = await chat_service.save_chat(
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
    """获取服务状态"""
    try:
        await chat_service.initialize()
        return JSONResponse(content={
            "success": True,
            "message": "服务正常运行"
        })
    except Exception as e:
        logger.error(f"获取服务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取服务状态失败: {str(e)}")
