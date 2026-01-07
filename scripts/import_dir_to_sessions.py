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
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 path
sys.path.append(os.getcwd())

from core.database import db
from core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 单个文件大小限制 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024

# 图片扩展名列表
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.svg', '.tiff'}

def estimate_tokens(text: str) -> int:
    """估算文本的 Token 数量 (简易版)"""
    token_count = 0
    for char in text:
        if ord(char) > 127: # 非 ASCII 字符 (如中文) 计为 1
            token_count += 1
        else:
            token_count += 0.25 # ASCII 字符 (如英文) 约 4 个字符为 1 token
    return int(token_count)

async def upload_file_api(session: aiohttp.ClientSession, api_url: str, file_path: Path, target_dir: str) -> Dict[str, Any]:
    """通过 API 上传文件 (JSON 方式)，返回文件信息"""
    
    # 检查文件大小
    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"文件大小超过限制 (100MB): {file_path} ({file_size} bytes)")

    filename = file_path.name
    ext = file_path.suffix.lower()
    is_image = ext in IMAGE_EXTENSIONS
    mime_type, _ = mimetypes.guess_type(file_path)
    
    content = ""
    is_base64 = False
    tokens = 0

    try:
        if is_image:
            # 图片强制使用 Base64
            with open(file_path, "rb") as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            is_base64 = True
        else:
            # 尝试作为文本读取
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                is_base64 = False
                tokens = estimate_tokens(content)
            except UnicodeDecodeError:
                # 如果不是文本，则使用 Base64
                with open(file_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode('utf-8')
                is_base64 = True
    except Exception as e:
        raise ValueError(f"读取文件失败: {file_path}, Error: {e}")

    url = f"{api_url.rstrip('/')}/upload"
    
    payload = {
        "filename": filename,
        "content": content,
        "is_base64": is_base64,
        "target_dir": str(target_dir)
    }
    
    async with session.post(url, json=payload) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise Exception(f"Upload failed: {resp.status} {text}")
        result = await resp.json()
        if result.get('code') != 0:
             raise Exception(f"Upload error: {result}")
        
        return {
            "url": result['data']['url'],
            "size": file_size,
            "tokens": tokens,
            "mime_type": mime_type,
            "extension": ext
        }

async def upsert_session_api(session: aiohttp.ClientSession, api_url: str, cname: str, filter_doc: dict, update_doc: dict):
    """通过 API 更新会话"""
    url = f"{api_url.rstrip('/')}/"
    
    # 转换 datetime 对象为字符串，因为 JSON 不支持 datetime
    def convert_dates(obj):
        if isinstance(obj, dict):
            return {k: convert_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_dates(i) for i in obj]
        elif isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return obj

    params = {
        "cname": cname,
        "filter": convert_dates(filter_doc),
        "update": convert_dates(update_doc)
    }
    
    payload = {
        "module_name": "services.database.data_service",
        "method_name": "upsert_document",
        "parameters": params
    }
    
    async with session.post(url, json=payload) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise Exception(f"Upsert failed: {resp.status} {text}")
        result = await resp.json()
        if result.get('code') != 0:
             raise Exception(f"Upsert error: {result}")
        return result['data']

async def import_directory(source_dir: str, target_base_dir: str = "static", api_url: str = None):
    """
    遍历源目录，上传文件并更新数据库会话
    """
    source_path = Path(source_dir).resolve()
    if not source_path.exists():
        logger.error(f"源目录不存在: {source_path}")
        return

    logger.info(f"开始扫描目录: {source_path}")
    logger.info(f"模式: {'API 远程上传' if api_url else '本地直接操作'}")
    
    # 只有在本地模式下才初始化数据库
    if not api_url:
        await db.initialize()
        collection = db.db[settings.collection_sessions]
    
    http_session = None
    if api_url:
        http_session = aiohttp.ClientSession()

    count_processed = 0
    count_updated = 0
    count_created = 0

    # 忽略的目录和文件列表
    IGNORE_DIRS = {'.git', 'node_modules', '__pycache__', '.idea', '.vscode', 'venv', 'env'}
    IGNORE_FILES = {'.DS_Store'}

    try:
        for root, dirs, files in os.walk(source_path):
            # 修改 dirs 列表以跳过忽略的目录 (os.walk 支持就地修改 dirs)
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
            
            for filename in files:
                if filename.startswith('.') or filename in IGNORE_FILES:  # 跳过隐藏文件和忽略文件
                    continue

                file_source_path = Path(root) / filename
                rel_path = file_source_path.relative_to(source_path)
                
                # 处理文件名过长问题
                target_filename = filename
                if len(filename.encode('utf-8')) > 200: 
                    name, ext = os.path.splitext(filename)
                    target_filename = name[:100] + ext
                    logger.warning(f"文件名过长，已截断: {filename} -> {target_filename}")

                # 1. 计算 Tags
                tags = list(rel_path.parent.parts)
                
                # 2. 处理文件上传/复制
                target_rel_path = rel_path.parent / target_filename
                
                # 3. 数据库操作准备
                filter_doc = {
                    "tags": tags,
                    "filename": target_filename
                }
                
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

                if api_url:
                    # API 模式
                    # 上传文件
                    # 计算目标目录 (相对于 static)
                    file_target_dir = Path(target_base_dir) / rel_path.parent
                    try:
                        upload_result = await upload_file_api(http_session, api_url, file_source_path, file_target_dir)
                        
                        update_doc["$set"]["file_path"] = upload_result['url']
                        update_doc["$set"]["size"] = upload_result['size']
                        update_doc["$set"]["tokens"] = upload_result['tokens']
                        update_doc["$set"]["mime_type"] = upload_result['mime_type']
                        update_doc["$set"]["extension"] = upload_result['extension']
                        
                        # 更新数据库
                        result = await upsert_session_api(http_session, api_url, settings.collection_sessions, filter_doc, update_doc)
                        
                        # API 返回的 upserted_id 是字符串或 None
                        if result.get('upserted_id'):
                            count_created += 1
                            logger.info(f"[API 新建] {rel_path} (Size: {upload_result['size']}, Tokens: {upload_result['tokens']})")
                        else:
                            count_updated += 1
                            logger.info(f"[API 更新] {rel_path} (Size: {upload_result['size']}, Tokens: {upload_result['tokens']})")
                    except ValueError as ve:
                        logger.error(f"[跳过] 文件上传失败 {rel_path}: {ve}")
                    except Exception as e:
                         logger.error(f"[错误] 处理 {rel_path} 时出错: {e}")
                        
                else:
                    # 本地模式
                    target_file_path = Path(target_base_dir) / target_rel_path
                    target_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(file_source_path, target_file_path)
                    
                    # 本地计算元数据
                    file_size = file_source_path.stat().st_size
                    mime_type, _ = mimetypes.guess_type(file_source_path)
                    ext = file_source_path.suffix.lower()
                    tokens = 0
                    
                    # 尝试计算 Token (仅对非图片)
                    if ext not in IMAGE_EXTENSIONS:
                         try:
                             with open(file_source_path, "r", encoding="utf-8") as f:
                                 content = f.read()
                                 tokens = estimate_tokens(content)
                         except:
                             pass # 忽略读取错误，可能是二进制文件

                    # 计算 URL
                    rel_path_str = str(target_rel_path).replace(os.sep, '/')
                    url_path = f"/{target_base_dir}/{rel_path_str}"
                    
                    update_doc["$set"]["file_path"] = url_path
                    update_doc["$set"]["size"] = file_size
                    update_doc["$set"]["tokens"] = tokens
                    update_doc["$set"]["mime_type"] = mime_type
                    update_doc["$set"]["extension"] = ext
                    
                    result = await collection.update_one(filter_doc, update_doc, upsert=True)
                    
                    if result.upserted_id:
                        count_created += 1
                        logger.info(f"[新建] {rel_path} (Size: {file_size}, Tokens: {tokens})")
                    else:
                        count_updated += 1
                        logger.info(f"[更新] {rel_path} (Size: {file_size}, Tokens: {tokens})")
                
                count_processed += 1

    except Exception as e:
        logger.error(f"导入过程中出错: {e}", exc_info=True)
    finally:
        if http_session:
            await http_session.close()
        if not api_url:
            await db.close()
        
        logger.info("-" * 30)
        logger.info(f"处理完成. 总计: {count_processed}, 新建: {count_created}, 更新: {count_updated}")

def main():
    parser = argparse.ArgumentParser(description="将指定目录下的内容导入到静态文件目录并创建会话")
    parser.add_argument("source_dir", help="源目录路径")
    parser.add_argument("--target", default="static", help="目标静态文件目录 (默认: static)")
    parser.add_argument("--api-url", help="API 基础 URL (例如 https://api.effiy.cn)，如果提供则使用 API 上传")
    
    args = parser.parse_args()
    
    asyncio.run(import_directory(args.source_dir, args.target, args.api_url))

if __name__ == "__main__":
    main()
