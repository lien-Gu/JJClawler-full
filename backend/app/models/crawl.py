"""
爬虫相关数据模型
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlTaskResponse(BaseModel):
    """爬虫任务响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    message: str = Field("", description="任务消息")
    page_ids: Optional[List[str]] = Field(None, description="涉及的页面ID列表")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="任务进度(0-1)")


class CrawlTaskStatusResponse(BaseModel):
    """爬虫任务状态响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    page_ids: Optional[List[str]] = Field(None, description="涉及的页面ID列表")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    progress: float = Field(0.0, description="任务进度")
    error_message: Optional[str] = Field(None, description="错误信息")
    results: Optional[Dict[str, Any]] = Field(None, description="任务结果")


class CrawlTaskDetailResponse(BaseModel):
    """爬虫任务详情响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    task_type: str = Field(..., description="任务类型")
    page_ids: Optional[List[str]] = Field(None, description="涉及的页面ID列表")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    progress: float = Field(0.0, description="任务进度")
    error_message: Optional[str] = Field(None, description="错误信息")
    results: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    logs: List[str] = Field([], description="任务日志")


class SystemStats(BaseModel):
    """系统统计信息"""
    total_tasks: int = Field(0, description="总任务数")
    pending_tasks: int = Field(0, description="待执行任务数")
    running_tasks: int = Field(0, description="运行中任务数")
    completed_tasks: int = Field(0, description="已完成任务数")
    failed_tasks: int = Field(0, description="失败任务数")
    success_rate: float = Field(0.0, description="成功率")


class CrawlerStats(BaseModel):
    """爬虫统计信息"""
    active_crawlers: int = Field(0, description="活跃爬虫数")
    total_pages_configured: int = Field(0, description="配置的页面总数")
    last_successful_crawl: Optional[datetime] = Field(None, description="最后成功爬取时间")
    total_books_crawled: int = Field(0, description="累计爬取书籍数")
    total_rankings_crawled: int = Field(0, description="累计爬取榜单数")


class CrawlSystemStatusResponse(BaseModel):
    """爬虫系统状态响应"""
    status: str = Field("healthy", description="系统状态")
    uptime: float = Field(0.0, description="运行时间（秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    scheduler_running: bool = Field(False, description="调度器是否运行")
    system_stats: SystemStats = Field(..., description="系统统计")
    crawler_stats: CrawlerStats = Field(..., description="爬虫统计")


class PageConfig(BaseModel):
    """页面配置"""
    page_id: str = Field(..., description="页面ID")
    name: str = Field(..., description="页面名称")
    url: str = Field(..., description="页面URL")
    is_active: bool = Field(True, description="是否启用")
    crawl_frequency: int = Field(60, description="爬取频率（分钟）")
    parser_type: str = Field("default", description="解析器类型")


class CrawlConfigResponse(BaseModel):
    """爬虫配置响应"""
    pages: List[PageConfig] = Field([], description="页面配置列表")
    global_settings: Dict[str, Any] = Field({}, description="全局设置")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")


class CrawlPagesRequest(BaseModel):
    """爬取页面请求"""
    page_ids: List[str] = Field(..., description="要爬取的页面ID列表", min_length=1)
    force: bool = Field(False, description="是否强制爬取（忽略间隔限制）")
    priority: int = Field(0, description="任务优先级")


class UpdateCrawlConfigRequest(BaseModel):
    """更新爬虫配置请求"""
    page_configs: Optional[List[PageConfig]] = Field(None, description="页面配置列表")
    global_settings: Optional[Dict[str, Any]] = Field(None, description="全局设置")


class CrawlResultItem(BaseModel):
    """爬取结果项"""
    page_id: str = Field(..., description="页面ID")
    success: bool = Field(..., description="是否成功")
    books_count: int = Field(0, description="爬取到的书籍数量")
    rankings_count: int = Field(0, description="爬取到的榜单数量")
    duration: float = Field(0.0, description="爬取时长（秒）")
    error_message: Optional[str] = Field(None, description="错误信息")


class BatchCrawlResponse(BaseModel):
    """批量爬取响应"""
    task_id: str = Field(..., description="任务ID")
    total_pages: int = Field(0, description="总页面数")
    results: List[CrawlResultItem] = Field([], description="爬取结果列表")
    success_count: int = Field(0, description="成功数量")
    failed_count: int = Field(0, description="失败数量")
    total_duration: float = Field(0.0, description="总时长（秒）") 