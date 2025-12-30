"""
文件存储服务 - 统一管理 ProjectFiles 和 Session 的文件内容存储

职责：
- 将文件内容存储在文件系统中，而不是 MongoDB
- 提供原子写入机制，确保数据安全
- 支持目录结构保持
"""
import os
import logging
import hashlib
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FileStorageService:
    """文件存储服务"""
    
    def __init__(self, base_dir: str = "./static/files"):
        """
        初始化文件存储服务
        
        Args:
            base_dir: 基础目录，默认：YiAi 项目的 ./static/files 目录
        """
        self.base_dir = os.path.abspath(base_dir)
        self._ensure_base_dir()
    
    def _ensure_base_dir(self):
        """确保基础目录存在"""
        try:
            os.makedirs(self.base_dir, exist_ok=True)
            logger.info(f"文件存储基础目录已准备: {self.base_dir}")
        except Exception as e:
            logger.error(f"创建文件存储基础目录失败: {self.base_dir}, 错误: {e}", exc_info=True)
            raise
    
    def get_file_path(self, project_files_id: str) -> str:
        """
        获取文件系统路径（统一使用 ProjectFiles ID 作为文件路径）
        
        Args:
            project_files_id: ProjectFiles ID，如：developer/process/process_claim_2025-12_xxx.md
        
        Returns:
            完整文件路径，如：./static/files/developer/process/process_claim_2025-12_xxx.md
        
        Raises:
            ValueError: 如果路径不安全（包含路径遍历攻击）
        """
        # 确保路径安全（防止路径遍历攻击）
        safe_path = os.path.normpath(project_files_id).lstrip('/')
        if '..' in safe_path or safe_path.startswith('/'):
            raise ValueError(f"无效的文件路径: {project_files_id}")
        
        return os.path.join(self.base_dir, safe_path)
    
    def read_file_content(self, project_files_id: str) -> str:
        """
        从文件系统读取文件内容（ProjectFiles 和 Session 共享同一个文件）
        
        Args:
            project_files_id: ProjectFiles ID，如：developer/process/process_claim_2025-12_xxx.md
        
        Returns:
            文件内容
        
        Raises:
            FileNotFoundError: 如果文件不存在
        """
        file_path = self.get_file_path(project_files_id)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.debug(f"成功读取文件: {file_path}, 大小: {len(content)} 字节")
                return content
        except FileNotFoundError:
            logger.warning(f"文件不存在: {file_path}")
            raise FileNotFoundError(f"文件不存在: {file_path}")
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, 错误: {e}", exc_info=True)
            raise
    
    def write_file_content(self, project_files_id: str, content: str) -> bool:
        """
        写入文件内容到文件系统（ProjectFiles 和 Session 共享同一个文件）
        使用原子写入机制（临时文件+重命名），确保数据安全
        
        Args:
            project_files_id: ProjectFiles ID，如：developer/process/process_claim_2025-12_xxx.md
            content: 文件内容
        
        Returns:
            是否写入成功
        """
        file_path = self.get_file_path(project_files_id)
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 写入文件（原子操作：先写入临时文件，再重命名）
            temp_path = f"{file_path}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 原子重命名
            os.replace(temp_path, file_path)
            
            logger.info(f"成功写入文件: {file_path}, 大小: {len(content)} 字节")
            return True
        except Exception as e:
            logger.error(f"写入文件失败: {file_path}, 错误: {e}", exc_info=True)
            # 清理临时文件
            temp_path = f"{file_path}.tmp"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return False
    
    def get_file_content_hash(self, project_files_id: str) -> str:
        """
        获取文件内容的哈希值
        
        Args:
            project_files_id: ProjectFiles ID
        
        Returns:
            文件内容的 MD5 哈希值
        """
        try:
            content = self.read_file_content(project_files_id)
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        except FileNotFoundError:
            return ""
    
    def file_exists(self, project_files_id: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            project_files_id: ProjectFiles ID
        
        Returns:
            文件是否存在
        """
        file_path = self.get_file_path(project_files_id)
        return os.path.exists(file_path)
    
    def delete_file(self, project_files_id: str) -> bool:
        """
        删除文件
        
        Args:
            project_files_id: ProjectFiles ID
        
        Returns:
            是否删除成功
        """
        file_path = self.get_file_path(project_files_id)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"成功删除文件: {file_path}")
                return True
            else:
                logger.warning(f"文件不存在，无法删除: {file_path}")
                return False
        except Exception as e:
            logger.error(f"删除文件失败: {file_path}, 错误: {e}", exc_info=True)
            return False
    
    def get_file_size(self, project_files_id: str) -> int:
        """
        获取文件大小（字节）
        
        Args:
            project_files_id: ProjectFiles ID
        
        Returns:
            文件大小（字节），如果文件不存在返回 0
        """
        file_path = self.get_file_path(project_files_id)
        try:
            return os.path.getsize(file_path)
        except FileNotFoundError:
            return 0
        except Exception as e:
            logger.error(f"获取文件大小失败: {file_path}, 错误: {e}", exc_info=True)
            return 0

