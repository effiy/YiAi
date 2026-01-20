"""
企业微信机器人 Webhook 接口
- 提供发送消息到企业微信机器人的功能
"""
import logging
import aiohttp
from fastapi import APIRouter
from core.error_codes import ErrorCode
from core.exceptions import BusinessException
from core.schemas import WeWorkWebhookRequest
from core.response import success

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/wework/send-message")
async def send_wework_message(request: WeWorkWebhookRequest):
    """
    发送消息到企业微信机器人
    
    Args:
        request: 包含 webhook_url 和 content 的请求对象
        
    Returns:
        成功响应或错误信息
    """
    webhook_url = request.webhook_url.strip()
    content = request.content.strip()
    
    if not webhook_url:
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="Webhook URL 不能为空")
    
    if not content:
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="消息内容不能为空")
    
    # 验证 URL 格式
    if not webhook_url.startswith("https://qyapi.weixin.qq.com/"):
        raise BusinessException(ErrorCode.INVALID_PARAMS, message="无效的企业微信 Webhook URL")
    
    # 构建企业微信消息格式
    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get("errmsg", f"HTTP {response.status}")
                    logger.error(f"企业微信 Webhook 请求失败: {error_msg}")
                    raise BusinessException(
                        ErrorCode.INTERNAL_ERROR,
                        message=f"发送失败: {error_msg}"
                    )
                
                # 检查企业微信返回的错误码
                errcode = response_data.get("errcode", 0)
                if errcode != 0:
                    errmsg = response_data.get("errmsg", "未知错误")
                    logger.error(f"企业微信返回错误: errcode={errcode}, errmsg={errmsg}")
                    raise BusinessException(
                        ErrorCode.INTERNAL_ERROR,
                        message=f"发送失败: {errmsg}"
                    )
                
                logger.info(f"成功发送消息到企业微信机器人: {webhook_url[:50]}...")
                return success(data={"message": "消息发送成功"})
                
    except aiohttp.ClientError as e:
        logger.error(f"企业微信 Webhook 请求异常: {str(e)}")
        raise BusinessException(
            ErrorCode.INTERNAL_ERROR,
            message=f"网络请求失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"发送企业微信消息时发生未知错误: {str(e)}", exc_info=True)
        raise BusinessException(
            ErrorCode.INTERNAL_ERROR,
            message=f"发送失败: {str(e)}"
        )
