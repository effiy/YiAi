import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from modules.services.chatService import ChatService

logger = logging.getLogger(__name__)

class SessionService:
    """会话管理服务 - 对接YiPet的会话管理"""
    
    def __init__(self):
        self.chat_service = ChatService()
        self.collection_name = "pet_sessions"
        
    async def initialize(self):
        """初始化服务"""
        await self.chat_service.initialize()
    
    def _convert_messages_format(self, pet_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将YiPet的消息格式转换为ChatService的格式
        
        YiPet格式: [{"type": "user", "content": "...", "timestamp": ...}, ...]
        ChatService格式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        chat_messages = []
        current_pair = None
        
        for msg in pet_messages:
            msg_type = msg.get("type", "")
            content = msg.get("content", "").strip()
            
            if not content:
                continue
            
            if msg_type == "user":
                # 如果已经有未配对的用户消息，先保存它
                if current_pair and current_pair.get("role") == "user":
                    chat_messages.append(current_pair)
                current_pair = {"role": "user", "content": content}
            elif msg_type == "pet":
                # pet消息对应assistant角色
                if current_pair and current_pair.get("role") == "user":
                    # 配对：用户消息 + 助手回复
                    chat_messages.append(current_pair)
                    chat_messages.append({"role": "assistant", "content": content})
                    current_pair = None
                else:
                    # 单独的助手消息（可能是欢迎消息等）
                    chat_messages.append({"role": "assistant", "content": content})
        
        # 如果还有未配对的用户消息，添加它
        if current_pair and current_pair.get("role") == "user":
            chat_messages.append(current_pair)
        
        return chat_messages
    
    async def save_session(
        self,
        session_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        保存YiPet会话数据到后端
        
        Args:
            session_data: YiPet会话数据，包含：
                - id: 会话ID
                - url: 页面URL
                - title: 会话标题
                - messages: 消息列表
                - pageContent: 页面内容
                - createdAt: 创建时间
                - updatedAt: 更新时间
            user_id: 用户ID（可选，如果不提供则使用session_id）
        
        Returns:
            保存结果，包含session_id和success状态
        """
        try:
            session_id = session_data.get("id")
            if not session_id:
                session_id = str(uuid.uuid4())
                session_data["id"] = session_id
            
            # 使用session_id作为user_id（如果没有提供user_id）
            if not user_id:
                user_id = f"pet_user_{session_id[:16]}"
            
            # 转换消息格式
            pet_messages = session_data.get("messages", [])
            chat_messages = self._convert_messages_format(pet_messages)
            
            if not chat_messages:
                logger.debug(f"会话 {session_id} 没有有效消息，跳过保存")
                return {
                    "session_id": session_id,
                    "success": True,
                    "message": "会话无有效消息，已跳过"
                }
            
            # 构建元数据
            metadata = {
                "session_id": session_id,
                "url": session_data.get("url", ""),
                "title": session_data.get("title", ""),
                "pageTitle": session_data.get("pageTitle", ""),
                "pageDescription": session_data.get("pageDescription", ""),
                "createdAt": session_data.get("createdAt"),
                "updatedAt": session_data.get("updatedAt"),
                "lastAccessTime": session_data.get("lastAccessTime")
            }
            
            # 保存到ChatService（使用conversation_id作为session_id）
            result = await self.chat_service.save_chat(
                user_id=user_id,
                conversation_id=session_id,
                messages=chat_messages,
                metadata=metadata
            )
            
            logger.info(f"会话 {session_id} 已保存到后端，包含 {len(chat_messages)} 条消息")
            
            return {
                "session_id": session_id,
                "conversation_id": result.get("conversation_id"),
                "doc_id": result.get("id"),
                "success": True,
                "message_count": len(chat_messages)
            }
        except Exception as e:
            logger.error(f"保存会话失败: {str(e)}", exc_info=True)
            raise
    
    async def get_session(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        根据会话ID获取会话数据
        
        Args:
            session_id: 会话ID
            user_id: 用户ID（可选）
        
        Returns:
            会话数据，如果不存在返回None
        """
        try:
            # 从ChatService获取会话的所有聊天记录
            if not user_id:
                # 尝试从会话中推断user_id
                chats = await self.chat_service.get_chats_by_conversation(
                    conversation_id=session_id,
                    limit=1
                )
                if chats:
                    user_id = chats[0].get("user_id")
            
            chats = await self.chat_service.get_chats_by_conversation(
                conversation_id=session_id,
                limit=100
            )
            
            if not chats:
                return None
            
            # 合并所有聊天记录
            all_messages = []
            metadata = {}
            for chat in chats:
                chat_messages = chat.get("messages", [])
                all_messages.extend(chat_messages)
                # 使用最新的metadata
                if chat.get("metadata"):
                    metadata = chat.get("metadata", {})
            
            # 转换为YiPet格式
            pet_messages = []
            for msg in all_messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    pet_messages.append({
                        "type": "user",
                        "content": content,
                        "timestamp": metadata.get("updatedAt") or int(datetime.now(timezone.utc).timestamp() * 1000)
                    })
                elif role == "assistant":
                    pet_messages.append({
                        "type": "pet",
                        "content": content,
                        "timestamp": metadata.get("updatedAt") or int(datetime.now(timezone.utc).timestamp() * 1000)
                    })
            
            # 构建会话对象
            session_data = {
                "id": session_id,
                "url": metadata.get("url", ""),
                "title": metadata.get("title", ""),
                "pageTitle": metadata.get("pageTitle", ""),
                "pageDescription": metadata.get("pageDescription", ""),
                "messages": pet_messages,
                "createdAt": metadata.get("createdAt"),
                "updatedAt": metadata.get("updatedAt"),
                "lastAccessTime": metadata.get("lastAccessTime")
            }
            
            return session_data
        except Exception as e:
            logger.error(f"获取会话失败: {str(e)}", exc_info=True)
            raise
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        列出所有会话
        
        Args:
            user_id: 用户ID（可选）
            limit: 返回数量限制
            skip: 跳过数量
        
        Returns:
            会话列表
        """
        try:
            if user_id:
                chats = await self.chat_service.get_chats_by_user(
                    user_id=user_id,
                    limit=limit,
                    skip=skip
                )
            else:
                # 如果没有user_id，返回所有会话（需要从MongoDB直接查询）
                from modules.database.mongoClient import MongoClient
                mongo_client = MongoClient()
                await mongo_client.initialize()
                
                # 获取所有唯一的conversation_id
                pipeline = [
                    {"$group": {"_id": "$conversation_id", "latest": {"$max": "$updated_time"}}},
                    {"$sort": {"latest": -1}},
                    {"$skip": skip},
                    {"$limit": limit}
                ]
                
                # 由于MongoClient可能没有聚合方法，我们使用find_many然后去重
                all_chats = await mongo_client.find_many(
                    collection_name="chat_records",
                    query={},
                    limit=limit * 10,  # 获取更多以支持去重
                    skip=skip,
                    sort=[("updated_time", -1)]
                )
                
                # 按conversation_id去重，保留最新的
                conversation_map = {}
                for chat in all_chats:
                    conv_id = chat.get("conversation_id")
                    if conv_id and conv_id not in conversation_map:
                        conversation_map[conv_id] = chat
                
                chats = list(conversation_map.values())[:limit]
            
            # 转换为会话列表格式
            sessions = []
            for chat in chats:
                metadata = chat.get("metadata", {})
                sessions.append({
                    "id": chat.get("conversation_id"),
                    "url": metadata.get("url", ""),
                    "title": metadata.get("title", ""),
                    "pageTitle": metadata.get("pageTitle", ""),
                    "message_count": chat.get("message_count", 0),
                    "createdAt": metadata.get("createdAt"),
                    "updatedAt": metadata.get("updatedAt") or chat.get("updated_time"),
                    "lastAccessTime": metadata.get("lastAccessTime")
                })
            
            return sessions
        except Exception as e:
            logger.error(f"列出会话失败: {str(e)}", exc_info=True)
            raise
    
    async def delete_session(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID（可选）
        
        Returns:
            是否删除成功
        """
        try:
            result = await self.chat_service.delete_conversation(conversation_id=session_id)
            return result > 0
        except Exception as e:
            logger.error(f"删除会话失败: {str(e)}", exc_info=True)
            raise
    
    async def search_sessions(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索会话
        
        Args:
            query: 搜索查询
            user_id: 用户ID（可选）
            limit: 返回数量限制
        
        Returns:
            匹配的会话列表
        """
        try:
            results = await self.chat_service.search_chats(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            # 转换为会话列表格式
            sessions = []
            for result in results:
                metadata = result.get("metadata", {})
                sessions.append({
                    "id": result.get("conversation_id"),
                    "url": metadata.get("url", ""),
                    "title": metadata.get("title", ""),
                    "pageTitle": metadata.get("pageTitle", ""),
                    "message_count": result.get("message_count", 0),
                    "relevance_score": result.get("relevance_score", 0),
                    "createdAt": metadata.get("createdAt"),
                    "updatedAt": metadata.get("updatedAt") or result.get("updated_time"),
                    "lastAccessTime": metadata.get("lastAccessTime")
                })
            
            return sessions
        except Exception as e:
            logger.error(f"搜索会话失败: {str(e)}", exc_info=True)
            raise

