"""
调度模块数据模型

定义调度器相关的请求/响应模型和数据结构：
- 任务状态和结果模型
- 调度器管理模型
- API请求/响应模型
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    SUCCESS = "success"  # 执行成功
    FAILED = "failed"  # 执行失败


class TriggerType(str, Enum):
    """触发器类型枚举"""

    INTERVAL = "interval"  # 间隔触发
    CRON = "cron"  # Cron表达式
    DATE = "date"  # 指定日期


class JobHandlerType(str, Enum):
    """任务处理器类型"""

    CRAWL = "CrawlJobHandler"  # 爬虫任务
    REPORT = "ReportJobHandler"  # 报告任务


class CrawTaskInfo(BaseModel):
    """
    爬虫任务信息
    """
    page_id: str = Field(..., description="页面ID")
    rankings: List[Dict[str, Any]] = Field(default_factory=list, description="该页面中的榜单列表")
    summary: Dict[str, Any] = Field(default_factory=dict, description="该爬取任务爬取了多少个榜单，多少本书籍")

class JobResultModel(BaseModel):
    """
    任务执行结果模型
    """
    success: bool = Field(default=True, description="任务是否执行成功")
    message: str = Field(default="成功完成任务", description="执行结果消息")
    data: Optional[CrawTaskInfo|Dict[str, Any]] = Field(None, description="执行结果数据")
    exception: Optional[str] = Field(None, description="异常信息")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    
    @classmethod
    def success_result(cls, message: str, data: Optional[Dict[str, Any]] = None) -> "JobResultModel":
        """创建成功结果"""
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_result(cls, message: str, exception: Optional[Exception] = None) -> "JobResultModel":
        """创建错误结果"""
        return cls(
            success=False,
            message=message,
            exception=str(exception) if exception else None
        )



class JobInfo(BaseModel):
    """
    调度任务信息
    """
    job_id: str = Field(..., description="调度任务ID")
    trigger_type: TriggerType = Field(..., description="调度任务触发器类型")
    trigger_time: Dict[str, Any] = Field(..., description="运行的时间参数，用于传给scheduler.add_job()作为参数")
    handler: JobHandlerType = Field(..., description="处理器类")
    status: Optional[Tuple[JobStatus, str]] = Field(None, description="调度任务运行的状态，完成了多少个任务了")
    page_ids: Optional[List[str]] = Field(None, description="爬虫任务需要爬取的页面")
    result: Optional[List[JobResultModel]] = Field(None, description="任务运行结果")
    desc: Optional[str] = Field(None, description="调度状态描述")


class SchedulerInfo(BaseModel):
    """
    调度器信息
    """
    status: str = Field(..., description="调度器当前的状态")
    jobs: List[Dict[str, Any]] = Field(default_factory=list, description="调度器中的任务列表")
    run_time: str = Field(..., description="调度器运行的时间，格式为：%d天%h小时%m分钟%s秒")


PREDEFINED_JOB_INFO = {
    "jiazi_crawl": JobInfo(
        job_id="jiazi_crawl",
        trigger_type=TriggerType.CRON,
        trigger_time={"hour": "*/1"},  # 每小时执行一次
        handler=JobHandlerType.CRAWL,
        status=(JobStatus.PENDING, "尚未初始化"),
        page_ids=["jiazi"],
        result=None,
        desc="夹子榜单定时爬取任务"
    ),
    "category_crawl": JobInfo(
        job_id="category_crawl",
        trigger_type=TriggerType.CRON,
        trigger_time={"hour": "6-18", "minute": "0"},  # 6-18点每小时执行
        handler=JobHandlerType.CRAWL,
        status=(JobStatus.PENDING, "尚未初始化"),
        page_ids=["category"],
        result=None,
        desc="分类页面定时爬取任务"
    )
}
