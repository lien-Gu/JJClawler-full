"""
任务调度器 - 使用APScheduler 3.10.x稳定版本

重构后的调度器使用APScheduler 3.x的SQLAlchemyJobStore和metadata存储，
移除了内存存储，实现了更简洁和稳定的架构。
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings, SchedulerSettings
from app.logger import get_logger
from app.models.schedule import (
    JobHandlerType,
    JobInfo,
    JobStatus,
    PREDEFINED_JOB_INFO,
    TriggerType,
)

from .handlers import BaseJobHandler, CrawlJobHandler, ReportJobHandler


class TaskScheduler:
    """任务调度器主类 - 基于APScheduler 3.x稳定版本
    
    重构后的调度器完全依赖APScheduler的存储机制，
    使用job metadata存储业务信息，实现了架构简化。
    """

    def __init__(self):
        """初始化调度器"""
        self.settings: SchedulerSettings = get_settings().scheduler
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.job_handlers: Dict[str, type[BaseJobHandler]] = {}
        self.logger = get_logger(__name__)
        self.start_time: Optional[datetime] = None

        # 注册默认任务处理器
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """注册默认任务处理器"""
        self.job_handlers = {
            JobHandlerType.CRAWL: CrawlJobHandler,
            JobHandlerType.REPORT: ReportJobHandler,
        }

    def _create_scheduler_with_config(self) -> AsyncIOScheduler:
        """创建APScheduler 3.x实例并应用配置"""
        db_url = self.settings.job_store_url
        # 创建调度器
        scheduler = AsyncIOScheduler(
            jobstores=SQLAlchemyJobStore(url=db_url, tablename='apscheduler_jobs'),
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
        self.scheduler.add_listener(self._on_job_executed,EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._on_job_error,EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._on_job_missed,EVENT_JOB_MISSED)

        self.logger.info("事件监听器注册完成")

    def _on_job_executed(self, event) -> None:
        """任务执行成功监听器"""
        job_id = event.job_id

        # 获取job并更新metadata
        job = self.scheduler.get_job(job_id)
        if job and job.metadata:
            job.metadata['status'] = JobStatus.SUCCESS
            job.metadata['status_message'] = '任务执行完成'
            job.metadata['last_run_time'] = datetime.now().isoformat()

            # 如果有执行结果，可以存储到metadata中
            if hasattr(event, 'retval') and event.retval:
                job.metadata['last_result'] = event.retval

            self.logger.info(f"任务 {job_id} 执行成功")

    def _on_job_error(self, event) -> None:
        """任务执行失败监听器"""
        job_id = event.job_id
        exception = event.exception

        job = self.scheduler.get_job(job_id)
        if job and job.metadata:
            retry_count = job.metadata.get('retry_count', 0)
            max_retries = self.settings.crawler.retry_times

            if retry_count < max_retries:
                # 安排重试
                retry_count += 1
                job.metadata['retry_count'] = retry_count
                job.metadata['status'] = JobStatus.PENDING
                job.metadata['status_message'] = f'准备第{retry_count}次重试'

                # 重新调度任务
                self._reschedule_job_for_retry(job, retry_count)

                self.logger.warning(
                    f"任务 {job_id} 将进行第{retry_count}次重试: {str(exception)}"
                )
            else:
                # 重试次数已达上限
                job.metadata['status'] = JobStatus.FAILED
                job.metadata['status_message'] = f'重试{max_retries}次后仍失败: {str(exception)}'
                job.metadata['failure_reason'] = str(exception)

                self.logger.error(f"任务 {job_id} 最终失败: {str(exception)}")

    def _on_job_missed(self, event) -> None:
        """任务错过执行时间监听器"""
        job_id = event.job_id

        job = self.scheduler.get_job(job_id)
        if job and job.metadata:
            job.metadata['status'] = JobStatus.FAILED
            job.metadata['status_message'] = '任务错过执行时间'

            self.logger.warning(f"任务 {job_id} 错过执行时间")

    def _reschedule_job_for_retry(self, job, retry_count: int) -> None:
        """重新调度失败的任务进行重试"""
        try:
            # 计算重试时间
            retry_delay = self.settings.crawler.retry_delay
            retry_time = datetime.now() + timedelta(seconds=retry_delay)

            # 获取原始的page_ids
            page_ids = job.metadata.get('page_ids', [])
            handler_type = job.metadata.get('handler_type', JobHandlerType.CRAWL)

            # 获取处理器
            handler_class = self.job_handlers.get(handler_type)
            if not handler_class:
                self.logger.error(f"未找到处理器: {handler_type}")
                return

            handler = handler_class()

            # 创建新的重试任务ID
            retry_job_id = f"{job.id}_retry_{retry_count}"

            # 复制原任务的metadata
            retry_metadata = job.metadata.copy()
            retry_metadata['original_job_id'] = job.id
            retry_metadata['is_retry'] = True

            # 添加重试任务
            self.scheduler.add_job(
                func=handler.execute,
                trigger=DateTrigger(run_date=retry_time),
                id=retry_job_id,
                args=[page_ids],
                metadata=retry_metadata
            )

            self.logger.info(f"任务 {job.id} 重试已调度，重试ID: {retry_job_id}")

        except Exception as e:
            self.logger.error(f"重新调度任务失败 {job.id}: {e}")
            if job.metadata:
                job.metadata['status'] = JobStatus.FAILED
                job.metadata['status_message'] = f'重试调度失败: {str(e)}'

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

    def _generate_job_id(self, job_type: str, page_id: Optional[str] = None) -> str:
        """生成任务ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if page_id:
            return f"{job_type}_{page_id}_{timestamp}"
        else:
            return f"{job_type}_{timestamp}_{str(uuid.uuid4())[:8]}"

    def _create_trigger(self, trigger_type: TriggerType, trigger_time: Dict[str, Any]):
        """根据触发器类型创建触发器"""
        if trigger_type == TriggerType.DATE:
            run_time = trigger_time.get("run_time")
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
                await self.add_job(job_info)
            except Exception as e:
                self.logger.error(f"加载预定义任务失败 {job_id}: {e}")

    async def add_job(self, job_info: JobInfo) -> JobInfo:
        """根据JobInfo添加调度任务"""
        # 如果没有job_id，生成一个
        if not job_info.job_id:
            job_info.job_id = self._generate_job_id(job_info.handler)

        # 获取完整的page_ids
        if job_info.page_ids:
            page_ids = self.get_full_page_ids(job_info.page_ids)
            job_info.page_ids = page_ids

        # 如果是多个页面的批次任务
        if job_info.page_ids and len(job_info.page_ids) > 1:
            return await self.add_batch_jobs(job_info)
        else:
            # 单个任务
            return await self._add_single_job(job_info)

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

    @staticmethod
    def get_full_page_ids(page_ids) -> List[str]:
        """获取完整的页面ID列表"""
        if not page_ids:
            return []

        try:
            from app.crawl_config import CrawlConfig
            crawl_config = CrawlConfig()
            return crawl_config.determine_page_ids(page_ids)
        except Exception:
            # 如果获取失败，返回原始列表
            return page_ids if isinstance(page_ids, list) else [page_ids]


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
