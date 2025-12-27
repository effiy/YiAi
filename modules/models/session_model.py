"""会话数据模型 - 统一前后端会话数据格式"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SessionMessage(BaseModel):
    """会话消息模型 - 统一格式，兼容会话消息和评论消息"""
    type: str = Field(..., description="消息类型: 'user' 或 'pet' (assistant)")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[int] = Field(None, description="消息时间戳(毫秒)")
    imageDataUrl: Optional[str] = Field(None, description="图片数据URL(可选)")
    
    # 兼容字段：role 映射到 type
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMessage":
        """从字典创建消息对象，支持多种字段格式"""
        normalized = {}
        
        # 统一 type 字段
        if "type" in data:
            normalized["type"] = data["type"]
        elif "role" in data:
            role = data["role"]
            if role in ["user", "me"]:
                normalized["type"] = "user"
            elif role in ["assistant", "pet", "bot", "ai"]:
                normalized["type"] = "pet"
            else:
                normalized["type"] = "user"  # 默认
        else:
            # 根据 author 判断
            author = str(data.get("author", "")).lower()
            if "ai" in author or "助手" in author or "assistant" in author:
                normalized["type"] = "pet"
            else:
                normalized["type"] = "user"
        
        # 统一 content 字段
        normalized["content"] = str(data.get("content") or data.get("text") or data.get("message") or "").strip()
        
        # 统一 timestamp 字段（转换为毫秒数）
        timestamp = data.get("timestamp") or data.get("createdTime") or data.get("createdAt") or data.get("ts")
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    normalized["timestamp"] = int(dt.timestamp() * 1000)
                except:
                    normalized["timestamp"] = int(datetime.now().timestamp() * 1000)
            elif isinstance(timestamp, (int, float)):
                # 如果是秒级时间戳，转换为毫秒
                if timestamp < 1e12:
                    normalized["timestamp"] = int(timestamp * 1000)
                else:
                    normalized["timestamp"] = int(timestamp)
            else:
                normalized["timestamp"] = int(datetime.now().timestamp() * 1000)
        else:
            normalized["timestamp"] = None
        
        # 统一 imageDataUrl 字段
        normalized["imageDataUrl"] = data.get("imageDataUrl") or data.get("image") or None
        
        return cls(**normalized)


class SessionData(BaseModel):
    """会话数据模型 - 用于前后端交互"""
    id: str = Field(..., description="会话ID")
    url: Optional[str] = Field(None, description="页面URL")
    title: Optional[str] = Field(None, description="会话标题")
    pageTitle: Optional[str] = Field(None, description="页面标题")
    pageDescription: Optional[str] = Field(None, description="页面描述")
    pageContent: Optional[str] = Field(None, description="页面内容")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="消息列表")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    createdAt: Optional[int] = Field(None, description="创建时间戳(毫秒)")
    updatedAt: Optional[int] = Field(None, description="更新时间戳(毫秒)")
    lastAccessTime: Optional[int] = Field(None, description="最后访问时间戳(毫秒)")
    user_id: Optional[str] = Field(None, description="用户ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "session_123456",
                "url": "https://example.com/page",
                "title": "示例会话",
                "pageTitle": "示例页面",
                "pageDescription": "这是一个示例页面",
                "pageContent": "页面内容...",
                "messages": [
                    {"type": "user", "content": "你好", "timestamp": 1699123456789},
                    {"type": "pet", "content": "你好！有什么可以帮助你的？", "timestamp": 1699123456790}
                ],
                "tags": ["重要", "工作"],
                "createdAt": 1699123456789,
                "updatedAt": 1699123456789,
                "lastAccessTime": 1699123456789,
                "user_id": "user_123"
            }
        }


class SessionListItem(BaseModel):
    """会话列表项模型（用于列表展示，不包含完整消息）"""
    id: str = Field(..., description="会话ID")
    url: Optional[str] = Field(None, description="页面URL")
    title: Optional[str] = Field(None, description="会话标题")
    pageTitle: Optional[str] = Field(None, description="页面标题")
    message_count: int = Field(0, description="消息数量")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    createdAt: Optional[int] = Field(None, description="创建时间戳(毫秒)")
    updatedAt: Optional[int] = Field(None, description="更新时间戳(毫秒)")
    lastAccessTime: Optional[int] = Field(None, description="最后访问时间戳(毫秒)")


def normalize_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    规范化消息格式，统一字段名
    
    Args:
        message: 原始消息数据（可能包含 role/type, content/text, timestamp/createdTime 等）
        
    Returns:
        规范化后的消息数据（统一使用 type, content, timestamp, imageDataUrl）
    """
    normalized = {}
    
    # 统一 type 字段
    if "type" in message:
        normalized["type"] = message["type"]
    elif "role" in message:
        role = str(message["role"]).lower()
        if role in ["user", "me"]:
            normalized["type"] = "user"
        elif role in ["assistant", "pet", "bot", "ai"]:
            normalized["type"] = "pet"
        else:
            normalized["type"] = "user"  # 默认
    else:
        # 根据 author 判断
        author = str(message.get("author", "")).lower()
        if "ai" in author or "助手" in author or "assistant" in author:
            normalized["type"] = "pet"
        else:
            normalized["type"] = "user"
    
    # 统一 content 字段
    normalized["content"] = str(message.get("content") or message.get("text") or message.get("message") or "").strip()
    
    # 统一 timestamp 字段（转换为毫秒数）
    timestamp = message.get("timestamp") or message.get("createdTime") or message.get("createdAt") or message.get("ts")
    if timestamp:
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                normalized["timestamp"] = int(dt.timestamp() * 1000)
            except:
                normalized["timestamp"] = int(datetime.now().timestamp() * 1000)
        elif isinstance(timestamp, (int, float)):
            # 如果是秒级时间戳，转换为毫秒
            if timestamp < 1e12:
                normalized["timestamp"] = int(timestamp * 1000)
            else:
                normalized["timestamp"] = int(timestamp)
        else:
            normalized["timestamp"] = int(datetime.now().timestamp() * 1000)
    else:
        normalized["timestamp"] = int(datetime.now().timestamp() * 1000)
    
    # 统一 imageDataUrl 字段
    image_data = message.get("imageDataUrl") or message.get("image")
    if image_data:
        normalized["imageDataUrl"] = image_data
    
    return normalized


def session_to_api_format(session_doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    将数据库文档转换为API响应格式
    
    Args:
        session_doc: MongoDB文档
        
    Returns:
        API格式的会话数据
    """
    result = {
        "id": session_doc.get("key") or session_doc.get("_id"),
        "url": session_doc.get("url", ""),
        "title": session_doc.get("title", ""),
        "pageTitle": session_doc.get("pageTitle", ""),
        "pageDescription": session_doc.get("pageDescription", ""),
        "pageContent": session_doc.get("pageContent", ""),
        "messages": [],
        "tags": session_doc.get("tags", []),
        "isFavorite": session_doc.get("isFavorite", False),
        "createdAt": session_doc.get("createdAt"),
        "updatedAt": session_doc.get("updatedAt"),
        "lastAccessTime": session_doc.get("lastAccessTime")
    }
    
    # 规范化消息列表
    messages = session_doc.get("messages", [])
    if messages:
        result["messages"] = [normalize_message(msg) for msg in messages if msg]
    
    # 添加 imageDataUrl 字段（如果存在）
    if "imageDataUrl" in session_doc:
        result["imageDataUrl"] = session_doc.get("imageDataUrl")
    
    return result


def session_to_list_item(session_doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    将数据库文档转换为列表项格式（用于列表展示）
    
    Args:
        session_doc: MongoDB文档
        
    Returns:
        列表项格式的会话数据（与前端期望的格式一致）
    """
    messages = session_doc.get("messages", [])
    return {
        "id": session_doc.get("key") or session_doc.get("_id"),
        "url": session_doc.get("url", ""),
        "title": session_doc.get("title", ""),
        "pageTitle": session_doc.get("pageTitle", ""),
        "pageDescription": session_doc.get("pageDescription", ""),
        "message_count": len(messages),
        "tags": session_doc.get("tags", []),
        "isFavorite": session_doc.get("isFavorite", False),
        # 为了兼容前端，也提供 messages 字段（但为空数组，避免列表接口返回大量数据）
        # 前端如需完整消息，应调用单个会话接口
        "messages": [],  # 列表项不包含完整消息，减少数据传输
        "createdAt": session_doc.get("createdAt"),
        "updatedAt": session_doc.get("updatedAt"),
        "lastAccessTime": session_doc.get("lastAccessTime")
    }




