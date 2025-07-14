"""
调度模块数据模型

定义调度器相关的请求/响应模型和数据结构：
- 任务状态和结果模型
- 调度器管理模型
- API请求/响应模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .base import BaseResponse


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


# 任务配置模型 - 统一为单一配置模型
class JobConfigModel(BaseModel):
    """任务配置模型"""
    job_id: str = Field(..., description="任务ID")
    trigger_type: TriggerType = Field(..., description="触发器类型")
    handler_class: JobHandlerType = Field(..., description="处理器类")
    enabled: bool = Field(default=True, description="是否启用")
    description: str = Field(default="", description="任务描述")
    
    # 触发器配置
    interval_seconds: Optional[int] = Field(None, ge=60, le=86400, description="间隔秒数")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")


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




# API响应模型 - 暂时保留空白，未来如需要可添加实际使用的响应模型


# 预定义任务配置
PREDEFINED_JOB_CONFIGS = {
    "jiazi_crawl": JobConfigModel(
        job_id="jiazi_crawl",
        trigger_type=TriggerType.INTERVAL,
        handler_class=JobHandlerType.CRAWL,
        interval_seconds=3600,  # 1小时
        description="夹子榜数据爬取任务，每小时更新一次"
    ),

    "category_crawl": JobConfigModel(
        job_id="category_crawl",
        trigger_type=TriggerType.CRON,
        handler_class=JobHandlerType.CRAWL,
        cron_expression="0 6,8,10,12,14,16,18 * * *",
        description="分类榜单数据爬取任务，工作时间内每2小时执行"
    )

}
