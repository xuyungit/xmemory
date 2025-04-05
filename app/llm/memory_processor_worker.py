#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Memory Processor Worker
======================
This script runs as a separate process to check for unprocessed RAW memories 
and process them using the memory_agent.update_insight_memory function.
"""

import asyncio
import logging
import time
import signal
import sys
from typing import List, Optional
from datetime import datetime
import pytz

from app.db.elasticsearch.memory_repository import MemoryRepository
from app.db.elasticsearch.models import MemoryDocument, MemoryType
from app.llm.memory_agent import update_insight_memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("memory_processor.log")
    ]
)
logger = logging.getLogger("memory_processor")

# Flag to control the worker loop
is_running = True

async def process_memory(memory_doc: MemoryDocument) -> bool:
    """
    处理一条记忆并更新状态
    
    Args:
        memory_doc: 待处理的记忆文档
        
    Returns:
        bool: 处理成功返回True，否则返回False
    """
    try:
        logger.info(f"处理记忆 ID: {memory_doc._id}, 用户: {memory_doc.user_id}, 记忆: {memory_doc.content}")
        
        # 使用记忆代理处理记忆
        await update_insight_memory(memory_doc)
        
        # 更新记忆状态为已处理
        memory_doc.processed = True
        memory_doc.updated_at = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%dT%H:%M:%S%z')
        
        # 更新数据库中的记忆状态
        repo = MemoryRepository()
        success = await repo.update_memory(memory_doc._id, memory_doc)
        
        if success:
            logger.info(f"成功处理记忆 ID: {memory_doc._id}")
        else:
            logger.error(f"更新记忆状态失败 ID: {memory_doc._id}")
            
        return success
    
    except Exception as e:
        logger.error(f"处理记忆时出错 ID: {memory_doc._id}: {str(e)}")
        return False

async def process_batch(batch_size: int = 10, user_id: Optional[str] = None) -> int:
    """
    处理一批未处理的记忆
    
    Args:
        batch_size: 每批处理的记忆数量
        user_id: 可选的用户ID过滤
    
    Returns:
        int: 成功处理的记忆数量
    """
    # 使用MemoryRepository类的方法获取未处理的记忆
    repo = MemoryRepository()
    memories = await repo.get_unprocessed_memories(batch_size, user_id)
    
    if not memories:
        return 0
    
    processed_count = 0
    for memory in memories:
        if await process_memory(memory):
            processed_count += 1
    
    return processed_count

async def memory_processor_loop(interval: int = 60, batch_size: int = 10):
    """
    记忆处理器的主循环，定期查找并处理未处理的记忆
    
    Args:
        interval: 轮询间隔（秒）
        batch_size: 每批处理的记忆数量
    """
    logger.info(f"记忆处理器已启动，轮询间隔: {interval}秒，批处理大小: {batch_size}")
    
    while is_running:
        try:
            processed_count = await process_batch(batch_size)
            
            if processed_count > 0:
                logger.info(f"已处理 {processed_count} 条记忆")
                # 如果成功处理了记忆，立即继续检查是否还有更多记忆需要处理
                continue
            else:
                logger.info("没有找到需要处理的记忆，等待下次轮询")
                
            # 等待指定的间隔时间后再次轮询
            await asyncio.sleep(interval)
            
        except Exception as e:
            logger.error(f"处理循环中发生错误: {str(e)}")
            # 出错后等待一段时间后再继续
            await asyncio.sleep(10)

def signal_handler(sig, frame):
    """信号处理器，用于优雅地关闭Worker"""
    global is_running
    logger.info("接收到中断信号，准备关闭...")
    is_running = False

def main():
    """Worker主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 从命令行参数获取配置
    import argparse
    parser = argparse.ArgumentParser(description="记忆处理Worker")
    parser.add_argument("--interval", type=int, default=60, help="轮询间隔（秒）")
    parser.add_argument("--batch-size", type=int, default=10, help="每批处理的记忆数量")
    parser.add_argument("--user-id", type=str, help="可选的用户ID过滤")
    
    args = parser.parse_args()
    
    logger.info(f"启动参数: 间隔={args.interval}s, 批处理大小={args.batch_size}, 用户ID={args.user_id or '所有'}")
    
    try:
        # 启动异步事件循环
        loop = asyncio.get_event_loop()
        
        # 创建并启动主处理循环
        task = loop.create_task(memory_processor_loop(
            interval=args.interval,
            batch_size=args.batch_size
        ))
        
        # 运行直到接收中断信号
        loop.run_until_complete(task)
        
    except Exception as e:
        logger.error(f"Worker发生未捕获异常: {str(e)}")
        return 1
    finally:
        logger.info("记忆处理Worker已关闭")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())