#!/usr/bin/env python3
"""
夹子榜爬虫手动执行脚本

用法:
    python manual_jiazi_crawl.py
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.modules.service.crawler_service import CrawlerService
from app.modules.service.task_service import get_task_manager, TaskType, execute_with_task


async def run_jiazi_crawl():
    """手动运行夹子榜爬虫"""
    print("开始执行夹子榜爬虫...")
    
    try:
        # 创建任务
        task_manager = get_task_manager()
        task_id = task_manager.create_task(
            TaskType.JIAZI, 
            {"trigger_source": "manual"}
        )
        print(f"创建任务: {task_id}")
        
        # 执行爬虫
        async def crawl_func():
            crawler_service = CrawlerService()
            try:
                result = await crawler_service.crawl_and_save_jiazi()
                print(f"爬取完成: {result}")
                return result
            finally:
                crawler_service.close()
        
        # 带任务跟踪执行
        success = await execute_with_task(task_id, crawl_func)
        
        if success:
            print(f"✅ 夹子榜爬虫执行成功，任务ID: {task_id}")
            
            # 显示任务详情
            task = task_manager.get_task(task_id)
            if task:
                print(f"任务状态: {task.status}")
                print(f"爬取条目: {task.items_crawled}")
        else:
            print(f"❌ 夹子榜爬虫执行失败，任务ID: {task_id}")
            
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("夹子榜爬虫手动执行脚本")
    print("=" * 40)
    asyncio.run(run_jiazi_crawl())