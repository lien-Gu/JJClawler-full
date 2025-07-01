"""
任务执行状态数据库模型

用于替代 tasks.json，将任务执行状态存储到数据库中
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON


class TaskExecution(SQLModel, table=True):
    """任务执行状态表"""
    __tablename__ = "task_executions"
    
    # 主键
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 任务标识
    task_id: str = Field(description="运行时生成的唯一任务ID", index=True)
    config_id: str = Field(description="配置任务ID（来自urls.json）", index=True)
    
    # 任务状态
    status: str = Field(description="任务状态", index=True)
    
    # 时间信息
    created_at: datetime = Field(description="创建时间", index=True)
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    
    # 执行信息
    progress: int = Field(default=0, description="进度百分比")
    items_crawled: int = Field(default=0, description="已爬取项目数")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    
    # 元数据
    task_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON), description="任务元数据")
    
    # 触发源
    trigger_source: Optional[str] = Field(default=None, description="触发源 (scheduled/manual)")
    
    def to_crawl_task_dict(self) -> Dict[str, Any]:
        """转换为CrawlTask兼容的字典格式"""
        return {
            "task_id": self.task_id,
            "id": self.config_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "items_crawled": self.items_crawled,
            "error_message": self.error_message,
            "metadata": self.task_metadata or {}
        }
    
    @classmethod
    def from_crawl_task(cls, crawl_task) -> "TaskExecution":
        """从CrawlTask创建TaskExecution实例"""
        # 处理时间字段
        def parse_time(time_str: Optional[str]) -> Optional[datetime]:
            if not time_str:
                return None
            if isinstance(time_str, datetime):
                return time_str
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        
        # 处理状态字段
        status_value = crawl_task.status
        if hasattr(status_value, 'value'):
            status_value = status_value.value
        elif not isinstance(status_value, str):
            status_value = str(status_value)
        
        return cls(
            task_id=crawl_task.task_id,
            config_id=crawl_task.id,
            status=status_value,
            created_at=parse_time(crawl_task.created_at) or datetime.now(),
            started_at=parse_time(crawl_task.started_at),
            completed_at=parse_time(crawl_task.completed_at),
            progress=crawl_task.progress,
            items_crawled=crawl_task.items_crawled,
            error_message=crawl_task.error_message,
            task_metadata=crawl_task.metadata or {},
            trigger_source=crawl_task.metadata.get('trigger_source') if crawl_task.metadata else None
        )