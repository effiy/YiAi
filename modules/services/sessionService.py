"""
会话管理服务 - 统一管理YiPet会话数据

职责：
- 管理YiPet扩展的会话数据（包含页面内容、消息等）
- 提供会话的CRUD操作
- 与ChatService的区别：
  - SessionService: 管理完整的会话上下文（页面内容、标题、URL等），用于YiPet扩展
  - ChatService: 管理聊天记录和向量搜索，用于AI对话服务
"""
import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from modules.database.mongoClient import MongoClient
from modules.utils.session_utils import normalize_session_id
from modules.models.session_model import (
    session_to_api_format,
    session_to_list_item
)

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
    
    def _deduplicate_and_convert_sessions(
        self,
        session_docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        去重并转换会话文档为API格式
        
        去重逻辑：按 key 分组，每个 key 只保留 updatedAt 最新的那个会话
        
        Args:
            session_docs: 会话文档列表
        
        Returns:
            去重并转换后的会话列表（按 updatedAt 倒序）
        """
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
        
        # 使用统一的数据模型转换函数
        sessions = []
        for doc in session_map.values():
            sessions.append(session_to_list_item(doc))
        
        # 重新排序，确保顺序正确（按 updatedAt 倒序）
        sessions.sort(key=lambda x: (x.get("updatedAt", 0), x.get("id", "")), reverse=True)
        
        return sessions
    
    def normalize_session_id(self, session_id: str) -> str:
        """规范化 session_id"""
        return normalize_session_id(session_id)
    
    def generate_session_id(self, url: Optional[str] = None) -> str:
        """
        生成会话ID
        
        Args:
            url: 页面URL（可选），如果提供则基于URL生成，否则生成UUID
        
        Returns:
            会话ID
        """
        if url:
            # 基于URL生成会话ID（会被normalize_session_id处理）
            return self.normalize_session_id(url)
        else:
            # 生成新的UUID
            return str(uuid.uuid4())
    
    def _prepare_session_doc(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        user_id: str,
        current_time: int
    ) -> Dict[str, Any]:
        """
        准备会话文档数据
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
            user_id: 用户ID
            current_time: 当前时间戳（毫秒）
        
        Returns:
            会话文档字典
        """
        doc = {
            "key": session_id,
            "user_id": user_id,
            "url": session_data.get("url", ""),
            "title": session_data.get("title", ""),
            "pageTitle": session_data.get("pageTitle", ""),
            "pageDescription": session_data.get("pageDescription", ""),
            "pageContent": session_data.get("pageContent", ""),
            "messages": session_data.get("messages", []),
            "tags": session_data.get("tags", []),
            "isFavorite": session_data.get("isFavorite", False),
            "createdAt": session_data.get("createdAt") or current_time,
            "updatedAt": session_data.get("updatedAt") or current_time,
            "lastAccessTime": session_data.get("lastAccessTime") or current_time,
            "createdTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            "updatedTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 添加 imageDataUrl 字段（如果存在）
        if "imageDataUrl" in session_data and session_data["imageDataUrl"] is not None:
            doc["imageDataUrl"] = session_data["imageDataUrl"]
        
        return doc
    
    def _prepare_update_doc(
        self,
        session_data: Dict[str, Any],
        existing: Dict[str, Any],
        current_time: int
    ) -> Dict[str, Any]:
        """
        准备更新文档（仅包含有变化的字段）
        
        Args:
            session_data: 新的会话数据
            existing: 现有会话数据
            current_time: 当前时间戳（毫秒）
        
        Returns:
            更新文档字典（如果没有变化则返回空字典）
        """
        update_doc = {}
        has_changes = False
        should_update_timestamp = False
        
        # 检查消息是否有变化
        messages = session_data.get("messages")
        if messages is not None:
            existing_messages = existing.get("messages", [])
            # 如果消息有变化，则更新（包括用空数组清空消息的情况）
            if messages != existing_messages:
                update_doc["messages"] = messages
                has_changes = True
                should_update_timestamp = True
        
        # 检查其他字段是否有变化
        # 包括 isFavorite 字段，允许通过 save 接口更新收藏状态
        for field in ["url", "title", "pageTitle", "pageDescription", "pageContent", "tags", "imageDataUrl", "isFavorite"]:
            if field in session_data and session_data[field] is not None:
                # 为不同字段设置合适的默认值
                if field == "tags":
                    existing_value = existing.get(field, [])
                elif field == "isFavorite":
                    existing_value = existing.get(field, False)
                else:
                    existing_value = existing.get(field, "")
                if session_data[field] != existing_value:
                    update_doc[field] = session_data[field]
                    has_changes = True
        
        # 更新时间戳
        updated_at = session_data.get("updatedAt")
        if updated_at is not None and updated_at != existing.get("updatedAt", 0):
            update_doc["updatedAt"] = updated_at
            has_changes = True
        elif should_update_timestamp:
            update_doc["updatedAt"] = current_time
            has_changes = True
        
        last_access_time = session_data.get("lastAccessTime")
        if last_access_time is not None and last_access_time != existing.get("lastAccessTime", 0):
            update_doc["lastAccessTime"] = last_access_time
            has_changes = True
        elif should_update_timestamp:
            update_doc["lastAccessTime"] = current_time
            has_changes = True
        
        if should_update_timestamp:
            update_doc["updatedTime"] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        return update_doc if has_changes else {}
    
    async def _create_session(
        self,
        session_id: str,
        session_doc: Dict[str, Any]
    ) -> None:
        """
        创建新会话
        
        Args:
            session_id: 会话ID
            session_doc: 会话文档
        """
        # 获取最大order值（使用find_many，因为find_one不支持sort参数）
        max_order_docs = await self.mongo_client.find_many(
            collection_name=self.collection_name,
            query={},
            sort=[("order", -1)],
            limit=1
        )
        max_order = max_order_docs[0].get("order", 0) if max_order_docs else 0
        session_doc["order"] = max_order + 1
        
        # 插入新会话
        await self.mongo_client.insert_one(
            collection_name=self.collection_name,
            document=session_doc
        )
        logger.info(f"新会话 {session_id} 已创建")
    
    async def update_session_field(
        self,
        session_id: str,
        field_name: str,
        field_value: Any,
        user_id: Optional[str] = None
    ) -> bool:
        """
        更新会话的单个字段
        
        Args:
            session_id: 会话ID
            field_name: 字段名
            field_value: 字段值
            user_id: 用户ID（可选，用于权限检查）
        
        Returns:
            是否更新成功
        """
        await self._ensure_initialized()
        
        try:
            # 规范化 session_id
            session_id = self.normalize_session_id(session_id)
            
            # 构建查询条件
            query = {"key": session_id}
            if user_id and user_id != "default_user":
                query["user_id"] = user_id
            
            # 检查会话是否存在
            existing = await self.mongo_client.find_one(
                collection_name=self.collection_name,
                query=query
            )
            
            if not existing:
                logger.warning(f"会话 {session_id} 不存在，无法更新字段 {field_name}")
                return False
            
            # 更新字段
            current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
            update_doc = {
                field_name: field_value,
                "updatedAt": current_time,
                "updatedTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            await self.mongo_client.update_one(
                collection_name=self.collection_name,
                query=query,
                update={"$set": update_doc}
            )
            
            logger.info(f"会话 {session_id} 的字段 {field_name} 已更新为 {field_value}")
            return True
        except Exception as e:
            logger.error(f"更新会话字段失败: {str(e)}", exc_info=True)
            raise
    
    async def _update_session(
        self,
        session_id: str,
        update_doc: Dict[str, Any]
    ) -> None:
        """
        更新现有会话
        
        Args:
            session_id: 会话ID
            update_doc: 更新文档
        """
        if not update_doc:
            logger.debug(f"会话 {session_id} 无变化，跳过更新")
            return
        
        await self.mongo_client.update_one(
            collection_name=self.collection_name,
            query={"key": session_id},
            update=update_doc
        )
        logger.info(f"会话 {session_id} 已更新")
    
    async def save_session(
        self,
        session_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        保存会话数据（自动判断创建或更新）
        
        Args:
            session_data: 会话数据，包含：
                - id: 会话ID（可选，如果不提供则自动生成）
                - url: 页面URL（可选，用于生成会话ID）
                - title: 会话标题
                - messages: 消息列表
                - pageContent: 页面内容
                - createdAt: 创建时间
                - updatedAt: 更新时间
                - lastAccessTime: 最后访问时间
            user_id: 用户ID（可选，如果不提供则自动生成）
        
        Returns:
            保存结果，包含session_id和success状态
        """
        await self._ensure_initialized()
        
        try:
            # 生成或使用现有的会话ID
            session_id = session_data.get("id")
            if not session_id:
                # 如果没有提供ID，尝试基于URL生成，否则生成UUID
                url = session_data.get("url")
                session_id = self.generate_session_id(url)
            else:
                # 规范化提供的会话ID
                session_id = self.normalize_session_id(session_id)
            
            # 如果没有提供user_id，生成一个
            if not user_id:
                user_id = f"pet_user_{session_id[:16]}"
            
            # 获取当前时间
            current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
            
            # 检查是否已存在
            existing = await self.mongo_client.find_one(
                collection_name=self.collection_name,
                query={"key": session_id}
            )
            
            if existing:
                # 更新现有会话
                update_doc = self._prepare_update_doc(session_data, existing, current_time)
                await self._update_session(session_id, update_doc)
                is_new = False
            else:
                # 创建新会话
                session_doc = self._prepare_session_doc(
                    session_id, session_data, user_id, current_time
                )
                await self._create_session(session_id, session_doc)
                is_new = True
            
            return {
                "session_id": session_id,
                "id": session_id,
                "success": True,
                "is_new": is_new
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
            
            # 使用统一的数据模型转换函数
            return session_to_api_format(session_doc)
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
            
            # 去重并转换为API格式
            sessions = self._deduplicate_and_convert_sessions(session_docs)
            
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
            
            # 构建查询条件（用于查找会话）
            query = {"key": session_id}
            if user_id and user_id != "default_user":
                query["user_id"] = user_id
            
            # 在删除之前，先获取会话的 URL，用于更新对应新闻的状态
            session_doc = await self.mongo_client.find_one(
                collection_name=self.collection_name,
                query=query
            )
            
            # 删除会话
            result = await self.mongo_client.delete_one(
                collection_name=self.collection_name,
                query=query
            )
            
            # 如果删除成功，处理关联数据
            if result > 0 and session_doc:
                session_url = session_doc.get("url")
                
                # 处理新闻状态更新
                if session_url:
                    try:
                        # 查找对应的新闻（通过 link 字段）
                        news_query = {"link": session_url}
                        # 更新新闻状态：清除 sessionId，设置 isRead 为 false
                        # 使用 $unset 清除 sessionId 字段（如果存在）
                        # 使用 $set 设置 isRead 为 false
                        update_data = {
                            "$unset": {"sessionId": ""},
                            "$set": {"isRead": False}
                        }
                        await self.mongo_client.update_many(
                            collection_name="rss",
                            query=news_query,
                            update=update_data
                        )
                        logger.info(f"已更新会话对应的新闻状态: {session_url}")
                    except Exception as e:
                        # 更新新闻状态失败不影响删除会话的结果
                        logger.warning(f"更新新闻状态失败: {str(e)}")
                
                # 处理 aicr 项目文件删除
                # 会话ID格式：aicr_{projectId}_{filePath}（filePath中的特殊字符被替换为下划线）
                if session_id.startswith("aicr_"):
                    try:
                        # 提取项目ID和文件路径
                        # 格式：aicr_{projectId}_{filePath}
                        parts = session_id.split("_", 2)  # 最多分割2次
                        if len(parts) >= 3:
                            project_id = parts[1]
                            file_path_normalized = parts[2]
                            # 将下划线还原为斜杠，得到原始文件路径
                            file_path = file_path_normalized.replace("_", "/")
                            
                            # 删除对应的项目文件
                            # 从 projectFiles 集合中删除，通过 fileId 或 path 字段匹配
                            files_query = {
                                "projectId": project_id,
                                "$or": [
                                    {"fileId": file_path},
                                    {"path": file_path},
                                    {"id": file_path}
                                ]
                            }
                            
                            deleted_files = await self.mongo_client.delete_many(
                                collection_name="projectFiles",
                                query=files_query
                            )
                            
                            if deleted_files > 0:
                                logger.info(f"已删除 aicr 项目文件: projectId={project_id}, filePath={file_path}, deleted={deleted_files}")
                            else:
                                logger.debug(f"未找到对应的 aicr 项目文件: projectId={project_id}, filePath={file_path}")
                            
                            # 检查该projectId是否还有其他aicr会话，如果没有，删除projectTree
                            try:
                                # 查询是否还有其他aicr_开头的会话使用这个projectId
                                other_aicr_query = {
                                    "$and": [
                                        {"key": {"$regex": f"^aicr_{project_id}_"}},
                                        {"key": {"$ne": session_id}}
                                    ]
                                }
                                # 如果提供了 user_id，也需要在查询中考虑 user_id
                                if user_id and user_id != "default_user":
                                    other_aicr_query["user_id"] = user_id
                                
                                other_aicr_sessions = await self.mongo_client.find_many(
                                    collection_name=self.collection_name,
                                    query=other_aicr_query
                                )
                                
                                # 如果没有其他aicr会话，删除projectTree
                                if not other_aicr_sessions or len(other_aicr_sessions) == 0:
                                    try:
                                        tree_query = {"projectId": project_id}
                                        deleted_trees = await self.mongo_client.delete_many(
                                            collection_name="projectTree",
                                            query=tree_query
                                        )
                                        if deleted_trees > 0:
                                            logger.info(f"已删除 aicr projectTree: projectId={project_id}, deleted={deleted_trees}")
                                        else:
                                            logger.debug(f"未找到对应的 aicr projectTree: projectId={project_id}")
                                    except Exception as e:
                                        # 删除projectTree失败不影响删除会话的结果
                                        logger.warning(f"删除 aicr projectTree 失败: {str(e)}")
                            except Exception as e:
                                # 检查其他会话失败不影响删除会话的结果
                                logger.warning(f"检查其他aicr会话失败: {str(e)}")
                    except Exception as e:
                        # 删除项目文件失败不影响删除会话的结果
                        logger.warning(f"删除 aicr 项目文件失败: {str(e)}")
                
                # 处理第一个标签是项目ID的情况
                # 如果会话的第一个标签是项目ID，检查是否还有其他会话的第一个标签也是这个项目ID
                # 如果没有其他会话，则删除项目（包括projectTree、projectFiles、comments和projects）
                try:
                    tags = session_doc.get("tags", [])
                    if isinstance(tags, list) and len(tags) > 0:
                        first_tag = tags[0]
                        if first_tag and isinstance(first_tag, str):
                            # 检查这个标签是否是项目ID（通过查询projects集合）
                            project_query = {"id": first_tag}
                            project_doc = await self.mongo_client.find_one(
                                collection_name="projects",
                                query=project_query
                            )
                            
                            if project_doc:
                                # 这是一个项目ID，检查是否还有其他会话的第一个标签也是这个项目ID
                                # 查询所有会话，查找第一个标签匹配的会话（排除当前会话）
                                other_sessions_query = {
                                    "tags.0": first_tag,
                                    "key": {"$ne": session_id}
                                }
                                # 如果提供了 user_id，也需要在查询中考虑 user_id
                                if user_id and user_id != "default_user":
                                    other_sessions_query["user_id"] = user_id
                                
                                other_sessions = await self.mongo_client.find_many(
                                    collection_name=self.collection_name,
                                    query=other_sessions_query
                                )
                                
                                # 如果没有其他会话的第一个标签是这个项目ID，则删除项目
                                if not other_sessions or len(other_sessions) == 0:
                                    project_id = first_tag
                                    logger.info(f"检测到会话的第一个标签是项目ID，且没有其他会话使用，开始删除项目: {project_id}")
                                    
                                    # 1. 删除projectTree
                                    try:
                                        tree_query = {"projectId": project_id}
                                        deleted_trees = await self.mongo_client.delete_many(
                                            collection_name="projectTree",
                                            query=tree_query
                                        )
                                        logger.info(f"已删除 projectTree: projectId={project_id}, deleted={deleted_trees}")
                                    except Exception as e:
                                        logger.warning(f"删除 projectTree 失败: {str(e)}")
                                    
                                    # 2. 删除projectFiles
                                    try:
                                        files_query = {"projectId": project_id}
                                        deleted_files = await self.mongo_client.delete_many(
                                            collection_name="projectFiles",
                                            query=files_query
                                        )
                                        logger.info(f"已删除 projectFiles: projectId={project_id}, deleted={deleted_files}")
                                    except Exception as e:
                                        logger.warning(f"删除 projectFiles 失败: {str(e)}")
                                    
                                    # 3. 删除comments
                                    try:
                                        comments_query = {"projectId": project_id}
                                        deleted_comments = await self.mongo_client.delete_many(
                                            collection_name="comments",
                                            query=comments_query
                                        )
                                        logger.info(f"已删除 comments: projectId={project_id}, deleted={deleted_comments}")
                                    except Exception as e:
                                        logger.warning(f"删除 comments 失败: {str(e)}")
                                    
                                    # 4. 删除项目本身
                                    try:
                                        project_key = project_doc.get("key") or project_doc.get("_id") or project_doc.get("id")
                                        if project_key:
                                            deleted_project = await self.mongo_client.delete_one(
                                                collection_name="projects",
                                                query={"key": project_key}
                                            )
                                            logger.info(f"已删除项目: projectId={project_id}, deleted={deleted_project}")
                                    except Exception as e:
                                        logger.warning(f"删除项目失败: {str(e)}")
                                else:
                                    logger.debug(f"还有其他会话使用项目ID {first_tag}，不删除项目")
                except Exception as e:
                    # 处理项目删除失败不影响删除会话的结果
                    logger.warning(f"处理第一个标签是项目ID的情况失败: {str(e)}")
            
            return result > 0
        except Exception as e:
            logger.error(f"删除会话失败: {str(e)}", exc_info=True)
            raise
    
    async def delete_sessions(
        self,
        session_ids: List[str],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量删除会话
        
        Args:
            session_ids: 会话ID列表
            user_id: 用户ID（可选，用于权限检查）
        
        Returns:
            包含成功和失败数量的字典
        """
        await self._ensure_initialized()
        
        if not session_ids:
            return {
                "success_count": 0,
                "failed_count": 0,
                "total": 0
            }
        
        try:
            # 规范化所有会话ID
            normalized_ids = [self.normalize_session_id(sid) for sid in session_ids]
            
            # 构建删除条件
            query = {"key": {"$in": normalized_ids}}
            if user_id and user_id != "default_user":
                query["user_id"] = user_id
            
            # 在删除之前，先获取所有要删除的会话（用于处理关联数据）
            sessions_to_delete = await self.mongo_client.find_many(
                collection_name=self.collection_name,
                query=query
            )
            
            # 批量删除
            result = await self.mongo_client.delete_many(
                collection_name=self.collection_name,
                query=query
            )
            
            deleted_count = result if isinstance(result, int) else (result.deleted_count if hasattr(result, 'deleted_count') else 0)
            
            # 处理关联数据：删除 aicr 项目文件
            if deleted_count > 0 and sessions_to_delete:
                aicr_sessions = [s for s in sessions_to_delete if s.get("key", "").startswith("aicr_")]
                if aicr_sessions:
                    try:
                        # 收集所有需要删除的文件路径
                        files_to_delete = []
                        for session in aicr_sessions:
                            session_id = session.get("key", "")
                            if session_id.startswith("aicr_"):
                                # 提取项目ID和文件路径
                                parts = session_id.split("_", 2)
                                if len(parts) >= 3:
                                    project_id = parts[1]
                                    file_path_normalized = parts[2]
                                    file_path = file_path_normalized.replace("_", "/")
                                    files_to_delete.append({
                                        "projectId": project_id,
                                        "filePath": file_path
                                    })
                        
                        # 批量删除项目文件
                        for file_info in files_to_delete:
                            try:
                                files_query = {
                                    "projectId": file_info["projectId"],
                                    "$or": [
                                        {"fileId": file_info["filePath"]},
                                        {"path": file_info["filePath"]},
                                        {"id": file_info["filePath"]}
                                    ]
                                }
                                deleted_files = await self.mongo_client.delete_many(
                                    collection_name="projectFiles",
                                    query=files_query
                                )
                                if deleted_files > 0:
                                    logger.info(f"批量删除中已删除 aicr 项目文件: projectId={file_info['projectId']}, filePath={file_info['filePath']}, deleted={deleted_files}")
                            except Exception as e:
                                logger.warning(f"批量删除 aicr 项目文件失败: {str(e)}")
                    except Exception as e:
                        logger.warning(f"批量删除 aicr 项目文件处理失败: {str(e)}")
            
            return {
                "success_count": deleted_count,
                "failed_count": len(normalized_ids) - deleted_count,
                "total": len(normalized_ids)
            }
        except Exception as e:
            logger.error(f"批量删除会话失败: {str(e)}", exc_info=True)
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
            
            # 构建文本搜索条件（在title、pageTitle、pageContent、tags中搜索）
            pattern = re.compile(f'.*{re.escape(query)}.*', re.IGNORECASE)
            search_query["$or"] = [
                {"title": pattern},
                {"pageTitle": pattern},
                {"pageContent": pattern},
                {"pageDescription": pattern},
                {"tags": {"$in": [query]}}  # 支持标签精确匹配
            ]
            
            # 查询会话
            session_docs = await self.mongo_client.find_many(
                collection_name=self.collection_name,
                query=search_query,
                limit=limit,
                sort=[("updatedAt", -1), ("order", -1)]
            )
            
            # 去重并转换为API格式
            sessions = self._deduplicate_and_convert_sessions(session_docs)
            
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
            for field in ["url", "title", "pageTitle", "pageDescription", "pageContent", "messages", "tags", "imageDataUrl", "isFavorite"]:
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
                update=update_doc
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






