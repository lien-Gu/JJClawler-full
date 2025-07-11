"""
数据库模块初始化
"""

from .db.base import Base
from .db.book import Book
from .db.ranking import Ranking
from .db.crawl_task import CrawlTask

# 导出所有模型以便数据库初始化时创建表
__all__ = [
    "Base",
    "Book", 
    "Ranking",
    "CrawlTask"
]