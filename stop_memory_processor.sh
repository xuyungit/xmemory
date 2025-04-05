#!/bin/bash
# 记忆处理工作器停止脚本

# 检查PID文件是否存在
if [ ! -f "memory_processor.pid" ]; then
    echo "找不到记忆处理工作器的PID文件，工作器可能未运行"
    exit 1
fi

# 读取PID
PID=$(cat memory_processor.pid)

# 检查进程是否存在
if ! ps -p $PID > /dev/null; then
    echo "记忆处理工作器 (PID: $PID) 已经不在运行"
    rm memory_processor.pid
    exit 0
fi

# 发送终止信号
echo "正在停止记忆处理工作器 (PID: $PID)..."
kill $PID

# 等待进程结束
TIMEOUT=10
for ((i=1; i<=TIMEOUT; i++)); do
    if ! ps -p $PID > /dev/null; then
        echo "记忆处理工作器已成功停止"
        rm memory_processor.pid
        exit 0
    fi
    sleep 1
done

# 如果进程仍然存在，强制终止
echo "记忆处理工作器未响应，强制终止..."
kill -9 $PID

if ! ps -p $PID > /dev/null; then
    echo "记忆处理工作器已强制终止"
else
    echo "无法终止记忆处理工作器，请手动检查"
fi

rm memory_processor.pid