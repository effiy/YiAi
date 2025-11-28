import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from bson import ObjectId
from modules.database.mongoClient import MongoClient
from modules.database.mem0Client import Mem0Client

logger = logging.getLogger(__name__)

class ChatService:
    """聊天记录管理服务"""
    
    def __init__(self):
        self.mongo_client = MongoClient()
        self.mem0_client = Mem0Client()
        self.collection_name = "chat_records"
        
    async def initialize(self):
        """初始化服务"""
        await self.mongo_client.initialize()
        # Mem0 会自动管理向量存储集合，无需手动创建
        if not self.mem0_client.is_available():
            logger.warning("Mem0 不可用，向量搜索功能将不可用")
    
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
            
            # 获取最后一条用户消息用于向量化
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
            
            # 只在 Mem0 可用时保存记忆
            if self.mem0_client.is_available():
                if user_messages:
                    last_user_message = user_messages[-1].get("content", "")
                    # 保存到 Mem0（自动处理向量化）- Mem0 API 是同步的
                    if last_user_message:
                        try:
                            result = self.mem0_client.add_memory(
                                memory=last_user_message,
                                user_id=user_id,
                                metadata={
                                    "conversation_id": conversation_id,
                                    "doc_id": doc_id,
                                    "message_type": "user",
                                    **(metadata or {})
                                }
                            )
                            if result.get("status") == "skipped":
                                logger.debug("Mem0 不可用，跳过添加用户记忆")
                        except Exception as e:
                            logger.warning(f"Mem0 添加记忆失败: {str(e)}")
                
                if assistant_messages:
                    last_assistant_message = assistant_messages[-1].get("content", "")
                    # 保存助手回复到 Mem0
                    if last_assistant_message:
                        try:
                            result = self.mem0_client.add_memory(
                                memory=last_assistant_message,
                                user_id=user_id,
                                metadata={
                                    "conversation_id": conversation_id,
                                    "doc_id": doc_id,
                                    "message_type": "assistant",
                                    **(metadata or {})
                                }
                            )
                            if result.get("status") == "skipped":
                                logger.debug("Mem0 不可用，跳过添加助手记忆")
                        except Exception as e:
                            logger.warning(f"Mem0 添加记忆失败: {str(e)}")
            else:
                logger.debug("Mem0 不可用，跳过记忆保存")
            
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
        """语义搜索聊天记录"""
        try:
            # 使用 Mem0 进行语义搜索 - Mem0 API 是同步的
            memories = self.mem0_client.search_memories(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            # 从记忆中提取 doc_id，然后从 MongoDB 获取完整记录
            results = []
            for memory in memories:
                doc_id = memory.get("metadata", {}).get("doc_id")
                if doc_id:
                    chat_doc = await self.get_chat_by_id(doc_id)
                    if chat_doc:
                        chat_doc["relevance_score"] = memory.get("score", 0)
                        results.append(chat_doc)
            
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
            # 先获取记录，以便从 Mem0 删除
            chat_doc = await self.get_chat_by_id(doc_id)
            if chat_doc:
                user_id = chat_doc.get("user_id")
                conversation_id = chat_doc.get("conversation_id")
                
                # 尝试从 Mem0 删除相关记忆
                try:
                    memories = self.mem0_client.get_memories(user_id=user_id)
                    for memory in memories:
                        mem_metadata = memory.get("metadata", {})
                        if mem_metadata.get("doc_id") == doc_id:
                            self.mem0_client.delete_memory(
                                memory_id=memory.get("id"),
                                user_id=user_id
                            )
                except Exception as e:
                    logger.warning(f"从 Mem0 删除记忆失败: {str(e)}")
            
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
            # 获取会话所有记录
            chats = await self.get_chats_by_conversation(conversation_id)
            
            # 删除 Mem0 中的相关记忆
            user_ids = set()
            for chat in chats:
                user_id = chat.get("user_id")
                if user_id:
                    user_ids.add(user_id)
            
            for user_id in user_ids:
                try:
                    memories = self.mem0_client.get_memories(user_id=user_id)
                    for memory in memories:
                        mem_metadata = memory.get("metadata", {})
                        if mem_metadata.get("conversation_id") == conversation_id:
                            self.mem0_client.delete_memory(
                                memory_id=memory.get("id"),
                                user_id=user_id
                            )
                except Exception as e:
                    logger.warning(f"从 Mem0 删除会话记忆失败: {str(e)}")
            
            # 从 MongoDB 删除
            result = await self.mongo_client.delete_many(
                collection_name=self.collection_name,
                query={"conversation_id": conversation_id}
            )
            
            return result
        except Exception as e:
            logger.error(f"删除会话失败: {str(e)}")
            raise

