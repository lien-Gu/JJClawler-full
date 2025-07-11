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

from pydantic import BaseModel, Field

from .base import BaseResponse


class JobStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    SUCCESS = "success"      # 执行成功
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消
    PAUSED = "paused"       # 已暂停
    RETRYING = "retrying"   # 重试中


class TriggerType(str, Enum):
    """触发器类型枚举"""
    INTERVAL = "interval"    # 间隔触发
    CRON = "cron"           # Cron表达式
    DATE = "date"           # 指定日期


class JobHandlerType(str, Enum):
    """任务处理器类型"""
    CRAWL = "CrawlJobHandler"              # 爬虫任务
    REPORT = "ReportJobHandler"            # 报告任务
    MAINTENANCE = "MaintenanceJobHandler"  # 维护任务


# 任务上下文模型
class JobContextModel(BaseModel):
    """任务执行上下文模型"""
    job_id: str = Field(..., description="任务ID")
    job_name: str = Field(..., description="任务名称")
    trigger_time: datetime = Field(..., description="触发时间")
    scheduled_time: datetime = Field(..., description="计划执行时间")
    executor: str = Field(default="default", description="执行器名称")
    job_data: Dict[str, Any] = Field(default_factory=dict, description="任务数据")
    retry_count: int = Field(default=0, description="重试次数")
    max_retries: int = Field(default=3, description="最大重试次数")

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
    retry_count: int = Field(default=0, description="重试次数")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 任务配置模型
class JobConfigModel(BaseModel):
    """任务配置模型"""
    job_id: str = Field(..., description="任务ID")
    trigger_type: TriggerType = Field(..., description="触发器类型")
    handler_class: JobHandlerType = Field(..., description="处理器类")
    max_instances: int = Field(default=1, ge=1, le=10, description="最大实例数")
    coalesce: bool = Field(default=True, description="是否合并执行")
    misfire_grace_time: int = Field(default=30, ge=0, description="错过执行宽限时间（秒）")
    enabled: bool = Field(default=True, description="是否启用")
    description: str = Field(default="", description="任务描述")


class IntervalJobConfigModel(JobConfigModel):
    """间隔触发任务配置"""
    trigger_type: TriggerType = Field(default=TriggerType.INTERVAL)
    interval_seconds: int = Field(..., ge=60, le=86400, description="间隔秒数")


class CronJobConfigModel(JobConfigModel):
    """Cron表达式任务配置"""
    trigger_type: TriggerType = Field(default=TriggerType.CRON)
    cron_expression: str = Field(..., description="Cron表达式")
    timezone: str = Field(default="Asia/Shanghai", description="时区")


# 任务信息模型
class JobInfoModel(BaseModel):
    """任务信息模型"""
    id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    status: JobStatus = Field(..., description="任务状态")
    trigger_type: TriggerType = Field(..., description="触发器类型")
    next_run_time: Optional[datetime] = Field(None, description="下次运行时间")
    last_run_time: Optional[datetime] = Field(None, description="上次运行时间")
    handler_class: str = Field(..., description="处理器类")
    max_instances: int = Field(..., description="最大实例数")
    enabled: bool = Field(..., description="是否启用")
    description: str = Field(default="", description="任务描述")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 调度器状态模型
class SchedulerStatusModel(BaseModel):
    """调度器状态模型"""
    status: str = Field(..., description="调度器状态")
    timezone: str = Field(..., description="时区")
    job_count: int = Field(..., description="任务总数")
    running_jobs: int = Field(..., description="运行中任务数")
    paused_jobs: int = Field(..., description="暂停任务数")
    state: str = Field(..., description="调度器内部状态")
    uptime: float = Field(default=0.0, description="运行时间（秒）")


# 调度器指标模型
class SchedulerMetricsModel(BaseModel):
    """调度器指标模型"""
    total_jobs: int = Field(..., description="总任务数")
    running_jobs: int = Field(..., description="运行中任务数")
    paused_jobs: int = Field(..., description="暂停任务数")
    scheduler_status: str = Field(..., description="调度器状态")
    uptime: float = Field(..., description="运行时间（秒）")
    success_rate: float = Field(default=0.0, description="成功率")
    average_execution_time: float = Field(default=0.0, description="平均执行时间")


# API请求模型
class AddJobRequest(BaseModel):
    """添加任务请求"""
    job_config: JobConfigModel = Field(..., description="任务配置")


class UpdateJobRequest(BaseModel):
    """更新任务请求"""
    enabled: Optional[bool] = Field(None, description="是否启用")
    max_instances: Optional[int] = Field(None, ge=1, le=10, description="最大实例数")
    coalesce: Optional[bool] = Field(None, description="是否合并执行")
    misfire_grace_time: Optional[int] = Field(None, ge=0, description="错过执行宽限时间")
    description: Optional[str] = Field(None, description="任务描述")


class JobActionRequest(BaseModel):
    """任务操作请求"""
    action: str = Field(..., description="操作类型（pause/resume/run）")


class JobHistoryQuery(BaseModel):
    """任务历史查询"""
    limit: int = Field(default=10, ge=1, le=100, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")
    status: Optional[JobStatus] = Field(None, description="状态过滤")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


# API响应模型
class JobResponse(BaseResponse):
    """任务响应"""
    data: JobInfoModel = Field(..., description="任务信息")


class JobListResponse(BaseResponse):
    """任务列表响应"""
    data: List[JobInfoModel] = Field(..., description="任务列表")
    total: int = Field(..., description="总数")


class JobResultResponse(BaseResponse):
    """任务结果响应"""
    data: JobResultModel = Field(..., description="任务结果")


class JobResultListResponse(BaseResponse):
    """任务结果列表响应"""
    data: List[JobResultModel] = Field(..., description="任务结果列表")
    total: int = Field(..., description="总数")


class SchedulerStatusResponse(BaseResponse):
    """调度器状态响应"""
    data: SchedulerStatusModel = Field(..., description="调度器状态")


class SchedulerMetricsResponse(BaseResponse):
    """调度器指标响应"""
    data: SchedulerMetricsModel = Field(..., description="调度器指标")


# 预定义任务配置
PREDEFINED_JOB_CONFIGS = {
    "jiazi_crawl": IntervalJobConfigModel(
        job_id="jiazi_crawl",
        handler_class=JobHandlerType.CRAWL,
        interval_seconds=3600,  # 1小时
        description="夹子榜数据爬取任务，每小时更新一次"
    ),
    
    "category_crawl": CronJobConfigModel(
        job_id="category_crawl",
        handler_class=JobHandlerType.CRAWL,
        cron_expression="0 6,8,10,12,14,16,18 * * *",
        max_instances=2,
        description="分类榜单数据爬取任务，工作时间内每2小时执行"
    ),
    
    "database_cleanup": CronJobConfigModel(
        job_id="database_cleanup",
        handler_class=JobHandlerType.MAINTENANCE,
        cron_expression="0 2 * * *",
        description="数据库清理任务，每天凌晨2点执行"
    ),
    
    "log_rotation": CronJobConfigModel(
        job_id="log_rotation",
        handler_class=JobHandlerType.MAINTENANCE,
        cron_expression="0 0 * * *",
        description="日志轮转任务，每天午夜执行"
    ),
    
    "system_health_check": CronJobConfigModel(
        job_id="system_health_check",
        handler_class=JobHandlerType.MAINTENANCE,
        cron_expression="0 */6 * * *",
        description="系统健康状态检查，每6小时执行"
    )
}