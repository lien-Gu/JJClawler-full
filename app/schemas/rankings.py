"""
榜单相关的数据模型
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BookInRanking(BaseModel):
    """榜单中的书籍信息"""
    book_id: str = Field(..., description="书籍ID")
    title: str = Field(..., description="书名")
    author_name: str = Field(..., description="作者名")
    author_id: str = Field(..., description="作者ID")
    position: int = Field(..., description="榜单位置")
    novel_class: Optional[str] = Field(None, description="小说分类")
    tags: Optional[str] = Field(None, description="标签")
    position_change: Optional[str] = Field(None, description="排名变化 (+2, -1, new)")


class RankingInfo(BaseModel):
    """榜单基本信息"""
    ranking_id: str = Field(..., description="榜单ID")
    name: str = Field(..., description="榜单名称")
    channel: str = Field(..., description="频道参数")


class RankingBooksResponse(BaseModel):
    """榜单书籍列表响应"""
    ranking: RankingInfo = Field(..., description="榜单信息")
    snapshot_time: datetime = Field(..., description="快照时间")
    total_books: int = Field(..., description="总书籍数")
    books: List[BookInRanking] = Field(..., description="书籍列表")


class RankingSnapshot(BaseModel):
    """榜单历史快照"""
    snapshot_time: datetime = Field(..., description="快照时间")
    total_books: int = Field(..., description="书籍总数")
    top_book_title: Optional[str] = Field(None, description="第一名书籍")


class RankingHistoryResponse(BaseModel):
    """榜单历史响应"""
    ranking: RankingInfo = Field(..., description="榜单信息")
    days: int = Field(..., description="历史天数")
    snapshots: List[RankingSnapshot] = Field(..., description="历史快照列表")


# 查询参数模型
class RankingBooksQuery(BaseModel):
    """榜单书籍查询参数"""
    date: Optional[str] = Field(None, description="指定日期 YYYY-MM-DD")
    limit: int = Field(50, ge=1, le=100, description="每页数量")
    offset: int = Field(0, ge=0, description="偏移量")


class RankingHistoryQuery(BaseModel):
    """榜单历史查询参数"""
    days: int = Field(7, ge=1, le=30, description="历史天数")