"""
书籍相关的数据模型
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BookDetail(BaseModel):
    """书籍详细信息"""
    book_id: str = Field(..., description="书籍ID")
    title: str = Field(..., description="书名")
    author_id: str = Field(..., description="作者ID")
    author_name: str = Field(..., description="作者名")
    novel_class: Optional[str] = Field(None, description="小说分类")
    tags: Optional[str] = Field(None, description="标签")
    first_seen: datetime = Field(..., description="首次发现时间")
    last_updated: datetime = Field(..., description="最后更新时间")
    
    # 最新统计数据
    latest_clicks: Optional[int] = Field(None, description="最新点击量")
    latest_favorites: Optional[int] = Field(None, description="最新收藏量")
    latest_comments: Optional[int] = Field(None, description="最新评论数")
    latest_chapters: Optional[int] = Field(None, description="最新章节数")


class BookRankingHistory(BaseModel):
    """书籍榜单历史"""
    ranking_id: str = Field(..., description="榜单ID")
    ranking_name: str = Field(..., description="榜单名称")
    position: int = Field(..., description="排名位置")
    snapshot_time: datetime = Field(..., description="快照时间")


class BookRankingsResponse(BaseModel):
    """书籍榜单历史响应"""
    book: BookDetail = Field(..., description="书籍信息")
    current_rankings: List[BookRankingHistory] = Field(..., description="当前在榜情况")
    history: List[BookRankingHistory] = Field(..., description="历史榜单记录")
    total_records: int = Field(..., description="总记录数")


class BookTrendData(BaseModel):
    """书籍趋势数据点"""
    date: str = Field(..., description="日期 YYYY-MM-DD")
    total_clicks: Optional[int] = Field(None, description="总点击量")
    total_favorites: Optional[int] = Field(None, description="总收藏量")
    comment_count: Optional[int] = Field(None, description="评论数")
    chapter_count: Optional[int] = Field(None, description="章节数")


class BookTrendsResponse(BaseModel):
    """书籍趋势响应"""
    book_id: str = Field(..., description="书籍ID")
    title: str = Field(..., description="书名")
    days: int = Field(..., description="趋势天数")
    trends: List[BookTrendData] = Field(..., description="趋势数据")


# 查询参数模型
class BookRankingsQuery(BaseModel):
    """书籍榜单查询参数"""
    days: int = Field(30, ge=1, le=365, description="历史天数")
    limit: int = Field(50, ge=1, le=100, description="每页数量")
    offset: int = Field(0, ge=0, description="偏移量")


class BookTrendsQuery(BaseModel):
    """书籍趋势查询参数"""
    days: int = Field(30, ge=1, le=365, description="趋势天数")


class BooksSearchQuery(BaseModel):
    """书籍搜索查询参数"""
    author: Optional[str] = Field(None, description="作者名筛选")
    tags: Optional[str] = Field(None, description="标签筛选")
    novel_class: Optional[str] = Field(None, description="分类筛选")
    limit: int = Field(20, ge=1, le=100, description="每页数量")
    offset: int = Field(0, ge=0, description="偏移量")


class BooksSearchResponse(BaseModel):
    """书籍搜索响应"""
    total: int = Field(..., description="总数量")
    books: List[BookDetail] = Field(..., description="书籍列表")