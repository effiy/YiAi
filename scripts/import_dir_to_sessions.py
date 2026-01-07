#!/usr/bin/env python3
"""
导入指定目录到会话并上传静态文件
用法: python3 scripts/import_dir_to_sessions.py /path/to/source/dir [--api-url https://api.effiy.cn]
"""
import os
import sys
import shutil
import asyncio
import logging
import argparse
import aiohttp
import base64
import mimetypes
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 path
sys.path.append(os.getcwd())

from core.database import db
from core.config import settings
from core.utils import estimate_tokens

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置常量
MAX_FILE_SIZE = 100 * 1024 * 1024
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.svg', '.tiff'}
IGNORE_DIRS = {'.git', 'node_modules', '__pycache__', '.idea', '.vscode', 'venv', 'env'}
IGNORE_FILES = {'.DS_Store'}

class ImportStrategy(ABC):
    @abstractmethod
    async def process_file(self, source_path: Path, target_rel_path: Path) -> Dict[str, Any]:
        """处理文件（上传或复制），返回元数据"""
        pass

    @abstractmethod
    async def upsert_session(self, filter_doc: dict, update_doc: dict) -> str:
        """更新会话，返回 'created' 或 'updated'"""
        pass

    @abstractmethod
    async def close(self):
        """关闭资源"""
        pass
    
    def _get_file_info(self, file_path: Path) -> Tuple[str, bool, int, str, str]:
        """读取文件内容并获取基本信息: (content, is_base64, tokens, mime_type, ext)"""
        mime_type, _ = mimetypes.guess_type(file_path)
        ext = file_path.suffix.lower()
        is_image = ext in IMAGE_EXTENSIONS
        tokens = 0
        content = ""
        is_base64 = False

        if is_image:
            with open(file_path, "rb") as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            is_base64 = True
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                tokens = estimate_tokens(content)
            except UnicodeDecodeError:
                with open(file_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode('utf-8')
                is_base64 = True
        
        return content, is_base64, tokens, mime_type, ext

class LocalStrategy(ImportStrategy):
    def __init__(self, target_base_dir: str):
        self.target_base_dir = target_base_dir
        self.collection = None

    async def initialize(self):
        await db.initialize()
        self.collection = db.db[settings.collection_sessions]

    async def process_file(self, source_path: Path, target_rel_path: Path) -> Dict[str, Any]:
        target_file_path = Path(self.target_base_dir) / target_rel_path
        target_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(source_path, target_file_path)
        
        # 获取信息用于元数据
        _, _, tokens, mime_type, ext = self._get_file_info(source_path)
        file_size = source_path.stat().st_size
        
        rel_path_str = str(target_rel_path).replace(os.sep, '/')
        url_path = f"/{self.target_base_dir}/{rel_path_str}".replace('//', '/')

        return {
            "file_path": url_path,
            "size": file_size,
            "tokens": tokens,
            "mime_type": mime_type,
            "extension": ext
        }

    async def upsert_session(self, filter_doc: dict, update_doc: dict) -> str:
        result = await self.collection.update_one(filter_doc, update_doc, upsert=True)
        return 'created' if result.upserted_id else 'updated'

    async def close(self):
        await db.close()

class ApiStrategy(ImportStrategy):
    def __init__(self, api_url: str, target_base_dir: str):
        self.api_url = api_url.rstrip('/')
        self.target_base_dir = target_base_dir
        self.session = aiohttp.ClientSession()

    async def process_file(self, source_path: Path, target_rel_path: Path) -> Dict[str, Any]:
        file_size = source_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"文件大小超过限制 (100MB): {file_size}")

        content, is_base64, tokens, mime_type, ext = self._get_file_info(source_path)
        
        target_dir = Path(self.target_base_dir) / target_rel_path.parent
        
        payload = {
            "filename": source_path.name,
            "content": content,
            "is_base64": is_base64,
            "target_dir": str(target_dir)
        }
        
        async with self.session.post(f"{self.api_url}/upload", json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"Upload failed: {resp.status} {await resp.text()}")
            result = await resp.json()
            if result.get('code') != 0:
                raise Exception(f"Upload error: {result}")
            
            return {
                "file_path": result['data']['url'],
                "size": file_size,
                "tokens": tokens,
                "mime_type": mime_type,
                "extension": ext
            }

    async def upsert_session(self, filter_doc: dict, update_doc: dict) -> str:
        # 递归处理字典中的 datetime
        def sanitize(obj):
            if isinstance(obj, dict):
                return {k: sanitize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize(i) for i in obj]
            elif isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            return obj

        params = {
            "cname": settings.collection_sessions,
            "filter": sanitize(filter_doc),
            "update": sanitize(update_doc)
        }
        
        payload = {
            "module_name": "services.database.data_service",
            "method_name": "upsert_document",
            "parameters": params
        }
        
        async with self.session.post(f"{self.api_url}/", json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"Upsert failed: {resp.status}")
            result = await resp.json()
            if result.get('code') != 0:
                raise Exception(f"Upsert error: {result}")
            
            return 'created' if result['data'].get('upserted_id') else 'updated'

    async def close(self):
        await self.session.close()

async def import_directory(source_dir: str, target_base_dir: str = "static", api_url: str = None):
    source_path = Path(source_dir).resolve()
    if not source_path.exists():
        logger.error(f"源目录不存在: {source_path}")
        return

    logger.info(f"开始扫描目录: {source_path}")
    logger.info(f"模式: {'API 远程上传' if api_url else '本地直接操作'}")
    
    strategy = ApiStrategy(api_url, target_base_dir) if api_url else LocalStrategy(target_base_dir)
    if isinstance(strategy, LocalStrategy):
        await strategy.initialize()

    stats = {'processed': 0, 'created': 0, 'updated': 0}
    
    try:
        for root, dirs, files in os.walk(source_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
            
            for filename in files:
                if filename.startswith('.') or filename in IGNORE_FILES: continue

                file_source_path = Path(root) / filename
                rel_path = file_source_path.relative_to(source_path)
                
                # 文件名截断处理
                target_filename = filename
                if len(filename.encode('utf-8')) > 200: 
                    name, ext = os.path.splitext(filename)
                    target_filename = name[:100] + ext
                
                # 准备数据
                tags = list(rel_path.parent.parts)
                target_rel_path = rel_path.parent / target_filename
                
                filter_doc = {"tags": tags, "filename": target_filename}
                update_doc = {
                    "$set": {
                        "tags": tags,
                        "filename": target_filename,
                        "updated_at": datetime.now()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now(),
                        "title": filename,
                    }
                }

                try:
                    # 执行策略
                    metadata = await strategy.process_file(file_source_path, target_rel_path)
                    update_doc["$set"].update(metadata)
                    
                    status = await strategy.upsert_session(filter_doc, update_doc)
                    
                    stats['processed'] += 1
                    if status == 'created':
                        stats['created'] += 1
                        logger.info(f"[新建] {rel_path} (Size: {metadata['size']}, Tokens: {metadata['tokens']})")
                    else:
                        stats['updated'] += 1
                        logger.info(f"[更新] {rel_path} (Size: {metadata['size']}, Tokens: {metadata['tokens']})")
                        
                except Exception as e:
                    logger.error(f"[错误] 处理 {rel_path} 失败: {e}")

    finally:
        await strategy.close()
        logger.info("-" * 30)
        logger.info(f"处理完成. 总计: {stats['processed']}, 新建: {stats['created']}, 更新: {stats['updated']}")

def main():
    parser = argparse.ArgumentParser(description="导入目录到会话")
    parser.add_argument("source_dir", help="源目录路径")
    parser.add_argument("--target", default="static", help="目标静态文件目录 (默认: static)")
    parser.add_argument("--api-url", help="API 基础 URL")
    args = parser.parse_args()
    
    asyncio.run(import_directory(args.source_dir, args.target, args.api_url))

if __name__ == "__main__":
    main()
