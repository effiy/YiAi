import logging
import asyncio
import functools
from typing import Dict, Any, Optional
from ollama import Client
from core.settings import settings

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
    stream = params.get("stream") is True

    loop = asyncio.get_running_loop()
    if not stream:
        return await loop.run_in_executor(
            None,
            functools.partial(
                service.generate_response,
                system_prompt=system_prompt,
                user_content=user_content,
                model_name=model_name
            )
        )

    async def gen():
        queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

        def _worker():
            try:
                client = service._get_client()
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
                for item in client.chat(model=model_name, messages=messages, stream=True):
                    try:
                        delta = ""
                        if isinstance(item, dict):
                            delta = (item.get("message") or {}).get("content") or ""
                        else:
                            delta = getattr(item, "message", {}).get("content", "") or ""
                        if delta:
                            asyncio.run_coroutine_threadsafe(queue.put(str(delta)), loop)
                    except Exception:
                        continue
            except Exception as e:
                asyncio.run_coroutine_threadsafe(queue.put(f"请求失败：{e}"), loop)
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(None), loop)

        asyncio.create_task(asyncio.to_thread(_worker))

        while True:
            item = await queue.get()
            if item is None:
                break
            yield {"data": {"message": item}}

    return gen()
