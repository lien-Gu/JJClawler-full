"""
书籍相关数据模型
"""
from typing import List, Optional
from datetime import datetime
from datetime import date as Date
from pydantic import BaseModel, Field


class BookResponse(BaseModel):
    """书籍基础信息响应"""
    id: int = Field(..., description="书籍ID")
    novel_id: int = Field(gt=0,  description="网站上的小说ID")
    title: str = Field(min_length=1, description="书名")


class BookTrendPoint(BaseModel):
    """书籍趋势数据点"""
    snapshot_time: datetime = Field(..., description="日期")
    clicks: Optional[int] = Field(None, description="点击数")
    favorites: Optional[int] = Field(None, description="收藏数")
    comments: Optional[int] = Field(None, description="评论数")
    recommendations: Optional[int] = Field(None, description="推荐数")


class BookTrendAggregatedPoint(BaseModel):
    """书籍聚合趋势数据点"""
    time_period: str = Field(..., description="时间周期")
    avg_favorites: float = Field(..., description="平均收藏数")
    avg_clicks: float = Field(..., description="平均点击数")
    avg_comments: float = Field(..., description="平均评论数")
    avg_recommendations: float = Field(..., description="平均推荐数")
    max_favorites: int = Field(..., description="最大收藏数")
    max_clicks: int = Field(..., description="最大点击数")
    min_favorites: int = Field(..., description="最小收藏数")
    min_clicks: int = Field(..., description="最小点击数")
    snapshot_count: int = Field(..., description="快照数量")
    period_start: datetime = Field(..., description="周期开始时间")
    period_end: datetime = Field(..., description="周期结束时间")


class BookDetailResponse(BookResponse, BookTrendPoint):
    """书籍详情响应，总是获取最新时间的point"""



class BookRankingInfo(BaseModel):
    """书籍排名信息"""
    book_id: int = Field(..., description="书籍ID")
    ranking_id: int = Field(..., description="榜单ID")
    ranking_name: str = Field(..., description="榜单名称")
    position: int = Field(..., description="排名位置")
    snapshot_time: datetime = Field(..., description="快照时间")


class BookRankingHistoryResponse(BaseModel):
    """书籍排名历史响应"""
    book_id: int = Field(..., description="书籍ID")
    ranking_history: List[BookRankingInfo] = Field([], description="排名历史")
