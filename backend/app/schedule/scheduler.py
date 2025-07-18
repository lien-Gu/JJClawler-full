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

from app.config import get_settings
from app.models.schedule import (
    JobConfigModel, JobHandlerType, TriggerType, PREDEFINED_JOB_CONFIGS
)
from app.models.schedule import JobContextModel
from .handlers import BaseJobHandler, CrawlJobHandler, ReportJobHandler


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
            JobHandlerType.REPORT: ReportJobHandler,
        }

    def _create_scheduler(self) -> AsyncIOScheduler:
        """创建APScheduler实例"""
        # 暂时使用内存存储避免序列化问题
        from apscheduler.jobstores.memory import MemoryJobStore
        
        # 配置job store
        jobstores = {
            'default': MemoryJobStore()
        }

        # 配置executor
        executors = {
            'default': AsyncIOExecutor()
        }

        # 创建调度器
        scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=self.settings.scheduler.job_defaults,
            timezone=self.settings.scheduler.timezone
        )

        # 不添加事件监听器以简化

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
        """加载预定义任务（支持多子任务）"""
        for job_id, job_config in PREDEFINED_JOB_CONFIGS.items():
            try:
                # 检查是否需要分解为多个子任务
                if job_config.is_single_page_task:
                    # 单页面任务，直接添加
                    await self.add_job(job_config)
                    self.logger.info(f"已加载预定义任务: {job_id}")
                else:
                    # 多页面任务，使用批量任务功能分解
                    result = await self.add_batch_jobs(
                        page_ids=job_config.page_ids,
                        force=job_config.force,
                        batch_id=f"predefined_{job_id}"
                    )
                    
                    if result["success"]:
                        self.logger.info(f"已加载预定义批量任务: {job_id}, 包含 {result['successful_tasks']} 个子任务")
                    else:
                        self.logger.error(f"加载预定义批量任务失败 {job_id}: {result['message']}")
                        
            except Exception as e:
                self.logger.error(f"加载预定义任务失败 {job_id}: {e}")

    async def add_job(self, job_config: JobConfigModel) -> bool:
        """统一的任务添加方法"""
        if self.scheduler is None:
            raise RuntimeError("调度器未启动")

        try:
            # 创建触发器
            trigger = job_config.build_trigger()

            # 添加任务到调度器（统一使用_execute_job函数）
            self.scheduler.add_job(
                func=self._execute_job,
                trigger=trigger,
                id=job_config.job_id,
                name=job_config.job_id,
                kwargs={
                    'job_config': job_config
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

    async def add_batch_jobs(self, page_ids: List[str], force: bool = False, batch_id: Optional[str] = None) -> Dict[str, Any]:
        """
        添加批量任务，为每个页面创建独立的任务
        
        Args:
            page_ids: 页面ID列表
            force: 是否强制执行
            batch_id: 批量任务ID，如果不提供则自动生成
            
        Returns:
            Dict[str, Any]: 包含批量任务信息的字典
        """
        from app.crawl.base import CrawlConfig

        if not batch_id:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 使用CrawlConfig来处理特殊字符
        config = CrawlConfig()
        resolved_page_ids = config.determine_page_ids(page_ids)

        if not resolved_page_ids:
            return {
                "success": False,
                "message": "没有找到有效的页面ID",
                "batch_id": batch_id,
                "task_ids": []
            }

        # 为每个页面创建独立的任务
        task_ids = []
        successful_tasks = 0

        for page_id in resolved_page_ids:
            job_config = JobConfigModel(
                job_id=f"crawl_{page_id}_{batch_id}",
                trigger_type=TriggerType.DATE,
                handler_class=JobHandlerType.CRAWL,
                page_ids=[page_id],
                batch_id=batch_id,
                force=force,
                description=f"批量任务 {batch_id} 中的页面: {page_id}"
            )

            success = await self.add_job(job_config)
            task_ids.append(job_config.job_id)

            if success:
                successful_tasks += 1
            else:
                self.logger.error(f"添加任务失败: {job_config.job_id}")

        return {
            "success": successful_tasks > 0,
            "message": f"批量任务 {batch_id}: 成功添加 {successful_tasks}/{len(resolved_page_ids)} 个任务",
            "batch_id": batch_id,
            "task_ids": task_ids,
            "total_pages": len(resolved_page_ids),
            "successful_tasks": successful_tasks,
            "failed_tasks": len(resolved_page_ids) - successful_tasks
        }

    async def _execute_job(self, job_config: JobConfigModel) -> None:
        """统一的任务执行函数"""
        # 获取处理器类
        handler_class = self.job_handlers.get(job_config.handler_class)
        if not handler_class:
            raise ValueError(f"未找到处理器: {job_config.handler_class}")

        # 创建处理器实例
        handler = handler_class(scheduler=self)

        # 创建任务上下文
        context = JobContextModel(
            job_id=job_config.job_id,
            job_name=job_config.job_id,
            trigger_time=datetime.now(),
            scheduled_time=datetime.now()
        )

        # 获取任务数据
        page_ids = job_config.page_ids or []

        # 执行任务
        result = await handler.execute_with_retry(page_ids=page_ids, context=context)

        # 记录结果
        self.logger.info(f"任务 {job_config.job_id} 执行完成: {result.message}")

    def get_jobs(self) -> List[Job]:
        """获取所有任务"""
        return self.scheduler.get_jobs() if self.scheduler else []

    def get_job(self, job_id: str) -> Optional[Job]:
        """获取指定任务"""
        return self.scheduler.get_job(job_id) if self.scheduler else None

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
        running_jobs = sum(1 for job in jobs if job.next_run_time is not None)
        paused_jobs = len(jobs) - running_jobs
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0.0

        return {
            "status": "running" if self.scheduler.running else "paused",
            "job_count": len(jobs),
            "running_jobs": running_jobs,
            "paused_jobs": paused_jobs,
            "uptime": uptime
        }


    def get_batch_jobs(self, batch_id: str) -> List[Job]:
        """获取批量任务中的所有任务"""
        return [job for job in self.get_jobs() if batch_id in job.id]

    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """获取批量任务的整体状态"""
        batch_jobs = self.get_batch_jobs(batch_id)

        if not batch_jobs:
            return {
                "batch_id": batch_id,
                "status": "not_found",
                "total_jobs": 0,
                "running_jobs": 0,
                "completed_jobs": 0
            }

        running_jobs = sum(1 for job in batch_jobs if job.next_run_time is not None)
        completed_jobs = len(batch_jobs) - running_jobs

        # 简化状态判断
        if running_jobs > 0:
            batch_status = "running"
        elif completed_jobs == len(batch_jobs):
            batch_status = "completed"
        else:
            batch_status = "partial"

        return {
            "batch_id": batch_id,
            "status": batch_status,
            "total_jobs": len(batch_jobs),
            "running_jobs": running_jobs,
            "completed_jobs": completed_jobs
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
