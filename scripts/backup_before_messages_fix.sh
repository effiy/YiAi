#!/bin/bash
# 备份脚本 - 在应用 messages 修复前备份数据

BACKUP_DIR="/var/backups/mongodb/messages_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "开始备份 sessions 集合..."
mongodump --uri="mongodb://localhost:27017/ruiyi" \
          --collection=sessions \
          --out="$BACKUP_DIR" \
          2>&1

if [ $? -eq 0 ]; then
    echo "✓ 备份完成：$BACKUP_DIR"
    echo "备份大小：$(du -sh $BACKUP_DIR | cut -f1)"
else
    echo "✗ 备份失败"
    exit 1
fi
