"""
任务调度器 - 使用APScheduler 3.10.x稳定版本

重构后的调度器使用APScheduler 3.x的SQLAlchemyJobStore，
移除metadata存储，仅保留基本的任务调度功能。
"""

from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Tuple

import humanize
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from app.config import SchedulerSettings, get_settings
from app.logger import get_logger
from app.models.schedule import (Job, JobType, SchedulerInfo, get_clean_up_job, get_predefined_jobs)
from app.schedule.listener import JobListener


class JobScheduler:
    """任务调度器主类 - 基于APScheduler 3.x稳定版本
    
    简化的调度器，仅提供基本的任务调度功能，
    不存储任务状态信息，专注于任务执行。
    """

    def __init__(self):
        """初始化调度器"""
        self.settings: SchedulerSettings = get_settings().scheduler
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.job_func_mapping: Dict = None
        self.logger = get_logger(__name__)
        self.start_time: Optional[datetime] = None
        self.listener: Optional[JobListener] = None

        from app.crawl import CrawlFlow
        self.job_func_mapping = {
            JobType.CRAWL: CrawlFlow().execute_crawl_task
        }

    def _get_job_func(self, job_type: JobType) -> Optional[Callable]:
        """获取任务执行函数 - 延迟初始化避免代理配置问题"""
        func = self.job_func_mapping.get(job_type, None)
        if func is None:
            raise ValueError(f"job type {job_type} is not supported")
        return func


    async def add_schedule_job(self, job: Job, exe_func=None) -> Job:
        """
        添加调度任务
        :param job:
        :param exe_func: 指定函数
        :return:
        """
        if not exe_func:
            func = self._get_job_func(job.job_type)
        else:
            func = exe_func
        args = job.page_ids if job.job_type == JobType.CRAWL else None
        if func is None:
            raise ValueError(f"cannot found execute function for {job.job_type}")
        # 添加任务到调度器 - 不使用metadata
        self.scheduler.add_job(
            func=func,
            trigger=job.trigger,
            id=job.job_id,
            args=[args],
            remove_on_complete=False
        )

        self.logger.info(f"单个任务添加成功: {job.job_id}")
        return job


    async def start(self) -> None:
        """启动调度器"""
        if self.scheduler is not None:
            self.logger.warning("调度器已经启动")
            return

        self.logger.info("正在启动任务调度器...")

        # 创建调度器并配置
        self.scheduler = AsyncIOScheduler(
            jobstores={
                'default': SQLAlchemyJobStore(
                    url=self.settings.job_store_url, 
                    tablename=self.settings.job_store_table_name
                )
            },
            executors={
                'default': ThreadPoolExecutor(self.settings.max_workers)
            },
            timezone=self.settings.timezone
        )
        self.logger.info("调度器配置完成")
        self.start_time = datetime.now()

        # 注册事件监听器 - 仅监听失败事件
        self.listener = JobListener()
        self.scheduler.add_listener(self.listener.listen_job_failure, EVENT_JOB_ERROR)

        self.logger.info("事件监听器注册完成")

        # 启动调度器
        self.scheduler.start()

        # 加载预定义任务
        self.logger.info("添加预定义任务")
        for job in get_predefined_jobs():
            await self.add_schedule_job(job)

        # 设置任务清理定时任务
        if self.settings.job_cleanup_enabled:
            self.logger.info("添加清理任务")
            await self.add_schedule_job(get_clean_up_job(), exe_func=self._cleanup_old_jobs)

        self.logger.info("任务调度器启动成功")

    async def shutdown(self) -> None:
        """关闭调度器"""
        if self.scheduler is None:
            return

        self.logger.info("正在关闭任务调度器...")
        self.scheduler.shutdown(wait=True)
        self.scheduler = None
        self.start_time = None
        self.listener = None
        self.logger.info("任务调度器已关闭")

    def _cleanup_old_jobs(self) -> Dict[str, Any]:
        """清理过期任务 - 简化版本，仅清理DateTrigger的已完成任务"""
        if not self.scheduler:
            return {"cleaned": 0, "error": "调度器未运行"}
        try:
            from datetime import timezone
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.settings.job_retention_days)
            all_jobs = self.scheduler.get_jobs()
            stats = {"cleaned_count": 0, "errors": []}
            
            for job in all_jobs:
                should_cleanup, reason = self._should_cleanup_job(job, cutoff_date)
                if should_cleanup:
                    try:
                        self.scheduler.remove_job(job.id)
                        stats["cleaned_count"] += 1
                        self.logger.info(f"清理过期任务: {job.id} (原因: {reason})")
                    except Exception as e:
                        error_msg = f"移除任务 {job.id}失败: {e}"
                        self.logger.error(error_msg)
                        stats["errors"].append(error_msg)
                        
                if stats["cleaned_count"] >= self.settings.cleanup_batch_size:
                    self.logger.info(f"达到单次清理限制({self.settings.cleanup_batch_size})，下次清理将继续处理剩余任务")
                    break
                    
            result = {
                "cleaned": stats["cleaned_count"],
                "cutoff_date": cutoff_date.isoformat(),
                "batch_size_reached": stats["cleaned_count"] >= self.settings.cleanup_batch_size,
                "errors": stats["errors"],
            }
            self.logger.info(f"任务清理完成: 清理了{stats['cleaned_count']}个任务")
            return result
        except Exception as e:
            error_msg = f"任务清理过程发生意外错误: {e}"
            self.logger.error(error_msg)
            return {"cleaned": 0, "error": error_msg}

    @staticmethod
    def _should_cleanup_job(job, cutoff_date: datetime) -> Tuple[bool, str]:
        """
        简化的任务清理判断 - 不依赖metadata
        :param job: 任务
        :param cutoff_date: 清理时间
        :return:
        """
        # 系统任务不清理
        if "__system_job" in job.id:
            return False, "system job"
            
        # 只清理DateTrigger且已经没有下次运行时间的任务
        is_onetime = isinstance(job.trigger, DateTrigger)
        if is_onetime and job.next_run_time is None:
            return True, "completed_onetime_job"
        
        return False, "active_job"

    def get_scheduler_info(self) -> SchedulerInfo:
        """获取调度器状态信息 - 简化版本，不依赖metadata"""
        if not self.scheduler:
            return SchedulerInfo(
                status="stopped",
                jobs=[],
                run_time="0天0小时0分钟0秒"
            )

        try:
            # 获取所有任务
            jobs = self.scheduler.get_jobs()

            job_list = []
            for job in jobs:
                job_data = {
                    "id": job.id,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                    "trigger": str(job.trigger),
                    "status": "scheduled" if job.next_run_time else "completed"
                }
                job_list.append(job_data)

            # 计算运行时间
            run_time = self._calculate_run_time()

            return SchedulerInfo(
                status="running",
                jobs=job_list,
                run_time=run_time
            )

        except Exception as e:
            self.logger.error(f"获取调度器状态失败: {e}")
            return SchedulerInfo(
                status="error",
                jobs=[],
                run_time="未知"
            )

    def _calculate_run_time(self) -> str:
        """计算并格式化运行时间 - 使用humanize库"""
        if not self.start_time:
            return "未知"

        try:
            delta = datetime.now() - self.start_time
            # 使用humanize库进行人性化时间格式化
            if delta.days > 0:
                return humanize.precisedelta(delta, minimum_unit="seconds")
            else:
                return humanize.naturaldelta(delta)
        except Exception as e:
            self.logger.warning(f"humanize库处理时间失败，回退到原始方法: {e}")
            # 回退到原始的时间格式化方法
            delta = datetime.now() - self.start_time
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{days}天{hours}小时{minutes}分钟{seconds}秒"


# 全局调度器实例
_scheduler: JobScheduler | None = None


def get_scheduler() -> JobScheduler:
    """获取调度器实例（单例模式）"""
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler


async def start_scheduler() -> None:
    """启动调度器"""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler() -> None:
    """停止调度器"""
    scheduler = get_scheduler()
    await scheduler.shutdown()
