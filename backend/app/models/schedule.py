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

from pydantic import BaseModel, Field, computed_field


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
    job_id: str
    job_type: JobType
    trigger_type: TriggerType
    trigger_time: Dict[str, Any]
    desc: str = ""

    # 状态字段
    status: JobStatus = JobStatus.PENDING

    # 结果字段
    execution_results: List[Dict[str, Any]] = Field(default_factory=list)
    last_result: Optional[Dict[str, Any]] = None


class Job(JobBasic):
    """统一的任务数据模型 - 使用Pydantic但保持简洁"""
    page_ids: List[str] = Field(default_factory=list)
    is_system_job: bool = False

    # 统计字段
    execution_count: int = 0
    success_count: int = 0
    last_execution_time: Optional[datetime] = None

    # 计算属性
    @computed_field
    @property
    def failure_count(self) -> int:
        return max(0, self.execution_count - self.success_count)

    def to_scheduler_metadata(self) -> Dict[str, Any]:
        data = self.model_dump(exclude={"job_id", "trigger_type", "trigger_time"})
        # 处理datetime序列化
        if data.get("last_execution_time"):
            data["last_execution_time"] = data["last_execution_time"].isoformat()
        return data

    @classmethod
    def from_scheduler_data(cls, job_id: str, trigger_type: TriggerType,
                            trigger_time: Dict[str, Any], metadata: Dict[str, Any]) -> "Job":
        if metadata.get("last_execution_time"):
            metadata["last_execution_time"] = datetime.fromisoformat(metadata["last_execution_time"])

        return cls(
            job_id=job_id,
            trigger_type=trigger_type,
            trigger_time=trigger_time,
            **metadata
        )


# 预定义任务配置 - 使用Job模型
def get_predefined_jobs()->List[Job]:
    """获取预定义的调度任务列表"""

    return [
        Job(
            job_id="jiazi_crawl",
            job_type=JobType.CRAWL,
            trigger_type=TriggerType.CRON,
            trigger_time={"hour": "*/1"},  # 每小时执行一次
            desc="夹子榜单定时爬取任务",
            page_ids=["jiazi"]
        ),
        Job(
            job_id="category_crawl",
            job_type=JobType.CRAWL,
            trigger_type=TriggerType.CRON,
            trigger_time={"hour": "6-18", "minute": "0"},  # 6-18点每小时执行
            desc="分类页面定时爬取任务",
            page_ids=["category"]
        )
    ]

def get_clean_up_job()->Job:
    """<UNK>"""
    from app.config import SchedulerSettings
    interval_hour = SchedulerSettings.cleanup_interval_hours
    return Job(
            job_id="__system_job_cleanup__",
            job_type=JobType.SYSTEM,
            trigger_type=TriggerType.INTERVAL,
            trigger_time={"hours": interval_hour},
            desc="自动清理过期任务",
            is_system_job=True
        )
