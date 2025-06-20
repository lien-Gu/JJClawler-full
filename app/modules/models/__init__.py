"""
数据模型包

导出所有数据模型类，提供统一的导入接口
"""
from .base import UpdateFrequency
from .database import Ranking, Book, BookSnapshot, RankingSnapshot  
from .api import (
    BookDetail, RankingInfo, BookInRanking, 
    BookRankingHistory, BookTrendData, RankingSnapshotSummary
)
from .request_response import (
    PageConfig, SubPageConfig, RankingConfig, PagesResponse,
    RankingBooksResponse, RankingHistoryResponse,
    BookRankingsResponse, BookTrendsResponse, BookSearchResponse,
    CrawlJiaziRequest, CrawlRankingRequest, TaskCreateResponse,
    TaskInfo, TasksResponse
)

__all__ = [
    # 枚举
    "UpdateFrequency",
    # 数据库模型
    "Ranking", "Book", "BookSnapshot", "RankingSnapshot",
    # API模型
    "BookDetail", "RankingInfo", "BookInRanking",
    "BookRankingHistory", "BookTrendData", "RankingSnapshotSummary",
    # 请求响应模型
    "PageConfig", "SubPageConfig", "RankingConfig", "PagesResponse",
    "RankingBooksResponse", "RankingHistoryResponse",
    "BookRankingsResponse", "BookTrendsResponse", "BookSearchResponse", 
    "CrawlJiaziRequest", "CrawlRankingRequest", "TaskCreateResponse",
    "TaskInfo", "TasksResponse"
]