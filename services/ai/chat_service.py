import logging
import asyncio
import functools
import base64
from typing import Dict, Any, Optional, List
import aiohttp
from ollama import Client
from core.settings import settings

logger = logging.getLogger(__name__)

def _extract_user_only_text(user_content: str) -> str:
    text = (user_content or "").strip()
    if not text:
        return ""
    if "## 当前消息" in text:
        after = text.split("## 当前消息", 1)[1].strip()
        if after.startswith("#"):
            after = after.lstrip("#").strip()
        if after.startswith("当前消息"):
            after = after[len("当前消息") :].strip()
        return after
    return text

def _is_http_url(v: str) -> bool:
    s = (v or "").strip().lower()
    return s.startswith("http://") or s.startswith("https://")

async def _fetch_image_bytes(url: str, *, timeout_seconds: float = 15.0, max_bytes: int = 10 * 1024 * 1024) -> Optional[bytes]:
    u = (url or "").strip()
    if not u:
        return None
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(u) as resp:
            if resp.status < 200 or resp.status >= 300:
                return None
            ct = (resp.headers.get("Content-Type") or "").lower()
            if ct and not ct.startswith("image/"):
                return None
            buf = bytearray()
            async for chunk in resp.content.iter_chunked(256 * 1024):
                if not chunk:
                    continue
                buf.extend(chunk)
                if len(buf) > max_bytes:
                    return None
            return bytes(buf)

async def _resolve_images(images: Any) -> List[bytes]:
    if not isinstance(images, list):
        return []
    out: List[bytes] = []
    http_urls: List[str] = []
    for item in images:
        raw = (item or "").strip() if isinstance(item, str) else ""
        if not raw:
            continue
        if _is_http_url(raw):
            http_urls.append(raw)
            continue
        if raw.startswith("data:"):
            comma = raw.find(",")
            if comma >= 0:
                raw = raw[comma + 1 :].strip()
        try:
            out.append(base64.b64decode(raw, validate=True))
        except Exception:
            continue

    if http_urls:
        sem = asyncio.Semaphore(4)

        async def _task(u: str) -> Optional[bytes]:
            async with sem:
                try:
                    return await _fetch_image_bytes(u)
                except Exception:
                    return None

        fetched = await asyncio.gather(*[_task(u) for u in http_urls], return_exceptions=False)
        out.extend([b for b in fetched if isinstance(b, (bytes, bytearray)) and b])
    return out

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
                          images: Optional[List[bytes]] = None,
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
        images = images or []
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content, **({"images": images} if images else {})}
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
    images_param = params.get("images")
    has_images_param = isinstance(images_param, list) and any(isinstance(x, str) and x.strip() for x in images_param)
    images = await _resolve_images(images_param)

    if has_images_param:
        model_name = "qwen3-vl"
        user_content = _extract_user_only_text(user_content)

    loop = asyncio.get_running_loop()
    if not stream:
        return await loop.run_in_executor(
            None,
            functools.partial(
                service.generate_response,
                system_prompt=system_prompt,
                user_content=user_content,
                model_name=model_name,
                images=images
            )
        )

    async def gen():
        queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

        def _worker():
            try:
                client = service._get_client()
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content, **({"images": images} if images else {})}
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
