import logging, json, re, os

from pydantic import BaseModel

from fastapi import APIRouter, Body
from typing import Dict, Any, List, Optional

from haystack import Pipeline
from haystack.dataclasses import ChatMessage
from haystack.components.builders import ChatPromptBuilder
from haystack_integrations.components.generators.ollama import OllamaChatGenerator

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
    try:
        template = [
            ChatMessage.from_system(request.fromSystem),
            ChatMessage.from_user(request.fromUser)
        ]

        # 创建LLM管道，支持自定义模型参数
        prompt_builder = ChatPromptBuilder(template=template)
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        llm = OllamaChatGenerator(model=request.model if request.model else "qwq", url=ollama_url)

        pipeline = Pipeline()
        pipeline.add_component("prompt_builder", prompt_builder)
        pipeline.add_component("llm", llm)
        pipeline.connect("prompt_builder.prompt", "llm.messages")

        # 运行管道生成指标建议
        result = pipeline.run(data={"prompt_builder": {}})
        # 修复返回结果为 null 的问题
        replies = result.get("llm", {}).get("replies", [])
        if not replies or not hasattr(replies[0], "text"):
            logger.error("LLM返回内容为空或格式不正确")
            return RespOk(data="AI未返回有效内容")
        result_text = replies[0].text # type: ignore
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

    except Exception as e:
        logger.error(f"生成角色信息JSON失败: {str(e)}", exc_info=True)
        return RespOk(data="AI生成失败，请稍后重试")
