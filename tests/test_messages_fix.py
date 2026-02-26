#!/usr/bin/env python3
"""
Sessions Messages 字段保护功能测试脚本

用途：验证 messages 字段在更新操作中不会被空数组覆盖

使用方法：
    python3 /var/www/YiAi/tests/test_messages_fix.py
"""

import asyncio
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, '/var/www/YiAi')

from core.database import db
from services.database.data_service import update_document, upsert_document, query_documents


class TestMessagesProtection:
    """Messages 字段保护功能测试类"""
    
    def __init__(self):
        self.test_key = 'test_messages_protection_session'
        self.passed_tests = 0
        self.failed_tests = 0
        self.total_tests = 0
    
    async def setup(self):
        """测试前准备"""
        await db.initialize()
        collection = db.db['sessions']
        
        # 清理可能存在的测试数据
        await collection.delete_one({'key': self.test_key})
        
        # 创建测试会话
        await collection.insert_one({
            'key': self.test_key,
            'title': '测试会话',
            'tags': ['test'],
            'messages': [
                {'type': 'user', 'message': '测试消息1', 'timestamp': 1000},
                {'type': 'pet', 'message': '测试回复1', 'timestamp': 1001}
            ],
            'createdTime': '2024-01-01 00:00:00',
            'updatedTime': '2024-01-01 00:00:00'
        })
        print('✓ 测试环境准备完成\n')
    
    async def teardown(self):
        """测试后清理"""
        collection = db.db['sessions']
        await collection.delete_one({'key': self.test_key})
        await db.close()
        print('\n✓ 测试环境清理完成')
    
    async def assert_messages_count(self, expected_count, test_name):
        """断言 messages 数量"""
        self.total_tests += 1
        collection = db.db['sessions']
        doc = await collection.find_one({'key': self.test_key}, {'messages': 1})
        actual_count = len(doc.get('messages', []))
        
        if actual_count == expected_count:
            print(f'  ✓ {test_name}: 通过 (messages 数量: {actual_count})')
            self.passed_tests += 1
            return True
        else:
            print(f'  ✗ {test_name}: 失败 (期望: {expected_count}, 实际: {actual_count})')
            self.failed_tests += 1
            return False
    
    async def test_update_with_empty_array(self):
        """测试 1: update_document 使用空 messages 数组"""
        print('测试 1: update_document 使用空 messages 数组')
        
        params = {
            'cname': 'sessions',
            'data': {
                'key': self.test_key,
                'title': '更新标题1',
                'messages': []
            }
        }
        await update_document(params)
        await self.assert_messages_count(2, 'update_document 空数组保护')
    
    async def test_update_with_non_empty_array(self):
        """测试 2: update_document 使用非空 messages 数组"""
        print('\n测试 2: update_document 使用非空 messages 数组')
        
        new_messages = [
            {'type': 'user', 'message': '新消息1', 'timestamp': 2000}
        ]
        params = {
            'cname': 'sessions',
            'data': {
                'key': self.test_key,
                'title': '更新标题2',
                'messages': new_messages
            }
        }
        await update_document(params)
        await self.assert_messages_count(1, 'update_document 非空数组更新')
    
    async def test_update_without_messages(self):
        """测试 3: update_document 不传 messages 字段"""
        print('\n测试 3: update_document 不传 messages 字段')
        
        params = {
            'cname': 'sessions',
            'data': {
                'key': self.test_key,
                'title': '更新标题3'
            }
        }
        await update_document(params)
        await self.assert_messages_count(1, 'update_document 不传 messages')
    
    async def test_upsert_with_empty_array(self):
        """测试 4: upsert_document 使用空 messages 数组"""
        print('\n测试 4: upsert_document 使用空 messages 数组')
        
        params = {
            'cname': 'sessions',
            'filter': {'key': self.test_key},
            'update': {
                '$set': {
                    'title': '更新标题4',
                    'messages': []
                }
            }
        }
        await upsert_document(params)
        await self.assert_messages_count(1, 'upsert_document 空数组保护')
    
    async def test_query_returns_messages(self):
        """测试 5: query_documents 返回 messages 字段"""
        print('\n测试 5: query_documents 返回 messages 字段')
        
        params = {
            'cname': 'sessions',
            'filter': {'key': self.test_key},
            'limit': 1
        }
        result = await query_documents(params)
        
        self.total_tests += 1
        if result.get('list') and len(result['list']) > 0:
            doc = result['list'][0]
            if 'messages' in doc:
                print(f'  ✓ query_documents 返回 messages: 通过 (messages 数量: {len(doc["messages"])})')
                self.passed_tests += 1
            else:
                print('  ✗ query_documents 返回 messages: 失败 (messages 字段不存在)')
                self.failed_tests += 1
        else:
            print('  ✗ query_documents 返回 messages: 失败 (未找到文档)')
            self.failed_tests += 1
    
    async def test_real_scenario(self):
        """测试 6: 真实场景 - 前端同步文件更新会话"""
        print('\n测试 6: 真实场景 - 前端同步文件更新会话')
        
        # 重置测试数据
        collection = db.db['sessions']
        await collection.update_one(
            {'key': self.test_key},
            {'$set': {'messages': [
                {'type': 'user', 'message': '用户问题1', 'timestamp': 1000},
                {'type': 'pet', 'message': 'AI回复1', 'timestamp': 1001},
                {'type': 'user', 'message': '用户问题2', 'timestamp': 1002},
                {'type': 'pet', 'message': 'AI回复2', 'timestamp': 1003}
            ]}}
        )
        
        # 模拟前端同步文件（传入空 messages）
        params = {
            'cname': 'sessions',
            'data': {
                'key': self.test_key,
                'title': '同步后的标题',
                'pageDescription': '文件：test/path.md',
                'tags': ['test', 'synced'],
                'messages': []  # 前端传入空数组
            }
        }
        await update_document(params)
        await self.assert_messages_count(4, '真实场景 - 对话历史保护')
    
    async def run_all_tests(self):
        """运行所有测试"""
        print('=' * 60)
        print('Sessions Messages 字段保护功能测试')
        print('=' * 60)
        print()
        
        try:
            await self.setup()
            
            await self.test_update_with_empty_array()
            await self.test_update_with_non_empty_array()
            await self.test_update_without_messages()
            await self.test_upsert_with_empty_array()
            await self.test_query_returns_messages()
            await self.test_real_scenario()
            
            await self.teardown()
            
            # 输出测试结果
            print()
            print('=' * 60)
            print('测试结果汇总')
            print('=' * 60)
            print(f'总测试数: {self.total_tests}')
            print(f'通过: {self.passed_tests}')
            print(f'失败: {self.failed_tests}')
            print(f'通过率: {self.passed_tests / self.total_tests * 100:.1f}%')
            print('=' * 60)
            
            if self.failed_tests == 0:
                print('\n✓ 所有测试通过！Messages 字段保护功能正常工作。')
                return 0
            else:
                print(f'\n✗ 有 {self.failed_tests} 个测试失败，请检查代码。')
                return 1
        
        except Exception as e:
            print(f'\n✗ 测试执行出错: {e}')
            import traceback
            traceback.print_exc()
            return 1


async def main():
    """主函数"""
    tester = TestMessagesProtection()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())
