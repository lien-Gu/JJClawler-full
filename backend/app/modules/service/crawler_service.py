"""
爬虫服务

集成新的爬虫管理器，提供统一的爬取接口
"""
from typing import Dict, Any
from datetime import datetime

from app.utils.log_utils import get_logger
from app.modules.crawler import get_crawler_manager
from app.modules.task import TaskStatus

logger = get_logger(__name__)


class CrawlerService:
    """爬虫服务 - 提供统一的爬取接口"""
    
    def __init__(self):
        self.crawler_manager = get_crawler_manager()
    
    async def crawl_and_save(self, task_id: str) -> Dict[str, Any]:
        """执行爬取和保存"""
        try:
            logger.info(f"开始执行爬取任务: {task_id}")
            
            # 使用爬虫管理器执行爬取
            result = await self.crawler_manager.crawl_task(task_id)
            
            logger.info(f"爬取任务完成 {task_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"爬取任务失败 {task_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "books_new": 0,
                "books_updated": 0,
                "total_books": 0
            }
    
    async def crawl_jiazi(self) -> Dict[str, Any]:
        """爬取夹子榜"""
        return await self.crawl_and_save("jiazi")
    
    async def crawl_page(self, page_id: str) -> Dict[str, Any]:
        """爬取分类页面"""
        return await self.crawl_and_save(page_id)
    
    async def close(self):
        """关闭资源"""
        await self.crawler_manager.close()


# 全局实例
_crawler_service = None


def get_crawler_service() -> CrawlerService:
    """获取爬虫服务实例"""
    global _crawler_service
    if _crawler_service is None:
        _crawler_service = CrawlerService()
    return _crawler_service


async def close_crawler_service():
    """关闭爬虫服务"""
    global _crawler_service
    if _crawler_service is not None:
        await _crawler_service.close()
        _crawler_service = None