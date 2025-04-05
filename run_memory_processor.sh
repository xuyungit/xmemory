#!/bin/bash
# 记忆处理后台工作器启动脚本

# 设置环境变量
export PYTHONPATH=$(pwd):$PYTHONPATH

# 启动参数（可根据需要调整）
INTERVAL=60  # 轮询间隔（秒）
BATCH_SIZE=20  # 每批处理的记忆数量
LOG_FILE="memory_processor.log"  # 日志文件

# 启动工作器在后台运行
echo "启动记忆处理工作器..."
nohup python -m app.llm.memory_processor_worker --interval $INTERVAL --batch-size $BATCH_SIZE > $LOG_FILE 2>&1 &

# 获取进程ID
PID=$!
echo "记忆处理工作器已启动 (PID: $PID)"
echo $PID > memory_processor.pid