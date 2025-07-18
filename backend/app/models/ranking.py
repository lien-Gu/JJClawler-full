"""
榜单相关数据模型
"""
from typing import List, Optional
from datetime import datetime
from datetime import date as Date
from pydantic import BaseModel, Field


class RankingResponse(BaseModel):
    """榜单基础信息响应"""
    ranking_id: str = Field(..., description="榜单ID")  # 修改为string类型
    name: str = Field(..., description="榜单名称")
    page_id: str = Field(..., description="页面ID")
    url: str = Field(..., description="榜单URL")
    category: Optional[str] = Field(None, description="榜单分类")
    is_active: bool = Field(True, description="是否启用")
    crawl_frequency: int = Field(60, description="爬取频率（分钟）")
    last_crawl_time: Optional[datetime] = Field(None, description="最后爬取时间")
    create_time: datetime = Field(..., description="创建时间")


class BookInRanking(BaseModel):
    """榜单中的书籍信息"""
    book_id: int = Field(..., description="书籍ID")
    title: str = Field(..., description="书名")
    position: int = Field(..., description="排名位置")
    score: Optional[float] = Field(None, description="得分")
    clicks: Optional[int] = Field(None, description="点击数")
    favorites: Optional[int] = Field(None, description="收藏数")
    comments: Optional[int] = Field(None, description="评论数")
    word_count: Optional[int] = Field(None, description="字数")


class RankingDetailResponse(BaseModel):
    """榜单详情响应"""
    ranking_id: str = Field(..., description="榜单ID")  # 修改为string类型
    name: str = Field(..., description="榜单名称")
    page_id: str = Field(..., description="页面ID")
    category: Optional[str] = Field(None, description="榜单分类")
    snapshot_time: datetime = Field(..., description="快照时间")
    books: List[BookInRanking] = Field([], description="榜单书籍列表")
    total_books: int = Field(0, description="书籍总数")


class RankingHistoryPoint(BaseModel):
    """榜单历史数据点"""
    date: Date = Field(..., description="日期")
    book_id: int = Field(..., description="书籍ID")
    title: str = Field(..., description="书名")
    position: int = Field(..., description="排名位置")
    score: Optional[float] = Field(None, description="得分")


class RankingHistoryResponse(BaseModel):
    """榜单历史响应"""
    ranking_id: int = Field(..., description="榜单ID")
    ranking_name: str = Field(..., description="榜单名称")
    start_date: Date = Field(..., description="开始日期")
    end_date: Date = Field(..., description="结束日期")
    history_data: List[RankingHistoryPoint] = Field([], description="历史数据")


class RankingStatsResponse(BaseModel):
    """榜单统计响应"""
    ranking_id: int = Field(..., description="榜单ID")
    ranking_name: str = Field(..., description="榜单名称")
    total_snapshots: int = Field(0, description="总快照数")
    unique_books: int = Field(0, description="上榜书籍总数")
    avg_books_per_snapshot: float = Field(0.0, description="平均每快照书籍数")
    most_stable_book: Optional[str] = Field(None, description="最稳定上榜书籍")
    first_snapshot_time: Optional[datetime] = Field(None, description="首次快照时间")
    last_snapshot_time: Optional[datetime] = Field(None, description="最新快照时间")


class RankingCompareRequest(BaseModel):
    """榜单对比请求"""
    ranking_ids: List[int] = Field(..., description="要对比的榜单ID列表", min_length=2, max_length=5)
    date: Optional[Date] = Field(None, description="对比日期，默认为最新")
    limit: int = Field(50, ge=1, le=200, description="每个榜单显示的书籍数量")


class RankingCompareResponse(BaseModel):
    """榜单对比响应"""
    compare_date: Date = Field(..., description="对比日期")
    rankings: List[RankingDetailResponse] = Field([], description="榜单详情列表")
    common_books: List[BookInRanking] = Field([], description="共同上榜书籍")
    unique_books_count: int = Field(0, description="各榜单独有书籍总数") 