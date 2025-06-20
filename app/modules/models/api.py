"""
API响应模型定义

定义API接口的请求和响应模型
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from .base import UpdateFrequency


class BookDetail(SQLModel, table=False):
    """书籍详情API模型"""
    # 基础书籍信息
    id: Optional[int] = Field(default=None)
    book_id: str = Field(description="书籍ID")
    title: str = Field(description="书名")
    author_id: str = Field(description="作者ID")
    author_name: str = Field(description="作者名")
    novel_class: Optional[str] = Field(default=None, description="小说分类")
    tags: Optional[str] = Field(default=None, description="标签")
    first_seen: datetime = Field(description="首次发现时间")
    last_updated: datetime = Field(description="最后更新时间")
    
    # API特有的聚合字段
    latest_clicks: Optional[int] = Field(default=None, description="最新点击量")
    latest_favorites: Optional[int] = Field(default=None, description="最新收藏量")
    latest_comments: Optional[int] = Field(default=None, description="最新评论数")
    latest_chapters: Optional[int] = Field(default=None, description="最新章节数")


class RankingInfo(SQLModel, table=False):
    """榜单信息API模型"""
    id: Optional[int] = Field(default=None)
    ranking_id: str = Field(description="榜单ID")
    name: str = Field(description="榜单中文名")
    channel: str = Field(description="API频道参数")
    frequency: UpdateFrequency = Field(description="更新频率")
    update_interval: int = Field(description="更新间隔(小时)")
    parent_id: Optional[str] = Field(default=None, description="父级榜单ID")


class BookInRanking(SQLModel, table=False):
    """榜单中的书籍信息API模型"""
    # 从Book模型选择性继承字段
    book_id: str = Field(description="书籍ID")
    title: str = Field(description="书名")
    author_name: str = Field(description="作者名")
    author_id: str = Field(description="作者ID")
    novel_class: Optional[str] = Field(default=None, description="小说分类")
    tags: Optional[str] = Field(default=None, description="标签")
    
    # 榜单特有字段
    position: int = Field(description="榜单位置")
    position_change: Optional[str] = Field(default=None, description="排名变化")


class BookRankingHistory(SQLModel, table=False):
    """书籍榜单历史API模型"""
    ranking_id: str = Field(description="榜单ID")
    ranking_name: str = Field(description="榜单名称")
    position: int = Field(description="排名位置")
    snapshot_time: datetime = Field(description="快照时间")


class BookTrendData(SQLModel, table=False):
    """书籍趋势数据API模型"""
    date: str = Field(description="日期 YYYY-MM-DD")
    total_clicks: Optional[int] = Field(default=None, description="总点击量")
    total_favorites: Optional[int] = Field(default=None, description="总收藏量")
    comment_count: Optional[int] = Field(default=None, description="评论数")
    chapter_count: Optional[int] = Field(default=None, description="章节数")


class RankingSnapshotSummary(SQLModel, table=False):
    """榜单历史快照摘要API模型"""
    snapshot_time: datetime = Field(description="快照时间")
    total_books: int = Field(description="书籍总数")
    top_book_title: Optional[str] = Field(default=None, description="第一名书籍")