#!/usr/bin/env python3
"""
页面爬虫手动执行脚本

用法:
    python manual_page_crawl.py          # 运行所有页面爬虫
    python manual_page_crawl.py yq       # 运行指定频道爬虫
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.modules.service.crawler_service import CrawlerService
from app.modules.service.task_service import get_task_manager, TaskType, execute_with_task
from app.modules.service.page_service import get_page_service


async def run_page_crawl(channel: str):
    """手动运行指定频道的页面爬虫"""
    print(f"开始执行频道 {channel} 的页面爬虫...")
    
    try:
        # 验证频道是否有效
        page_service = get_page_service()
        available_channels = page_service.get_ranking_channels()
        valid_channels = [c['channel'] for c in available_channels]
        
        if channel not in valid_channels:
            print(f"❌ 错误：无效频道 {channel}")
            print(f"可用频道：{valid_channels}")
            return False
        
        # 创建任务
        task_manager = get_task_manager()
        task_id = task_manager.create_task(
            TaskType.PAGE, 
            {"trigger_source": "manual", "channel": channel}
        )
        print(f"创建任务: {task_id}")
        
        # 执行爬虫
        async def crawl_func():
            crawler_service = CrawlerService()
            try:
                result = await crawler_service.crawl_and_save_page(channel)
                print(f"频道 {channel} 爬取完成: {result}")
                return result
            finally:
                crawler_service.close()
        
        # 带任务跟踪执行
        success = await execute_with_task(task_id, crawl_func)
        
        if success:
            print(f"✅ 频道 {channel} 爬虫执行成功，任务ID: {task_id}")
            
            # 显示任务详情
            task = task_manager.get_task(task_id)
            if task:
                print(f"任务状态: {task.status}")
                print(f"爬取条目: {task.items_crawled}")
        else:
            print(f"❌ 频道 {channel} 爬虫执行失败，任务ID: {task_id}")
        
        return success
        
    except Exception as e:
        print(f"❌ 频道 {channel} 执行错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_page_crawls():
    """运行所有页面爬虫"""
    print("开始执行所有页面爬虫...")
    
    try:
        page_service = get_page_service()
        channels = page_service.get_ranking_channels()
        
        success_count = 0
        total_count = 0
        
        for channel_info in channels:
            channel = channel_info['channel']
            if channel == 'jiazi':  # 跳过夹子榜，它有单独的爬虫
                continue
            
            total_count += 1
            zh_name = channel_info.get('zh_name', '未知')
            print(f"\n[{total_count}] 正在爬取频道：{channel} ({zh_name})")
            
            success = await run_page_crawl(channel)
            if success:
                success_count += 1
            
            # 添加延迟避免过于频繁的请求
            if total_count < len(channels) - 1:  # 最后一个不需要等待
                print("等待 2 秒...")
                await asyncio.sleep(2)
        
        print(f"\n{'='*50}")
        print(f"所有页面爬虫执行完成")
        print(f"成功: {success_count}/{total_count}")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"❌ 执行所有页面爬虫时出错: {e}")
        import traceback
        traceback.print_exc()


def show_available_channels():
    """显示可用频道"""
    try:
        from app.modules.service.page_service import get_page_service
        page_service = get_page_service()
        channels = page_service.get_ranking_channels()
        
        print("可用频道列表:")
        print("-" * 40)
        for channel_info in channels:
            channel = channel_info['channel']
            zh_name = channel_info.get('zh_name', '未知')
            frequency = channel_info.get('frequency', '未知')
            if channel != 'jiazi':  # 夹子榜有单独的脚本
                print(f"  {channel:<12} - {zh_name} ({frequency})")
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ 获取频道列表失败: {e}")


if __name__ == "__main__":
    print("页面爬虫手动执行脚本")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            show_available_channels()
        else:
            # 爬取指定频道
            channel = sys.argv[1]
            asyncio.run(run_page_crawl(channel))
    else:
        # 爬取所有频道
        asyncio.run(run_all_page_crawls())