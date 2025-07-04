"""
书籍相关数据模型
"""
from typing import List, Optional
from datetime import datetime
from datetime import date as Date
from pydantic import BaseModel, Field


class BookResponse(BaseModel):
    """书籍基础信息响应"""
    book_id: int = Field(..., description="书籍ID")
    title: str = Field(..., description="书名")
    author: str = Field(..., description="作者")
    category: Optional[str] = Field(None, description="分类")
    tags: List[str] = Field([], description="标签列表")
    status: Optional[str] = Field(None, description="连载状态")
    word_count: Optional[int] = Field(None, description="字数")
    chapter_count: Optional[int] = Field(None, description="章节数")
    update_time: Optional[datetime] = Field(None, description="最后更新时间")
    create_time: datetime = Field(..., description="创建时间")


class BookDetailResponse(BookResponse):
    """书籍详情响应"""
    description: Optional[str] = Field(None, description="简介")
    cover_url: Optional[str] = Field(None, description="封面链接")
    jj_url: Optional[str] = Field(None, description="晋江原文链接")
    total_clicks: Optional[int] = Field(None, description="总点击数")
    total_favorites: Optional[int] = Field(None, description="总收藏数")
    total_comments: Optional[int] = Field(None, description="总评论数")
    total_recommendations: Optional[int] = Field(None, description="总推荐数")
    avg_rating: Optional[float] = Field(None, description="平均评分")
    
    # 最新统计数据
    latest_clicks: Optional[int] = Field(None, description="最新点击数")
    latest_favorites: Optional[int] = Field(None, description="最新收藏数")
    latest_comments: Optional[int] = Field(None, description="最新评论数")
    latest_recommendations: Optional[int] = Field(None, description="最新推荐数")
    snapshot_time: Optional[datetime] = Field(None, description="统计快照时间")


class BookTrendPoint(BaseModel):
    """书籍趋势数据点"""
    date: Date = Field(..., description="日期")
    clicks: Optional[int] = Field(None, description="点击数")
    favorites: Optional[int] = Field(None, description="收藏数")
    comments: Optional[int] = Field(None, description="评论数")
    recommendations: Optional[int] = Field(None, description="推荐数")


class BookTrendResponse(BaseModel):
    """书籍趋势响应"""
    book_id: int = Field(..., description="书籍ID")
    title: str = Field(..., description="书名")
    trend_data: List[BookTrendPoint] = Field([], description="趋势数据")
    start_date: Date = Field(..., description="开始日期")
    end_date: Date = Field(..., description="结束日期")


class BookSearchRequest(BaseModel):
    """书籍搜索请求"""
    query: Optional[str] = Field(None, description="搜索关键词")
    author: Optional[str] = Field(None, description="作者筛选")
    category: Optional[str] = Field(None, description="分类筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    status: Optional[str] = Field(None, description="状态筛选")
    min_word_count: Optional[int] = Field(None, description="最小字数")
    max_word_count: Optional[int] = Field(None, description="最大字数")
    order_by: str = Field("update_time", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")


class BookRankingInfo(BaseModel):
    """书籍排名信息"""
    ranking_id: int = Field(..., description="榜单ID")
    ranking_name: str = Field(..., description="榜单名称")
    position: int = Field(..., description="排名位置")
    score: Optional[float] = Field(None, description="得分")
    snapshot_time: datetime = Field(..., description="快照时间")


class BookRankingHistoryResponse(BaseModel):
    """书籍排名历史响应"""
    book_id: int = Field(..., description="书籍ID")
    title: str = Field(..., description="书名")
    ranking_history: List[BookRankingInfo] = Field([], description="排名历史")
    total_rankings: int = Field(0, description="上榜总数")
    best_position: Optional[int] = Field(None, description="最佳排名")
    latest_position: Optional[int] = Field(None, description="最新排名") 