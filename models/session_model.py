"""会话数据模型 - 统一前后端会话数据格式"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SessionMessage(BaseModel):
    """会话消息模型"""
    role: str = Field(..., description="消息角色: user, assistant, system")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[int] = Field(None, description="消息时间戳")


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
    isFavorite: Optional[bool] = Field(False, description="是否收藏")
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
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "你好！有什么可以帮助你的？"}
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
    isFavorite: Optional[bool] = Field(False, description="是否收藏")
    createdAt: Optional[int] = Field(None, description="创建时间戳(毫秒)")
    updatedAt: Optional[int] = Field(None, description="更新时间戳(毫秒)")
    lastAccessTime: Optional[int] = Field(None, description="最后访问时间戳(毫秒)")


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
        "messages": session_doc.get("messages", []),
        "tags": session_doc.get("tags", []),
        "isFavorite": session_doc.get("isFavorite", False),
        "createdAt": session_doc.get("createdAt"),
        "updatedAt": session_doc.get("updatedAt"),
        "lastAccessTime": session_doc.get("lastAccessTime")
    }
    
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



