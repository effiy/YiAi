"""会话管理服务 - 统一管理YiPet会话数据"""
import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from modules.database.mongoClient import MongoClient
from modules.utils.session_utils import normalize_session_id

logger = logging.getLogger(__name__)


class SessionService:
    """会话管理服务"""
    
    def __init__(self):
        self.mongo_client = MongoClient()
        self.collection_name = "sessions"
        self._initialized = False
        
    async def initialize(self):
        """初始化服务"""
        if not self._initialized:
            await self.mongo_client.initialize()
            self._initialized = True
    
    async def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            await self.initialize()
    
    def normalize_session_id(self, session_id: str) -> str:
        """规范化 session_id"""
        return normalize_session_id(session_id)
    
    async def save_session(
        self,
        session_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        保存会话数据
        
        Args:
            session_data: 会话数据，包含：
                - id: 会话ID（可选）
                - url: 页面URL
                - title: 会话标题
                - messages: 消息列表
                - pageContent: 页面内容
                - createdAt: 创建时间
                - updatedAt: 更新时间
                - lastAccessTime: 最后访问时间
            user_id: 用户ID（可选，默认从请求头获取）
        
        Returns:
            保存结果，包含session_id和success状态
        """
        await self._ensure_initialized()
        
        try:
            # 生成或使用现有的会话ID
            session_id = session_data.get("id")
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # 规范化 session_id
            session_id = self.normalize_session_id(session_id)
            
            # 如果没有提供user_id，生成一个
            if not user_id:
                user_id = f"pet_user_{session_id[:16]}"
            
            # 获取当前时间
            current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
            
            # 构建会话文档
            session_doc = {
                "key": session_id,
                "user_id": user_id,
                "url": session_data.get("url", ""),
                "title": session_data.get("title", ""),
                "pageTitle": session_data.get("pageTitle", ""),
                "pageDescription": session_data.get("pageDescription", ""),
                "pageContent": session_data.get("pageContent", ""),
                "messages": session_data.get("messages", []),
                "createdAt": session_data.get("createdAt") or current_time,
                "updatedAt": session_data.get("updatedAt") or current_time,
                "lastAccessTime": session_data.get("lastAccessTime") or current_time,
                "createdTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                "updatedTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 检查是否已存在
            existing = await self.mongo_client.find_one(
                collection_name=self.collection_name,
                query={"key": session_id}
            )
            
            if existing:
                # 更新现有会话（保留createdAt和order，增量更新）
                update_doc = {}
                needs_update = False
                should_update_timestamp = False
                
                # 检查消息是否有变化
                messages = session_data.get("messages")
                if messages is not None:
                    existing_messages = existing.get("messages", [])
                    if len(messages) != len(existing_messages) or messages != existing_messages:
                        update_doc["messages"] = messages
                        needs_update = True
                        should_update_timestamp = True
                
                # 检查其他字段
                for field in ["url", "title", "pageTitle", "pageDescription", "pageContent"]:
                    if field in session_data and session_data[field] is not None:
                        if session_data[field] != existing.get(field, ""):
                            update_doc[field] = session_data[field]
                            needs_update = True
                
                # 更新时间戳
                if session_data.get("updatedAt") is not None:
                    if session_data["updatedAt"] != existing.get("updatedAt", 0):
                        update_doc["updatedAt"] = session_data["updatedAt"]
                        needs_update = True
                elif should_update_timestamp:
                    update_doc["updatedAt"] = current_time
                    needs_update = True
                
                if session_data.get("lastAccessTime") is not None:
                    if session_data["lastAccessTime"] != existing.get("lastAccessTime", 0):
                        update_doc["lastAccessTime"] = session_data["lastAccessTime"]
                        needs_update = True
                elif should_update_timestamp:
                    update_doc["lastAccessTime"] = current_time
                    needs_update = True
                
                if should_update_timestamp:
                    update_doc["updatedTime"] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                
                # 只在有变化时才执行更新
                if needs_update:
                    await self.mongo_client.update_one(
                        collection_name=self.collection_name,
                        query={"key": session_id},
                        update={"$set": update_doc}
                    )
                    logger.info(f"会话 {session_id} 已更新")
                else:
                    logger.debug(f"会话 {session_id} 无变化，跳过更新")
            else:
                # 插入新会话，设置order字段
                max_order_doc = await self.mongo_client.find_one(
                    collection_name=self.collection_name,
                    query={},
                    sort=[("order", -1)],
                    projection={"order": 1}
                )
                max_order = max_order_doc.get("order", 0) if max_order_doc else 0
                session_doc["order"] = max_order + 1
                await self.mongo_client.insert_one(
                    collection_name=self.collection_name,
                    document=session_doc
                )
                logger.info(f"新会话 {session_id} 已创建")
            
            return {
                "session_id": session_id,
                "id": session_id,
                "success": True
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
            user_id: 用户ID（可选，用于权限检查）
        
        Returns:
            会话数据，如果不存在返回None
        """
        await self._ensure_initialized()
        
        try:
            # 规范化 session_id
            session_id = self.normalize_session_id(session_id)
            
            # 构建查询条件
            query = {"key": session_id}
            if user_id and user_id != "default_user":
                query["user_id"] = user_id
            
            # 查询会话
            session_doc = await self.mongo_client.find_one(
                collection_name=self.collection_name,
                query=query
            )
            
            if not session_doc:
                return None
            
            # 转换为API响应格式
            return {
                "id": session_doc.get("key"),
                "url": session_doc.get("url", ""),
                "title": session_doc.get("title", ""),
                "pageTitle": session_doc.get("pageTitle", ""),
                "pageDescription": session_doc.get("pageDescription", ""),
                "pageContent": session_doc.get("pageContent", ""),
                "messages": session_doc.get("messages", []),
                "createdAt": session_doc.get("createdAt"),
                "updatedAt": session_doc.get("updatedAt"),
                "lastAccessTime": session_doc.get("lastAccessTime")
            }
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
        await self._ensure_initialized()
        
        try:
            # 构建查询条件
            query = {}
            if user_id and user_id != "default_user":
                query["user_id"] = user_id
            
            # 查询会话，按更新时间倒序
            session_docs = await self.mongo_client.find_many(
                collection_name=self.collection_name,
                query=query,
                skip=skip,
                limit=limit,
                sort=[("updatedAt", -1), ("order", -1)]
            )
            
            # 去重：按 key 分组，每个 key 只保留 updatedAt 最新的那个会话
            session_map = {}
            for doc in session_docs:
                session_key = doc.get("key")
                if not session_key:
                    continue
                
                # 如果该 key 已存在，比较 updatedAt，保留更新的
                if session_key in session_map:
                    existing_updated_at = session_map[session_key].get("updatedAt", 0)
                    current_updated_at = doc.get("updatedAt", 0)
                    if current_updated_at > existing_updated_at:
                        session_map[session_key] = doc
                else:
                    session_map[session_key] = doc
            
            # 转换为API响应格式
            sessions = []
            for doc in session_map.values():
                sessions.append({
                    "id": doc.get("key"),
                    "url": doc.get("url", ""),
                    "title": doc.get("title", ""),
                    "pageTitle": doc.get("pageTitle", ""),
                    "message_count": len(doc.get("messages", [])),
                    "createdAt": doc.get("createdAt"),
                    "updatedAt": doc.get("updatedAt"),
                    "lastAccessTime": doc.get("lastAccessTime")
                })
            
            # 重新排序，确保顺序正确（按 updatedAt 倒序）
            sessions.sort(key=lambda x: (x.get("updatedAt", 0), x.get("id", "")), reverse=True)
            
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
            user_id: 用户ID（可选，用于权限检查）
        
        Returns:
            是否删除成功
        """
        await self._ensure_initialized()
        
        try:
            # 规范化 session_id
            session_id = self.normalize_session_id(session_id)
            
            # 构建删除条件
            query = {"key": session_id}
            if user_id and user_id != "default_user":
                query["user_id"] = user_id
            
            result = await self.mongo_client.delete_one(
                collection_name=self.collection_name,
                query=query
            )
            
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
        搜索会话（基于文本搜索）
        
        Args:
            query: 搜索查询
            user_id: 用户ID（可选）
            limit: 返回数量限制
        
        Returns:
            匹配的会话列表
        """
        await self._ensure_initialized()
        
        try:
            import re
            
            # 构建搜索条件
            search_query = {}
            if user_id and user_id != "default_user":
                search_query["user_id"] = user_id
            
            # 构建文本搜索条件（在title、pageTitle、pageContent中搜索）
            pattern = re.compile(f'.*{re.escape(query)}.*', re.IGNORECASE)
            search_query["$or"] = [
                {"title": pattern},
                {"pageTitle": pattern},
                {"pageContent": pattern},
                {"pageDescription": pattern}
            ]
            
            # 查询会话
            session_docs = await self.mongo_client.find_many(
                collection_name=self.collection_name,
                query=search_query,
                limit=limit,
                sort=[("updatedAt", -1), ("order", -1)]
            )
            
            # 去重：按 key 分组，每个 key 只保留 updatedAt 最新的那个会话
            session_map = {}
            for doc in session_docs:
                session_key = doc.get("key")
                if not session_key:
                    continue
                
                if session_key in session_map:
                    existing_updated_at = session_map[session_key].get("updatedAt", 0)
                    current_updated_at = doc.get("updatedAt", 0)
                    if current_updated_at > existing_updated_at:
                        session_map[session_key] = doc
                else:
                    session_map[session_key] = doc
            
            # 转换为API响应格式
            sessions = []
            for doc in session_map.values():
                sessions.append({
                    "id": doc.get("key"),
                    "url": doc.get("url", ""),
                    "title": doc.get("title", ""),
                    "pageTitle": doc.get("pageTitle", ""),
                    "message_count": len(doc.get("messages", [])),
                    "createdAt": doc.get("createdAt"),
                    "updatedAt": doc.get("updatedAt"),
                    "lastAccessTime": doc.get("lastAccessTime")
                })
            
            # 重新排序
            sessions.sort(key=lambda x: (x.get("updatedAt", 0), x.get("id", "")), reverse=True)
            
            return sessions
        except Exception as e:
            logger.error(f"搜索会话失败: {str(e)}", exc_info=True)
            raise
    
    async def update_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新会话数据
        
        Args:
            session_id: 会话ID
            session_data: 要更新的会话数据
            user_id: 用户ID（可选）
        
        Returns:
            更新结果
        """
        await self._ensure_initialized()
        
        try:
            # 规范化 session_id
            session_id = self.normalize_session_id(session_id)
            
            # 检查会话是否存在
            query = {"key": session_id}
            if user_id and user_id != "default_user":
                query["user_id"] = user_id
            
            existing = await self.mongo_client.find_one(
                collection_name=self.collection_name,
                query=query
            )
            
            if not existing:
                raise ValueError(f"会话 {session_id} 不存在")
            
            # 获取当前时间
            current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
            
            # 构建更新数据（保留原有数据，只更新提供的字段）
            update_doc = {
                "updatedTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 更新字段
            for field in ["url", "title", "pageTitle", "pageDescription", "pageContent", "messages"]:
                if field in session_data and session_data[field] is not None:
                    update_doc[field] = session_data[field]
            
            # 更新时间戳
            if session_data.get("updatedAt") is not None:
                update_doc["updatedAt"] = session_data["updatedAt"]
            else:
                update_doc["updatedAt"] = current_time
            
            if session_data.get("lastAccessTime") is not None:
                update_doc["lastAccessTime"] = session_data["lastAccessTime"]
            else:
                update_doc["lastAccessTime"] = current_time
            
            # 更新会话
            await self.mongo_client.update_one(
                collection_name=self.collection_name,
                query={"key": session_id},
                update={"$set": update_doc}
            )
            
            logger.info(f"会话 {session_id} 已更新")
            
            return {
                "session_id": session_id,
                "id": session_id,
                "success": True
            }
        except Exception as e:
            logger.error(f"更新会话失败: {str(e)}", exc_info=True)
            raise
