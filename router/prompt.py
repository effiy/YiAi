import logging, json, os
import uuid
import base64
from typing import Optional, List, Union, Dict, Any
import aiohttp

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

from ollama import Client
from modules.services.chatService import ChatService
from modules.utils.session_utils import normalize_session_id
from router.utils import get_user_id

# 设置日志
logger = logging.getLogger(__name__)

# 尝试导入 Qwen3-VL 相关工具（可选）
try:
    from qwen_vl_utils import process_vision_info
    QWEN_VL_AVAILABLE = True
except ImportError:
    QWEN_VL_AVAILABLE = False
    logger.warning("qwen-vl-utils 未安装，将使用基础的多模态支持")

router = APIRouter(
    prefix="/prompt",
    tags=["AI prompt generate result"],
    responses={404: {"description": "未找到"}},
)

# 初始化聊天服务
chat_service = ChatService()

class ContentRequest(BaseModel):
    fromSystem: Optional[str] = "你是一个有用的AI助手。"  # 系统提示词，默认为通用助手
    fromUser: Optional[str] = ""  # 用户消息，默认为空
    model: Optional[str] = "deepseek-r1:32b"  # 模型名称，默认使用 "deepseek-r1:32b"
    images: Optional[List[str]] = None  # 图片列表（支持 data URL 或 URL）
    videos: Optional[List[str]] = None  # 视频列表（支持 URL，参考 Qwen3-VL 格式）
    user_id: Optional[str] = None  # 用户ID，用于存储聊天记录
    conversation_id: Optional[str] = None  # 会话ID，用于关联多轮对话
    use_qwen_format: Optional[bool] = None  # 是否使用 Qwen3-VL 格式（None 时自动检测）


class ChatQueryRequest(BaseModel):
    query: str  # 搜索关键词
    user_id: Optional[str] = None
    limit: int = 10


class ChatUpdateRequest(BaseModel):
    messages: List[dict]
    metadata: Optional[dict] = None


def build_qwen_vl_message(
    text: str,
    images: Optional[List[str]] = None,
    videos: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    构建 Qwen3-VL 格式的消息内容
    
    Qwen3-VL 格式示例：
    [
        {"type": "image", "image": "https://..."},
        {"type": "video", "video": "https://..."},
        {"type": "text", "text": "用户消息"}
    ]
    """
    content = []
    
    # 添加图片
    if images:
        for img in images:
            content.append({
                "type": "image",
                "image": img
            })
    
    # 添加视频
    if videos:
        for video in videos:
            content.append({
                "type": "video",
                "video": video
            })
    
    # 添加文本（如果有）
    if text:
        content.append({
            "type": "text",
            "text": text
        })
    
    return content


def normalize_image_url(img: str) -> str:
    """规范化图片 URL，支持 data URL 和普通 URL"""
    if img.startswith('data:'):
        return img
    elif img.startswith('http://') or img.startswith('https://'):
        return img
    else:
        # 假设是 base64 字符串
        return img


async def validate_image_url(img_url: str, timeout: int = 5) -> bool:
    """
    验证图片 URL 是否可访问
    
    Args:
        img_url: 图片 URL
        timeout: 超时时间（秒）
    
    Returns:
        True 如果 URL 可访问，False 否则
    """
    # data URL 和 base64 字符串不需要验证
    if img_url.startswith('data:') or not (img_url.startswith('http://') or img_url.startswith('https://')):
        return True
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(img_url, timeout=aiohttp.ClientTimeout(total=timeout), allow_redirects=True) as response:
                # 检查状态码，200-299 表示成功
                return 200 <= response.status < 300
    except Exception as e:
        logger.warning(f"验证图片 URL 失败: {img_url}, 错误: {str(e)}")
        return False


async def download_image_to_base64(img_url: str, timeout: int = 10) -> Optional[str]:
    """
    下载 http/https 图片并转换为 base64 字符串
    
    Args:
        img_url: 图片 URL
        timeout: 超时时间（秒）
    
    Returns:
        base64 编码的图片数据（不含 data: 前缀），如果下载失败则返回 None
    """
    if not (img_url.startswith('http://') or img_url.startswith('https://')):
        return None
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=timeout), allow_redirects=True) as response:
                if response.status != 200:
                    logger.warning(f"下载图片失败，状态码: {response.status}, URL: {img_url}")
                    return None
                
                # 读取图片数据
                image_data = await response.read()
                
                # 转换为 base64
                base64_data = base64.b64encode(image_data).decode('utf-8')
                logger.info(f"成功下载并转换图片为 base64: {img_url} (大小: {len(image_data)} 字节)")
                return base64_data
    except Exception as e:
        logger.warning(f"下载图片失败: {img_url}, 错误: {str(e)}")
        return None


async def convert_image_to_base64(img: str) -> Optional[str]:
    """
    将图片转换为 base64 格式
    
    Args:
        img: 图片数据，可以是 data URL、http/https URL 或 base64 字符串
    
    Returns:
        base64 编码的图片数据（不含 data: 前缀），如果转换失败则返回 None
    """
    # 如果是 data URL，提取 base64 部分
    if img.startswith('data:'):
        if ',' in img:
            base64_data = img.split(',', 1)[1]
            return base64_data
        else:
            return None
    
    # 如果是 http/https URL，下载并转换为 base64
    if img.startswith('http://') or img.startswith('https://'):
        return await download_image_to_base64(img)
    
    # 如果已经是 base64 字符串（不含 data: 前缀），直接返回
    return img


async def filter_valid_images(images: List[str]) -> List[str]:
    """
    过滤出可访问的图片 URL
    
    Args:
        images: 图片 URL 列表
    
    Returns:
        可访问的图片 URL 列表
    """
    if not images:
        return []
    
    valid_images = []
    for img in images:
        if await validate_image_url(img):
            valid_images.append(img)
        else:
            logger.warning(f"图片 URL 不可访问，已跳过: {img}")
    
    if len(valid_images) < len(images):
        logger.info(f"过滤图片: {len(images)} -> {len(valid_images)} (移除了 {len(images) - len(valid_images)} 个不可访问的图片)")
    
    return valid_images


async def clean_messages_images(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    清理消息列表中的所有无效图片 URL
    
    Args:
        messages: 消息列表
    
    Returns:
        清理后的消息列表
    """
    cleaned_messages = []
    
    for msg in messages:
        cleaned_msg = msg.copy()
        content = cleaned_msg.get("content", "")
        images = cleaned_msg.get("images", [])
        
        # 处理 content 字段中的图片（Qwen3-VL 格式）
        if isinstance(content, list):
            cleaned_content = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "image":
                    img_url = item.get("image", "")
                    # 如果是 http/https URL，转换为 base64
                    if img_url.startswith('http://') or img_url.startswith('https://'):
                        if await validate_image_url(img_url):
                            # 转换为 base64
                            base64_data = await convert_image_to_base64(img_url)
                            if base64_data:
                                # 更新为 base64 数据（保持 Qwen3-VL 格式，但使用 base64）
                                cleaned_item = item.copy()
                                cleaned_item["image"] = base64_data
                                cleaned_content.append(cleaned_item)
                            else:
                                logger.warning(f"清理消息时无法转换图片 URL 为 base64，已跳过: {img_url}")
                        else:
                            logger.warning(f"清理消息时发现无效图片 URL，已跳过: {img_url}")
                    else:
                        # 非 URL 图片（data URL 或 base64），直接保留
                        cleaned_content.append(item)
                else:
                    cleaned_content.append(item)
            cleaned_msg["content"] = cleaned_content
        
        # 处理独立的 images 字段（Ollama 格式）
        if images:
            valid_images = []
            for img in images:
                # 如果是 http/https URL，转换为 base64
                if img.startswith('http://') or img.startswith('https://'):
                    # 验证 URL 是否可访问
                    if await validate_image_url(img):
                        # 转换为 base64
                        base64_data = await convert_image_to_base64(img)
                        if base64_data:
                            valid_images.append(base64_data)
                        else:
                            logger.warning(f"清理消息时无法转换图片 URL 为 base64，已跳过: {img}")
                    else:
                        logger.warning(f"清理消息时发现无效图片 URL，已跳过: {img}")
                else:
                    # base64 字符串和 data URL 直接保留
                    valid_images.append(img)
            
            if valid_images:
                cleaned_msg["images"] = valid_images
            else:
                # 如果没有有效图片，移除 images 字段
                cleaned_msg.pop("images", None)
        
        cleaned_messages.append(cleaned_msg)
    
    return cleaned_messages


def convert_to_qwen_vl_messages(
    messages: List[Dict[str, Any]],
    is_multimodal: bool = False
) -> List[Dict[str, Any]]:
    """
    将消息转换为 Qwen3-VL 格式
    
    Qwen3-VL 格式：
    [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": "..."},
                {"type": "text", "text": "..."}
            ]
        }
    ]
    """
    qwen_messages = []
    
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        images = msg.get("images", [])
        
        # 如果已经是 Qwen3-VL 格式（content 是列表）
        if isinstance(content, list):
            qwen_messages.append({
                "role": role,
                "content": content
            })
        else:
            # 转换为 Qwen3-VL 格式
            qwen_content = build_qwen_vl_message(
                text=str(content) if content else "",
                images=[normalize_image_url(img) for img in images] if images else None
            )
            
            qwen_messages.append({
                "role": role,
                "content": qwen_content
            })
    
    return qwen_messages


async def convert_to_ollama_messages(
    messages: List[Dict[str, Any]],
    is_multimodal: bool = False
) -> List[Dict[str, Any]]:
    """
    将消息转换为 Ollama 格式
    
    Ollama 格式：
    [
        {
            "role": "user",
            "content": "文本内容",
            "images": ["base64..."]  # 仅 base64，不含 data: 前缀
        }
    ]
    """
    ollama_messages = []
    
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        images = msg.get("images", [])
        
        # 如果 content 是 Qwen3-VL 格式（列表），需要转换
        if isinstance(content, list):
            text_parts = []
            images_base64 = []
            
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "image":
                        img_data = item.get("image", "")
                        # 转换为 base64（如果是 http/https URL，会下载并转换）
                        base64_data = await convert_image_to_base64(img_data)
                        if base64_data:
                            images_base64.append(base64_data)
                        else:
                            logger.warning(f"无法转换图片为 base64，已跳过: {img_data}")
                elif isinstance(item, str):
                    text_parts.append(item)
            
            ollama_msg = {
                "role": role,
                "content": " ".join(text_parts) if text_parts else ""
            }
            
            if images_base64 and is_multimodal:
                ollama_msg["images"] = images_base64
            
            ollama_messages.append(ollama_msg)
        else:
            # 已经是 Ollama 格式或纯文本
            ollama_msg = {
                "role": role,
                "content": str(content) if content else ""
            }
            
            if images and is_multimodal:
                # 转换为 base64（如果是 http/https URL，会下载并转换）
                images_base64 = []
                for img in images:
                    base64_data = await convert_image_to_base64(img)
                    if base64_data:
                        images_base64.append(base64_data)
                    else:
                        logger.warning(f"无法转换图片为 base64，已跳过: {img}")
                
                if images_base64:
                    ollama_msg["images"] = images_base64
            
            ollama_messages.append(ollama_msg)
    
    return ollama_messages


async def stream_ollama_response(request: ContentRequest, chat_service: ChatService, http_request: Request):
    """生成流式响应，并保存聊天记录"""
    assistant_content = ""
    conversation_id = request.conversation_id
    
    # 规范化 conversation_id：如果是 URL 格式，则进行 MD5 处理
    if conversation_id:
        conversation_id = normalize_session_id(conversation_id)
    
    # 获取用户ID（从参数、X-User 或默认值）
    user_id = get_user_id(http_request, request.user_id, default="bigboom")
    
    try:
        # 初始化聊天服务
        await chat_service.initialize()
        
        # 创建Ollama客户端
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        # 检测多模态输入
        has_images = request.images and len(request.images) > 0
        has_videos = request.videos and len(request.videos) > 0
        has_multimodal = has_images or has_videos
        
        # 如果请求中包含图片/视频且未指定模型，则默认使用 qwen3-vl 模型
        # 如果用户明确指定了模型，则使用用户指定的模型
        if has_multimodal:
            if request.model:
                model_name = request.model
                logger.info(f"检测到多模态输入，使用用户指定的模型: {model_name} (图片: {len(request.images) if request.images else 0}, 视频: {len(request.videos) if request.videos else 0})")
            else:
                model_name = "qwen3-vl"
                logger.info(f"检测到多模态输入，默认使用 qwen3-vl 模型 (图片: {len(request.images) if request.images else 0}, 视频: {len(request.videos) if request.videos else 0})")
        else:
            model_name = request.model if request.model else "deepseek-r1:32b"
            logger.info(f"使用模型: {model_name}")
        
        # 判断模型是否支持多模态
        is_multimodal = "-vl" in model_name.lower() or "vision" in model_name.lower() or has_multimodal
        
        # 决定是否使用 Qwen3-VL 格式
        # 如果明确指定或检测到多模态且 qwen-vl-utils 可用，使用 Qwen3-VL 格式
        use_qwen_format = request.use_qwen_format
        if use_qwen_format is None:
            use_qwen_format = (has_multimodal and QWEN_VL_AVAILABLE) or model_name.startswith("qwen")
        
        # 获取认证信息
        ollama_auth = os.getenv("OLLAMA_AUTH", "")
        
        # 配置客户端
        if ollama_auth:
            if ':' in ollama_auth:
                username, password = ollama_auth.split(':', 1)
            else:
                username = ollama_auth
                password = ""
            client = Client(host=ollama_url, auth=(username, password))
        else:
            client = Client(host=ollama_url)
        
        # 使用系统提示
        enhanced_system_prompt = request.fromSystem
        
        # 验证并过滤当前请求中的图片
        valid_images = []
        if request.images:
            valid_images = await filter_valid_images(request.images)
            if len(valid_images) < len(request.images):
                logger.warning(f"当前请求中有 {len(request.images) - len(valid_images)} 个图片 URL 不可访问")
        
        # 准备当前用户消息
        if use_qwen_format:
            # 使用 Qwen3-VL 格式
            user_content = build_qwen_vl_message(
                text=request.fromUser if request.fromUser else "",
                images=valid_images if valid_images else None,
                videos=request.videos
            )
            current_user_message = {
                "role": "user",
                "content": user_content
            }
        else:
            # 使用 Ollama 格式
            user_content = request.fromUser if request.fromUser else ""
            current_user_message = {
                "role": "user",
                "content": user_content
            }
            if valid_images and is_multimodal:
                # 转换为 base64（如果是 http/https URL，会下载并转换）
                images_base64 = []
                for img in valid_images:
                    base64_data = await convert_image_to_base64(img)
                    if base64_data:
                        images_base64.append(base64_data)
                    else:
                        logger.warning(f"无法转换图片为 base64，已跳过: {img}")
                
                if images_base64:
                    current_user_message["images"] = images_base64
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": enhanced_system_prompt},
            current_user_message
        ]
        
        # 如果有会话ID，获取历史消息构建完整的对话上下文
        if conversation_id and user_id:
            try:
                # 获取会话的所有历史消息（限制最多 20 条记录，每条记录包含一对消息）
                history_chats = await chat_service.get_chats_by_conversation(
                    conversation_id=conversation_id,
                    limit=20
                )
                
                # 将历史消息添加到 messages 中（按时间正序，最新的在前面）
                history_messages = []
                for chat in reversed(history_chats):
                    chat_messages = chat.get("messages", [])
                    if chat_messages:
                        # 规范化历史消息的 content 格式
                        for msg in chat_messages:
                            # 确保消息格式正确
                            normalized_msg = {"role": msg.get("role", "user")}
                            msg_content = msg.get("content", "")
                            
                            # 根据消息格式处理
                            if isinstance(msg_content, list):
                                # 已经是 Qwen3-VL 格式（列表）
                                if use_qwen_format:
                                    # 验证并过滤图片 URL
                                    filtered_content = []
                                    for item in msg_content:
                                        if isinstance(item, dict) and item.get("type") == "image":
                                            img_url = item.get("image", "")
                                            if await validate_image_url(img_url):
                                                filtered_content.append(item)
                                            else:
                                                logger.warning(f"历史消息中的图片 URL 不可访问，已跳过: {img_url}")
                                        else:
                                            filtered_content.append(item)
                                    normalized_msg["content"] = filtered_content
                                else:
                                    # 转换为 Ollama 格式
                                    text_parts = []
                                    images_base64 = []
                                    for item in msg_content:
                                        if isinstance(item, dict):
                                            if item.get("type") == "text":
                                                text_parts.append(item.get("text", ""))
                                            elif item.get("type") == "image":
                                                img_data = item.get("image", "")
                                                # 验证图片 URL（仅对 http/https URL 进行验证）
                                                if img_data.startswith('http://') or img_data.startswith('https://'):
                                                    if not await validate_image_url(img_data):
                                                        logger.warning(f"历史消息中的图片 URL 不可访问，已跳过: {img_data}")
                                                        continue
                                                # 转换为 base64（如果是 http/https URL，会下载并转换）
                                                base64_data = await convert_image_to_base64(img_data)
                                                if base64_data:
                                                    images_base64.append(base64_data)
                                                else:
                                                    logger.warning(f"无法转换历史消息中的图片为 base64，已跳过: {img_data}")
                                        elif isinstance(item, str):
                                            text_parts.append(item)
                                    normalized_msg["content"] = " ".join(text_parts) if text_parts else ""
                                    if images_base64 and is_multimodal:
                                        normalized_msg["images"] = images_base64
                            elif isinstance(msg_content, str):
                                # 字符串格式
                                normalized_msg["content"] = msg_content
                                # 检查是否有单独的 images 字段
                                if "images" in msg:
                                    # 验证并过滤图片
                                    msg_images = msg.get("images", [])
                                    valid_msg_images = await filter_valid_images(msg_images)
                                    if use_qwen_format:
                                        # 转换为 Qwen3-VL 格式
                                        content_list = build_qwen_vl_message(
                                            text=msg_content,
                                            images=valid_msg_images if valid_msg_images else None
                                        )
                                        normalized_msg["content"] = content_list
                                    else:
                                        # 转换为 base64（如果是 http/https URL，会下载并转换）
                                        images_base64 = []
                                        for img in valid_msg_images:
                                            base64_data = await convert_image_to_base64(img)
                                            if base64_data:
                                                images_base64.append(base64_data)
                                            else:
                                                logger.warning(f"无法转换历史消息中的图片为 base64，已跳过: {img}")
                                        
                                        if images_base64:
                                            normalized_msg["images"] = images_base64
                            else:
                                # 其他类型，转换为字符串
                                normalized_msg["content"] = str(msg_content) if msg_content else ""
                            
                            history_messages.append(normalized_msg)
                
                # 如果历史消息过多，只保留最近的（保留最后 30 条消息，约 15 轮对话）
                if len(history_messages) > 30:
                    history_messages = history_messages[-30:]
                    logger.info(f"会话 {conversation_id} 历史消息过多，仅保留最近 30 条")
                
                # 构建完整的消息列表：历史消息 + 当前系统提示 + 当前用户消息
                if history_messages:
                    messages = history_messages.copy()
                    # 在历史消息后添加当前的系统提示和用户消息
                    messages.append({"role": "system", "content": enhanced_system_prompt})
                    messages.append(current_user_message)
                    logger.info(f"已加载会话 {conversation_id} 的 {len(history_messages)} 条历史消息")
                else:
                    logger.debug(f"会话 {conversation_id} 暂无历史消息")
            except Exception as e:
                logger.warning(f"获取历史消息失败: {str(e)}")
        
        # 如果使用 Qwen3-VL 格式但需要转换为 Ollama 格式（因为 Ollama 可能不支持 Qwen3-VL 格式）
        # 注意：这里我们假设 Ollama 支持 Qwen3-VL 格式，如果不支持，需要转换
        # 为了兼容性，如果检测到使用 Qwen3-VL 格式，我们仍然转换为 Ollama 格式发送
        if use_qwen_format:
            # 对于 Ollama，我们需要将 Qwen3-VL 格式转换为 Ollama 格式
            # 注意：convert_to_ollama_messages 现在是异步函数，需要 await
            messages = await convert_to_ollama_messages(messages, is_multimodal)
        
        # 在发送给 Ollama 之前，最后清理一次所有消息中的无效图片 URL
        # 这确保即使之前的验证有遗漏，也不会导致 Ollama 调用失败
        messages = await clean_messages_images(messages)
        
        # 调用Ollama流式API
        try:
            stream = client.chat(
                model=model_name, 
                messages=messages,
                stream=True
            )
            
            # 流式返回响应
            for chunk in stream:
                # 转换 chunk 为字典
                if hasattr(chunk, 'model_dump'):
                    chunk_dict = chunk.model_dump()
                elif hasattr(chunk, 'dict'):
                    chunk_dict = chunk.dict()
                elif hasattr(chunk, '__dict__'):
                    chunk_dict = chunk.__dict__
                else:
                    chunk_dict = {
                        'message': chunk.message.dict() if hasattr(chunk.message, 'dict') else str(chunk.message),
                        'done': chunk.done if hasattr(chunk, 'done') else False,
                        'total_duration': getattr(chunk, 'total_duration', None),
                        'load_duration': getattr(chunk, 'load_duration', None),
                        'prompt_eval_count': getattr(chunk, 'prompt_eval_count', None),
                        'prompt_eval_duration': getattr(chunk, 'prompt_eval_duration', None),
                        'eval_count': getattr(chunk, 'eval_count', None),
                        'eval_duration': getattr(chunk, 'eval_duration', None)
                    }
                
                # 累积助手回复内容
                if chunk_dict.get('message') and chunk_dict['message'].get('content'):
                    assistant_content += chunk_dict['message']['content']
                
                chunk_data = json.dumps(chunk_dict, ensure_ascii=False)
                yield f"data: {chunk_data}\n\n"
        except Exception as e:
            logger.error(f"Ollama调用失败: {str(e)}")
            error_data = json.dumps({
                "type": "error",
                "data": f"AI服务调用失败: {str(e)}"
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
            
    except Exception as e:
        logger.error(f"流式处理错误: {str(e)}", exc_info=True)
        error_data = json.dumps({
            "type": "error",
            "data": f"处理失败: {str(e)}"
        }, ensure_ascii=False)
        yield f"data: {error_data}\n\n"


@router.post("/")
async def generate_role_ai_json(request: ContentRequest, http_request: Request):
    """处理 /prompt/ 路由，支持流式响应和聊天记录存储
    
    所有参数都是可选的，如果未提供将使用默认值：
    - fromSystem: 默认 "你是一个有用的AI助手。"
    - fromUser: 默认为空字符串（如果为空，可能无法正常对话）
    - model: 默认使用 "deepseek-r1:32b"；如果请求中包含图片/视频且未指定模型，则默认使用 "qwen3-vl"
    - images: 默认为 None，支持图片URL列表或 data URL（如果提供图片，会自动使用 qwen3-vl 模型）
    - videos: 默认为 None，支持视频URL列表（参考 Qwen3-VL 格式）
    - user_id: 默认从 X-User 请求头获取，或使用 "bigboom"
    - conversation_id: 默认为 None，会自动生成新的会话ID
    - use_qwen_format: 是否使用 Qwen3-VL 格式（None 时自动检测，如果检测到多模态且 qwen-vl-utils 可用则使用）
    
    消息格式：
    - Qwen3-VL 格式（当 use_qwen_format=True 时）：
      {
        "role": "user",
        "content": [
          {"type": "image", "image": "https://..."},
          {"type": "video", "video": "https://..."},
          {"type": "text", "text": "用户消息"}
        ]
      }
    - Ollama 格式（默认）：
      {
        "role": "user",
        "content": "用户消息",
        "images": ["base64..."]
      }
    """
    # 确保 fromSystem 和 fromUser 有默认值
    if not request.fromSystem:
        request.fromSystem = "你是一个有用的AI助手。"
    if request.fromUser is None:
        request.fromUser = ""
    
    return StreamingResponse(
        stream_ollama_response(request, chat_service, http_request),
        media_type="text/event-stream"
    )


@router.post("/save")
async def save_chat(
    http_request: Request,
    user_id: Optional[str] = None,
    messages: List[dict] = None,
    conversation_id: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """保存聊天记录"""
    try:
        user_id = get_user_id(http_request, user_id, default="bigboom")
        messages = messages or []
        
        if not messages:
            raise HTTPException(status_code=400, detail="消息列表不能为空")
        
        # 如果没有 conversation_id，创建新的会话
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # 规范化 conversation_id：如果是 URL 格式，则进行 MD5 处理
        conversation_id = normalize_session_id(conversation_id)
        
        # 使用聊天服务保存记录
        await chat_service.initialize()
        result = await chat_service.save_chat(
            user_id=user_id,
            conversation_id=conversation_id,
            messages=messages,
            metadata=metadata
        )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存聊天记录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{doc_id}")
async def get_chat(doc_id: str):
    """根据ID获取聊天记录"""
    try:
        await chat_service.initialize()
        chat = await chat_service.get_chat_by_id(doc_id)
        if not chat:
            raise HTTPException(status_code=404, detail="聊天记录未找到")
        return JSONResponse(content=chat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/conversation/{conversation_id}")
async def get_chats_by_conversation(
    conversation_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    skip: int = Query(default=0, ge=0)
):
    """根据会话ID获取所有聊天记录"""
    try:
        # 规范化 conversation_id：如果是 URL 格式，则进行 MD5 处理
        conversation_id = normalize_session_id(conversation_id)
        
        await chat_service.initialize()
        chats = await chat_service.get_chats_by_conversation(
            conversation_id=conversation_id,
            limit=limit,
            skip=skip
        )
        return JSONResponse(content={
            "conversation_id": conversation_id,
            "count": len(chats),
            "chats": chats
        })
    except Exception as e:
        logger.error(f"获取会话聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/user/{user_id}")
async def get_chats_by_user(
    user_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    skip: int = Query(default=0, ge=0)
):
    """根据用户ID获取所有聊天记录"""
    try:
        await chat_service.initialize()
        chats = await chat_service.get_chats_by_user(
            user_id=user_id,
            limit=limit,
            skip=skip
        )
        return JSONResponse(content={
            "user_id": user_id,
            "count": len(chats),
            "chats": chats
        })
    except Exception as e:
        logger.error(f"获取用户聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/search")
async def search_chats(request: ChatQueryRequest, http_request: Request):
    """语义搜索聊天记录"""
    try:
        await chat_service.initialize()
        user_id = get_user_id(http_request, request.user_id, default="bigboom")
        results = await chat_service.search_chats(
            query=request.query,
            user_id=user_id,
            limit=request.limit
        )
        return JSONResponse(content={
            "query": request.query,
            "count": len(results),
            "results": results
        })
    except Exception as e:
        logger.error(f"搜索聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/chat/{doc_id}")
async def update_chat(
    doc_id: str,
    request: ChatUpdateRequest
):
    """更新聊天记录"""
    try:
        await chat_service.initialize()
        success = await chat_service.update_chat(
            doc_id=doc_id,
            messages=request.messages,
            metadata=request.metadata
        )
        if not success:
            raise HTTPException(status_code=404, detail="聊天记录未找到或更新失败")
        return JSONResponse(content={"success": True, "doc_id": doc_id})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/{doc_id}")
async def delete_chat(doc_id: str):
    """删除聊天记录"""
    try:
        await chat_service.initialize()
        success = await chat_service.delete_chat(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="聊天记录未找到或删除失败")
        return JSONResponse(content={"success": True, "doc_id": doc_id})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """删除整个会话的所有聊天记录"""
    try:
        # 规范化 conversation_id：如果是 URL 格式，则进行 MD5 处理
        conversation_id = normalize_session_id(conversation_id)
        
        await chat_service.initialize()
        deleted_count = await chat_service.delete_conversation(conversation_id)
        return JSONResponse(content={
            "success": True,
            "conversation_id": conversation_id,
            "deleted_count": deleted_count
        })
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_service_status():
    """获取服务状态"""
    try:
        await chat_service.initialize()
        return JSONResponse(content={
            "success": True,
            "message": "服务正常运行",
            "qwen_vl_available": QWEN_VL_AVAILABLE
        })
    except Exception as e:
        logger.error(f"获取服务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取服务状态失败: {str(e)}")

