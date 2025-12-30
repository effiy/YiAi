"""
树同步服务 - 确保 static 目录与 MongoDB projectTree 数据保持一致

职责：
- 同步 projectTree 到 static 目录结构
- 同步 projectFiles 到 static 目录文件
- 确保目录名称、文件名、文件数量、文件内容完全一致
"""
import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from modules.database.mongoClient import MongoClient
from modules.services.fileStorageService import FileStorageService

logger = logging.getLogger(__name__)


class TreeSyncService:
    """树同步服务"""
    
    def __init__(self):
        self.mongo_client = MongoClient()
        self.file_storage = FileStorageService()
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
    
    async def sync_project_tree_to_static(self, project_id: str) -> Dict[str, Any]:
        """
        同步项目的 projectTree 到 static 目录
        
        Args:
            project_id: 项目ID
        
        Returns:
            同步结果
        """
        await self._ensure_initialized()
        
        try:
            # 1. 获取 projectTree 数据
            tree_docs = await self.mongo_client.find_many(
                collection_name="projectTree",
                query={"projectId": project_id}
            )
            
            if not tree_docs or len(tree_docs) == 0:
                logger.warning(f"项目 {project_id} 的 projectTree 数据为空")
                return {"success": False, "error": "projectTree 数据为空"}
            
            # 取第一个树文档（通常一个项目只有一个树文档）
            tree_doc = tree_docs[0]
            tree_data = tree_doc.get("data", [])
            
            if not tree_data:
                logger.warning(f"项目 {project_id} 的树数据为空")
                return {"success": False, "error": "树数据为空"}
            
            # 2. 获取 projectFiles 数据
            files_docs = await self.mongo_client.find_many(
                collection_name="projectFiles",
                query={"projectId": project_id}
            )
            
            # 构建文件映射：fileId -> content
            files_map = {}
            for file_doc in files_docs:
                file_id = file_doc.get("fileId") or file_doc.get("id") or file_doc.get("path")
                if file_id:
                    # 从文件系统读取内容
                    if self.file_storage.file_exists(file_id):
                        try:
                            content = self.file_storage.read_file_content(file_id)
                            files_map[file_id] = content
                        except Exception as e:
                            logger.warning(f"读取文件内容失败: fileId={file_id}, 错误: {str(e)}")
                            files_map[file_id] = ""
            
            # 3. 递归构建 static 目录结构
            created_dirs = []
            created_files = []
            updated_files = []
            deleted_files = []
            
            # 获取 static 目录下该项目的所有现有文件
            project_static_dir = self.file_storage.get_file_path(project_id)
            existing_files = set()
            if os.path.exists(project_static_dir):
                for root, dirs, files in os.walk(project_static_dir):
                    rel_root = os.path.relpath(root, project_static_dir)
                    if rel_root == '.':
                        rel_root = ''
                    for file in files:
                        if rel_root:
                            file_path = f"{project_id}/{rel_root}/{file}"
                        else:
                            file_path = f"{project_id}/{file}"
                        existing_files.add(file_path)
            
            # 从树数据构建应该存在的文件集合
            expected_files = set()
            
            def process_tree_node(node: Dict[str, Any], parent_path: str = ""):
                """递归处理树节点"""
                node_id = node.get("id", "")
                node_name = node.get("name", "")
                node_type = node.get("type", "")
                
                if not node_id:
                    return
                
                # 构建完整路径
                if parent_path:
                    full_path = f"{parent_path}/{node_name}"
                else:
                    full_path = node_id
                
                if node_type == "folder":
                    # 创建目录
                    dir_path = self.file_storage.get_file_path(full_path)
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path, exist_ok=True)
                        created_dirs.append(full_path)
                        logger.debug(f"创建目录: {full_path}")
                    
                    # 递归处理子节点
                    children = node.get("children", [])
                    for child in children:
                        process_tree_node(child, full_path)
                
                elif node_type == "file":
                    # 处理文件
                    expected_files.add(node_id)
                    
                    # 确保文件存在且内容正确
                    file_path = self.file_storage.get_file_path(node_id)
                    file_content = files_map.get(node_id, "")
                    
                    # 检查文件是否存在
                    if os.path.exists(file_path):
                        # 检查内容是否一致
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                existing_content = f.read()
                            if existing_content != file_content:
                                # 内容不一致，更新文件
                                self.file_storage.write_file_content(node_id, file_content)
                                updated_files.append(node_id)
                                logger.debug(f"更新文件: {node_id}")
                        except Exception as e:
                            logger.warning(f"读取文件失败: {node_id}, 错误: {str(e)}")
                            # 重新写入文件
                            self.file_storage.write_file_content(node_id, file_content)
                            updated_files.append(node_id)
                    else:
                        # 文件不存在，创建文件
                        self.file_storage.write_file_content(node_id, file_content)
                        created_files.append(node_id)
                        logger.debug(f"创建文件: {node_id}")
            
            # 处理所有树节点
            for root_node in tree_data:
                process_tree_node(root_node, "")
            
            # 4. 删除不应该存在的文件
            for existing_file in existing_files:
                if existing_file not in expected_files:
                    try:
                        if self.file_storage.file_exists(existing_file):
                            self.file_storage.delete_file(existing_file)
                            deleted_files.append(existing_file)
                            logger.debug(f"删除文件: {existing_file}")
                    except Exception as e:
                        logger.warning(f"删除文件失败: {existing_file}, 错误: {str(e)}")
            
            # 5. 清理空目录
            self._cleanup_empty_dirs(project_id)
            
            logger.info(
                f"同步项目树完成: projectId={project_id}, "
                f"创建目录={len(created_dirs)}, 创建文件={len(created_files)}, "
                f"更新文件={len(updated_files)}, 删除文件={len(deleted_files)}"
            )
            
            return {
                "success": True,
                "project_id": project_id,
                "created_dirs": created_dirs,
                "created_files": created_files,
                "updated_files": updated_files,
                "deleted_files": deleted_files
            }
        
        except Exception as e:
            logger.error(f"同步项目树失败: projectId={project_id}, 错误: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _cleanup_empty_dirs(self, project_id: str):
        """清理空目录"""
        try:
            project_static_dir = self.file_storage.get_file_path(project_id)
            if not os.path.exists(project_static_dir):
                return
            
            # 从最深层的目录开始，向上清理空目录
            for root, dirs, files in os.walk(project_static_dir, topdown=False):
                # 如果目录为空，删除它
                if not dirs and not files:
                    try:
                        os.rmdir(root)
                        logger.debug(f"删除空目录: {root}")
                    except Exception as e:
                        logger.debug(f"删除空目录失败（可能非空）: {root}, 错误: {str(e)}")
        except Exception as e:
            logger.warning(f"清理空目录失败: projectId={project_id}, 错误: {str(e)}")
    
    async def sync_project_file_to_static(self, file_id: str, project_id: str, content: str) -> Dict[str, Any]:
        """
        同步单个 projectFile 到 static 目录
        
        Args:
            file_id: 文件ID
            project_id: 项目ID
            content: 文件内容
        
        Returns:
            同步结果
        """
        await self._ensure_initialized()
        
        try:
            # 确保文件ID以项目ID开头
            if not file_id.startswith(f"{project_id}/"):
                file_id = f"{project_id}/{file_id}"
            
            # 写入文件系统
            success = self.file_storage.write_file_content(file_id, content)
            
            if success:
                logger.info(f"同步文件到 static 目录成功: fileId={file_id}")
                return {"success": True, "file_id": file_id}
            else:
                logger.warning(f"同步文件到 static 目录失败: fileId={file_id}")
                return {"success": False, "error": "写入文件失败"}
        
        except Exception as e:
            logger.error(f"同步文件到 static 目录失败: fileId={file_id}, 错误: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def delete_project_file_from_static(self, file_id: str) -> Dict[str, Any]:
        """
        从 static 目录删除文件
        
        Args:
            file_id: 文件ID
        
        Returns:
            删除结果
        """
        await self._ensure_initialized()
        
        try:
            if self.file_storage.file_exists(file_id):
                success = self.file_storage.delete_file(file_id)
                if success:
                    logger.info(f"从 static 目录删除文件成功: fileId={file_id}")
                    return {"success": True, "file_id": file_id}
                else:
                    logger.warning(f"从 static 目录删除文件失败: fileId={file_id}")
                    return {"success": False, "error": "删除文件失败"}
            else:
                logger.debug(f"文件不存在，跳过删除: fileId={file_id}")
                return {"success": True, "file_id": file_id, "skipped": True}
        
        except Exception as e:
            logger.error(f"从 static 目录删除文件失败: fileId={file_id}, 错误: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def verify_project_tree_sync(self, project_id: str) -> Dict[str, Any]:
        """
        验证项目树同步状态
        
        Args:
            project_id: 项目ID
        
        Returns:
            验证结果
        """
        await self._ensure_initialized()
        
        try:
            # 获取 projectTree 数据
            tree_docs = await self.mongo_client.find_many(
                collection_name="projectTree",
                query={"projectId": project_id}
            )
            
            if not tree_docs or len(tree_docs) == 0:
                return {
                    "success": True,
                    "project_id": project_id,
                    "synced": False,
                    "reason": "projectTree 数据为空"
                }
            
            tree_doc = tree_docs[0]
            tree_data = tree_doc.get("data", [])
            
            # 获取 projectFiles 数据
            files_docs = await self.mongo_client.find_many(
                collection_name="projectFiles",
                query={"projectId": project_id}
            )
            
            # 从树数据构建应该存在的文件集合
            expected_files = set()
            
            def collect_files(node: Dict[str, Any]):
                """递归收集文件ID"""
                node_id = node.get("id", "")
                node_type = node.get("type", "")
                
                if node_type == "file" and node_id:
                    expected_files.add(node_id)
                
                children = node.get("children", [])
                for child in children:
                    collect_files(child)
            
            for root_node in tree_data:
                collect_files(root_node)
            
            # 检查 static 目录中的文件
            project_static_dir = self.file_storage.get_file_path(project_id)
            actual_files = set()
            if os.path.exists(project_static_dir):
                for root, dirs, files in os.walk(project_static_dir):
                    rel_root = os.path.relpath(root, project_static_dir)
                    if rel_root == '.':
                        rel_root = ''
                    for file in files:
                        if rel_root:
                            file_path = f"{project_id}/{rel_root}/{file}"
                        else:
                            file_path = f"{project_id}/{file}"
                        actual_files.add(file_path)
            
            # 比较差异
            missing_files = expected_files - actual_files
            extra_files = actual_files - expected_files
            
            synced = len(missing_files) == 0 and len(extra_files) == 0
            
            return {
                "success": True,
                "project_id": project_id,
                "synced": synced,
                "expected_count": len(expected_files),
                "actual_count": len(actual_files),
                "missing_files": list(missing_files),
                "extra_files": list(extra_files)
            }
        
        except Exception as e:
            logger.error(f"验证项目树同步状态失败: projectId={project_id}, 错误: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

