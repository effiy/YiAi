#!/bin/bash
# 修复 "Too many open files" 错误的辅助脚本

echo "检查当前文件描述符限制..."
current_limit=$(ulimit -n)
echo "当前限制: $current_limit"

if [ "$current_limit" -lt 65535 ]; then
    echo ""
    echo "文件描述符限制过低，建议增加到 65535"
    echo ""
    echo "临时解决方案（当前终端会话有效）："
    echo "  执行: ulimit -n 65535"
    echo ""
    echo "永久解决方案（macOS）："
    echo "  1. 编辑 ~/.zshrc 或 ~/.bash_profile，添加以下行："
    echo "     ulimit -n 65535"
    echo "  2. 然后执行: source ~/.zshrc 或 source ~/.bash_profile"
    echo ""
    echo "如果使用 launchd（推荐用于长期运行的 Python 服务）："
    echo "  创建 /Library/LaunchDaemons/limit.maxfiles.plist 文件"
    echo ""
    
    # 检查是否需要提升权限
    if [ "$EUID" -ne 0 ]; then
        echo "注意: 某些永久性更改可能需要管理员权限"
    fi
else
    echo "文件描述符限制已足够"
fi

echo ""
echo "检查 Qdrant 进程..."
if pgrep -f qdrant > /dev/null; then
    echo "Qdrant 服务正在运行"
    echo "检查 Qdrant 服务的文件描述符使用情况..."
    qdrant_pid=$(pgrep -f qdrant | head -n 1)
    if [ -n "$qdrant_pid" ]; then
        echo "Qdrant PID: $qdrant_pid"
        lsof_count=$(lsof -p $qdrant_pid 2>/dev/null | wc -l)
        echo "当前打开的文件数: $lsof_count"
    fi
else
    echo "Qdrant 服务未运行"
fi

echo ""
echo "检查 Python 进程的文件描述符使用情况..."
if pgrep -f python > /dev/null; then
    python_pid=$(pgrep -f python | head -n 1)
    if [ -n "$python_pid" ]; then
        echo "Python PID: $python_pid"
        lsof_count=$(lsof -p $python_pid 2>/dev/null | wc -l)
        echo "当前打开的文件数: $lsof_count"
    fi
fi

