import logging
from typing import Dict, Any
from services.ai.ollama_client import OllamaService

logger = logging.getLogger(__name__)

async def chat(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    结构化对话接口
    
    Args:
        params: 参数字典
            - system (str): 系统提示词 (可选)
            - user (str): 用户输入 (必填)
            - model (str): 模型名称 (可选)
            
    Returns:
        Dict[str, Any]: 对话响应

    Example:
        GET /?module_name=services.ai.chat_service&method_name=chat&parameters={"user": "Hello", "model": "qwen3"}
    """
    service = OllamaService()
    system_prompt = params.get("system", "你是一个有用的AI助手。")
    user_content = params.get("user", "")
    model_name = params.get("model", "qwen3")
    
    return service.generate_response(
        system_prompt=system_prompt,
        user_content=user_content,
        model_name=model_name
    )

