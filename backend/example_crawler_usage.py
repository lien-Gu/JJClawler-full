"""
爬虫管理器使用示例 - 包含数据存储功能
"""
import asyncio
from app.crawl.manager import CrawlerManager


async def main():
    """
    演示爬虫管理器的使用，包括数据存储到数据库
    """
    # 创建爬虫管理器
    manager = CrawlerManager(request_delay=1.0)
    
    try:
        print("开始爬取任务...")
        
        # 方式1：爬取单个任务
        print("\n1. 爬取单个任务:")
        results = await manager.crawl("jiazi")
        for result in results:
            print(f"任务: {result['task_id']}")
            print(f"成功: {result['success']}")
            if result['success']:
                print(f"榜单数量: {len(result.get('rankings', []))}")
                print(f"书籍数量: {len(result.get('books', []))}")
                print(f"数据已自动保存到数据库!")
            print("-" * 50)
        
        # 方式2：爬取多个任务
        print("\n2. 爬取多个任务:")
        results = await manager.crawl(["task1", "task2"])
        print(f"完成 {len(results)} 个任务，数据已保存到数据库")
        
        # 方式3：根据分类爬取
        print("\n3. 根据分类爬取:")
        results = await manager.crawl_tasks_by_category("romance")
        print(f"完成言情分类下的 {len(results)} 个任务")
        
        # 获取统计信息
        print("\n4. 获取统计信息:")
        stats = manager.get_stats()
        print(f"统计信息: {stats}")
        
    except Exception as e:
        print(f"爬取过程中出现错误: {e}")
        
    finally:
        # 关闭连接
        await manager.close()
        print("\n爬虫管理器已关闭")


if __name__ == "__main__":
    # 注意：这只是一个示例，实际运行需要正确的数据库配置和URL配置
    print("这是一个示例文件，展示了爬虫管理器的新功能:")
    print("- 自动数据存储到数据库")
    print("- 榜单数据和书籍数据的分离存储")
    print("- 事务管理和异常处理")
    print("- 完整的日志记录")
    print("\n要实际运行，请确保:")
    print("1. 数据库连接配置正确")
    print("2. data/urls.json 配置文件存在")
    print("3. 目标网站可访问")
    
    # asyncio.run(main())  # 取消注释以实际运行