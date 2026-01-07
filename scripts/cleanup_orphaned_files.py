#!/usr/bin/env python3
"""
清理孤儿文件脚本
扫描 static 目录，删除数据库中不存在的文件引用。
用法:
    python3 scripts/cleanup_orphaned_files.py [--dry-run]
"""
import sys
import os
import asyncio
import argparse
from pathlib import Path

# 添加项目根目录到 path
sys.path.append(os.getcwd())

from core.database import db
from core.config import settings

async def cleanup(dry_run: bool = True):
    print(f"模式: {'[Dry Run] (不执行删除)' if dry_run else '[Live] (执行删除)'}")
    
    await db.initialize()
    collection = db.db[settings.collection_sessions]
    
    # 1. 获取数据库中所有文件路径
    print("正在从数据库读取文件列表...")
    db_files = set()
    async for doc in collection.find({}, {'file_path': 1}):
        path = doc.get('file_path')
        if path:
            # 数据库路径通常是 /static/xxx
            # 我们将其标准化为相对路径 static/xxx (去除开头的 /)
            if path.startswith('/'):
                path = path[1:]
            db_files.add(path)
            
    print(f"数据库中包含 {len(db_files)} 个文件记录。")
    
    # 2. 扫描 static 目录
    static_base = settings.static_base_dir
    # 如果配置是相对路径 (./static)，转换为绝对路径或保持相对路径
    # 这里我们假设脚本在项目根目录运行
    if static_base.startswith('./'):
        static_base = static_base[2:]
        
    static_dir = Path(os.getcwd()) / static_base
    
    if not static_dir.exists():
        print(f"错误: 静态文件目录不存在: {static_dir}")
        await db.close()
        return

    print(f"正在扫描目录: {static_dir}")
    
    orphaned_count = 0
    reclaimed_space = 0
    
    # 忽略的文件
    IGNORE_FILES = {'.DS_Store', '.gitkeep', 'index.html', 'favicon.ico'}
    
    for root, dirs, files in os.walk(static_dir):
        for file in files:
            if file in IGNORE_FILES: continue
            
            file_abs_path = Path(root) / file
            
            # 计算相对于项目根目录的路径，例如 static/subdir/file.txt
            try:
                rel_path = file_abs_path.relative_to(os.getcwd())
            except ValueError:
                # 如果文件不在当前工作目录下（不太可能），则跳过
                continue
                
            rel_path_str = str(rel_path)
            
            # 检查是否在数据库中
            if rel_path_str not in db_files:
                orphaned_count += 1
                size = file_abs_path.stat().st_size
                reclaimed_space += size
                
                if dry_run:
                    print(f"[待删除] {rel_path_str} ({size} bytes)")
                else:
                    try:
                        os.remove(file_abs_path)
                        print(f"[已删除] {rel_path_str}")
                    except Exception as e:
                        print(f"[删除失败] {rel_path_str}: {e}")
                        
        # 尝试删除空目录 (仅在非 dry-run 模式且目录为空时)
        if not dry_run:
             for d in dirs:
                 d_path = Path(root) / d
                 try:
                     # 仅当目录为空时 rmdir 才会成功
                     d_path.rmdir()
                 except OSError:
                     pass # 目录非空

    print("-" * 30)
    print(f"扫描完成.")
    print(f"孤儿文件数量: {orphaned_count}")
    print(f"可释放空间: {reclaimed_space / 1024 / 1024:.2f} MB")
    
    if dry_run and orphaned_count > 0:
        print("\n提示: 使用 --no-dry-run 参数来执行实际删除操作。")
        print("python3 scripts/cleanup_orphaned_files.py --no-dry-run")

    await db.close()

def main():
    parser = argparse.ArgumentParser(description="清理孤儿文件")
    parser.add_argument("--no-dry-run", action="store_true", help="执行实际删除操作 (默认仅模拟)")
    
    args = parser.parse_args()
    
    # dry_run 默认为 True，除非指定了 --no-dry-run
    dry_run = not args.no_dry_run
    
    asyncio.run(cleanup(dry_run))

if __name__ == "__main__":
    main()
