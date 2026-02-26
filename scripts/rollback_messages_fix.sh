#!/bin/bash
# 回滚脚本 - 如果需要回滚 messages 修复

echo "警告：此操作将回滚 messages 字段修复"
echo "请确认是否继续？(yes/no)"
read -r confirm

if [ "$confirm" != "yes" ]; then
    echo "已取消回滚操作"
    exit 0
fi

echo "开始回滚..."

# 1. 备份当前代码
cp /var/www/YiAi/services/database/data_service.py \
   /var/www/YiAi/services/database/data_service.py.fixed.backup

# 2. 恢复原始代码（需要手动编辑）
echo "请手动编辑 data_service.py，移除以下代码："
echo "  - 第 369-371 行（update_document 函数）"
echo "  - 第 417-419 行（upsert_document 函数）"
echo ""
echo "编辑完成后，按回车继续..."
read -r

# 3. 重启服务
echo "重启 API 服务..."
kill -HUP $(pgrep -f "python3 main.py")

echo "✓ 回滚完成"
echo "请运行测试验证：python3 /var/www/YiAi/tests/test_messages_fix.py"
