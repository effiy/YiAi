"""
关联映射服务 - 管理 ProjectFiles ID 与 Session ID 的映射关系

职责：
- 创建和维护 ProjectFiles 与 Session 的关联映射
- 提供版本号管理（乐观锁）
- 记录同步状态和最后修改信息
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from modules.database.mongoClient import MongoClient

logger = logging.getLogger(__name__)


class MappingService:
    """关联映射服务"""
    
    def __init__(self):
        self.mongo_client = MongoClient()
        self.collection_name = "fileSessionMapping"
        self._initialized = False
    
    async def initialize(self):
        """初始化服务"""
        if not self._initialized:
            await self.mongo_client.initialize()
            await self._ensure_indexes()
            self._initialized = True
    
    async def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            await self.initialize()
    
    async def _ensure_indexes(self):
        """确保索引存在"""
        try:
            # 确保数据库已初始化
            await self.mongo_client.initialize()
            collection = self.mongo_client.db[self.collection_name]
            # 创建唯一索引
            await collection.create_index("fileId", unique=True, background=True)
            await collection.create_index("sessionId", unique=True, background=True)
            # 创建复合索引
            await collection.create_index([("projectId", 1), ("filePath", 1)], background=True)
            await collection.create_index([("syncStatus", 1), ("lastSyncTime", 1)], background=True)
            await collection.create_index("version", background=True)
            logger.info("映射表索引已创建")
        except Exception as e:
            logger.warning(f"创建映射表索引失败（可能已存在）: {str(e)}")
    
    async def get_mapping_by_file_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ProjectFiles ID 获取映射关系
        
        Args:
            file_id: ProjectFiles ID
        
        Returns:
            映射关系，如果不存在返回 None
        """
        await self._ensure_initialized()
        
        try:
            mapping = await self.mongo_client.find_one(
                collection_name=self.collection_name,
                query={"fileId": file_id}
            )
            return mapping
        except Exception as e:
            logger.error(f"获取映射关系失败: fileId={file_id}, 错误: {str(e)}", exc_info=True)
            return None
    
    async def get_mapping_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 Session ID 获取映射关系
        
        Args:
            session_id: Session ID
        
        Returns:
            映射关系，如果不存在返回 None
        """
        await self._ensure_initialized()
        
        try:
            mapping = await self.mongo_client.find_one(
                collection_name=self.collection_name,
                query={"sessionId": session_id}
            )
            return mapping
        except Exception as e:
            logger.error(f"获取映射关系失败: sessionId={session_id}, 错误: {str(e)}", exc_info=True)
            return None
    
    async def create_mapping(
        self,
        file_id: str,
        session_id: str,
        project_id: str,
        sync_status: str = "synced"
    ) -> Dict[str, Any]:
        """
        创建映射关系
        
        Args:
            file_id: ProjectFiles ID
            session_id: Session ID
            project_id: 项目ID
            sync_status: 同步状态（默认：synced）
        
        Returns:
            创建的映射关系
        """
        await self._ensure_initialized()
        
        current_time = datetime.now(timezone.utc)
        mapping_doc = {
            "fileId": file_id,
            "sessionId": session_id,
            "projectId": project_id,
            "filePath": file_id,  # 文件系统路径，等于 fileId
            "createdAt": current_time,
            "updatedAt": current_time,
            "syncStatus": sync_status,
            "lastSyncTime": current_time,
            "version": 1,  # 初始版本号为 1
            "lastModifiedBy": None,
            "lastModifiedAt": current_time
        }
        
        try:
            await self.mongo_client.insert_one(
                collection_name=self.collection_name,
                document=mapping_doc
            )
            logger.info(f"创建映射关系成功: fileId={file_id}, sessionId={session_id}")
            return mapping_doc
        except Exception as e:
            logger.error(f"创建映射关系失败: fileId={file_id}, sessionId={session_id}, 错误: {str(e)}", exc_info=True)
            raise
    
    async def get_or_create_mapping(
        self,
        file_id: str,
        session_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        获取或创建映射关系
        
        Args:
            file_id: ProjectFiles ID
            session_id: Session ID
            project_id: 项目ID
        
        Returns:
            映射关系
        """
        # 先尝试通过 fileId 查找
        mapping = await self.get_mapping_by_file_id(file_id)
        if mapping:
            return mapping
        
        # 再尝试通过 sessionId 查找
        mapping = await self.get_mapping_by_session_id(session_id)
        if mapping:
            return mapping
        
        # 如果都不存在，创建新的映射关系
        return await self.create_mapping(file_id, session_id, project_id)
    
    async def update_mapping(
        self,
        file_id: str,
        session_id: str,
        project_id: str,
        sync_status: Optional[str] = None,
        last_modified_by: Optional[str] = None,
        version: Optional[int] = None
    ) -> bool:
        """
        更新映射关系
        
        Args:
            file_id: ProjectFiles ID
            session_id: Session ID
            project_id: 项目ID
            sync_status: 同步状态（可选）
            last_modified_by: 最后修改来源：yiweb/yipet/yih5（可选）
            version: 版本号（可选，如果不提供则自动递增）
        
        Returns:
            是否更新成功
        """
        await self._ensure_initialized()
        
        current_time = datetime.now(timezone.utc)
        update_doc = {
            "updatedAt": current_time,
            "lastSyncTime": current_time
        }
        
        if sync_status is not None:
            update_doc["syncStatus"] = sync_status
        
        if last_modified_by is not None:
            update_doc["lastModifiedBy"] = last_modified_by
            update_doc["lastModifiedAt"] = current_time
        
        # 处理版本号
        if version is not None:
            update_doc["version"] = version
        else:
            # 如果没有提供版本号，先获取当前版本号，然后递增
            existing = await self.get_mapping_by_file_id(file_id)
            if existing:
                current_version = existing.get("version", 0)
                update_doc["version"] = current_version + 1
            else:
                update_doc["version"] = 1
        
        try:
            result = await self.mongo_client.update_one(
                collection_name=self.collection_name,
                query={"fileId": file_id},
                update={"$set": update_doc}
            )
            if result > 0:
                logger.debug(f"更新映射关系成功: fileId={file_id}, version={update_doc.get('version')}")
                return True
            else:
                logger.warning(f"更新映射关系失败: 未找到映射关系 fileId={file_id}")
                return False
        except Exception as e:
            logger.error(f"更新映射关系失败: fileId={file_id}, 错误: {str(e)}", exc_info=True)
            return False
    
    async def delete_mapping(self, file_id: str) -> bool:
        """
        删除映射关系
        
        Args:
            file_id: ProjectFiles ID
        
        Returns:
            是否删除成功
        """
        await self._ensure_initialized()
        
        try:
            result = await self.mongo_client.delete_one(
                collection_name=self.collection_name,
                query={"fileId": file_id}
            )
            if result > 0:
                logger.info(f"删除映射关系成功: fileId={file_id}")
                return True
            else:
                logger.warning(f"删除映射关系失败: 未找到映射关系 fileId={file_id}")
                return False
        except Exception as e:
            logger.error(f"删除映射关系失败: fileId={file_id}, 错误: {str(e)}", exc_info=True)
            return False

