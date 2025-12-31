"""
会话管理服务 - 统一管理YiPet会话数据

职责：
- 管理YiPet扩展的会话数据（包含页面内容、消息等）
- 提供会话的CRUD操作
- 与ChatService的区别：
  - SessionService: 管理完整的会话上下文（页面内容、标题、URL等），用于YiPet扩展
  - ChatService: 管理聊天记录和向量搜索，用于AI对话服务
- 支持文件化存储：AICR 相关的 Session 的 pageContent 存储在文件系统中
"""
import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from modules.database.mongoClient import MongoClient
from modules.utils.session_utils import normalize_session_id
from modules.utils.idConverter import (
    is_aicr_session_id,
    extract_project_id_from_file_path,
    parse_session_id_to_file_path
)
from modules.services.fileStorageService import FileStorageService
from modules.services.syncService import SyncService
from modules.models.session_model import (
    session_to_api_format,
    session_to_list_item,
    normalize_message
)

logger = logging.getLogger(__name__)


class SessionService:
    """会话管理服务"""
    
    def __init__(self):
        self.mongo_client = MongoClient()
        self.collection_name = "sessions"
        self.file_storage = FileStorageService()
        self.sync_service = SyncService()
        self._initialized = False
        
    async def initialize(self):
        """初始化服务"""
        if not self._initialized:
            await self.mongo_client.initialize()
            await self.sync_service.initialize()
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
    
    def _try_parse_file_path_from_session_id(self, session_id: str) -> Optional[str]:
        """
        从 Session ID 尝试解析文件路径，尝试多种路径组合
        
        对于 session ID 如 knowledge_constructing_codereview_cr_claim_amount_2025_12_md，
        会尝试以下路径组合：
        1. knowledge/constructing/codereview/cr_claim_amount_2025_12.md (将下划线转换为斜杠)
        2. knowledge/constructing/codereview/cr_claim-amount_2025-12.md (尝试连字符变体)
        3. knowledge/constructing/codereview/cr_claim_amount_2025_12_*.md (模糊匹配)
        4. 其他可能的组合...
        
        Args:
            session_id: Session ID，如：knowledge_constructing_codereview_cr_claim_amount_2025_12_md
        
        Returns:
            文件路径（如果找到存在的文件），否则返回 None
        """
        import os
        import glob
        from modules.utils.idConverter import parse_session_id_to_file_path
        
        # 从 Session ID 提取项目ID
        parts = session_id.split("_", 2)
        if len(parts) < 3:
            return None
        
        project_id = parts[1]
        path_part = parts[2] if len(parts) > 2 else ""
        
        # 处理扩展名（格式：path_md -> path.md）
        file_ext = ''
        if '_' in path_part:
            # 检查最后一部分是否是扩展名（通常是 1-5 个字符）
            path_parts = path_part.rsplit('_', 1)
            if len(path_parts) == 2 and len(path_parts[1]) <= 5 and path_parts[1].isalnum():
                path_part = path_parts[0]
                file_ext = path_parts[1]
        
        # 如果没有扩展名，默认使用 .md
        if not file_ext:
            file_ext = 'md'
        
        # 生成可能的路径组合
        # 将下划线分隔的路径部分转换为可能的文件路径
        path_segments = path_part.split('_')
        
        # 尝试不同的下划线到斜杠的转换方式
        # 策略：优先尝试将下划线转换为斜杠的路径（更符合目录结构）
        possible_paths = []
        
        # 优先尝试：将下划线转换为斜杠的路径（从最深层到最浅层）
        # 例如：constructing_codereview_cr_claim_amount_2025_12 -> constructing/codereview/cr_claim_amount_2025_12
        if len(path_segments) >= 2:
            # 尝试不同的分割点，从后往前（保留更多目录层级）
            for i in range(1, len(path_segments)):
                dir_part = '/'.join(path_segments[:i])
                file_part = '_'.join(path_segments[i:])
                # 基本路径
                possible_paths.append(f"{project_id}/{dir_part}/{file_part}.{file_ext}")
                # 尝试连字符变体（将文件名中的下划线替换为连字符）
                # 例如：cr_claim_amount -> cr_claim-amount
                if '_' in file_part:
                    file_part_with_dash = file_part.replace('_', '-', 1) if file_part.count('_') > 0 else file_part
                    if file_part_with_dash != file_part:
                        possible_paths.append(f"{project_id}/{dir_part}/{file_part_with_dash}.{file_ext}")
        
        # 备用方案：保持所有下划线不变（原始逻辑）
        original_path = '_'.join(path_segments)
        possible_paths.append(f"{project_id}/{original_path}.{file_ext}")
        
        # 去重（保持顺序）
        seen = set()
        unique_paths = []
        for path in possible_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)
        possible_paths = unique_paths
        
        # 检查每个可能的路径，返回第一个存在的文件
        for file_path in possible_paths:
            if self.file_storage.file_exists(file_path):
                logger.debug(f"找到存在的文件路径: sessionId={session_id}, filePath={file_path}")
                return file_path
        
        # 如果精确匹配都失败，尝试模糊匹配（查找相似的文件名）
        # 例如：constructing_codereview_cr_claim_amount_2025_12 可能对应 constructing/codereview/cr_claim-amount_2025-12_胡俊天.md
        # 策略：尝试不同的目录/文件名分割点，在目录中查找匹配的文件
        if len(path_segments) >= 2:
            # 尝试不同的分割点：从 2 个目录段开始，到 len(path_segments)-1
            # 例如：对于 constructing_codereview_cr_claim_amount_2025_12
            # 尝试：constructing/codereview/ + cr_claim_amount_2025_12*
            #       constructing/ + codereview_cr_claim_amount_2025_12*
            for dir_end_idx in range(1, len(path_segments)):
                base_dir_segments = path_segments[:dir_end_idx]
                file_name_parts = path_segments[dir_end_idx:]
                
                if not base_dir_segments or not file_name_parts:
                    continue
                
                base_dir = f"{project_id}/{'/'.join(base_dir_segments)}"
                base_dir_path = self.file_storage.get_file_path(base_dir)
                
                if not os.path.isdir(base_dir_path):
                    continue
                
                # 构建文件名基础（使用下划线连接）
                file_name_base = '_'.join(file_name_parts)
                
                # 在目录中查找匹配的文件
                # 查找以 file_name_base 开头的 .md 文件
                pattern = os.path.join(base_dir_path, f"{file_name_base}*.{file_ext}")
                matches = glob.glob(pattern)
                if matches:
                    # 找到匹配的文件，转换为相对路径
                    matched_file = matches[0]
                    rel_path = os.path.relpath(matched_file, self.file_storage.base_dir)
                    # 统一使用正斜杠
                    file_path = rel_path.replace(os.sep, '/')
                    logger.debug(f"通过模糊匹配找到文件: sessionId={session_id}, filePath={file_path}")
                    return file_path
                
                # 也尝试将文件名中的下划线替换为连字符的变体
                # 例如：cr_claim_amount_2025_12 -> cr_claim-amount_2025-12
                # 尝试替换第一个下划线为连字符
                if '_' in file_name_base:
                    # 尝试多种连字符变体
                    variants = []
                    # 替换第一个下划线
                    first_dash = file_name_base.replace('_', '-', 1)
                    if first_dash != file_name_base:
                        variants.append(first_dash)
                    # 替换所有下划线
                    all_dash = file_name_base.replace('_', '-')
                    if all_dash != file_name_base and all_dash not in variants:
                        variants.append(all_dash)
                    
                    for variant in variants:
                        pattern = os.path.join(base_dir_path, f"{variant}*.{file_ext}")
                        matches = glob.glob(pattern)
                        if matches:
                            matched_file = matches[0]
                            rel_path = os.path.relpath(matched_file, self.file_storage.base_dir)
                            file_path = rel_path.replace(os.sep, '/')
                            logger.debug(f"通过模糊匹配（连字符变体）找到文件: sessionId={session_id}, filePath={file_path}")
                            return file_path
        
        # 如果所有路径都不存在，返回默认解析的路径（使用原始逻辑）
        default_path = parse_session_id_to_file_path(session_id, project_id)
        logger.debug(f"未找到存在的文件，使用默认路径: sessionId={session_id}, filePath={default_path}")
        return default_path
    
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
        
        注意：对于 AICR 相关的 Session，pageContent 不存储在 MongoDB 中，
        而是存储在文件系统中，这里只存储哈希值用于一致性检测。
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
            user_id: 用户ID
            current_time: 当前时间戳（毫秒）
        
        Returns:
            会话文档字典
        """
        # 规范化消息列表
        messages = session_data.get("messages", [])
        normalized_messages = []
        if messages:
            normalized_messages = [normalize_message(msg) for msg in messages if msg]
        
        page_content = session_data.get("pageContent", "")
        
        # 对于 AICR 相关的 Session，计算 pageContent 的哈希值
        page_content_hash = None
        if is_aicr_session_id(session_id) and page_content:
            import hashlib
            page_content_hash = hashlib.md5(page_content.encode('utf-8')).hexdigest()
            # 不存储实际内容，只存储哈希值
            page_content = ""
        
        doc = {
            "key": session_id,
            "user_id": user_id,
            "url": session_data.get("url", ""),
            "title": session_data.get("title", ""),
            "pageTitle": session_data.get("pageTitle", ""),
            "pageDescription": session_data.get("pageDescription", ""),
            "pageContent": page_content,  # AICR 相关的 Session 这里为空
            "pageContentHash": page_content_hash,  # 存储哈希值用于一致性检测
            "messages": normalized_messages,
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
            # 规范化消息列表
            normalized_messages = []
            if messages:
                normalized_messages = [normalize_message(msg) for msg in messages if msg]
            
            existing_messages = existing.get("messages", [])
            # 如果消息有变化，则更新（包括用空数组清空消息的情况）
            if normalized_messages != existing_messages:
                update_doc["messages"] = normalized_messages
                has_changes = True
                should_update_timestamp = True
        
        # 检查其他字段是否有变化
        # 包括 isFavorite 字段，允许通过 save 接口更新收藏状态
        # 注意：对于 AICR 相关的 Session，pageContent 需要特殊处理
        for field in ["url", "title", "pageTitle", "pageDescription", "tags", "imageDataUrl", "isFavorite"]:
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
        
        # 特殊处理 pageContent 字段（对于 AICR 相关的 Session）
        if "pageContent" in session_data and session_data["pageContent"] is not None:
            page_content = session_data["pageContent"]
            session_id = existing.get("key", "")
            
            if is_aicr_session_id(session_id):
                # 对于 AICR 相关的 Session，计算哈希值而不是存储内容
                import hashlib
                page_content_hash = hashlib.md5(page_content.encode('utf-8')).hexdigest()
                existing_hash = existing.get("pageContentHash", "")
                
                if page_content_hash != existing_hash:
                    update_doc["pageContentHash"] = page_content_hash
                    update_doc["pageContent"] = ""  # 不存储实际内容
                    has_changes = True
                    should_update_timestamp = True
            else:
                # 对于非 AICR 相关的 Session，正常处理
                existing_content = existing.get("pageContent", "")
                if page_content != existing_content:
                    update_doc["pageContent"] = page_content
                    has_changes = True
                    should_update_timestamp = True
        
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
        user_id: Optional[str] = None,
        source_client: str = "yipet"
    ) -> Dict[str, Any]:
        """
        保存会话数据（自动判断创建或更新）
        
        对于 AICR 相关的 Session，会将 pageContent 写入文件系统并同步到 ProjectFiles。
        
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
            source_client: 来源客户端：yiweb/yipet/yih5（默认：yipet）
        
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
            
            # 对于 AICR 相关的 Session，处理文件存储和同步
            page_content = session_data.get("pageContent", "")
            if is_aicr_session_id(session_id) and page_content:
                # 提取项目ID
                project_id = None
                # 尝试从映射表获取
                mapping = await self.sync_service.mapping_service.get_mapping_by_session_id(session_id)
                if mapping:
                    project_id = mapping.get("projectId")
                    file_id = mapping.get("fileId")
                else:
                    # 尝试从 Session ID 解析
                    # Session ID 格式：{projectId}_{filePath}
                    parts = session_id.split("_", 2)
                    if len(parts) >= 3:
                        project_id = parts[1]
                        file_id = parse_session_id_to_file_path(session_id, project_id)
                    else:
                        file_id = None
                
                if project_id and file_id:
                    # 同步到文件系统
                    sync_result = await self.sync_service.sync_session_to_project_file(
                        session_id=session_id,
                        content=page_content,
                        project_id=project_id,
                        source_client=source_client
                    )
                    if not sync_result.get("success"):
                        logger.warning(f"同步 Session 到文件系统失败: {session_id}, 错误: {sync_result.get('error')}")
            
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
        
        对于 AICR 相关的 Session，会从文件系统读取 pageContent。
        
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
            
            # 对于 AICR 相关的 Session，从文件系统读取 pageContent
            if is_aicr_session_id(session_id):
                logger.debug(f"检测到 AICR 会话，尝试从文件系统读取 pageContent: sessionId={session_id}")
                # 查询映射表获取文件ID
                mapping = await self.sync_service.mapping_service.get_mapping_by_session_id(session_id)
                file_id = None
                if mapping:
                    file_id = mapping.get("fileId")
                    logger.debug(f"找到映射关系: sessionId={session_id}, fileId={file_id}")
                
                # 如果映射表不存在，尝试从 Session ID 解析文件路径（备用方案）
                if not file_id:
                    file_id = self._try_parse_file_path_from_session_id(session_id)
                    if file_id:
                        logger.debug(f"从 Session ID 解析文件路径: sessionId={session_id}, fileId={file_id}")
                
                if file_id:
                    if self.file_storage.file_exists(file_id):
                        try:
                            page_content = self.file_storage.read_file_content(file_id)
                            logger.info(f"成功从文件系统读取 pageContent: sessionId={session_id}, fileId={file_id}, 大小={len(page_content)} 字节")
                            # 替换 MongoDB 中的 pageContent（可能是空的或哈希值）
                            session_doc["pageContent"] = page_content
                        except Exception as e:
                            logger.warning(f"从文件系统读取 pageContent 失败: sessionId={session_id}, fileId={file_id}, 错误: {str(e)}")
                            # 如果读取失败，保持原有内容（可能为空）
                    else:
                        logger.warning(f"文件不存在: sessionId={session_id}, fileId={file_id}")
                else:
                    logger.warning(f"无法获取文件ID: sessionId={session_id}, mapping={mapping}")
            
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
                
                # 处理静态文件删除
                # 对于所有包含下划线的 session_id，都尝试删除对应的静态文件
                # 会话ID格式可能是：{projectId}_{filePath}（filePath中的特殊字符被替换为下划线）
                file_id = None
                
                # 首先尝试从映射表获取文件ID（最可靠的方式）
                try:
                    mapping = await self.sync_service.mapping_service.get_mapping_by_session_id(session_id)
                    if mapping:
                        file_id = mapping.get("fileId")
                        logger.info(f"[删除会话] 从映射表找到文件ID: sessionId={session_id}, fileId={file_id}")
                except Exception as e:
                    logger.debug(f"[删除会话] 从映射表获取文件ID失败: sessionId={session_id}, 错误: {str(e)}")
                
                # 如果映射表不存在，尝试从 Session ID 解析文件路径（备用方案）
                if not file_id:
                    # 对于包含下划线的 session_id，尝试解析文件路径
                    if '_' in session_id:
                        try:
                            file_id = self._try_parse_file_path_from_session_id(session_id)
                            if file_id:
                                logger.info(f"[删除会话] 从 Session ID 解析文件路径: sessionId={session_id}, fileId={file_id}")
                        except Exception as e:
                            logger.debug(f"[删除会话] 解析文件路径失败: sessionId={session_id}, 错误: {str(e)}")
                
                # 如果仍然没有找到 file_id，但 session_id 包含下划线，尝试直接使用 session_id 作为文件路径
                if not file_id and '_' in session_id:
                    # 尝试将 session_id 转换为可能的文件路径
                    # 例如：knowledge_constructing_codereview_test_md -> knowledge/constructing/codereview_test.md
                    try:
                        parts = session_id.split('_')
                        if len(parts) >= 2:
                            # 处理扩展名（最后一部分可能是扩展名）
                            if len(parts) >= 3 and len(parts[-1]) <= 5 and parts[-1].isalnum():
                                # 最后一部分是扩展名
                                project_id = parts[0]
                                path_parts = parts[1:-1]
                                ext = parts[-1]
                                # 尝试不同的路径组合
                                possible_paths = [
                                    f"{project_id}/{'/'.join(path_parts)}.{ext}",  # 所有下划线转斜杠
                                    f"{project_id}/{'_'.join(path_parts)}.{ext}",  # 保持下划线
                                ]
                                # 检查哪个路径存在
                                for possible_path in possible_paths:
                                    if self.file_storage.file_exists(possible_path):
                                        file_id = possible_path
                                        logger.info(f"[删除会话] 通过路径匹配找到文件: sessionId={session_id}, fileId={file_id}")
                                        break
                    except Exception as e:
                        logger.debug(f"[删除会话] 尝试路径匹配失败: sessionId={session_id}, 错误: {str(e)}")
                
                # 删除静态文件系统中的文件
                if file_id:
                    try:
                        logger.info(f"[删除会话] 开始删除静态文件: sessionId={session_id}, fileId={file_id}")
                        if self.file_storage.file_exists(file_id):
                            deleted = self.file_storage.delete_file(file_id)
                            if deleted:
                                logger.info(f"[删除会话] 成功删除静态文件: sessionId={session_id}, fileId={file_id}")
                            else:
                                logger.warning(f"[删除会话] 删除静态文件失败: sessionId={session_id}, fileId={file_id}")
                        else:
                            logger.debug(f"[删除会话] 静态文件不存在，跳过删除: sessionId={session_id}, fileId={file_id}")
                    except Exception as e:
                        # 删除静态文件失败不影响删除会话的结果
                        logger.warning(f"[删除会话] 删除静态文件异常: sessionId={session_id}, fileId={file_id}, 错误: {str(e)}")
                else:
                    logger.debug(f"[删除会话] 无法确定文件ID，跳过删除静态文件: sessionId={session_id}")
                
                # 处理 aicr 项目文件删除（仅对 AICR 格式的 session）
                if is_aicr_session_id(session_id):
                    try:
                        
                        # 提取项目ID和文件路径（用于删除 MongoDB 中的 projectFiles）
                        # 格式：{projectId}_{filePath}
                        # 例如：knowledge_constructing_codereview_test_md
                        # parts[0] = 'knowledge' (项目ID)
                        # parts[1] = 'constructing' (路径第一部分)
                        # parts[2] = 'codereview_test_md' (路径剩余部分)
                        parts = session_id.split("_", 2)  # 最多分割2次
                        if len(parts) >= 2:
                            project_id = parts[0]  # 项目ID是第一部分
                            if len(parts) >= 3:
                                # 将路径部分合并，下划线转换为斜杠
                                file_path_normalized = f"{parts[1]}/{parts[2].replace('_', '/')}"
                            else:
                                file_path_normalized = parts[1]
                            # 处理扩展名（如果最后一部分是扩展名，如 _md）
                            if '_' in file_path_normalized:
                                path_parts = file_path_normalized.rsplit('_', 1)
                                if len(path_parts) == 2 and len(path_parts[1]) <= 5 and path_parts[1].isalnum():
                                    # 最后一部分是扩展名，转换为点号格式
                                    file_path = f"{path_parts[0]}.{path_parts[1]}"
                                else:
                                    file_path = file_path_normalized.replace("_", "/")
                            else:
                                file_path = file_path_normalized
                            
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
                            
                            # 检查该projectId是否还有其他aicr会话，如果没有，删除所有projectFiles和projectTree
                            try:
                                # 查询是否还有其他会话使用这个projectId
                                other_aicr_query = {
                                    "$and": [
                                        {"key": {"$regex": f"^{project_id}_"}},
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
                                
                                # 如果没有其他aicr会话，删除所有projectFiles和projectTree
                                if not other_aicr_sessions or len(other_aicr_sessions) == 0:
                                    # 删除所有projectFiles
                                    try:
                                        all_files_query = {"projectId": project_id}
                                        deleted_all_files = await self.mongo_client.delete_many(
                                            collection_name="projectFiles",
                                            query=all_files_query
                                        )
                                        if deleted_all_files > 0:
                                            logger.info(f"已删除所有 aicr projectFiles: projectId={project_id}, deleted={deleted_all_files}")
                                        else:
                                            logger.debug(f"未找到对应的 aicr projectFiles: projectId={project_id}")
                                    except Exception as e:
                                        # 删除所有projectFiles失败不影响删除会话的结果
                                        logger.warning(f"删除所有 aicr projectFiles 失败: {str(e)}")
                                    
                                    # 删除projectTree
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
                aicr_sessions = [s for s in sessions_to_delete if is_aicr_session_id(s.get("key", ""))]
                if aicr_sessions:
                    try:
                        # 收集所有需要删除的文件路径
                        files_to_delete = []
                        for session in aicr_sessions:
                            session_id = session.get("key", "")
                            if is_aicr_session_id(session_id):
                                # 首先尝试从映射表获取文件ID
                                file_id = None
                                try:
                                    mapping = await self.sync_service.mapping_service.get_mapping_by_session_id(session_id)
                                    if mapping:
                                        file_id = mapping.get("fileId")
                                except Exception as e:
                                    logger.debug(f"获取映射关系失败: sessionId={session_id}, 错误: {str(e)}")
                                
                                # 如果映射表不存在，尝试从 Session ID 解析文件路径（备用方案）
                                if not file_id:
                                    file_id = self._try_parse_file_path_from_session_id(session_id)
                                
                                # 删除静态文件系统中的文件
                                if file_id:
                                    try:
                                        if self.file_storage.file_exists(file_id):
                                            deleted = self.file_storage.delete_file(file_id)
                                            if deleted:
                                                logger.info(f"批量删除中已删除 aicr 静态文件: sessionId={session_id}, fileId={file_id}")
                                            else:
                                                logger.warning(f"批量删除 aicr 静态文件失败: sessionId={session_id}, fileId={file_id}")
                                    except Exception as e:
                                        logger.warning(f"批量删除 aicr 静态文件失败: sessionId={session_id}, fileId={file_id}, 错误: {str(e)}")
                                
                                # 提取项目ID和文件路径（用于删除 MongoDB 中的 projectFiles）
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
        user_id: Optional[str] = None,
        source_client: str = "yipet"
    ) -> Dict[str, Any]:
        """
        更新会话数据
        
        对于 AICR 相关的 Session，会将 pageContent 写入文件系统并同步到 ProjectFiles。
        
        Args:
            session_id: 会话ID
            session_data: 要更新的会话数据
            user_id: 用户ID（可选）
            source_client: 来源客户端：yiweb/yipet/yih5（默认：yipet）
        
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
            
            # 对于 AICR 相关的 Session，处理文件存储和同步
            page_content = session_data.get("pageContent")
            if is_aicr_session_id(session_id) and page_content is not None:
                # 提取项目ID
                project_id = None
                # 尝试从映射表获取
                mapping = await self.sync_service.mapping_service.get_mapping_by_session_id(session_id)
                if mapping:
                    project_id = mapping.get("projectId")
                    file_id = mapping.get("fileId")
                else:
                    # 尝试从 Session ID 解析
                    parts = session_id.split("_", 2)
                    if len(parts) >= 3:
                        project_id = parts[1]
                        file_id = parse_session_id_to_file_path(session_id, project_id)
                    else:
                        file_id = None
                
                if project_id and file_id:
                    # 同步到文件系统
                    sync_result = await self.sync_service.sync_session_to_project_file(
                        session_id=session_id,
                        content=page_content,
                        project_id=project_id,
                        source_client=source_client
                    )
                    if not sync_result.get("success"):
                        logger.warning(f"同步 Session 到文件系统失败: {session_id}, 错误: {sync_result.get('error')}")
            
            # 获取当前时间
            current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
            
            # 构建更新数据（保留原有数据，只更新提供的字段）
            update_doc = {
                "updatedTime": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 更新字段
            for field in ["url", "title", "pageTitle", "pageDescription", "tags", "imageDataUrl", "isFavorite"]:
                if field in session_data and session_data[field] is not None:
                    update_doc[field] = session_data[field]
            
            # 特殊处理 pageContent 字段（对于 AICR 相关的 Session）
            if "pageContent" in session_data and session_data["pageContent"] is not None:
                page_content = session_data["pageContent"]
                if is_aicr_session_id(session_id):
                    # 对于 AICR 相关的 Session，计算哈希值而不是存储内容
                    import hashlib
                    page_content_hash = hashlib.md5(page_content.encode('utf-8')).hexdigest()
                    update_doc["pageContentHash"] = page_content_hash
                    update_doc["pageContent"] = ""  # 不存储实际内容
                else:
                    # 对于非 AICR 相关的 Session，正常处理
                    update_doc["pageContent"] = page_content
            
            # 特殊处理 messages 字段，需要规范化
            if "messages" in session_data and session_data["messages"] is not None:
                messages = session_data["messages"]
                normalized_messages = []
                if messages:
                    normalized_messages = [normalize_message(msg) for msg in messages if msg]
                update_doc["messages"] = normalized_messages
            
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






