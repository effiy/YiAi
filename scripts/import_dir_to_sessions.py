#!/usr/bin/env python3
"""
导入指定目录到会话并上传静态文件
用法: python3 scripts/import_dir_to_sessions.py /path/to/source/dir
"""
import os
import sys
import shutil
import asyncio
import logging
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 path
sys.path.append(os.getcwd())

from core.database import db
from core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def import_directory(source_dir: str, target_base_dir: str = "static/uploads"):
    """
    遍历源目录，上传文件并更新数据库会话
    """
    source_path = Path(source_dir).resolve()
    if not source_path.exists():
        logger.error(f"源目录不存在: {source_path}")
        return

    logger.info(f"开始扫描目录: {source_path}")
    
    # 确保数据库连接
    await db.initialize()
    collection = db.db[settings.collection_sessions]

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
                
                # 1. 计算 Tags (基于目录结构)
                # 例如 rel_path = "category/sub/file.txt" -> tags = ["category", "sub"]
                tags = list(rel_path.parent.parts)
                
                # 2. 处理静态文件
                # 保持相同的目录结构
                target_file_path = Path(target_base_dir) / rel_path
                target_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件 (覆盖模式)
                shutil.copy2(file_source_path, target_file_path)
                
                # 3. 数据库操作
                # 相对 URL 路径 (用于前端访问)
                url_path = f"/{target_base_dir}/{rel_path}"
                
                # 构建查询条件：目录(tags) 和 文件名相同
                filter_doc = {
                    "tags": tags,
                    "filename": filename
                }
                
                # 更新内容
                update_doc = {
                    "$set": {
                        "tags": tags,
                        "filename": filename,
                        "file_path": str(url_path),  # 存储 web 可访问路径
                        "updated_at": datetime.now()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now(),
                        "title": filename,  # 默认标题
                    }
                }

                result = await collection.update_one(filter_doc, update_doc, upsert=True)
                
                count_processed += 1
                if result.upserted_id:
                    count_created += 1
                    logger.info(f"[新建] {rel_path}")
                else:
                    count_updated += 1
                    logger.info(f"[更新] {rel_path}")

    except Exception as e:
        logger.error(f"导入过程中出错: {e}", exc_info=True)
    finally:
        logger.info("-" * 30)
        logger.info(f"处理完成. 总计: {count_processed}, 新建: {count_created}, 更新: {count_updated}")
        await db.close()

def main():
    parser = argparse.ArgumentParser(description="将指定目录下的内容导入到静态文件目录并创建会话")
    parser.add_argument("source_dir", help="源目录路径")
    parser.add_argument("--target", default="static/uploads", help="目标静态文件目录 (默认: static/uploads)")
    
    args = parser.parse_args()
    
    asyncio.run(import_directory(args.source_dir, args.target))

if __name__ == "__main__":
    main()
