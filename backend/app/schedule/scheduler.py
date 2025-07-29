"""
任务调度器
"""

from datetime import datetime
from tkinter import Listbox
from typing import Any, List

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.job import Job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.logger import get_logger
from app.models.schedule import (
    PREDEFINED_JOB_INFO,
    JobHandlerType,
    TriggerType,
)

from .handlers import BaseJobHandler, CrawlJobHandler, ReportJobHandler
from ..models import JobInfo


class TaskScheduler:
    """任务调度器主类"""

    def __init__(self):
        """初始化调度器"""
        self.settings = get_settings()
        self.scheduler: AsyncIOScheduler | None = None
        self.job_handlers: dict[str, type[BaseJobHandler]] = {}
        self.logger = get_logger(__name__)
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
        # 使用SQLite数据库存储调度任务，从配置中获取数据库URL
        scheduler_config = self.settings.scheduler

        # 配置job store - 使用SQLAlchemyJobStore存储到数据库
        job_stores = {
            "default": SQLAlchemyJobStore(
                url=scheduler_config.job_store_url or self.settings.database.url
            )
        }

        # 配置executor
        executors = {"default": AsyncIOExecutor()}

        # 创建调度器
        scheduler = AsyncIOScheduler(
            jobstores=job_stores,
            executors=executors,
            job_defaults=scheduler_config.job_defaults,
            timezone=scheduler_config.timezone,
        )

        self.logger.info(
            f"调度器配置完成，任务存储URL: {scheduler_config.job_store_url or self.settings.database.url}"
        )

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
        for job_id, job_info in PREDEFINED_JOB_INFO.items():
            try:
                if job_info.handler == JobHandlerType.REPORT:
                    return
                await self.add_job(job_info)
            except Exception as e:
                self.logger.error(f"加载预定义任务失败 {job_id}: {e}")

    async def add_job(self, job_info: JobInfo) -> JobInfo:
        """
        根据调度任务信息来添加一个调度任务
        如果是爬虫类任务，并且page id不是单个，就需要调用add_batch_jobs来处理
        需要监视器跟踪任务的情况然后补充job_info,完成任务后需要将结果记录到job_info的result中

        :param job_info:
        :return: 返回创建后的调度任务信息
        """
        page_ids = self.get_full_page_ids(job_info.page_ids)
        job_info.page_ids = page_ids
        if len(job_info.page_ids) > 1:
            return await self.add_batch_jobs(job_info)
        pass

    async def add_batch_jobs(
        self, job_info: JobInfo) -> JobInfo:
        """
        添加多个调度任务，将job_info中的page_ids中的每个页面都生成一个爬虫调度任务，然后添加到调度器中
        需要监视器跟踪任务的情况然后补充job_info,JobInfo.status中需要记录完成了多少个任务，任务执行情况
        完成任务后需要将结果记录到job_info的result中

        :param job_info:
        :return:
        """

    @staticmethod
    def get_full_page_ids(page_ids) -> List[str]:
        from app.crawl_config import CrawlConfig
        crawl_config = CrawlConfig()
        return crawl_config.determine_page_ids(page_ids)


# 全局调度器实例
_scheduler: TaskScheduler | None = None


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
