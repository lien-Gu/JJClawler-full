"""
Service层

业务逻辑层，组合DAO操作实现业务功能：
- BookService: 书籍业务逻辑
- RankingService: 榜单业务逻辑  
- CrawlerService: 爬虫业务逻辑
- TaskService: 任务管理业务逻辑
- PageService: 页面配置业务逻辑（T4.2实现）
- SchedulerService: 调度器业务逻辑（T4.3实现）
"""
from .book_service import BookService
from .ranking_service import RankingService
from .crawler_service import CrawlerService
from .task_service import get_task_manager, TaskManager
from .page_service import PageService, get_page_service
from .scheduler_service import SchedulerService, get_scheduler_service

__all__ = [
    "BookService", 
    "RankingService", 
    "CrawlerService",
    "TaskManager",
    "get_task_manager",
    "PageService",
    "get_page_service",
    "SchedulerService",
    "get_scheduler_service"
]