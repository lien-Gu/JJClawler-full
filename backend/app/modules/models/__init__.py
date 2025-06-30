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
    # Book相关 - 保留用于内部数据处理
    BookDetail, BookInRanking, BookRankingHistory, BookTrendData,
    # Ranking相关 - 保留用于内部数据处理 
    RankingInfo, RankingSnapshotSummary,
    # 请求模型 - 仍然需要
    CrawlJiaziRequest, CrawlRankingRequest,
    # 内部任务信息模型 - 用于数据转换
    TaskInfo,
    # 页面配置相关 - rankings.py 仍在使用
    RankingConfig
)

__all__ = [
    # 基础类型
    "UpdateFrequency",
    
    # 数据库模型
    "Book", "BookSnapshot", "Ranking", "RankingSnapshot",
    
    # API模型
    "BookDetail", "BookInRanking", "BookRankingHistory", "BookTrendData",
    "RankingInfo", "RankingSnapshotSummary",
    
    # 请求模型
    "CrawlJiaziRequest", "CrawlRankingRequest",
    # 内部数据模型
    "TaskInfo", "RankingConfig"
]