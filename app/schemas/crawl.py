"""
爬虫任务相关的数据模型
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TaskInfo(BaseModel):
    """任务信息"""
    task_id: str = Field(..., description="任务ID")
    task_type: str = Field(..., description="任务类型 (jiazi/ranking/book_detail)")
    status: str = Field(..., description="任务状态 (pending/running/completed/failed)")
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    progress: Optional[int] = Field(None, ge=0, le=100, description="进度百分比")
    items_crawled: int = Field(0, description="已爬取项目数")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 额外信息
    ranking_id: Optional[str] = Field(None, description="榜单ID(如果是榜单爬取)")


class TasksResponse(BaseModel):
    """任务列表响应"""
    current_tasks: List[TaskInfo] = Field(..., description="当前任务")
    completed_tasks: List[TaskInfo] = Field(..., description="已完成任务")
    total_current: int = Field(..., description="当前任务数")
    total_completed: int = Field(..., description="已完成任务数")


class TaskCreateResponse(BaseModel):
    """任务创建响应"""
    task_id: str = Field(..., description="任务ID")
    message: str = Field(..., description="响应消息")
    status: str = Field(..., description="任务状态")


# 请求模型
class CrawlJiaziRequest(BaseModel):
    """夹子爬取请求"""
    force: bool = Field(False, description="是否强制重新爬取")


class CrawlRankingRequest(BaseModel):
    """榜单爬取请求"""
    page_type: Optional[str] = Field(None, description="页面类型")
    channel: Optional[str] = Field(None, description="频道参数")
    force: bool = Field(False, description="是否强制重新爬取")


# 查询参数模型
class TasksQuery(BaseModel):
    """任务查询参数"""
    status: Optional[str] = Field(None, description="状态筛选")
    task_type: Optional[str] = Field(None, description="类型筛选")
    limit: int = Field(20, ge=1, le=100, description="每页数量")
    offset: int = Field(0, ge=0, description="偏移量")