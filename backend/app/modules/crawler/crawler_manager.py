"""
爬虫管理器

统一管理不同类型的爬虫，提供统一的接口
"""

from typing import Dict, Any
from app.utils.log_utils import get_logger
from .jiazi_crawler import JiaziCrawler
from .page_crawler import PageCrawler

logger = get_logger(__name__)


class CrawlerManager:
    """爬虫管理器"""

    def __init__(self):
        self.jiazi_crawler = JiaziCrawler()
        self.page_crawler = PageCrawler()

    async def crawl_task(self, task_id: str) -> Dict[str, Any]:
        """根据任务ID执行相应的爬取"""
        try:
            logger.info(f"开始执行爬取任务: {task_id}")

            if task_id == "jiazi":
                # 夹子榜爬取
                result = await self.jiazi_crawler.crawl()
            else:
                # 分类页面爬取
                result = await self.page_crawler.crawl(task_id)

            logger.info(f"爬取任务完成 {task_id}: {result.get('success', False)}")
            return result

        except Exception as e:
            logger.error(f"爬取任务失败 {task_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "books_new": 0,
                "books_updated": 0,
                "total_books": 0,
            }

    async def close(self):
        """关闭所有爬虫资源"""
        await self.jiazi_crawler.close()
        await self.page_crawler.close()


# 全局爬虫管理器实例
_crawler_manager = None


def get_crawler_manager() -> CrawlerManager:
    """获取爬虫管理器实例"""
    global _crawler_manager
    if _crawler_manager is None:
        _crawler_manager = CrawlerManager()
    return _crawler_manager


async def close_crawler_manager():
    """关闭爬虫管理器"""
    global _crawler_manager
    if _crawler_manager is not None:
        await _crawler_manager.close()
        _crawler_manager = None
