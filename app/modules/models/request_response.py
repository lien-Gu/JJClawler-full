"""
API请求和响应模型

定义所有API端点的请求体和响应体模型
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ==================== 页面配置相关 ====================
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


# ==================== 榜单相关 ====================
class RankingBooksResponse(BaseModel):
    """榜单书籍列表响应"""
    ranking: RankingConfig = Field(description="榜单信息")
    books: List[dict] = Field(description="书籍列表")  # 使用dict以兼容现有的mock数据
    total: int = Field(description="书籍总数")
    page: int = Field(description="当前页码")
    limit: int = Field(description="每页数量")


class RankingHistoryResponse(BaseModel):
    """榜单历史响应"""
    ranking: RankingConfig = Field(description="榜单信息")
    snapshots: List[dict] = Field(description="历史快照")
    days: int = Field(description="查询天数")


# ==================== 书籍相关 ====================
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


# ==================== 爬虫管理相关 ====================
class CrawlJiaziRequest(BaseModel):
    """夹子爬取请求"""
    force: bool = Field(default=False, description="是否强制爬取")


class CrawlRankingRequest(BaseModel):
    """榜单爬取请求"""
    force: bool = Field(default=False, description="是否强制爬取")


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


# 更新模型引用
PageConfig.model_rebuild()
SubPageConfig.model_rebuild()