"""
调度模块数据模型

定义调度器相关的请求/响应模型和数据结构：
- 任务状态和结果模型
- 调度器管理模型
- API请求/响应模型
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel, Field, computed_field


class JobStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    SUCCESS = "success"  # 执行成功
    FAILED = "failed"  # 执行失败
    NOT_STARTED = "not_started"


class JobType(str, Enum):
    """任务处理器类型"""

    CRAWL = "crawl"  # 爬虫任务
    REPORT = "report"  # 报告任务
    SYSTEM = "system"  # 系统任务


class SchedulerInfo(BaseModel):
    """
    调度器信息
    """
    status: str = Field(..., description="调度器当前的状态")
    jobs: List[Dict[str, Any]] = Field(default_factory=list, description="调度器中的任务列表")
    run_time: str = Field(..., description="调度器运行的时间，格式为：%d天%h小时%m分钟%s秒")


class JobBasic(BaseModel):
    # 核心字段
    job_id: str = ""
    job_type: JobType = JobType.CRAWL
    desc: str = ""
    err: Optional[str] = None


class JobInfo(JobBasic):
    # 业务字段
    page_ids: List[str] = Field(default_factory=list)

    status: JobStatus = JobStatus.PENDING

    # 结果字段
    execution_results: List[Dict[str, Any]] = Field(default_factory=list)

    # 统计字段
    execution_count: int = 0
    success_count: int = 0
    last_execution_time: Optional[datetime] = None

    # 计算属性
    @computed_field
    @property
    def failure_count(self) -> int:
        return max(0, self.execution_count - self.success_count)

    def last_result(self) -> Optional[Dict[str, Any]]:
        if not self.execution_results:
            return None
        return self.execution_results[-1]


class Job(JobInfo):
    """统一的任务数据模型 - 使用Pydantic但保持简洁"""
    trigger: BaseTrigger = Field(..., description="调度任务触发器")

    is_system_job: bool = False
    
    model_config = {"arbitrary_types_allowed": True}


# 预定义任务配置 - 使用Job模型
def get_predefined_jobs() -> List[Job]:
    """获取预定义的调度任务列表"""

    return [
        Job(
            job_id="jiazi_crawl",
            job_type=JobType.CRAWL,
            trigger=CronTrigger(hour=1),  # 每小时执行一次
            desc="夹子榜单定时爬取任务",
            page_ids=["jiazi"]
        ),
        Job(
            job_id="category_crawl",
            job_type=JobType.CRAWL,
            trigger=CronTrigger(hour=1),  # 每天执行一次
            desc="分类页面定时爬取任务",
            page_ids=["category"]
        )
    ]


def get_clean_up_job() -> Job:
    """<UNK>"""
    from app.config import SchedulerSettings
    interval_hour = SchedulerSettings.cleanup_interval_hours
    return Job(
        job_id="__system_job_cleanup__",
        job_type=JobType.SYSTEM,
        trigger=IntervalTrigger(hours=interval_hour),
        desc="自动清理过期任务",
        is_system_job=True
    )
