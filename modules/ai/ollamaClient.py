import logging, re, json
from typing import Dict, Any
from ollama import chat # type: ignore
from ollama import ChatResponse # type: ignore

# 配置日志
logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> Any:
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

# 示例请求:
# GET http://localhost:8000/api/?module_name=modules.ai.ollamaClient&method_name=chat_with_ollama&params={"model":"qwen2.5","messages":[{"role":"user","content":"为什么天空是蓝色的?"}],"temperature":0.7}
#
# curl 示例:
# curl -X GET "http://localhost:8000/api/?module_name=modules.ai.ollamaClient&method_name=chat_with_ollama&params=%7B%22model%22%3A%22qwen2.5%22%2C%22messages%22%3A%5B%7B%22role%22%3A%22user%22%2C%22content%22%3A%22%E4%B8%BA%E4%BB%80%E4%B9%88%E5%A4%A9%E7%A9%BA%E6%98%AF%E8%93%9D%E8%89%B2%E7%9A%84%3F%22%7D%5D%2C%22temperature%22%3A0.7%7D"
#
# 参数说明:
# - model: 要使用的模型名称，默认为"qwen2.5"
# - messages: 对话消息列表，每条消息包含role和content
# - temperature: 温度参数，控制输出的随机性，默认为0.7

async def chat_with_ollama(params: Dict[str, Any] = None) -> Dict[str, Any]:
    if params is None:
        params = {}
    
    model = params.get("model", "qwen2.5")
    messages = params.get("messages", [
        {
            'role': 'user',
            'content': 'Why is the sky blue?',
        }
    ])
    temperature = params.get("temperature", 0.7)
    
    try:
        response: ChatResponse = chat(
            model=model, 
            messages=messages,
            options={"temperature": temperature}
        )
        
        logger.info(f"模型 {model} 响应成功")
        content = response.message.content
        extracted_content = extract_json_from_text(content)
        
        return {
            "content": content, 
            "extracted_content": extracted_content,
            "model": model,
            "full_response": response
        }
    except Exception as e:
        logger.error(f"调用Ollama模型时出错: {e}")
        raise

async def main(params: Dict[str, Any] = None) -> Dict[str, Any]:
    if params is None:
        params = {
            "model": "qwen2.5",
            "messages": [
                {
                    "role": "user",
                    "content": "用中文简要介绍一下量子计算"
                }
            ],
            "temperature": 0.7
        }
    
    return await chat_with_ollama(params)

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(main())
    print(f"模型回复: {result['content']}")