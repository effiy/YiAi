import logging, json, os

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional

from ollama import Client

# 设置日志
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/prompt",
    tags=["AI prompt generate result"],
    responses={404: {"description": "未找到"}},
)

class ContentRequest(BaseModel):
    fromSystem: str
    fromUser: str
    model: Optional[str] = None  # 新增模型参数，允许可选
    images: Optional[list[str]] = None  # 支持图片 base64 列表

async def stream_ollama_response(request: ContentRequest):
    """生成流式响应"""
    try:
        # 创建Ollama客户端
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        model_name = request.model if request.model else "qwen3"
        
        # 获取认证信息
        ollama_auth = os.getenv("OLLAMA_AUTH", "")
        
        # 配置客户端
        if ollama_auth:
            # 分离用户名和密码
            if ':' in ollama_auth:
                username, password = ollama_auth.split(':', 1)
            else:
                username = ollama_auth
                password = ""
            client = Client(host=ollama_url, auth=(username, password))
        else:
            client = Client(host=ollama_url)
        
        # 准备消息
        # 检查是否有图片输入（视觉模型支持）
        if request.images and len(request.images) > 0:
            # 视觉模型需要特殊格式
            content = []
            content.append({"type": "text", "text": request.fromUser})
            for img in request.images:
                content.append({"type": "image_url", "image_url": {"url": img}})
            messages = [
                {"role": "system", "content": request.fromSystem},
                {"role": "user", "content": content}
            ]
        else:
            # 纯文本消息
            messages = [
                {"role": "system", "content": request.fromSystem},
                {"role": "user", "content": request.fromUser}
            ]
        
        # 调用Ollama流式API
        try:
            stream = client.chat(
                model=model_name, 
                messages=messages,
                stream=True
            )
            
            # 直接转发 ollama 的完整响应
            for chunk in stream:
                # 完整转发 ollama 的原始 chunk
                # 将 ChatResponse 对象转换为字典
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
async def generate_role_ai_json(request: ContentRequest):
    """处理 /prompt/ 路由，支持流式响应"""
    # 参数验证
    if not request.fromSystem or not request.fromUser:
        raise HTTPException(
            status_code=400, 
            detail="fromSystem和fromUser参数不能为空"
        )
    
    return StreamingResponse(
        stream_ollama_response(request),
        media_type="text/event-stream"
    )

