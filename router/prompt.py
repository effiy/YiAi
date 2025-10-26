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
            
            full_response = ""
            for chunk in stream:
                if chunk.get('message', {}).get('content'):
                    content = chunk['message']['content']
                    full_response += content
                    # 以JSON格式发送每个块
                    chunk_data = json.dumps({
                        "type": "content",
                        "data": content
                    }, ensure_ascii=False)
                    yield f"data: {chunk_data}\n\n"
            
            # 发送结束标志
            end_data = json.dumps({
                "type": "done",
                "data": full_response
            }, ensure_ascii=False)
            yield f"data: {end_data}\n\n"
            
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

