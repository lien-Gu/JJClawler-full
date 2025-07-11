"""
调度模块 - 基于APScheduler的任务调度器

功能特性:
- 异步任务调度和执行
- 动态任务管理（添加、删除、暂停、恢复）
- 智能重试机制和异常处理
- 任务状态监控和结果记录
- 预定义任务自动加载
- 数据库持久化存储
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.job import Job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler import events

from app.config import get_settings
from app.models.schedule import (
    JobConfigModel, JobContextModel, JobHandlerType, JobResultModel, 
    JobStatus, TriggerType, PREDEFINED_JOB_CONFIGS
)


# 任务上下文（兼容原有base_handler）
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


# 任务执行结果（兼容原有base_handler）
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


# 任务处理器基类
class BaseJobHandler(ABC):
    """任务处理器基类"""
    
    def __init__(self, scheduler=None):
        self.scheduler = scheduler
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def execute(self, context: JobContext) -> JobResult:
        """执行任务（子类必须实现）"""
        pass
    
    async def execute_with_retry(self, context: JobContext) -> JobResult:
        """带重试机制的任务执行"""
        start_time = time.time()
        last_exception = None
        
        for attempt in range(context.max_retries + 1):
            context.retry_count = attempt
            
            try:
                self.logger.info(f"开始执行任务 {context.job_id}，第 {attempt + 1} 次尝试")
                
                # 执行任务
                result = await self.execute(context)
                
                # 记录执行时间
                result.execution_time = time.time() - start_time
                result.retry_count = attempt
                
                if result.success:
                    # 执行成功
                    await self.on_success(context, result)
                    self.logger.info(f"任务 {context.job_id} 执行成功")
                    return result
                else:
                    # 执行失败，但没有异常
                    last_exception = result.exception
                    if attempt < context.max_retries and self.should_retry(last_exception, attempt):
                        await self.on_retry(context, attempt + 1)
                        continue
                    else:
                        await self.on_failure(context, last_exception)
                        return result
                        
            except Exception as e:
                last_exception = e
                self.logger.error(f"任务 {context.job_id} 执行异常 (尝试 {attempt + 1}): {e}")
                
                # 判断是否需要重试
                if attempt < context.max_retries and self.should_retry(e, attempt):
                    await self.on_retry(context, attempt + 1)
                    
                    # 计算重试延迟
                    retry_delay = self.get_retry_delay(attempt + 1)
                    if retry_delay > 0:
                        await asyncio.sleep(retry_delay)
                    
                    continue
                else:
                    # 达到最大重试次数或不应重试
                    break
        
        # 所有重试都失败了
        result = JobResult.error_result(
            f"任务执行失败，已重试 {context.max_retries} 次",
            last_exception
        )
        result.execution_time = time.time() - start_time
        result.retry_count = context.max_retries
        
        await self.on_failure(context, last_exception)
        return result
    
    async def on_success(self, context: JobContext, result: JobResult) -> None:
        """任务执行成功时的回调"""
        self.logger.debug(f"任务 {context.job_id} 执行成功: {result.message}")
    
    async def on_failure(self, context: JobContext, exception: Optional[Exception]) -> None:
        """任务执行失败时的回调"""
        self.logger.error(f"任务 {context.job_id} 执行失败: {exception}")
    
    async def on_retry(self, context: JobContext, attempt: int) -> None:
        """任务重试时的回调"""
        self.logger.warning(f"任务 {context.job_id} 将进行第 {attempt} 次重试")
    
    def should_retry(self, exception: Optional[Exception], attempt: int) -> bool:
        """判断是否应该重试"""
        if exception is None:
            return False
        
        retryable_exceptions = (
            ConnectionError,
            TimeoutError,
        )
        
        return isinstance(exception, retryable_exceptions)
    
    def get_retry_delay(self, attempt: int) -> int:
        """获取重试延迟时间（秒）"""
        # 指数退避策略：1, 2, 4, 8, ... 秒，最大60秒
        delay = min(2 ** (attempt - 1), 60)
        return delay


# 具体任务处理器实现
class CrawlJobHandler(BaseJobHandler):
    """爬虫任务处理器"""
    
    async def execute(self, context: JobContext) -> JobResult:
        """执行爬虫任务"""
        try:
            job_type = context.job_data.get('type', 'unknown')
            
            if job_type == 'jiazi':
                # 执行夹子榜爬取任务
                # TODO: 集成实际的爬虫逻辑
                await asyncio.sleep(1)  # 模拟任务执行
                return JobResult.success_result(f"夹子榜爬取完成", {"crawled_count": 50})
                
            elif job_type == 'category':
                # 执行分类榜单爬取任务
                # TODO: 集成实际的爬虫逻辑
                await asyncio.sleep(2)  # 模拟任务执行
                return JobResult.success_result(f"分类榜单爬取完成", {"crawled_count": 100})
                
            else:
                return JobResult.error_result(f"未知的爬虫任务类型: {job_type}")
                
        except Exception as e:
            return JobResult.error_result(f"爬虫任务执行失败: {str(e)}", e)


class MaintenanceJobHandler(BaseJobHandler):
    """维护任务处理器"""
    
    async def execute(self, context: JobContext) -> JobResult:
        """执行维护任务"""
        try:
            job_type = context.job_data.get('type', 'unknown')
            
            if job_type == 'database_cleanup':
                # 执行数据库清理
                # TODO: 集成实际的数据库清理逻辑
                await asyncio.sleep(0.5)  # 模拟任务执行
                return JobResult.success_result("数据库清理完成", {"cleaned_records": 1000})
                
            elif job_type == 'log_rotation':
                # 执行日志轮转
                # TODO: 集成实际的日志轮转逻辑
                await asyncio.sleep(0.5)  # 模拟任务执行
                return JobResult.success_result("日志轮转完成", {"rotated_files": 5})
                
            elif job_type == 'health_check':
                # 执行健康检查
                # TODO: 集成实际的健康检查逻辑
                await asyncio.sleep(0.3)  # 模拟任务执行
                return JobResult.success_result("系统健康检查完成", {"status": "healthy"})
                
            else:
                return JobResult.error_result(f"未知的维护任务类型: {job_type}")
                
        except Exception as e:
            return JobResult.error_result(f"维护任务执行失败: {str(e)}", e)


class ReportJobHandler(BaseJobHandler):
    """报告任务处理器"""
    
    async def execute(self, context: JobContext) -> JobResult:
        """执行报告任务"""
        try:
            job_type = context.job_data.get('type', 'unknown')
            
            if job_type == 'data_analysis':
                # 执行数据分析报告
                # TODO: 集成实际的数据分析逻辑
                await asyncio.sleep(3)  # 模拟任务执行
                return JobResult.success_result("数据分析报告生成完成", {"report_size": "2.5MB"})
                
            else:
                return JobResult.error_result(f"未知的报告任务类型: {job_type}")
                
        except Exception as e:
            return JobResult.error_result(f"报告任务执行失败: {str(e)}", e)


# 主调度器类
class TaskScheduler:
    """任务调度器主类"""
    
    def __init__(self):
        """初始化调度器"""
        self.settings = get_settings()
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.job_handlers: Dict[str, Type[BaseJobHandler]] = {}
        self.logger = logging.getLogger(__name__)
        self.start_time = None
        
        # 注册默认任务处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """注册默认任务处理器"""
        self.job_handlers = {
            JobHandlerType.CRAWL: CrawlJobHandler,
            JobHandlerType.MAINTENANCE: MaintenanceJobHandler,
            JobHandlerType.REPORT: ReportJobHandler,
        }
    
    def _create_scheduler(self) -> AsyncIOScheduler:
        """创建APScheduler实例"""
        # 使用现有数据库配置
        job_store_url = self.settings.scheduler.job_store_url or self.settings.database.url
        
        # 配置job store
        jobstores = {
            'default': SQLAlchemyJobStore(url=job_store_url)
        }
        
        # 配置executor
        executors = {
            'default': AsyncIOExecutor(max_workers=self.settings.scheduler.max_workers)
        }
        
        # 创建调度器
        scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=self.settings.scheduler.job_defaults,
            timezone=self.settings.scheduler.timezone
        )
        
        # 添加事件监听器
        scheduler.add_listener(self._job_listener, 
                             events.EVENT_ALL)
        
        return scheduler
    
    async def start(self) -> None:
        """启动调度器"""
        if self.scheduler is not None:
            self.logger.warning("调度器已经启动")
            return
        
        self.logger.info("正在启动任务调度器...")
        self.scheduler = self._create_scheduler()
        self.start_time = datetime.now()
        
        # 加载预定义任务
        await self._load_predefined_jobs()
        
        # 启动调度器
        self.scheduler.start()
        
        self.logger.info("任务调度器启动成功")
    
    async def shutdown(self, wait: bool = True) -> None:
        """关闭调度器"""
        if self.scheduler is None:
            return
        
        self.logger.info("正在关闭任务调度器...")
        self.scheduler.shutdown(wait=wait)
        self.scheduler = None
        self.start_time = None
        self.logger.info("任务调度器已关闭")
    
    async def _load_predefined_jobs(self) -> None:
        """加载预定义任务"""
        for job_id, job_config in PREDEFINED_JOB_CONFIGS.items():
            try:
                await self.add_job(job_config)
                self.logger.info(f"已加载预定义任务: {job_id}")
            except Exception as e:
                self.logger.error(f"加载预定义任务失败 {job_id}: {e}")
    
    async def add_job(self, job_config: JobConfigModel) -> bool:
        """添加任务"""
        if self.scheduler is None:
            raise RuntimeError("调度器未启动")
        
        try:
            # 获取处理器类
            handler_class = self.job_handlers.get(job_config.handler_class)
            if not handler_class:
                raise ValueError(f"未找到处理器: {job_config.handler_class}")
            
            # 创建触发器
            if job_config.trigger_type == TriggerType.INTERVAL:
                if hasattr(job_config, 'interval_seconds'):
                    trigger = IntervalTrigger(seconds=job_config.interval_seconds)
                else:
                    raise ValueError("间隔任务缺少 interval_seconds 参数")
            elif job_config.trigger_type == TriggerType.CRON:
                if hasattr(job_config, 'cron_expression'):
                    # 解析cron表达式
                    cron_parts = job_config.cron_expression.split()
                    if len(cron_parts) == 5:
                        trigger = CronTrigger(
                            minute=cron_parts[0],
                            hour=cron_parts[1], 
                            day=cron_parts[2],
                            month=cron_parts[3],
                            day_of_week=cron_parts[4],
                            timezone=getattr(job_config, 'timezone', self.settings.scheduler.timezone)
                        )
                    else:
                        raise ValueError(f"无效的cron表达式: {job_config.cron_expression}")
                else:
                    raise ValueError("Cron任务缺少 cron_expression 参数")
            else:
                raise ValueError(f"不支持的触发器类型: {job_config.trigger_type}")
            
            # 添加任务到调度器
            self.scheduler.add_job(
                func=self._execute_job,
                trigger=trigger,
                id=job_config.job_id,
                name=job_config.job_id,
                max_instances=job_config.max_instances,
                coalesce=job_config.coalesce,
                misfire_grace_time=job_config.misfire_grace_time,
                kwargs={
                    'job_config': job_config,
                    'handler_class': handler_class
                }
            )
            
            # 如果任务被禁用，则暂停
            if not job_config.enabled:
                self.scheduler.pause_job(job_config.job_id)
            
            self.logger.info(f"成功添加任务: {job_config.job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加任务失败 {job_config.job_id}: {e}")
            return False
    
    async def _execute_job(self, job_config: JobConfigModel, handler_class: Type[BaseJobHandler]) -> None:
        """执行任务的包装函数"""
        # 创建处理器实例
        handler = handler_class(scheduler=self)
        
        # 创建任务上下文
        context = JobContext(
            job_id=job_config.job_id,
            job_name=job_config.job_id,
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data=self._get_job_data_by_type(job_config),
            max_retries=3
        )
        
        # 执行任务
        result = await handler.execute_with_retry(context)
        
        # 记录结果
        self.logger.info(f"任务 {job_config.job_id} 执行完成: {result.message}")
    
    def _get_job_data_by_type(self, job_config: JobConfigModel) -> Dict[str, Any]:
        """根据任务配置获取任务数据"""
        if job_config.job_id == "jiazi_crawl":
            return {"type": "jiazi"}
        elif job_config.job_id == "category_crawl":
            return {"type": "category"}
        elif job_config.job_id == "database_cleanup":
            return {"type": "database_cleanup"}
        elif job_config.job_id == "log_rotation":
            return {"type": "log_rotation"}
        elif job_config.job_id == "system_health_check":
            return {"type": "health_check"}
        elif job_config.job_id == "data_analysis_report":
            return {"type": "data_analysis"}
        else:
            return {}
    
    def _job_listener(self, event) -> None:
        """任务事件监听器"""
        self.logger.debug(f"任务事件: {event}")
    
    def remove_job(self, job_id: str) -> bool:
        """删除任务"""
        if self.scheduler is None:
            return False
        
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"成功删除任务: {job_id}")
            return True
        except Exception as e:
            self.logger.error(f"删除任务失败 {job_id}: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """暂停任务"""
        if self.scheduler is None:
            return False
        
        try:
            self.scheduler.pause_job(job_id)
            self.logger.info(f"成功暂停任务: {job_id}")
            return True
        except Exception as e:
            self.logger.error(f"暂停任务失败 {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """恢复任务"""
        if self.scheduler is None:
            return False
        
        try:
            self.scheduler.resume_job(job_id)
            self.logger.info(f"成功恢复任务: {job_id}")
            return True
        except Exception as e:
            self.logger.error(f"恢复任务失败 {job_id}: {e}")
            return False
    
    def get_jobs(self) -> List[Job]:
        """获取所有任务"""
        if self.scheduler is None:
            return []
        
        return self.scheduler.get_jobs()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """获取指定任务"""
        if self.scheduler is None:
            return None
        
        return self.scheduler.get_job(job_id)
    
    def is_running(self) -> bool:
        """检查调度器是否运行中"""
        return self.scheduler is not None and self.scheduler.running
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        if self.scheduler is None:
            return {
                "status": "stopped",
                "job_count": 0,
                "running_jobs": 0,
                "paused_jobs": 0,
                "uptime": 0.0
            }
        
        jobs = self.get_jobs()
        running_jobs = len([job for job in jobs if job.next_run_time is not None])
        paused_jobs = len([job for job in jobs if job.next_run_time is None])
        
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "status": "running" if self.scheduler.running else "paused",
            "timezone": str(self.scheduler.timezone),
            "job_count": len(jobs),
            "running_jobs": running_jobs,
            "paused_jobs": paused_jobs,
            "state": str(self.scheduler.state),
            "uptime": uptime
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取调度器指标"""
        status = self.get_status()
        
        return {
            "total_jobs": status["job_count"],
            "running_jobs": status["running_jobs"],
            "paused_jobs": status["paused_jobs"],
            "scheduler_status": status["status"],
            "uptime": status["uptime"],
            "success_rate": 0.95,  # TODO: 从实际统计数据计算
            "average_execution_time": 2.5  # TODO: 从实际统计数据计算
        }


# 全局调度器实例
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """获取调度器实例（单例模式）"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler


async def start_scheduler() -> None:
    """启动调度器"""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler() -> None:
    """停止调度器"""
    scheduler = get_scheduler()
    await scheduler.shutdown()


# 用于兼容性的导出
__all__ = [
    "TaskScheduler",
    "BaseJobHandler", 
    "JobContext",
    "JobResult",
    "CrawlJobHandler",
    "MaintenanceJobHandler", 
    "ReportJobHandler",
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler"
]