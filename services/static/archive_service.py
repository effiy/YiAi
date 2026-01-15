import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def unzip_from_path(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    解压本地 ZIP 文件到 static 目录
    
    Args:
        params: 参数字典
            - file_path (str): 本地 ZIP 文件绝对路径
            - project_id (str, optional): 项目 ID
            
    Returns:
        Dict[str, Any]: 解压结果
            - success (bool): 是否成功
            - target_directory (str): 目标目录
            - extracted_files_count (int): 解压文件数
            
    Raises:
        ValueError: 文件路径为空、文件不存在或解压失败

    Example:
        GET /?module_name=services.static.archive_service&method_name=unzip_from_path&parameters={"file_path": "/tmp/test.zip", "project_id": "my_project"}
    """
    file_path = params.get('file_path')
    project_id = params.get('project_id')
    
    if not file_path:
        raise ValueError("file_path is required")
        
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
        
    import zipfile
    import shutil
    from core.settings import settings
    
    base_dir = settings.static_base_dir
    if project_id:
        target_dir = os.path.join(base_dir, project_id)
    else:
        # 如果没有 project_id，使用文件名（无后缀）作为目录
        zip_name = os.path.splitext(os.path.basename(file_path))[0]
        target_dir = os.path.join(base_dir, zip_name)
        
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
            
        return {
            "success": True,
            "target_directory": target_dir,
            "extracted_files_count": len(zip_ref.namelist())
        }
    except Exception as e:
        logger.error(f"Failed to unzip file: {e}")
        raise ValueError(f"Failed to unzip file: {str(e)}")
