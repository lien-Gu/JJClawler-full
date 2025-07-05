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


class CrawlTaskRequest(BaseModel):
    """爬虫任务请求"""
    page_ids: Optional[List[str]] = Field(None, description="指定要爬取的页面ID列表")
    force: bool = Field(False, description="是否强制爬取（忽略间隔限制）")
    

class CrawlTaskResponse(BaseModel):
    """爬虫任务响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    message: str = Field("", description="任务消息")
    page_ids: Optional[List[str]] = Field(None, description="涉及的页面ID列表")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")





class CrawlResultItem(BaseModel):
    """爬取结果项"""
    page_id: str = Field(..., description="页面ID")
    success: bool = Field(..., description="是否成功")
    books_count: int = Field(0, description="爬取到的书籍数量")
    rankings_count: int = Field(0, description="爬取到的榜单数量")
    duration: float = Field(0.0, description="爬取时长（秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
