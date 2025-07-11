"""
任务执行结果
"""
from datetime import datetime
from typing import Dict, Any, Optional

from app.models.schedule import JobResultModel


class JobResult:
    """任务执行结果"""
    
    def __init__(self, success: bool, message: str, data: Dict[str, Any] = None,
                 exception: Exception = None, execution_time: float = 0.0,
                 retry_count: int = 0):
        self.success = success
        self.message = message
        self.data = data
        self.exception = exception
        self.execution_time = execution_time
        self.timestamp = datetime.now()
        self.retry_count = retry_count
    
    def to_model(self) -> JobResultModel:
        """转换为Pydantic模型"""
        return JobResultModel(
            success=self.success,
            message=self.message,
            data=self.data,
            exception=str(self.exception) if self.exception else None,
            execution_time=self.execution_time,
            timestamp=self.timestamp,
            retry_count=self.retry_count
        )
    
    @classmethod
    def success_result(cls, message: str, data: Dict[str, Any] = None) -> 'JobResult':
        """创建成功结果"""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error_result(cls, message: str, exception: Exception = None) -> 'JobResult':
        """创建失败结果"""
        return cls(success=False, message=message, exception=exception)