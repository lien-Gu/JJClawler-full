"""
调度模块数据模型

定义调度器相关的请求/响应模型和数据结构：
- 基础任务模型
- 调度器管理模型
- API请求/响应模型
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel, Field


class JobType(str, Enum):
    """任务处理器类型"""

    CRAWL = "crawl"  # 爬虫任务
    REPORT = "report"  # 报告任务
    CLEAN = "clean"  # 系统任务


class SchedulerInfo(BaseModel):
    """
    调度器信息
    """
    status: str = Field(..., description="调度器当前的状态")
    jobs: List[Dict[str, Any]] = Field(default_factory=list, description="调度器中的任务列表")
    run_time: str = Field(..., description="调度器运行的时间，格式为：%d天%h小时%m分钟%s秒")


class JobBasic(BaseModel):
    """基础任务信息 - 仅包含核心字段"""
    job_id: str = ""
    job_type: JobType = JobType.CRAWL
    desc: str = ""
    err: Optional[str] = None


class Job(JobBasic):
    """任务数据模型 - 简化版本"""
    trigger: BaseTrigger = Field(..., description="调度任务触发器")
    page_ids: List[str] = Field(default_factory=list, description="页面ID列表") 
    is_system_job: bool = False
    
    model_config = {"arbitrary_types_allowed": True}


# 预定义任务配置 - 使用Job模型
def get_predefined_jobs() -> List[Job]:
    """获取预定义的调度任务列表"""
    from app.config import get_settings
    settings = get_settings()
    interval_hour = settings.scheduler.cleanup_interval_hours

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
        ),
        Job(
            job_id="__system_job_cleanup__",
            job_type=JobType.CLEAN,
            trigger=IntervalTrigger(hours=interval_hour),
            desc="自动清理过期任务",
            is_system_job=True
        )
    ]


