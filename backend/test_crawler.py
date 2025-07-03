#!/usr/bin/env python3
"""
爬虫模块测试脚本

测试新重构的爬虫模块功能
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.modules.crawler import get_crawler_manager


async def test_crawler():
    """测试爬虫功能"""
    crawler_manager = get_crawler_manager()
    
    print("🕷️ 测试夹子榜爬虫...")
    try:
        result = await crawler_manager.crawl_task("jiazi")
        print(f"✅ 夹子榜爬虫测试完成: {result}")
    except Exception as e:
        print(f"❌ 夹子榜爬虫测试失败: {e}")
    
    print("\n🕷️ 测试页面爬虫...")
    try:
        result = await crawler_manager.crawl_task("index")
        print(f"✅ 页面爬虫测试完成: {result}")
    except Exception as e:
        print(f"❌ 页面爬虫测试失败: {e}")
    
    # 关闭资源
    await crawler_manager.close()
    print("\n🔧 爬虫管理器已关闭")


if __name__ == "__main__":
    print("🚀 开始测试爬虫模块...")
    try:
        asyncio.run(test_crawler())
        print("✨ 测试完成！")
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"💥 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()