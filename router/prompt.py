import logging, json, re

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
        llm = OllamaChatGenerator(model=request.model if request.model else "qwq", url="https://yiai.cpolar.io")

        pipeline = Pipeline()
        pipeline.add_component("prompt_builder", prompt_builder)
        pipeline.add_component("llm", llm)
        pipeline.connect("prompt_builder.prompt", "llm.messages")

        # 运行管道生成指标建议
        result = pipeline.run(data={"prompt_builder": {}})
        result_text = result["llm"]["replies"][0].text # type: ignore
        try:
            json_text = extract_json_from_text(result_text)
            result = json.loads(json_text)
        except Exception as e:
            logger.error(f"提取JSON失败: {str(e)}", exc_info=True)
            result = result_text

        return RespOk(data=result)

    except Exception as e:
        logger.error(f"生成角色信息JSON失败: {str(e)}", exc_info=True)
