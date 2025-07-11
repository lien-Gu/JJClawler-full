"""
爬虫任务数据库模型
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CrawlTask(Base):
    """爬虫任务表"""
    __tablename__ = "crawl_tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    page_ids: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # 存储为JSON数组
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # 任务类型相关字段
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    total_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # 结果和错误信息
    result_data: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 创建和更新时间
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self) -> str:
        return f"<CrawlTask(task_id='{self.task_id}', status='{self.status}', type='{self.task_type}')>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "message": self.message,
            "page_ids": self.page_ids,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
            "task_type": self.task_type,
            "total_pages": self.total_pages,
            "completed_pages": self.completed_pages,
            "progress": self.progress,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }