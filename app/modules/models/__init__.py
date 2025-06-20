"""
Model层

统一导出所有数据模型
"""
# 基础类型
from .base import UpdateFrequency

# 数据库模型
from .book import Book, BookSnapshot
from .ranking import Ranking, RankingSnapshot

# API模型
from .api import (
    # Book相关
    BookDetail, BookInRanking, BookRankingHistory, BookTrendData,
    # Ranking相关  
    RankingInfo, RankingSnapshotSummary,
    # 请求响应模型
    PageConfig, SubPageConfig, RankingConfig, PagesResponse,
    RankingBooksResponse, RankingHistoryResponse,
    BookRankingsResponse, BookTrendsResponse, BookSearchResponse,
    CrawlJiaziRequest, CrawlRankingRequest, TaskCreateResponse,
    TaskInfo, TasksResponse
)

__all__ = [
    # 基础类型
    "UpdateFrequency",
    
    # 数据库模型
    "Book", "BookSnapshot", "Ranking", "RankingSnapshot",
    
    # API模型
    "BookDetail", "BookInRanking", "BookRankingHistory", "BookTrendData",
    "RankingInfo", "RankingSnapshotSummary",
    
    # 请求响应模型
    "PageConfig", "SubPageConfig", "RankingConfig", "PagesResponse",
    "RankingBooksResponse", "RankingHistoryResponse",
    "BookRankingsResponse", "BookTrendsResponse", "BookSearchResponse",
    "CrawlJiaziRequest", "CrawlRankingRequest", "TaskCreateResponse",
    "TaskInfo", "TasksResponse"
]