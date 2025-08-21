"""
数据库模块初始化
"""

from .base import Base
from .book import Book, BookSnapshot
from .ranking import Ranking, RankingSnapshot

__all__ = ["Base", "Book", "BookSnapshot", "Ranking", "RankingSnapshot"]