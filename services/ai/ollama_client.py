import logging
from typing import Optional, Dict, Any, Union
from ollama import Client
from core.config import settings

logger = logging.getLogger(__name__)

class OllamaService:
    """Ollama 服务客户端封装"""
    def __init__(self, host: Optional[str] = None, auth: Optional[str] = None):
        """
        初始化 Ollama 服务客户端
        
        Args:
            host: Ollama 服务地址，默认从配置读取
            auth: 认证信息，默认从配置读取
        """
        self.ollama_url = host or settings.ollama_url
        self.ollama_auth = auth or settings.ollama_auth

    def _get_client(self) -> Client:
        """获取 Ollama 客户端实例"""
        if self.ollama_auth:
            if ':' in self.ollama_auth:
                username, password = self.ollama_auth.split(':', 1)
            else:
                username = self.ollama_auth
                password = ""
            return Client(host=self.ollama_url, auth=(username, password))
        else:
            return Client(host=self.ollama_url)

    def generate_response(self, 
                          system_prompt: str = "你是一个有用的AI助手。", 
                          user_content: str = "", 
                          model_name: str = "qwen3",
                          max_retries: int = 2) -> Dict[str, Any]:
        """
        生成 AI 响应
        
        Args:
            system_prompt: 系统提示词
            user_content: 用户输入内容
            model_name: 模型名称
            max_retries: 最大重试次数
        """
        client = self._get_client()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        attempt = 0
        last_error: Optional[str] = None
        while attempt <= max_retries:
            try:
                response = client.chat(model=model_name, messages=messages)
                if isinstance(response, dict):
                    result = response.get("message", {}).get("content", "")
                else:
                    result = getattr(response, "message", {}).get("content", "")
                return {
                    "success": True,
                    "model": model_name,
                    "message": result
                }
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Ollama 调用失败: {last_error}, attempt={attempt}")
                attempt += 1
        logger.error(f"Ollama 调用最终失败: {last_error}")
        return {
            "success": False,
            "error": last_error or "unknown error",
            "model": model_name
        }

