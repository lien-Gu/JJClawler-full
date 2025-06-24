"""
API模型定义

包含API响应模型和请求响应模型
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlmodel import SQLModel
from .base import UpdateFrequency


# ==================== Book相关API模型 ====================
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


class BookInRanking(SQLModel, table=False):
    """榜单中的书籍信息API模型"""
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


# ==================== Ranking相关API模型 ====================
class RankingInfo(SQLModel, table=False):
    """榜单信息API模型"""
    id: Optional[int] = Field(default=None)
    ranking_id: str = Field(description="榜单ID")
    name: str = Field(description="榜单中文名")
    channel: str = Field(description="API频道参数")
    frequency: UpdateFrequency = Field(description="更新频率")
    update_interval: int = Field(description="更新间隔(小时)")
    parent_id: Optional[str] = Field(default=None, description="父级榜单ID")


class RankingSnapshotSummary(SQLModel, table=False):
    """榜单历史快照摘要API模型"""
    snapshot_time: datetime = Field(description="快照时间")
    total_books: int = Field(description="书籍总数")
    top_book_title: Optional[str] = Field(default=None, description="第一名书籍")


# ==================== 请求响应模型 ====================
class PageConfig(BaseModel):
    """页面配置"""
    name: str = Field(description="页面名称")
    path: str = Field(description="页面路径")
    sub_pages: List["SubPageConfig"] = Field(description="子页面列表")


class SubPageConfig(BaseModel):
    """子页面配置"""
    name: str = Field(description="子页面名称")
    path: str = Field(description="子页面路径")
    rankings: List["RankingConfig"] = Field(description="榜单列表")


class RankingConfig(BaseModel):
    """榜单配置"""
    ranking_id: str = Field(description="榜单ID")
    name: str = Field(description="榜单名称")
    update_frequency: str = Field(description="更新频率")


class PagesResponse(BaseModel):
    """页面配置响应"""
    pages: List[PageConfig] = Field(description="页面列表")
    total_pages: int = Field(description="页面总数")
    total_rankings: int = Field(description="榜单总数")


class RankingBooksResponse(BaseModel):
    """榜单书籍列表响应"""
    ranking: RankingConfig = Field(description="榜单信息")
    books: List[dict] = Field(description="书籍列表")
    total: int = Field(description="书籍总数")
    page: int = Field(description="当前页码")
    limit: int = Field(description="每页数量")


class RankingHistoryResponse(BaseModel):
    """榜单历史响应"""
    ranking: RankingConfig = Field(description="榜单信息")
    snapshots: List[dict] = Field(description="历史快照")
    days: int = Field(description="查询天数")


class BookRankingsResponse(BaseModel):
    """书籍榜单历史响应"""
    book: dict = Field(description="书籍信息")
    current_rankings: List[dict] = Field(description="当前榜单")
    history: List[dict] = Field(description="历史榜单")
    total_records: int = Field(description="总记录数")


class BookTrendsResponse(BaseModel):
    """书籍趋势响应"""
    book_id: str = Field(description="书籍ID")
    title: str = Field(description="书籍标题")
    trends: List[dict] = Field(description="趋势数据")
    days: int = Field(description="查询天数")


class BookSearchResponse(BaseModel):
    """书籍搜索响应"""
    books: List[dict] = Field(description="书籍列表")
    total: int = Field(description="总数")


class RankingSearchResponse(BaseModel):
    """榜单搜索响应"""
    rankings: List[dict] = Field(description="榜单列表")
    total: int = Field(description="总数")
    query: Optional[str] = Field(default=None, description="搜索关键词")
    has_next: bool = Field(description="是否有下一页")


class CrawlJiaziRequest(BaseModel):
    """夹子爬取请求"""
    force: bool = Field(default=False, description="是否强制爬取")
    immediate: bool = Field(default=True, description="是否立即执行")


class CrawlRankingRequest(BaseModel):
    """榜单爬取请求"""
    force: bool = Field(default=False, description="是否强制爬取")
    immediate: bool = Field(default=True, description="是否立即执行")


class TaskCreateResponse(BaseModel):
    """任务创建响应"""
    task_id: str = Field(description="任务ID")
    message: str = Field(description="创建消息")
    status: str = Field(description="任务状态")


class TaskInfo(BaseModel):
    """任务信息"""
    task_id: str = Field(description="任务ID")
    task_type: str = Field(description="任务类型")
    status: str = Field(description="任务状态")
    created_at: datetime = Field(description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    progress: int = Field(default=0, description="进度百分比")
    items_crawled: int = Field(default=0, description="已爬取项目数")
    ranking_id: Optional[str] = Field(default=None, description="榜单ID")


class TasksResponse(BaseModel):
    """任务列表响应"""
    current_tasks: List[TaskInfo] = Field(description="当前任务")
    completed_tasks: List[TaskInfo] = Field(description="已完成任务")
    total_current: int = Field(description="当前任务总数")
    total_completed: int = Field(description="已完成任务总数")


# ==================== 新增统计和热门榜单API模型 ====================
class OverviewStats(BaseModel):
    """首页概览统计"""
    total_books: int = Field(description="书籍总数")
    total_rankings: int = Field(description="榜单总数")
    recent_snapshots: int = Field(description="最近24小时快照数")
    active_rankings: int = Field(description="活跃榜单数")
    last_updated: datetime = Field(description="最后更新时间")


class HotRankingItem(BaseModel):
    """热门榜单项"""
    ranking_id: str = Field(description="榜单ID")
    name: str = Field(description="榜单名称")
    update_frequency: str = Field(description="更新频率")
    recent_activity: int = Field(description="最近活跃度")
    total_books: int = Field(description="榜单书籍总数")
    last_updated: Optional[datetime] = Field(default=None, description="最后更新时间")


class RankingListItem(BaseModel):
    """榜单列表项"""
    ranking_id: str = Field(description="榜单ID")
    name: str = Field(description="榜单名称")
    update_frequency: str = Field(description="更新频率")
    total_books: int = Field(description="榜单书籍总数")
    last_updated: Optional[datetime] = Field(default=None, description="最后更新时间")
    parent_id: Optional[str] = Field(default=None, description="父级榜单ID")


class OverviewResponse(BaseModel):
    """首页概览响应"""
    stats: OverviewStats = Field(description="统计数据")
    status: str = Field(default="ok", description="状态")


class HotRankingsResponse(BaseModel):
    """热门榜单响应"""
    rankings: List[HotRankingItem] = Field(description="热门榜单列表")
    total: int = Field(description="总数")


class RankingsListResponse(BaseModel):
    """榜单列表响应"""
    rankings: List[RankingListItem] = Field(description="榜单列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    limit: int = Field(description="每页数量")
    has_next: bool = Field(description="是否有下一页")


# 更新模型引用
PageConfig.model_rebuild()
SubPageConfig.model_rebuild()