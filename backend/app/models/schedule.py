"""
调度模块数据模型

定义调度器相关的请求/响应模型和数据结构：
- 任务状态和结果模型
- 调度器管理模型
- API请求/响应模型
"""

from enum import Enum
from typing import Dict, List, Tuple

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
    page_id: str = Field(...)
    rankings: List = Field(..., description="该页面中的榜单列表")
    summary: Dict[str, str] = Field(..., description="该爬取任务爬取了多少个榜单，多少本书籍")


class JobInfo(BaseModel):
    """
    调度任务信息
    """
    job_id: str = Field(..., description="调度任务ID")
    trigger_type: TriggerType = Field(..., description="调度任务触发器类型")
    trigger_time: Dict[str, str] = Field(..., description="运行的时间参数，用于传给scheduler.add_job()作为参数")
    status: Tuple[JobStatus, str] = Field(..., description="调度任务运行的状态，完成了多少个任务了")
    handler: JobHandlerType = Field(..., description="处理器类")
    page_ids: List[str] | None = Field(..., description="爬虫任务需要爬取的页面")
    result: List[CrawTaskInfo] | None = Field(..., description="任务运行结果")
    desc: str = Field(..., description="调度状态描述")


class SchedulerInfo(BaseModel):
    """
    调度器信息
    """
    status: str = Field(..., description="调度器当前的状态")
    job_wait: List = Field(..., description="等待运行的任务列表")
    job_running: List = Field(..., description="正在运行的任务列表")
    run_time: str = Field(..., description="调度器运行的时间，格式为：%d天%h小时%m分钟%s秒")


PREDEFINED_JOB_INFO = {
    "jiazi_crawl": JobInfo(
        job_id="jiazi_crawl",
        trigger_type=TriggerType.CRON,
        trigger_time={},
        status=(JobStatus.PENDING, "尚未初始化"),
        handler=JobHandlerType.CRAWL,
        page_ids=["jiazi_crawl"],
        result=None
    ),
    "category_crawl": JobInfo(
        job_id="category_crawl",
        trigger_type=TriggerType.CRON,
        trigger_time={},
        status=(JobStatus.PENDING, "尚未初始化"),
        handler=JobHandlerType.CRAWL,
        page_ids=["category"],
        result=None
    )
}
