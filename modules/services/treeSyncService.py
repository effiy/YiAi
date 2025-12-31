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
            
            # 规范化函数（提前定义，供 files_map 构建使用）
            def normalize_file_id_for_map(file_id: str) -> str:
                """规范化文件ID，去除重复的 project_id 前缀"""
                if not file_id:
                    return ""
                
                # 去除开头的斜杠和多余的空格，统一路径分隔符
                normalized = file_id.strip().lstrip('/').replace('\\', '/')
                
                # 分割路径为部分，去除空部分
                parts = [p for p in normalized.split('/') if p]
                
                if not parts:
                    return ""
                
                # 去除所有重复的 project_id 前缀（不区分大小写）
                while len(parts) > 1 and parts[0].lower() == project_id.lower() and parts[1].lower() == project_id.lower():
                    # 去除第一个重复的 project_id
                    parts = parts[1:]
                
                # 确保路径以 project_id 开头（不区分大小写）
                if parts[0].lower() != project_id.lower():
                    # 不以 project_id 开头，添加前缀
                    return f"{project_id}/{'/'.join(parts)}"
                else:
                    # 已经以 project_id 开头，直接使用
                    return '/'.join(parts)
            
            # 构建文件映射：fileId -> content（同时支持原始和规范化的 file_id）
            files_map = {}
            for file_doc in files_docs:
                file_id = file_doc.get("fileId") or file_doc.get("id") or file_doc.get("path")
                if file_id:
                    # 规范化 file_id
                    normalized_file_id = normalize_file_id_for_map(file_id)
                    
                    # 从文件系统读取内容（优先使用规范化后的 file_id）
                    content = ""
                    if normalized_file_id and self.file_storage.file_exists(normalized_file_id):
                        try:
                            content = self.file_storage.read_file_content(normalized_file_id)
                        except Exception as e:
                            logger.warning(f"读取文件内容失败: fileId={normalized_file_id}, 错误: {str(e)}")
                    elif self.file_storage.file_exists(file_id):
                        try:
                            content = self.file_storage.read_file_content(file_id)
                        except Exception as e:
                            logger.warning(f"读取文件内容失败: fileId={file_id}, 错误: {str(e)}")
                    
                    # 同时存储原始和规范化的 file_id，方便查找
                    files_map[file_id] = content
                    if normalized_file_id and normalized_file_id != file_id:
                        files_map[normalized_file_id] = content
            
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
            
            # 使用与 files_map 相同的规范化函数
            normalize_node_id = normalize_file_id_for_map
            
            def process_tree_node(node: Dict[str, Any], parent_path: str = ""):
                """递归处理树节点"""
                node_id = node.get("id", "")
                node_name = node.get("name", "")
                node_type = node.get("type", "")
                
                if not node_id:
                    return
                
                # 规范化 node_id，去除重复的 project_id 前缀
                normalized_node_id = normalize_node_id(node_id)
                
                # 构建完整路径
                if parent_path:
                    # 如果 parent_path 存在，使用 parent_path + node_name
                    # 但需要确保 parent_path 和 node_name 不会导致重复的 project_id
                    parent_parts = [p for p in parent_path.split('/') if p]
                    # 如果 parent_path 已经以 project_id 开头，且 node_name 也是 project_id，则跳过
                    if parent_parts and parent_parts[0].lower() == project_id.lower() and node_name.lower() == project_id.lower():
                        full_path = parent_path
                    else:
                        full_path = f"{parent_path}/{node_name}"
                else:
                    # 如果没有 parent_path，使用规范化后的 node_id
                    full_path = normalized_node_id
                
                # 再次规范化 full_path，确保没有重复的 project_id
                full_path = normalize_node_id(full_path)
                
                if node_type == "folder":
                    # 创建目录
                    dir_path = self.file_storage.get_file_path(full_path)
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path, exist_ok=True)
                        created_dirs.append(full_path)
                        logger.debug(f"创建目录: {full_path} (原始 node_id: {node_id})")
                    
                    # 递归处理子节点
                    children = node.get("children", [])
                    for child in children:
                        process_tree_node(child, full_path)
                
                elif node_type == "file":
                    # 处理文件 - 使用规范化后的 node_id
                    normalized_file_id = normalized_node_id
                    expected_files.add(normalized_file_id)
                    
                    # 确保文件存在且内容正确
                    file_path = self.file_storage.get_file_path(normalized_file_id)
                    # 使用原始 node_id 从 files_map 获取内容（因为 files_map 的 key 可能是原始 node_id）
                    file_content = files_map.get(node_id, "") or files_map.get(normalized_file_id, "")
                    
                    # 检查文件是否存在
                    if os.path.exists(file_path):
                        # 检查内容是否一致
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                existing_content = f.read()
                            if existing_content != file_content:
                                # 内容不一致，更新文件
                                self.file_storage.write_file_content(normalized_file_id, file_content)
                                updated_files.append(normalized_file_id)
                                logger.debug(f"更新文件: {normalized_file_id} (原始 node_id: {node_id})")
                        except Exception as e:
                            logger.warning(f"读取文件失败: {normalized_file_id}, 错误: {str(e)}")
                            # 重新写入文件
                            self.file_storage.write_file_content(normalized_file_id, file_content)
                            updated_files.append(normalized_file_id)
                    else:
                        # 文件不存在，创建文件
                        self.file_storage.write_file_content(normalized_file_id, file_content)
                        created_files.append(normalized_file_id)
                        logger.debug(f"创建文件: {normalized_file_id} (原始 node_id: {node_id})")
            
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
        
        确保文件路径格式与 ZIP 导入保持一致：
        - ZIP 导入：fileId 不包含 projectId（如 "src/file.js"），需要添加 projectId 前缀
        - 创建文件：fileId 包含 projectId（如 "myProject/src/file.js"），直接使用
        - 处理重复：如果 fileId 包含重复的 projectId（如 "myProject/myProject/src/file.js"），去除重复部分
        
        Args:
            file_id: 文件ID
            project_id: 项目ID
            content: 文件内容
        
        Returns:
            同步结果
        """
        await self._ensure_initialized()
        
        try:
            # 规范化文件路径
            # 1. 去除开头的斜杠和多余的空格，统一路径分隔符
            normalized_file_id = file_id.strip().lstrip('/').replace('\\', '/')
            
            # 2. 分割路径为部分，去除空部分
            parts = [p for p in normalized_file_id.split('/') if p]
            
            if not parts:
                # 空路径，使用 project_id 作为文件名（不应该发生，但做保护）
                normalized_file_id = project_id
            else:
                # 3. 去除所有重复的 project_id 前缀（不区分大小写）
                # 只去除开头的连续重复 project_id，保留路径中间可能存在的同名目录
                while len(parts) > 1 and parts[0].lower() == project_id.lower() and parts[1].lower() == project_id.lower():
                    # 去除第一个重复的 project_id
                    parts = parts[1:]
                
                # 4. 确保路径以 project_id 开头（不区分大小写），且只有一个 project_id 前缀
                if parts[0].lower() != project_id.lower():
                    # 不以 project_id 开头，添加前缀
                    normalized_file_id = f"{project_id}/{'/'.join(parts)}"
                else:
                    # 已经以 project_id 开头，直接使用（已经处理了开头的连续重复）
                    normalized_file_id = '/'.join(parts)
            
            # 写入文件系统
            success = self.file_storage.write_file_content(normalized_file_id, content)
            
            if success:
                logger.info(f"同步文件到 static 目录成功: fileId={normalized_file_id} (原始: {file_id})")
                return {"success": True, "file_id": normalized_file_id}
            else:
                logger.warning(f"同步文件到 static 目录失败: fileId={normalized_file_id}")
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

