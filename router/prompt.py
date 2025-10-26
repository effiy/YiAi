import logging, json, re, os

from pydantic import BaseModel

from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any, List, Optional

from ollama import Client

from Resp import RespOk

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

def extract_json_from_text(text: str) -> str:
    """从文本中提取JSON部分"""
    text = text.strip()
    # 尝试匹配```json```格式
    json_pattern = re.compile(r'```(?:json)?(.*?)```', re.DOTALL)
    match = json_pattern.search(text)
    if match:
        return match.group(1).strip()
    # 如果没有代码块，则尝试直接解析整个文本
    return text

@router.post("/")
async def generate_role_ai_json(request: ContentRequest):
    """处理 /prompt/ 路由"""
    try:
        # 参数验证
        if not request.fromSystem or not request.fromUser:
            raise HTTPException(
                status_code=400, 
                detail="fromSystem和fromUser参数不能为空"
            )
        
        return await generate_role_ai_json_internal(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"请求处理错误: {str(e)}")
        raise HTTPException(status_code=400, detail=f"请求处理失败: {str(e)}")

async def generate_role_ai_json_internal(request: ContentRequest):
    """内部处理函数，避免代码重复"""
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
        
        # 调用Ollama
        try:
            response = client.chat(model=model_name, messages=messages)
            result_text = response['message']['content']
        except Exception as e:
            logger.error(f"Ollama调用失败: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"AI服务调用失败: {str(e)}"
            )
        
        # 处理返回结果
        if not result_text:
            logger.error("LLM返回内容为空")
            return RespOk(data="AI未返回有效内容")
        
        try:
            json_text = extract_json_from_text(result_text)
            # 先尝试解析为JSON对象
            parsed_result = None
            if json_text:
                try:
                    parsed_result = json.loads(json_text)
                except Exception as e:
                    logger.warning(f"内容不是有效JSON，返回原始文本: {str(e)}")
                    parsed_result = json_text
            else:
                parsed_result = result_text
            # 如果解析后为None或空，返回原始文本
            if parsed_result is None or parsed_result == "" or parsed_result == {} or parsed_result == []:
                parsed_result = result_text
            return RespOk(data=parsed_result)
        except Exception as e:
            logger.error(f"提取JSON失败: {str(e)}", exc_info=True)
            return RespOk(data=result_text)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成角色信息JSON失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"AI生成失败: {str(e)}"
        )
