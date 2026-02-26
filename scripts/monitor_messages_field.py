#!/usr/bin/env python3
"""
Messages 字段监控脚本

用途：监控 sessions 集合中 messages 字段的状态

使用方法：
    python3 /var/www/YiAi/scripts/monitor_messages_field.py
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, '/var/www/YiAi')

from core.database import db


async def monitor():
    """监控 messages 字段状态"""
    await db.initialize()
    collection = db.db['sessions']
    
    print('=' * 60)
    print('Sessions Messages 字段监控报告')
    print('=' * 60)
    print(f'时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    # 统计总会话数
    total = await collection.count_documents({})
    print(f'总会话数：{total}')
    
    # 统计有 messages 字段的会话数
    with_messages_field = await collection.count_documents({'messages': {'$exists': True}})
    print(f'有 messages 字段的会话数：{with_messages_field}')
    
    # 统计 messages 不为空的会话数
    with_messages_data = await collection.count_documents({
        'messages': {'$exists': True, '$ne': [], '$not': {'$size': 0}}
    })
    print(f'messages 不为空的会话数：{with_messages_data}')
    
    # 统计 messages 为空数组的会话数
    with_empty_messages = await collection.count_documents({'messages': []})
    print(f'messages 为空数组的会话数：{with_empty_messages}')
    
    # 统计没有 messages 字段的会话数
    without_messages = await collection.count_documents({'messages': {'$exists': False}})
    print(f'没有 messages 字段的会话数：{without_messages}')
    
    print()
    print('=' * 60)
    
    # 分析
    if with_messages_data > 0:
        percentage = (with_messages_data / total * 100) if total > 0 else 0
        print(f'✓ 有 {with_messages_data} 个会话包含对话历史（{percentage:.1f}%）')
    else:
        print('⚠ 当前所有会话的 messages 都是空的')
    
    # 检查最近更新的会话
    print()
    print('最近更新的 5 个会话：')
    recent_sessions = collection.find(
        {},
        {'key': 1, 'title': 1, 'messages': 1, 'updatedTime': 1}
    ).sort('updatedTime', -1).limit(5)
    
    async for session in recent_sessions:
        messages_count = len(session.get('messages', []))
        print(f'  - {session.get("title", "未命名")}: {messages_count} 条消息')
    
    await db.close()


if __name__ == '__main__':
    asyncio.run(monitor())
