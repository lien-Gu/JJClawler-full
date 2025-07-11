"""
任务上下文
"""
from datetime import datetime
from typing import Dict, Any

from app.models.schedule import JobContextModel


class JobContext:
    """任务执行上下文"""
    
    def __init__(self, job_id: str, job_name: str, trigger_time: datetime, 
                 scheduled_time: datetime, executor: str = "default",
                 job_data: Dict[str, Any] = None, retry_count: int = 0, 
                 max_retries: int = 3):
        self.job_id = job_id
        self.job_name = job_name
        self.trigger_time = trigger_time
        self.scheduled_time = scheduled_time
        self.executor = executor
        self.job_data = job_data or {}
        self.retry_count = retry_count
        self.max_retries = max_retries
    
    def to_model(self) -> JobContextModel:
        """转换为Pydantic模型"""
        return JobContextModel(
            job_id=self.job_id,
            job_name=self.job_name,
            trigger_time=self.trigger_time,
            scheduled_time=self.scheduled_time,
            executor=self.executor,
            job_data=self.job_data,
            retry_count=self.retry_count,
            max_retries=self.max_retries
        )