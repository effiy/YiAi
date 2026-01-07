#!/usr/bin/env python3
"""
RSS 源管理工具
用法:
    python3 scripts/rss_manager.py list
    python3 scripts/rss_manager.py add <url> [--name NAME]
    python3 scripts/rss_manager.py remove <url>
    python3 scripts/rss_manager.py enable <url>
    python3 scripts/rss_manager.py disable <url>
"""
import sys
import os
import asyncio
import argparse
from datetime import datetime

# 添加项目根目录到 path
sys.path.append(os.getcwd())

from core.database import db
from core.config import settings

async def list_feeds():
    await db.initialize()
    collection = db.db[settings.collection_seeds]
    cursor = collection.find({})
    
    print(f"{'Status':<10} | {'Name':<30} | {'URL'}")
    print("-" * 80)
    
    count = 0
    async for doc in cursor:
        name = doc.get('name', 'N/A') or 'N/A'
        url = doc.get('url', 'N/A')
        enabled = doc.get('enabled', True)
        status = "[ON]" if enabled else "[OFF]"
        
        # 截断过长的名字
        if len(name) > 28:
            name = name[:25] + "..."
            
        print(f"{status:<10} | {name:<30} | {url}")
        count += 1
        
    print("-" * 80)
    print(f"Total: {count}")
    await db.close()

async def add_feed(url: str, name: str = None):
    await db.initialize()
    collection = db.db[settings.collection_seeds]
    
    # Check if exists
    existing = await collection.find_one({'url': url})
    if existing:
        print(f"Error: Feed already exists: {url}")
        await db.close()
        return

    doc = {
        'url': url,
        'enabled': True,
        'created_at': datetime.now()
    }
    if name:
        doc['name'] = name
    
    await collection.insert_one(doc)
    print(f"Success: Added feed: {url} ({name})")
    await db.close()

async def remove_feed(url: str):
    await db.initialize()
    collection = db.db[settings.collection_seeds]
    result = await collection.delete_one({'url': url})
    if result.deleted_count > 0:
        print(f"Success: Removed feed: {url}")
    else:
        print(f"Error: Feed not found: {url}")
    await db.close()

async def toggle_feed(url: str, enabled: bool):
    await db.initialize()
    collection = db.db[settings.collection_seeds]
    result = await collection.update_one(
        {'url': url},
        {'$set': {'enabled': enabled}}
    )
    if result.matched_count > 0:
        status = "Enabled" if enabled else "Disabled"
        print(f"Success: {status} feed: {url}")
    else:
        print(f"Error: Feed not found: {url}")
    await db.close()

def main():
    parser = argparse.ArgumentParser(description="RSS Feed Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # List
    subparsers.add_parser("list", help="List all RSS feeds")
    
    # Add
    add_parser = subparsers.add_parser("add", help="Add a new RSS feed")
    add_parser.add_argument("url", help="RSS Feed URL")
    add_parser.add_argument("--name", help="Feed Name (optional)")
    
    # Remove
    rm_parser = subparsers.add_parser("remove", help="Remove an RSS feed")
    rm_parser.add_argument("url", help="RSS Feed URL")
    
    # Enable
    en_parser = subparsers.add_parser("enable", help="Enable an RSS feed")
    en_parser.add_argument("url", help="RSS Feed URL")
    
    # Disable
    dis_parser = subparsers.add_parser("disable", help="Disable an RSS feed")
    dis_parser.add_argument("url", help="RSS Feed URL")
    
    args = parser.parse_args()
    
    if args.command == "list":
        asyncio.run(list_feeds())
    elif args.command == "add":
        asyncio.run(add_feed(args.url, args.name))
    elif args.command == "remove":
        asyncio.run(remove_feed(args.url))
    elif args.command == "enable":
        asyncio.run(toggle_feed(args.url, True))
    elif args.command == "disable":
        asyncio.run(toggle_feed(args.url, False))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
