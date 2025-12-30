"""
同步服务 - 实现 ProjectFiles 与 Session 的多端双向同步

职责：
- 同步 ProjectFiles 到 Session
- 同步 Session 到 ProjectFiles
- 冲突检测与解决（Last Write Wins 策略）
"""
import logging
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from modules.services.fileStorageService import FileStorageService
from modules.services.mappingService import MappingService
from modules.utils.idConverter import (
    normalize_file_path_to_session_id,
    parse_session_id_to_file_path,
    extract_project_id_from_file_path
)

logger = logging.getLogger(__name__)


class SyncService:
    """同步服务"""
    
    def __init__(self):
        self.file_storage = FileStorageService()
        self.mapping_service = MappingService()
        self._initialized = False
    
    async def initialize(self):
        """初始化服务"""
        if not self._initialized:
            await self.mapping_service.initialize()
            self._initialized = True
    
    async def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            await self.initialize()
    
    async def sync_project_file_to_session(
        self,
        file_id: str,
        project_id: str,
        source_client: str = "yiweb"
    ) -> Dict[str, Any]:
        """
        同步 ProjectFiles 到 Session
        
        Args:
            file_id: ProjectFiles ID
            project_id: 项目ID
            source_client: 来源客户端：yiweb/yipet/yih5
        
        Returns:
            同步结果
        """
        await self._ensure_initialized()
        
        try:
            # 1. 读取文件内容
            if not self.file_storage.file_exists(file_id):
                logger.warning(f"文件不存在，无法同步: {file_id}")
                return {"success": False, "error": "文件不存在"}
            
            content = self.file_storage.read_file_content(file_id)
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # 2. 生成或查询 Session ID
            session_id = normalize_file_path_to_session_id(file_id, project_id)
            
            # 3. 查询或创建映射关系
            mapping = await self.mapping_service.get_or_create_mapping(
                file_id, session_id, project_id
            )
            
            # 4. 更新映射表（增加版本号）
            await self.mapping_service.update_mapping(
                file_id,
                session_id,
                project_id,
                sync_status="synced",
                last_modified_by=source_client,
                version=mapping.get("version", 0) + 1
            )
            
            logger.info(f"同步 ProjectFiles 到 Session 成功: fileId={file_id}, sessionId={session_id}")
            return {
                "success": True,
                "session_id": session_id,
                "file_id": file_id,
                "content_hash": content_hash
            }
        except Exception as e:
            logger.error(f"同步 ProjectFiles 到 Session 失败: fileId={file_id}, 错误: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def sync_session_to_project_file(
        self,
        session_id: str,
        content: str,
        project_id: Optional[str] = None,
        source_client: str = "yipet",
        expected_version: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        同步 Session 到 ProjectFiles
        
        Args:
            session_id: Session ID
            content: 文件内容
            project_id: 项目ID（可选，如果不提供则从映射表或 Session ID 解析）
            source_client: 来源客户端：yiweb/yipet/yih5
            expected_version: 期望的版本号（用于冲突检测）
        
        Returns:
            同步结果
        """
        await self._ensure_initialized()
        
        try:
            # 1. 查询映射表获取 ProjectFiles ID
            mapping = await self.mapping_service.get_mapping_by_session_id(session_id)
            
            if not mapping:
                # 尝试反向解析（备用方案）
                if not project_id:
                    logger.warning(f"无法找到 Session ID 对应的映射关系，且未提供 project_id: {session_id}")
                    return {"success": False, "error": "无法找到映射关系"}
                
                file_id = parse_session_id_to_file_path(session_id, project_id)
                if not file_id:
                    logger.warning(f"无法从 Session ID 解析文件路径: {session_id}")
                    return {"success": False, "error": "无法解析文件路径"}
                
                # 创建映射关系
                mapping = await self.mapping_service.create_mapping(
                    file_id, session_id, project_id
                )
            else:
                file_id = mapping["fileId"]
                if not project_id:
                    project_id = mapping["projectId"]
            
            # 2. 冲突检测
            if expected_version is not None:
                current_version = mapping.get("version", 0)
                if current_version != expected_version:
                    logger.warning(
                        f"检测到版本冲突: sessionId={session_id}, "
                        f"expected={expected_version}, actual={current_version}"
                    )
                    # 采用 Last Write Wins 策略，继续执行
            
            # 3. 写入文件系统
            success = self.file_storage.write_file_content(file_id, content)
            if not success:
                return {"success": False, "error": "写入文件失败"}
            
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # 4. 更新映射表（增加版本号）
            await self.mapping_service.update_mapping(
                file_id,
                session_id,
                project_id,
                sync_status="synced",
                last_modified_by=source_client,
                version=mapping.get("version", 0) + 1
            )
            
            logger.info(f"同步 Session 到 ProjectFiles 成功: sessionId={session_id}, fileId={file_id}")
            return {
                "success": True,
                "file_id": file_id,
                "session_id": session_id,
                "content_hash": content_hash
            }
        except Exception as e:
            logger.error(f"同步 Session 到 ProjectFiles 失败: sessionId={session_id}, 错误: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def get_sync_status(self, file_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取同步状态
        
        Args:
            file_id: ProjectFiles ID（可选）
            session_id: Session ID（可选）
        
        Returns:
            同步状态信息
        """
        await self._ensure_initialized()
        
        try:
            if file_id:
                mapping = await self.mapping_service.get_mapping_by_file_id(file_id)
            elif session_id:
                mapping = await self.mapping_service.get_mapping_by_session_id(session_id)
            else:
                return {"success": False, "error": "必须提供 file_id 或 session_id"}
            
            if not mapping:
                return {"success": False, "error": "映射关系不存在"}
            
            # 检查文件是否存在
            file_exists = self.file_storage.file_exists(mapping["fileId"])
            
            return {
                "success": True,
                "mapping": mapping,
                "file_exists": file_exists,
                "file_size": self.file_storage.get_file_size(mapping["fileId"]) if file_exists else 0
            }
        except Exception as e:
            logger.error(f"获取同步状态失败: 错误: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

