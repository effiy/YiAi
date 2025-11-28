import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from bson import ObjectId
from modules.database.mongoClient import MongoClient

logger = logging.getLogger(__name__)

class ChatService:
    """聊天记录管理服务"""
    
    def __init__(self):
        self.mongo_client = MongoClient()
        self.collection_name = "chat_records"
        
    async def initialize(self):
        """初始化服务"""
        await self.mongo_client.initialize()
    
    async def save_chat(
        self,
        user_id: str,
        conversation_id: Optional[str],
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        保存聊天记录
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID（可选，如果为None则创建新会话）
            messages: 消息列表，格式：[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            metadata: 额外元数据
        """
        try:
            # 如果没有 conversation_id，创建新的会话
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            # 构建聊天记录文档
            chat_doc = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "messages": messages,
                "message_count": len(messages),
                "created_time": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                "updated_time": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                "metadata": metadata or {}
            }
            
            # 保存到 MongoDB
            doc_id = await self.mongo_client.insert_one(
                collection_name=self.collection_name,
                document=chat_doc
            )
            
            
            return {
                "id": doc_id,
                "conversation_id": conversation_id,
                "success": True
            }
        except Exception as e:
            logger.error(f"保存聊天记录失败: {str(e)}")
            raise
    
    async def get_chat_by_id(
        self,
        doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """根据文档ID获取聊天记录"""
        try:
            document = await self.mongo_client.find_one(
                collection_name=self.collection_name,
                query={"_id": ObjectId(doc_id)}
            )
            
            if document and "_id" in document:
                document["_id"] = str(document["_id"])
            
            return document
        except Exception as e:
            logger.error(f"获取聊天记录失败: {str(e)}")
            raise
    
    async def get_chats_by_conversation(
        self,
        conversation_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """根据会话ID获取所有聊天记录"""
        try:
            documents = await self.mongo_client.find_many(
                collection_name=self.collection_name,
                query={"conversation_id": conversation_id},
                skip=skip,
                limit=limit,
                sort=[("created_time", -1)]  # 按时间倒序
            )
            
            # 转换 ObjectId
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            
            return documents
        except Exception as e:
            logger.error(f"获取会话聊天记录失败: {str(e)}")
            raise
    
    async def get_chats_by_user(
        self,
        user_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """根据用户ID获取所有聊天记录"""
        try:
            documents = await self.mongo_client.find_many(
                collection_name=self.collection_name,
                query={"user_id": user_id},
                skip=skip,
                limit=limit,
                sort=[("created_time", -1)]
            )
            
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            
            return documents
        except Exception as e:
            logger.error(f"获取用户聊天记录失败: {str(e)}")
            raise
    
    async def search_chats(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索聊天记录（文本搜索）"""
        try:
            # 使用 MongoDB 文本搜索
            documents = await self.mongo_client.find_many(
                collection_name=self.collection_name,
                query={
                    "$or": [
                        {"messages.content": {"$regex": query, "$options": "i"}},
                        {"user_id": user_id} if user_id else {}
                    ]
                },
                limit=limit,
                sort=[("created_time", -1)]
            )
            
            # 转换 ObjectId
            results = []
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                results.append(doc)
            
            return results
        except Exception as e:
            logger.error(f"搜索聊天记录失败: {str(e)}")
            raise
    
    async def update_chat(
        self,
        doc_id: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新聊天记录"""
        try:
            update_data = {
                "updated_time": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if messages is not None:
                update_data["messages"] = messages
                update_data["message_count"] = len(messages)
            
            if metadata is not None:
                update_data["metadata"] = metadata
            
            result = await self.mongo_client.update_one(
                collection_name=self.collection_name,
                query={"_id": ObjectId(doc_id)},
                update=update_data
            )
            
            return result > 0
        except Exception as e:
            logger.error(f"更新聊天记录失败: {str(e)}")
            raise
    
    async def delete_chat(
        self,
        doc_id: str
    ) -> bool:
        """删除聊天记录"""
        try:
            # 从 MongoDB 删除
            result = await self.mongo_client.delete_one(
                collection_name=self.collection_name,
                query={"_id": ObjectId(doc_id)}
            )
            
            return result > 0
        except Exception as e:
            logger.error(f"删除聊天记录失败: {str(e)}")
            raise
    
    async def delete_conversation(
        self,
        conversation_id: str
    ) -> int:
        """删除整个会话的所有聊天记录"""
        try:
            # 从 MongoDB 删除
            result = await self.mongo_client.delete_many(
                collection_name=self.collection_name,
                query={"conversation_id": conversation_id}
            )
            
            return result
        except Exception as e:
            logger.error(f"删除会话失败: {str(e)}")
            raise

