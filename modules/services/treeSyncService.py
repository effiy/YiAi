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
                    
                    # 尝试从多个可能的路径获取文件内容：
                    # 1. 使用原始 node_id（可能包含旧路径）
                    # 2. 使用规范化后的 node_id（新路径）
                    # 3. 如果文件在新路径已存在，直接从文件系统读取
                    file_content = ""
                    
                    # 首先尝试从 files_map 获取（支持原始和规范化路径）
                    file_content = files_map.get(node_id, "") or files_map.get(normalized_file_id, "")
                    
                    # 如果 files_map 中没有找到，且文件在新路径已存在，直接从文件系统读取
                    if not file_content and os.path.exists(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                        except Exception as e:
                            logger.warning(f"从文件系统读取内容失败: {normalized_file_id}, 错误: {str(e)}")
                    
                    # 如果仍然没有内容，尝试从旧路径读取（处理重命名情况）
                    if not file_content:
                        # 尝试从 existing_files 中找到可能的旧路径
                        # 通过文件名匹配（不包含路径）
                        file_name = os.path.basename(normalized_file_id)
                        for existing_file in existing_files:
                            if existing_file.endswith(file_name) and existing_file != normalized_file_id:
                                # 找到可能的旧路径，尝试读取
                                try:
                                    old_file_path = self.file_storage.get_file_path(existing_file)
                                    if os.path.exists(old_file_path):
                                        with open(old_file_path, 'r', encoding='utf-8') as f:
                                            file_content = f.read()
                                        logger.info(f"从旧路径读取文件内容: {existing_file} -> {normalized_file_id}")
                                        break
                                except Exception as e:
                                    logger.debug(f"从旧路径读取失败: {existing_file}, 错误: {str(e)}")
                    
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
            # 注意：如果文件被重命名，新路径的文件已经在步骤3中创建，这里只需要删除旧路径的文件
            for existing_file in existing_files:
                if existing_file not in expected_files:
                    # 文件不在预期列表中，需要删除
                    # 这包括：被删除的文件、被重命名后旧路径的文件
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
            # 使用统一的规范化方法，确保与删除时使用完全相同的逻辑
            normalized_file_id = self._normalize_file_id_for_static(file_id, project_id)
            
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
    
    async def delete_project_file_from_static(self, file_id: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        从 static 目录删除文件
        
        Args:
            file_id: 文件ID（可能是规范化后的，也可能是原始的）
            project_id: 项目ID（可选，用于尝试多种路径格式）
        
        Returns:
            删除结果
        """
        await self._ensure_initialized()
        
        try:
            # 尝试删除的路径列表（按优先级排序）
            paths_to_try = []
            
            # 如果提供了 project_id，尝试多种路径格式
            if project_id:
                from modules.utils.idConverter import normalize_project_file_id
                
                # 规范化 file_id（去除首尾空格和斜杠）
                clean_file_id = file_id.strip().lstrip('/').replace('\\', '/')
                parts = [p for p in clean_file_id.split('/') if p]
                
                # 1. 规范化后的路径（确保以 projectId 开头）- 使用 normalize_project_file_id
                normalized = normalize_project_file_id(clean_file_id, project_id)
                paths_to_try.append(normalized)
                
                # 2. 如果 file_id 已经包含 projectId，尝试去除 projectId 前缀
                if parts and len(parts) > 1 and parts[0].lower() == project_id.lower():
                    without_prefix = '/'.join(parts[1:])
                    if without_prefix:
                        paths_to_try.append(without_prefix)
                
                # 3. 如果 file_id 不包含 projectId，尝试添加 projectId 前缀
                if not parts or parts[0].lower() != project_id.lower():
                    with_prefix = f"{project_id}/{clean_file_id}"
                    paths_to_try.append(with_prefix)
                
                # 4. 使用 sync_project_file_to_static 的规范化逻辑（与写入时保持一致）
                # 这个逻辑与写入文件时使用的逻辑完全一致
                normalized_file_id = self._normalize_file_id_for_static(clean_file_id, project_id)
                if normalized_file_id and normalized_file_id not in paths_to_try:
                    paths_to_try.append(normalized_file_id)
            
            # 添加原始 file_id（去重）
            if file_id not in paths_to_try:
                paths_to_try.append(file_id)
            
            # 去重并保持顺序
            seen = set()
            unique_paths = []
            for path in paths_to_try:
                if path and path not in seen:
                    seen.add(path)
                    unique_paths.append(path)
            
            logger.debug(f"[删除静态文件] 尝试路径列表: fileId={file_id}, projectId={project_id}, paths={unique_paths}")
            
            # 尝试每个路径
            for path in unique_paths:
                try:
                    if self.file_storage.file_exists(path):
                        success = self.file_storage.delete_file(path)
                        if success:
                            logger.info(f"从 static 目录删除文件成功: fileId={path} (原始: {file_id})")
                            return {"success": True, "file_id": path, "original_file_id": file_id}
                        else:
                            logger.warning(f"从 static 目录删除文件失败: fileId={path}")
                            # 继续尝试下一个路径
                            continue
                except Exception as e:
                    logger.debug(f"检查路径失败: {path}, 错误: {str(e)}")
                    continue
            
            # 如果所有路径都尝试过了还没找到，尝试通过文件名扫描匹配
            if project_id:
                logger.debug(f"路径匹配失败，尝试通过文件名扫描匹配: fileId={file_id}, projectId={project_id}")
                matched_path = await self._find_file_by_name_in_project(file_id, project_id)
                if matched_path:
                    try:
                        if self.file_storage.file_exists(matched_path):
                            success = self.file_storage.delete_file(matched_path)
                            if success:
                                logger.info(f"通过文件名扫描找到并删除文件: fileId={matched_path} (原始: {file_id})")
                                return {"success": True, "file_id": matched_path, "original_file_id": file_id, "found_by_scan": True}
                    except Exception as e:
                        logger.warning(f"删除扫描到的文件失败: {matched_path}, 错误: {str(e)}")
            
            # 所有方法都尝试过了，文件不存在
            logger.debug(f"文件不存在，跳过删除: fileId={file_id}, 尝试的路径: {unique_paths}")
            return {"success": True, "file_id": file_id, "skipped": True}
        
        except Exception as e:
            logger.error(f"从 static 目录删除文件失败: fileId={file_id}, 错误: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _normalize_file_id_for_static(self, file_id: str, project_id: str) -> str:
        """
        规范化文件ID，与 sync_project_file_to_static 使用完全相同的逻辑
        
        Args:
            file_id: 文件ID
            project_id: 项目ID
        
        Returns:
            规范化后的文件ID
        """
        # 1. 去除开头的斜杠和多余的空格，统一路径分隔符
        normalized_file_id = file_id.strip().lstrip('/').replace('\\', '/')
        
        # 2. 分割路径为部分，去除空部分
        parts = [p for p in normalized_file_id.split('/') if p]
        
        if not parts:
            # 空路径，使用 project_id 作为文件名（不应该发生，但做保护）
            return project_id
        
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
        
        return normalized_file_id
    
    async def _find_file_by_name_in_project(self, file_id: str, project_id: str) -> Optional[str]:
        """
        通过扫描项目目录，根据文件名匹配找到文件路径
        
        Args:
            file_id: 文件ID（可能是完整路径或只是文件名）
            project_id: 项目ID
        
        Returns:
            找到的文件路径，如果没找到返回 None
        """
        try:
            # 获取文件名（路径的最后一部分）
            file_name = os.path.basename(file_id.replace('\\', '/'))
            if not file_name:
                return None
            
            # 获取项目目录路径
            project_dir = self.file_storage.get_file_path(project_id)
            if not os.path.exists(project_dir) or not os.path.isdir(project_dir):
                logger.debug(f"项目目录不存在: {project_dir}")
                return None
            
            logger.debug(f"扫描项目目录查找文件: projectId={project_id}, fileName={file_name}, projectDir={project_dir}")
            
            # 递归扫描项目目录下的所有文件
            matched_files = []
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    if file == file_name:
                        # 找到匹配的文件，构建相对路径
                        full_path = os.path.join(root, file)
                        # 转换为相对于 static 目录的路径
                        relative_path = os.path.relpath(full_path, self.file_storage.base_dir)
                        # 统一使用正斜杠
                        relative_path = relative_path.replace('\\', '/')
                        matched_files.append(relative_path)
                        logger.debug(f"找到匹配文件: {relative_path}")
            
            if matched_files:
                # 如果有多个匹配，优先选择路径最接近 file_id 的
                if len(matched_files) == 1:
                    return matched_files[0]
                else:
                    # 如果有多个匹配，尝试找到路径最接近的
                    file_id_parts = file_id.replace('\\', '/').strip('/').split('/')
                    best_match = None
                    best_score = -1
                    
                    for matched_path in matched_files:
                        matched_parts = matched_path.replace('\\', '/').strip('/').split('/')
                        # 计算匹配度：相同路径部分的数量
                        score = 0
                        min_len = min(len(file_id_parts), len(matched_parts))
                        for i in range(min_len):
                            if i < len(file_id_parts) and i < len(matched_parts):
                                if file_id_parts[-1-i].lower() == matched_parts[-1-i].lower():
                                    score += 1
                                else:
                                    break
                        
                        if score > best_score:
                            best_score = score
                            best_match = matched_path
                    
                    logger.info(f"找到 {len(matched_files)} 个匹配文件，选择最佳匹配: {best_match}")
                    return best_match if best_match else matched_files[0]
            
            logger.debug(f"未找到匹配文件: fileName={file_name}, projectId={project_id}")
            return None
            
        except Exception as e:
            logger.warning(f"扫描项目目录查找文件失败: fileId={file_id}, projectId={project_id}, 错误: {str(e)}")
            return None
    
    async def delete_project_folder_from_static(self, folder_id: str) -> Dict[str, Any]:
        """
        从 static 目录递归删除文件夹及其所有子文件
        
        Args:
            folder_id: 文件夹ID（路径）
        
        Returns:
            删除结果，包含删除的文件数量
        """
        await self._ensure_initialized()
        
        try:
            folder_path = self.file_storage.get_file_path(folder_id)
            deleted_count = 0
            
            if os.path.exists(folder_path):
                if os.path.isdir(folder_path):
                    # 递归删除文件夹下的所有文件
                    for root, dirs, files in os.walk(folder_path, topdown=False):
                        # 先删除所有文件
                        for file_name in files:
                            file_path = os.path.join(root, file_name)
                            try:
                                os.remove(file_path)
                                deleted_count += 1
                                logger.debug(f"删除文件: {file_path}")
                            except Exception as e:
                                logger.warning(f"删除文件失败: {file_path}, 错误: {str(e)}")
                        
                        # 再删除空目录
                        try:
                            os.rmdir(root)
                            logger.debug(f"删除空目录: {root}")
                        except Exception as e:
                            logger.debug(f"删除目录失败（可能非空）: {root}, 错误: {str(e)}")
                    
                    logger.info(f"从 static 目录递归删除文件夹成功: folderId={folder_id}, 删除文件数={deleted_count}")
                    return {"success": True, "folder_id": folder_id, "deleted_count": deleted_count}
                else:
                    # 如果是文件而不是文件夹，使用文件删除方法
                    return await self.delete_project_file_from_static(folder_id)
            else:
                logger.debug(f"文件夹不存在，跳过删除: folderId={folder_id}")
                return {"success": True, "folder_id": folder_id, "skipped": True, "deleted_count": 0}
        
        except Exception as e:
            logger.error(f"从 static 目录递归删除文件夹失败: folderId={folder_id}, 错误: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e), "deleted_count": deleted_count}
    
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

