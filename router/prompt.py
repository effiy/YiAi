import logging, json, os
from typing import Optional, List

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

from ollama import Client
from modules.services.chatService import ChatService

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
    fromSystem: str
    fromUser: str
    model: Optional[str] = None
    images: Optional[List[str]] = None
    user_id: Optional[str] = None  # 用户ID，用于存储聊天记录
    conversation_id: Optional[str] = None  # 会话ID，用于关联多轮对话
    save_chat: bool = True  # 是否保存聊天记录


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
        
        # 准备消息
        if request.images and len(request.images) > 0:
            content = []
            content.append({"type": "text", "text": request.fromUser})
            for img in request.images:
                content.append({"type": "image_url", "image_url": {"url": img}})
            messages = [
                {"role": "system", "content": request.fromSystem},
                {"role": "user", "content": content}
            ]
        else:
            messages = [
                {"role": "system", "content": request.fromSystem},
                {"role": "user", "content": request.fromUser}
            ]
        
        # 如果有会话ID，获取历史消息
        if conversation_id and user_id:
            try:
                history_chats = await chat_service.get_chats_by_conversation(
                    conversation_id=conversation_id,
                    limit=10
                )
                # 将历史消息添加到 messages 中（按时间正序）
                for chat in reversed(history_chats):
                    chat_messages = chat.get("messages", [])
                    # 只取最后的消息对，避免消息过多
                    if chat_messages:
                        messages = messages[:-1]  # 移除当前的 system 和 user 消息
                        messages.extend(chat_messages)
                        messages.append({"role": "system", "content": request.fromSystem})
                        messages.append({"role": "user", "content": request.fromUser})
                        break
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
            
            # 保存聊天记录
            if request.save_chat and user_id and assistant_content:
                try:
                    chat_messages = [
                        {"role": "user", "content": request.fromUser},
                        {"role": "assistant", "content": assistant_content}
                    ]
                    
                    result = await chat_service.save_chat(
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
    """处理 /prompt/ 路由，支持流式响应和聊天记录存储"""
    # 参数验证
    if not request.fromSystem or not request.fromUser:
        raise HTTPException(
            status_code=400, 
            detail="fromSystem和fromUser参数不能为空"
        )
    
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
        await chat_service.initialize()
        result = await chat_service.save_chat(
            user_id=user_id,
            conversation_id=conversation_id,
            messages=messages or [],
            metadata=metadata
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"保存聊天记录失败: {str(e)}")
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
