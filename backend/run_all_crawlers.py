#!/usr/bin/env python3
"""
完整爬虫执行脚本 - 运行所有爬虫任务

用法:
    python run_all_crawlers.py
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from manual_jiazi_crawl import run_jiazi_crawl
from manual_page_crawl import run_all_page_crawls


async def run_all_crawlers():
    """运行所有爬虫任务"""
    start_time = datetime.now()
    
    print("=" * 60)
    print("JJCrawler 完整爬虫任务执行")
    print("=" * 60)
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. 运行夹子榜爬虫
        print("🚀 第一步：执行夹子榜爬虫")
        print("-" * 40)
        await run_jiazi_crawl()
        
        print("\n等待 3 秒...")
        await asyncio.sleep(3)
        
        # 2. 运行所有页面爬虫
        print("\n🚀 第二步：执行所有页面爬虫")
        print("-" * 40)
        await run_all_page_crawls()
        
        # 执行完成
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("✅ 所有爬虫任务执行完成")
        print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {duration}")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
        
    except Exception as e:
        print(f"\n\n❌ 执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


async def run_with_status_check():
    """带状态检查的执行"""
    try:
        # 检查系统状态
        print("🔍 检查系统状态...")
        
        from app.modules.service.task_service import get_task_manager
        task_manager = get_task_manager()
        
        # 显示当前任务状态
        summary = task_manager.get_task_summary()
        print(f"当前任务状态:")
        print(f"  - 运行中: {summary['current_count']}")
        print(f"  - 已完成: {summary['completed_count']}")
        print(f"  - 失败: {summary['failed_count']}")
        
        if summary['current_count'] > 0:
            print("\n⚠️  警告：有任务正在运行中，建议等待完成后再执行")
            print("是否继续执行？(y/N): ", end="")
            
            if input().lower() != 'y':
                print("已取消执行")
                return
        
        print()
        
        # 执行所有爬虫
        await run_all_crawlers()
        
        # 显示最终状态
        print("\n📊 最终任务状态:")
        final_summary = task_manager.get_task_summary()
        print(f"  - 运行中: {final_summary['current_count']}")
        print(f"  - 已完成: {final_summary['completed_count']}")
        print(f"  - 失败: {final_summary['failed_count']}")
        
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")
        # 即使状态检查失败，也尝试执行爬虫
        await run_all_crawlers()


def show_help():
    """显示帮助信息"""
    print("JJCrawler 完整爬虫执行脚本")
    print()
    print("用法:")
    print("  python run_all_crawlers.py              # 执行所有爬虫任务")
    print("  python run_all_crawlers.py --check      # 带状态检查的执行")
    print("  python run_all_crawlers.py --help       # 显示帮助")
    print()
    print("说明:")
    print("  本脚本将依次执行:")
    print("  1. 夹子榜爬虫 (jiazi)")
    print("  2. 所有页面爬虫 (yq, ca, ys, nocp_plus, bh, index)")
    print()
    print("注意:")
    print("  - 确保后端服务正在运行")
    print("  - 爬取过程中避免中断，以免数据不一致")
    print("  - 建议在网络稳定的环境下执行")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            show_help()
        elif sys.argv[1] == "--check":
            asyncio.run(run_with_status_check())
        else:
            print(f"未知参数: {sys.argv[1]}")
            print("使用 --help 查看帮助")
    else:
        asyncio.run(run_all_crawlers())