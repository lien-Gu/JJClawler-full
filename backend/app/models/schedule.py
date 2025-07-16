"""
调度模块数据模型

定义调度器相关的请求/响应模型和数据结构：
- 任务状态和结果模型
- 调度器管理模型
- API请求/响应模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    SUCCESS = "success"  # 执行成功
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消
    PAUSED = "paused"  # 已暂停


class TriggerType(str, Enum):
    """触发器类型枚举"""
    INTERVAL = "interval"  # 间隔触发
    CRON = "cron"  # Cron表达式
    DATE = "date"  # 指定日期


class JobHandlerType(str, Enum):
    """任务处理器类型"""
    CRAWL = "CrawlJobHandler"  # 爬虫任务
    REPORT = "ReportJobHandler"  # 报告任务


# 任务上下文模型
class JobContextModel(BaseModel):
    """任务执行上下文模型"""
    job_id: str = Field(..., description="任务ID")
    job_name: str = Field(..., description="任务名称")
    trigger_time: datetime = Field(..., description="触发时间")
    scheduled_time: datetime = Field(..., description="计划执行时间")
    executor: str = Field(default="default", description="执行器名称")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 任务结果模型
class JobResultModel(BaseModel):
    """任务执行结果模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="执行消息")
    data: Optional[Dict[str, Any]] = Field(None, description="结果数据")
    exception: Optional[str] = Field(None, description="异常信息")
    execution_time: float = Field(default=0.0, description="执行耗时（秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @classmethod
    def success_result(cls, message: str, data: Dict[str, Any] = None) -> 'JobResultModel':
        """创建成功结果"""
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_result(cls, message: str, exception: Exception = None) -> 'JobResultModel':
        """创建失败结果"""
        return cls(success=False, message=message,
                   exception=str(exception) if exception else None)


# 任务配置模型
class JobConfigModel(BaseModel):
    """任务配置模型"""
    job_id: str = Field(..., description="任务ID")
    trigger_type: TriggerType = Field(..., description="触发器类型")
    handler_class: JobHandlerType = Field(..., description="处理器类")
    enabled: bool = Field(default=True, description="是否启用")
    force: bool = Field(default=False, description="是否强制执行")
    description: str = Field(default=None, description="任务描述")

    # 触发器配置（根据触发器类型使用不同字段）
    interval_seconds: Optional[int] = Field(None, ge=60, le=86400, description="间隔秒数")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    run_date: Optional[datetime] = Field(None, description="指定执行时间")

    # 任务数据
    page_ids: List[str] = Field(default_factory=list, description="页面id列表，可以是特殊字符all/jiazi/category")
    batch_id: Optional[str] = Field(None, description="批量任务ID，用于跟踪相关任务")
    parent_task_id: Optional[str] = Field(None, description="父任务ID，用于任务依赖关系")

    @property
    def is_single_page_task(self) -> bool:
        """判断是否为单页面任务"""
        return len(self.page_ids) == 1 and self.page_ids[0] not in ["all", "jiazi", "category"]
    
    def build_trigger(self) -> None | DateTrigger | IntervalTrigger | CronTrigger:
        """创建触发器"""
        if self.trigger_type == TriggerType.DATE:
            # 日期触发器（一次性任务）
            from apscheduler.triggers.date import DateTrigger
            run_date = self.run_date or datetime.now()
            return DateTrigger(run_date=run_date)

        elif self.trigger_type == TriggerType.INTERVAL:
            # 间隔触发器（重复任务）
            interval_seconds = self.interval_seconds or 3600
            return IntervalTrigger(seconds=interval_seconds)

        elif self.trigger_type == TriggerType.CRON:
            # Cron触发器（重复任务）
            cron_expr = self.cron_expression or '0 * * * *'
            cron_parts = cron_expr.split()
            if len(cron_parts) >= 5:
                return CronTrigger(
                    minute=cron_parts[0],
                    hour=cron_parts[1],
                    day=cron_parts[2],
                    month=cron_parts[3],
                    day_of_week=cron_parts[4],
                    timezone='Asia/Shanghai'
                )

        # 简化：使用默认配置
        return CronTrigger(minute='0', timezone='Asia/Shanghai')

# 预定义任务配置
PREDEFINED_JOB_CONFIGS = {
    "jiazi_crawl": JobConfigModel(
        job_id="jiazi_crawl",
        trigger_type=TriggerType.INTERVAL,
        handler_class=JobHandlerType.CRAWL,
        interval_seconds=3600,  # 1小时
        page_ids=["jiazi"],  # 直接提供任务数据
        description="夹子榜数据爬取任务，每小时更新一次"
    ),

    "category_crawl": JobConfigModel(
        job_id="category_crawl",
        trigger_type=TriggerType.CRON,
        handler_class=JobHandlerType.CRAWL,
        cron_expression="0 6,8,10,12,14,16,18 * * *",
        page_ids=["category"],
        description="分类榜单数据爬取任务，工作时间内每2小时执行"
    )

}
