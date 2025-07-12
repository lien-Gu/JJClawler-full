"""
任务调度器
"""
import logging
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
    JobConfigModel, JobHandlerType, TriggerType, PREDEFINED_JOB_CONFIGS
)
from app.models.schedule import JobContextModel
from .handlers import BaseJobHandler, CrawlJobHandler, MaintenanceJobHandler, ReportJobHandler


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
            # 添加字符串映射以支持动态任务
            "crawl": CrawlJobHandler,
            "maintenance": MaintenanceJobHandler,
            "report": ReportJobHandler,
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
        scheduler.add_listener(self._job_listener, events.EVENT_ALL)
        
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
            trigger = self._create_trigger(job_config)
            
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
    
    async def add_one_time_job(self, job_id: str, handler_class_name: str, job_data: dict, 
                             run_date: datetime = None) -> bool:
        """
        添加一次性执行的任务
        
        Args:
            job_id: 任务ID
            handler_class_name: 处理器类名
            job_data: 任务数据
            run_date: 执行时间，None表示立即执行
            
        Returns:
            bool: 是否添加成功
        """
        if self.scheduler is None:
            raise RuntimeError("调度器未启动")
        
        try:
            # 获取处理器类
            handler_class = self.job_handlers.get(handler_class_name)
            if not handler_class:
                raise ValueError(f"未找到处理器: {handler_class_name}")
            
            # 创建任务上下文
            context_data = {
                'job_id': job_id,
                'job_data': job_data
            }
            
            # 添加一次性任务
            if run_date is None:
                # 立即执行
                self.scheduler.add_job(
                    func=self._execute_one_time_job,
                    id=job_id,
                    name=job_id,
                    kwargs={
                        'handler_class': handler_class,
                        'context_data': context_data
                    }
                )
            else:
                # 定时执行
                from apscheduler.triggers.date import DateTrigger
                self.scheduler.add_job(
                    func=self._execute_one_time_job,
                    trigger=DateTrigger(run_date=run_date),
                    id=job_id,
                    name=job_id,
                    kwargs={
                        'handler_class': handler_class,
                        'context_data': context_data
                    }
                )
            
            self.logger.info(f"成功添加一次性任务: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加一次性任务失败 {job_id}: {e}")
            return False
    
    def _create_trigger(self, job_config: JobConfigModel):
        """创建触发器"""
        if job_config.trigger_type == TriggerType.INTERVAL:
            if hasattr(job_config, 'interval_seconds'):
                return IntervalTrigger(seconds=job_config.interval_seconds)
            else:
                raise ValueError("间隔任务缺少 interval_seconds 参数")
        elif job_config.trigger_type == TriggerType.CRON:
            if hasattr(job_config, 'cron_expression'):
                # 解析cron表达式
                cron_parts = job_config.cron_expression.split()
                if len(cron_parts) == 5:
                    return CronTrigger(
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
    
    async def _execute_job(self, job_config: JobConfigModel, handler_class: Type[BaseJobHandler]) -> None:
        """执行任务的包装函数"""
        # 创建处理器实例
        handler = handler_class(scheduler=self)
        
        # 创建任务上下文
        context = JobContextModel(
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
    
    async def _execute_one_time_job(self, handler_class: Type[BaseJobHandler], context_data: dict) -> None:
        """执行一次性任务的包装函数"""
        # 创建处理器实例
        handler = handler_class(scheduler=self)
        
        # 创建任务上下文
        context = JobContextModel(
            job_id=context_data['job_id'],
            job_name=context_data['job_id'],
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data=context_data.get('job_data', {}),
            max_retries=1  # 一次性任务只重试一次
        )
        
        # 执行任务
        result = await handler.execute_with_retry(context)
        
        # 记录结果
        self.logger.info(f"一次性任务 {context_data['job_id']} 执行完成: {result.message}")
        
        # 任务执行完成后自动删除
        try:
            self.scheduler.remove_job(context_data['job_id'])
            self.logger.debug(f"一次性任务 {context_data['job_id']} 已自动删除")
        except Exception as e:
            self.logger.warning(f"删除一次性任务失败 {context_data['job_id']}: {e}")
    
    def _get_job_data_by_type(self, job_config: JobConfigModel) -> Dict[str, Any]:
        """根据任务配置获取任务数据"""
        job_data_map = {
            "jiazi_crawl": {"type": "jiazi"},
            "category_crawl": {"type": "category"},
            "database_cleanup": {"type": "database_cleanup"},
            "log_rotation": {"type": "log_rotation"},
            "system_health_check": {"type": "health_check"},
            "data_analysis_report": {"type": "data_analysis"},
        }
        return job_data_map.get(job_config.job_id, {})
    
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
            "uptime": status["uptime"]
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