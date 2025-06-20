import os
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from Resp import RespOk

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/docs", tags=["docs"])

# docs目录的绝对路径
DOCS_DIR = Path(__file__).parent.parent / "docs"

@router.get("/")
async def list_docs_directories():
    """
    列出docs目录下的所有子目录
    """
    try:
        if not DOCS_DIR.exists():
            raise HTTPException(status_code=404, detail="docs目录不存在")
        
        directories = []
        for item in DOCS_DIR.iterdir():
            if item.is_dir():
                directories.append({
                    "name": item.name,
                    "path": str(item.relative_to(DOCS_DIR))
                })
        
        return RespOk(data=directories, msg="成功获取docs目录列表")
    except Exception as e:
        logger.error(f"获取docs目录列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取目录列表失败: {str(e)}")

@router.get("/{directory_name}")
async def list_directory_files(directory_name: str):
    """
    列出指定目录下的所有文件
    """
    try:
        target_dir = DOCS_DIR / directory_name
        if not target_dir.exists() or not target_dir.is_dir():
            raise HTTPException(status_code=404, detail=f"目录 {directory_name} 不存在")
        
        files = []
        for item in target_dir.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(target_dir)
                files.append({
                    "name": item.name,
                    "path": str(relative_path),
                    "size": item.stat().st_size,
                    "type": item.suffix
                })
        
        return RespOk(data=files, msg=f"成功获取 {directory_name} 目录文件列表")
    except Exception as e:
        logger.error(f"获取目录文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@router.get("/{directory_name}/{file_path:path}")
async def get_file_content(directory_name: str, file_path: str):
    """
    获取指定文件的内容
    支持文本文件和二进制文件的读取
    """
    try:
        target_file = DOCS_DIR / directory_name / file_path
        
        # 安全检查：确保文件路径在docs目录内
        if not str(target_file.resolve()).startswith(str(DOCS_DIR.resolve())):
            raise HTTPException(status_code=403, detail="访问被拒绝")
        
        if not target_file.exists() or not target_file.is_file():
            raise HTTPException(status_code=404, detail=f"文件 {file_path} 不存在")
        
        # 获取文件扩展名
        file_extension = target_file.suffix.lower()
        
        # 文本文件扩展名列表
        text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.ini', '.cfg', '.conf', '.log'}
        
        if file_extension in text_extensions:
            # 读取文本文件
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                return RespOk(data={
                    "content": content,
                    "file_path": str(target_file.relative_to(DOCS_DIR)),
                    "file_size": target_file.stat().st_size,
                    "file_type": "text"
                }, msg="成功读取文件内容")
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试其他编码
                try:
                    with open(target_file, 'r', encoding='gbk') as f:
                        content = f.read()
                    return RespOk(data={
                        "content": content,
                        "file_path": str(target_file.relative_to(DOCS_DIR)),
                        "file_size": target_file.stat().st_size,
                        "file_type": "text"
                    }, msg="成功读取文件内容")
                except:
                    raise HTTPException(status_code=500, detail="文件编码不支持")
        else:
            # 对于二进制文件，返回文件信息而不是内容
            return RespOk(data={
                "file_path": str(target_file.relative_to(DOCS_DIR)),
                "file_size": target_file.stat().st_size,
                "file_type": "binary",
                "message": "这是二进制文件，无法直接显示内容"
            }, msg="二进制文件信息")
            
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

@router.get("/download/{directory_name}/{file_path:path}")
async def download_file(directory_name: str, file_path: str):
    """
    下载指定文件
    """
    try:
        target_file = DOCS_DIR / directory_name / file_path
        
        # 安全检查：确保文件路径在docs目录内
        if not str(target_file.resolve()).startswith(str(DOCS_DIR.resolve())):
            raise HTTPException(status_code=403, detail="访问被拒绝")
        
        if not target_file.exists() or not target_file.is_file():
            raise HTTPException(status_code=404, detail=f"文件 {file_path} 不存在")
        
        return FileResponse(
            path=target_file,
            filename=target_file.name,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}") 