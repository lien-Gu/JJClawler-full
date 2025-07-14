"""
数据模型模块 - 定义API请求和响应的数据结构
"""

from .base import *
from .book import *
from .ranking import *
from .crawl import *
from .schedule import *

__all__ = [
    # 基础模型
    "BaseResponse",
    "PaginatedResponse",
    "ErrorResponse",
    
    # 书籍相关模型
    "BookResponse",
    "BookDetailResponse", 
    "BookTrendResponse",
    "BookSearchRequest",
    
    # 榜单相关模型
    "RankingResponse",
    "RankingDetailResponse",
    "RankingHistoryResponse",
    
    # 爬虫相关模型
    "CrawlTaskResponse",
    "CrawlTaskStatusResponse",
    "CrawlTaskDetailResponse",
    "CrawlSystemStatusResponse",
    "CrawlConfigResponse",
    "CrawlPagesRequest",
    "UpdateCrawlConfigRequest",
    
    # 调度相关模型
    "JobStatus",
    "TriggerType", 
    "JobHandlerType",
    "JobContextModel",
    "JobResultModel",
    "JobConfigModel",
    "JobInfoModel",
    "PREDEFINED_JOB_CONFIGS",
] 