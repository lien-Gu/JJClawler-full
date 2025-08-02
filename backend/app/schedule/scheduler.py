"""
任务调度器 - 使用APScheduler 3.10.x稳定版本

重构后的调度器使用APScheduler 3.x的SQLAlchemyJobStore和metadata存储，
移除了内存存储，实现了更简洁和稳定的架构。
"""

from datetime import datetime
from typing import Any, Dict, Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED, EVENT_JOB_SUBMITTED
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import SchedulerSettings, get_settings
from app.crawl import CrawlFlow
from app.logger import get_logger
from app.models.schedule import (
    JobHandlerType,
    JobInfo,
    JobStatus,
    PREDEFINED_JOB_INFO,
    TriggerType,
)

craw_task = CrawlFlow()


class JobScheduler:
    """任务调度器主类 - 基于APScheduler 3.x稳定版本
    
    重构后的调度器完全依赖APScheduler的存储机制，
    使用job metadata存储业务信息，实现了架构简化。
    """

    def __init__(self):
        """初始化调度器"""
        self.settings: SchedulerSettings = None
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.job_handlers: Dict = {}
        self.logger = None
        self.start_time: Optional[datetime] = None

        # 初始化参数
        self._initial_variety()

    def _initial_variety(self):
        """注册默认任务处理器"""
        self.settings = get_settings().scheduler
        self.job_handlers = {
            JobHandlerType.CRAWL: self._add_report_job,
            JobHandlerType.REPORT: self._add_report_job,
        }
        self.logger = get_logger(__name__)

    def _create_scheduler_with_config(self) -> AsyncIOScheduler:
        """创建APScheduler 3.x实例并应用配置"""
        db_url = self.settings.job_store_url
        # 创建调度器
        scheduler = AsyncIOScheduler(
            jobstores=SQLAlchemyJobStore(url=db_url, tablename=self.settings.job_store_table_name),
            executors=ThreadPoolExecutor(self.settings.max_workers),
            timezone=self.settings.timezone
        )
        self.logger.info(
            f"调度器配置完成 - 最大工作线程: {self.settings.max_workers}, "
            f"任务存储URL: {db_url}"
        )
        return scheduler

    def _register_event_listeners(self) -> None:
        """注册事件监听器 - 3.x版本API"""
        if self.scheduler is None:
            return
        # 注册事件监听器
        self.scheduler.add_listener(self._job_listener,
                                    EVENT_JOB_SUBMITTED | EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)

        self.logger.info("事件监听器注册完成")

    def _job_listener(self, event):
        job_id = event.job_id
        job = self.scheduler.get_job(job_id)
        if not job or not job.metadata:
            raise ValueError("Job ID {} not found".format(job_id))
        update_dict = job.metadata.copy()
        update_dict['timestamp'] = datetime.now()
        if event.code == EVENT_JOB_SUBMITTED:
            update_dict["status"] = JobStatus.RUNNING
            update_dict["description"] = "任务正在执行或者排队"
            self.logger.info(f"任务 {job_id} 正在执行或者排队")

        elif event.code == EVENT_JOB_EXECUTED:
            update_dict["status"] = JobStatus.SUCCESS
            update_dict["description"] = "任务执行完成"
            self.logger.info(f"任务 {job_id} 执行成功")

        elif event.code == EVENT_JOB_ERROR:
            update_dict["status"] = JobStatus.FAILED
            exception = event.exception
            update_dict["description"] = "任务失败，失败原因：{}".format(str(exception))
            self.logger.error("任务失败，失败原因：{}".format(str(exception)))

        elif event.code == EVENT_JOB_MISSED:
            update_dict["status"] = JobStatus.FAILED
            update_dict["description"] = "任务错过执行时间"
            self.logger.warning(f"任务 {job_id} 错过执行时间")

        job.modify(metadata=update_dict)

    async def add_crawl_job(self, job_info: JobInfo) -> JobInfo:
        """
        添加爬虫调度任务
        :param job_info:
        :return:
        """
        trigger = self._create_trigger(job_info.trigger_type, job_info.trigger_time)
        # 准备metadata - 存储所有业务信息
        metadata = job_info.to_metadata()

        # 添加任务到调度器
        self.scheduler.add_job(
            func=craw_task.execute_crawl_task(job_info.page_ids),
            trigger=trigger,
            id=job_info.job_id,
            args=[job_info.page_ids or []],
            metadata=metadata,
            remove_on_complete=False
        )

        self.logger.info(f"单个任务添加成功: {job_info.job_id}")

        return job_info

    async def _add_report_job(self, job_info: JobInfo) -> JobInfo:

        """
        添加报告调度任务，暂时不实现

        :param trigger_type:
        :param trigger_time:
        :return:
        """
        pass

    async def start(self) -> None:
        """启动调度器"""
        if self.scheduler is not None:
            self.logger.warning("调度器已经启动")
            return

        self.logger.info("正在启动任务调度器...")

        # 创建调度器并配置
        self.scheduler = self._create_scheduler_with_config()
        self.start_time = datetime.now()

        # 注册事件监听器
        self._register_event_listeners()

        # 启动调度器
        self.scheduler.start()

        # 加载预定义任务
        await self._load_predefined_jobs()
        self.logger.info("任务调度器启动成功")

    async def shutdown(self) -> None:
        """关闭调度器"""
        if self.scheduler is None:
            return

        self.logger.info("正在关闭任务调度器...")
        self.scheduler.shutdown(wait=True)
        self.scheduler = None
        self.start_time = None
        self.logger.info("任务调度器已关闭")

    @staticmethod
    def _create_trigger(trigger_type: TriggerType, trigger_time: Dict[str, Any]):
        """
        根据触发器类型创建触发器

        :param trigger_type:
        :param trigger_time:
        :return:
        """
        if trigger_type == TriggerType.DATE:
            run_time = trigger_time.get("run_time", None)
            if not run_time:
                run_time = datetime.now()
            return DateTrigger(run_date=run_time)
        elif trigger_type == TriggerType.CRON:
            return CronTrigger(**trigger_time)
        elif trigger_type == TriggerType.INTERVAL:
            return IntervalTrigger(**trigger_time)
        else:
            raise ValueError(f"不支持的触发器类型: {trigger_type}")

    async def _load_predefined_jobs(self) -> None:
        """加载预定义任务"""
        for job_id, job_info in PREDEFINED_JOB_INFO.items():
            try:
                if job_info.handler == JobHandlerType.REPORT:
                    continue  # 跳过报告任务
                await self.add_crawl_job(job_info)
            except Exception as e:
                self.logger.error(f"加载预定义任务失败 {job_id}: {e}")

    async def _add_single_job(self, job_info: JobInfo) -> JobInfo:
        """添加单个任务到调度器"""
        try:
            # 创建触发器
            trigger = self._create_trigger(job_info.trigger_type, job_info.trigger_time)

            # 获取处理器
            handler_class = self.job_handlers.get(job_info.handler)
            if not handler_class:
                raise ValueError(f"未找到处理器: {job_info.handler}")

            handler = handler_class()

            # 准备metadata - 存储所有业务信息
            metadata = {
                'handler_type': job_info.handler,
                'page_ids': job_info.page_ids or [],
                'status': JobStatus.PENDING,
                'status_message': '任务已添加到调度器',
                'desc': job_info.desc or f"{job_info.handler}任务",
                'retry_count': 0,
                'created_at': datetime.now().isoformat(),
                'is_retry': False
            }

            # 添加任务到调度器
            self.scheduler.add_job(
                func=handler.execute,
                trigger=trigger,
                id=job_info.job_id,
                args=[job_info.page_ids or []],
                metadata=metadata
            )

            self.logger.info(f"单个任务添加成功: {job_info.job_id}")
            return job_info

        except Exception as e:
            self.logger.error(f"添加单个任务失败 {job_info.job_id}: {e}")
            job_info.status = (JobStatus.FAILED, f"添加任务失败: {str(e)}")
            raise

    async def add_batch_jobs(self, job_info: JobInfo) -> JobInfo:
        """添加多个调度任务"""
        try:
            batch_jobs = []
            failed_jobs = []

            for page_id in job_info.page_ids:
                try:
                    # 为每个页面创建子任务
                    sub_job_id = self._generate_job_id(job_info.handler, page_id)

                    # 创建子任务
                    sub_job_info = JobInfo(
                        job_id=sub_job_id,
                        trigger_type=job_info.trigger_type,
                        trigger_time=job_info.trigger_time,
                        handler=job_info.handler,
                        page_ids=[page_id],
                        desc=f"{job_info.handler}任务 - {page_id}"
                    )

                    # 添加子任务
                    await self._add_single_job(sub_job_info)
                    batch_jobs.append(sub_job_id)

                except Exception as e:
                    self.logger.error(f"添加子任务失败 {page_id}: {e}")
                    failed_jobs.append(page_id)

            # 更新批次任务状态
            total_jobs = len(job_info.page_ids)
            success_jobs = len(batch_jobs)
            failed_count = len(failed_jobs)

            if success_jobs == total_jobs:
                job_info.status = (JobStatus.PENDING, f"批次任务全部添加成功 ({success_jobs}/{total_jobs})")
            elif success_jobs > 0:
                job_info.status = (JobStatus.PENDING,
                                   f"批次任务部分添加成功 ({success_jobs}/{total_jobs}), 失败: {failed_count}")
            else:
                job_info.status = (JobStatus.FAILED, f"批次任务全部添加失败 ({failed_count}/{total_jobs})")

            if failed_jobs:
                job_info.desc = f"{job_info.desc or '批次任务'} - 失败页面: {', '.join(failed_jobs)}"

            self.logger.info(f"批次任务处理完成: {job_info.job_id}, 成功: {success_jobs}, 失败: {failed_count}")
            return job_info

        except Exception as e:
            self.logger.error(f"添加批次任务失败 {job_info.job_id}: {e}")
            job_info.status = (JobStatus.FAILED, f"批次任务处理失败: {str(e)}")
            raise

    def get_job_info(self, job_id: str) -> Optional[JobInfo]:
        """从APScheduler的metadata获取任务信息"""
        if not self.scheduler:
            return None

        job = self.scheduler.get_job(job_id)
        if not job or not job.metadata:
            return None

        # 从metadata重构JobInfo
        metadata = job.metadata

        # 从触发器推断trigger_type和trigger_time
        trigger_type = TriggerType.DATE  # 默认值
        trigger_time = {}

        if isinstance(job.trigger, CronTrigger):
            trigger_type = TriggerType.CRON
            # 简化的trigger_time，实际可能需要更复杂的逻辑
            trigger_time = {"hour": "*", "minute": "*"}
        elif isinstance(job.trigger, IntervalTrigger):
            trigger_type = TriggerType.INTERVAL
            trigger_time = {"seconds": job.trigger.interval.total_seconds()}
        elif isinstance(job.trigger, DateTrigger):
            trigger_type = TriggerType.DATE
            trigger_time = {"run_time": job.trigger.run_date}

        return JobInfo(
            job_id=job.id,
            trigger_type=trigger_type,
            trigger_time=trigger_time,
            handler=metadata.get('handler_type', JobHandlerType.CRAWL),
            status=(
                metadata.get('status', JobStatus.PENDING),
                metadata.get('status_message', '未知状态')
            ),
            page_ids=metadata.get('page_ids', []),
            desc=metadata.get('desc', ''),
            result=metadata.get('last_result')
        )

    def get_scheduler_info(self) -> Dict[str, Any]:
        """获取调度器状态信息"""
        if not self.scheduler:
            return {
                "status": "stopped",
                "job_wait": [],
                "job_running": [],
                "run_time": "0天0小时0分钟0秒"
            }

        try:
            # 获取所有任务
            jobs = self.scheduler.get_jobs()

            job_list = []
            for job in jobs:
                job_data = {
                    "id": job.id,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                    "trigger": str(job.trigger),
                    "status": job.metadata.get('status', 'unknown') if job.metadata else 'unknown'
                }
                job_list.append(job_data)

            # 计算运行时间
            run_time = "0天0小时0分钟0秒"
            if self.start_time:
                delta = datetime.now() - self.start_time
                days = delta.days
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                run_time = f"{days}天{hours}小时{minutes}分钟{seconds}秒"

            return {
                "status": "running",
                "job_wait": job_list,  # 简化：将所有任务都列为等待状态
                "job_running": [],
                "run_time": run_time
            }

        except Exception as e:
            self.logger.error(f"获取调度器状态失败: {e}")
            return {
                "status": "error",
                "job_wait": [],
                "job_running": [],
                "run_time": "未知"
            }


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
