"""
任务调度器 - 使用APScheduler 3.10.x稳定版本

重构后的调度器使用APScheduler 3.x的SQLAlchemyJobStore，
移除metadata存储，仅保留基本的任务调度功能。
"""

from datetime import datetime
from typing import Optional

import humanize
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import SchedulerSettings, get_settings
from app.logger import get_logger
from app.models.schedule import (Job, JobType, SchedulerInfo, get_predefined_jobs)
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
        self.logger = get_logger(__name__)
        self.start_time: Optional[datetime] = None
        self.listener: Optional[JobListener] = None

    async def add_schedule_job(self, job: Job, exe_func=None) -> Job:
        """
        添加调度任务
        :param job:
        :param exe_func: 指定函数
        :return:
        """
        job_args = []
        # 为不同任务类型准备参数
        if job.job_type == JobType.CRAWL:
            # 使用包装函数解决异步调用问题
            from ..crawl.crawl_flow import crawl_task_wrapper
            exe_func = crawl_task_wrapper
            job_args = [job.page_ids]

        if exe_func is None:
            self.logger.error(f"{job.job_id}未给定调度函数")

        # 添加任务到调度器 - 不使用metadata
        self.scheduler.add_job(
            func=exe_func,
            trigger=job.trigger,
            id=job.job_id,
            args=job_args,
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

        # 智能加载预定义任务 - 仅添加数据库中不存在的任务
        self.logger.info("检查并添加预定义任务")
        await self._ensure_predefined_jobs()

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

    def is_running(self) -> bool:
        """检查调度器是否运行中"""
        return self.scheduler is not None and self.scheduler.running

    async def _ensure_predefined_jobs(self) -> None:
        """
        确保预定义任务存在
        """
        predefined_jobs = get_predefined_jobs()
        existing_job_ids = {job.id for job in self.scheduler.get_jobs()}

        added_count = 0
        skipped_count = 0

        for job in predefined_jobs:
            if job.job_id in existing_job_ids:
                self.logger.info(f"任务已存在，跳过添加: {job.job_id}")
                skipped_count += 1
            else:
                try:
                    await self.add_schedule_job(job)
                    added_count += 1
                    self.logger.info(f"成功添加新任务: {job.job_id}")
                except Exception as e:
                    self.logger.error(f"添加任务失败 {job.job_id}: {e}")

        self.logger.info(f"预定义任务检查完成: 新增{added_count}个, 跳过{skipped_count}个")

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


async def check_scheduler() -> bool:
    """检查调度器状态"""
    scheduler = get_scheduler()
    return scheduler.is_running()