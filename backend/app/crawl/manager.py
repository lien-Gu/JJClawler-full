"""
爬虫管理器 - 简化版本
"""
from typing import Dict, List, Any, Union
from .crawl_flow import CrawlFlow
from app.config import settings


class CrawlerManager:
    """爬虫管理器，基于流程设计"""
    
    def __init__(self, request_delay: float = None):
        """
        初始化爬虫管理器
        
        Args:
            request_delay: 请求间隔时间（秒）
        """
        self.request_delay = request_delay or settings.crawler.request_delay
        self.flow = CrawlFlow(self.request_delay)
    
    async def crawl(self, task_ids: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """
        执行爬取任务
        
        Args:
            task_ids: 任务ID或任务ID列表
            
        Returns:
            爬取结果列表
        """
        if isinstance(task_ids, str):
            return [await self.flow.execute_crawl_task(task_ids)]
        else:
            return await self.flow.execute_multiple_tasks(task_ids)

    
    async def crawl_all_tasks(self) -> List[Dict[str, Any]]:
        """爬取所有配置的任务"""
        from .base import CrawlConfig
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        task_ids = [task["id"] for task in all_tasks]
        return await self.crawl(task_ids)
    
    async def crawl_tasks_by_category(self, category: str) -> List[Dict[str, Any]]:
        """根据分类爬取任务"""
        from .base import CrawlConfig
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        
        matching_tasks = []
        for task in all_tasks:
            task_id = task["id"]
            if task_id == category or task_id.startswith(f"{category}."):
                matching_tasks.append(task_id)
        
        return await self.crawl(matching_tasks) if matching_tasks else []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.flow.get_stats()
    
    def get_data(self) -> Dict[str, List]:
        """获取爬取数据"""
        return self.flow.get_all_data()
    
    async def close(self):
        """关闭连接"""
        await self.flow.close()