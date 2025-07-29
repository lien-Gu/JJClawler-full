"""
数据模型模块 - 定义API请求和响应的数据结构
"""

from .base import *
from .book import *
from .ranking import *
from .schedule import *

__all__ = [
    # 基础模型
    "BaseResponse",
    # 书籍相关模型
    "BookBasic",
    "BookDetail",
    "BookSnapshot",
    # 榜单相关模型
    "RankingBasic",
    "RankingDetail",
    # 调度相关模型
    "JobStatus",
    "TriggerType",
    "JobHandlerType",
]
