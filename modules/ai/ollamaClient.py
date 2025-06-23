import logging, re, json, os
from typing import Dict, Any
import httpx

# 配置日志
logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> Any:
    """从文本中提取JSON内容"""
    text = text.strip()
    # 尝试匹配```json```格式
    json_pattern = re.compile(r'```(?:json)?(.*?)```', re.DOTALL)
    match = json_pattern.search(text)
    
    try:
        if match:
            return json.loads(match.group(1).strip())
        # 如果没有代码块，则尝试直接解析整个文本
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("无法解析JSON，返回原始文本")
        return text

async def chat_with_ollama(params: Dict[str, Any] = None) -> Dict[str, Any]:
    """与Ollama模型进行对话
    
    参数:
    - model: 要使用的模型名称，默认为"qwq"
    - messages: 对话消息列表，每条消息包含role和content
    - temperature: 温度参数，控制输出的随机性，默认为0.7
    - host: Ollama服务器地址，默认为本地
    """
    params = params or {}
    
    model = params.get("model", "qwq")
    messages = params.get("messages", [{'role': 'user', 'content': 'Why is the sky blue?'}])
    temperature = params.get("temperature", 0.7)
    host = params.get("host", os.getenv("OLLAMA_URL", "http://localhost:11434"))
    
    try:
        # 发送请求到Ollama服务器
        async with httpx.AsyncClient(base_url=host) as client:
            response = await client.post(
                "/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "options": {"temperature": temperature}
                }
            )
            response.raise_for_status()
            result = response.json()
            
        logger.info(f"模型 {model} 响应成功，服务器地址: {host}")
        content = result["message"]["content"]
        
        return {
            "content": content, 
            "extracted_content": extract_json_from_text(content),
            "model": model,
            "host": host,
            "full_response": result
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}，服务器地址: {host}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {e}，服务器地址: {host}")
        raw_content = response.text if 'response' in locals() else "无法获取响应内容"
        logger.debug(f"原始响应内容: {raw_content}")
        
        # 尝试修复JSON解析错误
        if 'response' in locals():
            try:
                first_json_match = re.search(r'(\{.*?\})', response.text, re.DOTALL)
                if first_json_match:
                    result = json.loads(first_json_match.group(1))
                    logger.info("成功提取第一个有效的JSON对象")
                    return {
                        "content": result.get("message", {}).get("content", ""),
                        "extracted_content": "",
                        "model": model,
                        "host": host,
                        "full_response": result,
                        "error": "原始JSON解析错误，已提取第一个有效对象"
                    }
            except Exception as inner_e:
                logger.error(f"尝试修复JSON时出错: {inner_e}")
        raise
    except Exception as e:
        logger.error(f"调用Ollama模型时出错: {e}，服务器地址: {host}")
        raise

async def main(params: Dict[str, Any] = None) -> Dict[str, Any]:
    """测试函数"""
    if params is None:
        params = {
            "model": "qwq",
            "messages": [{"role": "user", "content": "用中文简要介绍一下量子计算"}],
            "temperature": 0.7,
            "host": os.getenv("OLLAMA_URL", "http://localhost:11434")
        }
    
    return await chat_with_ollama(params)

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(main())
    print(f"模型回复: {result['content']}")