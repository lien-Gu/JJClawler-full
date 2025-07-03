"""
Service层

业务逻辑层，提供核心业务功能：
- BookService: 书籍业务逻辑
- RankingService: 榜单业务逻辑  
- CrawlerService: 统一爬虫服务
"""

from .book_service import BookService
from .ranking_service import RankingService
from .crawler_service import CrawlerService, get_crawler_service

__all__ = ["BookService", "RankingService", "CrawlerService", "get_crawler_service"]
