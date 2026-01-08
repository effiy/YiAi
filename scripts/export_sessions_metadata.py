#!/usr/bin/env python3
"""
导出数据库会话元数据到 JSON 文件
用法:
    python3 scripts/export_sessions_metadata.py output.json
"""
import sys
import os
import asyncio
import argparse
import json
from datetime import datetime

# 添加项目根目录到 path
sys.path.append(os.getcwd())

from core.database import db
from core.settings import settings

# JSON Encoder for datetime
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

async def export(output_file: str):
    await db.initialize()
    collection = db.db[settings.collection_sessions]
    
    print(f"Exporting sessions to {output_file}...")
    
    sessions = []
    async for doc in collection.find({}):
        # Remove internal MongoDB _id
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        sessions.append(doc)
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, cls=DateTimeEncoder, indent=2, ensure_ascii=False)
        
    print(f"Exported {len(sessions)} sessions.")
    await db.close()

def main():
    parser = argparse.ArgumentParser(description="Export sessions metadata to JSON")
    parser.add_argument("output_file", help="Output JSON file path")
    
    args = parser.parse_args()
    
    asyncio.run(export(args.output_file))

if __name__ == "__main__":
    main()
