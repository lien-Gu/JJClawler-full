"""
任务调度器 - 使用APScheduler 3.10.x稳定版本

重构后的调度器使用APScheduler 3.x的SQLAlchemyJobStore和metadata存储，
移除了内存存储，实现了更简洁和稳定的架构。
"""

from datetime import datetime, timedelta
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
    JobType,
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
        self.job_func_mapping: Dict = {}
        self.logger = None
        self.start_time: Optional[datetime] = None

        # 初始化参数
        self._initial_variety()

    def _initial_variety(self):
        """注册默认任务处理器"""
        self.settings = get_settings().scheduler
        self.job_func_mapping = {
            JobType.CRAWL: self.add_crawl_job,
            JobType.REPORT: self._add_report_job,
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
        current_time = datetime.now()
        update_dict['updated_at'] = current_time.isoformat()

        if event.code == EVENT_JOB_SUBMITTED:
            update_dict["status"] = JobStatus.RUNNING
            update_dict["status_message"] = "任务正在执行或者排队"
            update_dict['execution_count'] = update_dict.get('execution_count', 0) + 1
            self.logger.info(f"任务 {job_id} 正在执行或者排队 (第{update_dict['execution_count']}次)")

        elif event.code == EVENT_JOB_EXECUTED:
            update_dict["status"] = JobStatus.SUCCESS
            update_dict["status_message"] = "任务执行完成"
            update_dict['total_success_count'] = update_dict.get('total_success_count', 0) + 1
            update_dict['last_execution_time'] = current_time.isoformat()

            # 存储任务执行结果
            execution_result = {
                'timestamp': current_time.isoformat(),
                'status': 'success',
                'result': getattr(event, 'retval', None),
                'duration': None  # 可以后续添加执行时间计算
            }

            # 更新执行结果历史(保留最近10次)
            execution_results = update_dict.get('execution_results', [])
            execution_results.append(execution_result)
            update_dict['execution_results'] = execution_results[-10:]
            update_dict['last_result'] = execution_result

            self.logger.info(f"任务 {job_id} 执行成功 (成功{update_dict['total_success_count']}次)")

        elif event.code == EVENT_JOB_ERROR:
            update_dict["status"] = JobStatus.FAILED
            exception = event.exception
            error_msg = str(exception)
            update_dict["status_message"] = f"任务失败，失败原因：{error_msg}"
            update_dict['total_failure_count'] = update_dict.get('total_failure_count', 0) + 1
            update_dict['last_execution_time'] = current_time.isoformat()

            # 存储失败信息
            failure_result = {
                'timestamp': current_time.isoformat(),
                'status': 'failed',
                'error': error_msg,
                'exception_type': exception.__class__.__name__
            }

            execution_results = update_dict.get('execution_results', [])
            execution_results.append(failure_result)
            update_dict['execution_results'] = execution_results[-10:]
            update_dict['last_result'] = failure_result

            self.logger.error(f"任务 {job_id} 执行失败 (失败{update_dict['total_failure_count']}次): {error_msg}")

        elif event.code == EVENT_JOB_MISSED:
            update_dict["status"] = JobStatus.FAILED
            update_dict["status_message"] = "任务错过执行时间"
            update_dict['total_failure_count'] = update_dict.get('total_failure_count', 0) + 1
            update_dict['last_execution_time'] = current_time.isoformat()

            # 存储错过执行的信息
            missed_result = {
                'timestamp': current_time.isoformat(),
                'status': 'missed',
                'error': '任务错过执行时间',
                'exception_type': 'MissedExecution'
            }

            execution_results = update_dict.get('execution_results', [])
            execution_results.append(missed_result)
            update_dict['execution_results'] = execution_results[-10:]
            update_dict['last_result'] = missed_result

            self.logger.warning(f"任务 {job_id} 错过执行时间")

        job.modify(metadata=update_dict)

    async def add_schedule_job(self, job_info: JobInfo) -> JobInfo:
        """
        添加调度任务
        :param job_info:
        :return:
        """
        if not job_info.type:
            raise ValueError("Job missing important field: type")
        return self.job_func_mapping.get(job_info.type)(job_info)

    async def add_crawl_job(self, job_info: JobInfo) -> JobInfo:
        """
        添加爬虫调度任务
        :param job_info:
        :return:
        """
        trigger = self._create_trigger(job_info.trigger_type, job_info.trigger_time)
        # 准备metadata - 存储所有业务信息
        metadata = job_info.to_metadata()

        # 增强metadata结构以支持结果存储
        metadata.update({
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'execution_results': [],  # 存储最近10次执行结果历史
            'last_result': None,  # 最后一次执行结果
            'last_execution_time': None,  # 最后执行时间
        })

        # 添加任务到调度器
        self.scheduler.add_job(
            func=craw_task.execute_crawl_task,
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

        # 设置任务清理定时任务
        await self._setup_cleanup_job()

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

    async def _setup_cleanup_job(self) -> None:
        """设置任务清理定时任务"""
        if not self.settings.job_cleanup_enabled:
            self.logger.info("任务清理功能已禁用，跳过设置清理任务")
            return

        cleanup_trigger = IntervalTrigger(hours=self.settings.cleanup_interval_hours)

        # 添加清理任务
        self.scheduler.add_job(
            func=self._cleanup_old_jobs,
            trigger=cleanup_trigger,
            id="__system_job_cleanup__",
            metadata={
                'job_type': 'system',
                'status': JobStatus.PENDING,
                'status_message': '系统任务清理器',
                'desc': '自动清理过期任务',
                'is_system_job': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'execution_results': [],
                'last_result': None,
                'last_execution_time': None,
                'execution_count': 0,
                'total_success_count': 0,
                'total_failure_count': 0,
            },
            remove_on_complete=False
        )

        self.logger.info(
            f"任务清理器已设置，每{self.settings.cleanup_interval_hours}小时执行一次，保留{self.settings.job_retention_days}天内的任务")

    def _cleanup_old_jobs(self) -> Dict[str, Any]:
        """清理过期任务"""
        if not self.scheduler:
            return {"cleaned": 0, "error": "调度器未运行"}

        try:
            cutoff_date = datetime.now() - timedelta(days=self.settings.job_retention_days)
            all_jobs = self.scheduler.get_jobs()

            cleaned_count = 0
            skipped_system = 0
            skipped_active = 0
            errors = []

            for job in all_jobs:
                if not job.metadata:
                    continue

                # 跳过系统任务
                if job.metadata.get('is_system_job', False):
                    skipped_system += 1
                    continue

                # 检查任务创建时间
                created_at_str = job.metadata.get('created_at')
                if not created_at_str:
                    continue

                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    if created_at < cutoff_date:
                        # 检查是否为一次性已完成任务，或者失败任务
                        status = job.metadata.get('status')
                        if status in [JobStatus.SUCCESS, JobStatus.FAILED]:
                            self.scheduler.remove_job(job.id)
                            cleaned_count += 1
                            self.logger.debug(f"清理过期任务: {job.id}")
                            if cleaned_count >= self.settings.cleanup_batch_size:
                                break
                        else:
                            skipped_active += 1

                except (ValueError, AttributeError) as e:
                    error_msg = f"解析任务创建时间失败 {job.id}: {e}"
                    self.logger.warning(error_msg)
                    errors.append(error_msg)
                    continue

            result = {
                "cleaned": cleaned_count,
                "cutoff_date": cutoff_date.isoformat(),
                "skipped_system": skipped_system,
                "skipped_active": skipped_active,
                "errors": errors
            }

            self.logger.info(
                f"任务清理完成: 清理{cleaned_count}个, 跳过系统任务{skipped_system}个, 跳过活动任务{skipped_active}个")
            return result

        except Exception as e:
            error_msg = f"任务清理失败: {e}"
            self.logger.error(error_msg)
            return {"cleaned": 0, "error": error_msg}

    def get_cleanup_status(self) -> Dict[str, Any]:
        """获取清理任务状态"""
        if not self.scheduler:
            return {"status": "scheduler_not_running"}

        cleanup_job = self.scheduler.get_job("__system_job_cleanup__")
        if not cleanup_job:
            return {"status": "cleanup_job_not_found"}

        metadata = cleanup_job.metadata or {}
        return {
            "status": "active",
            "next_run_time": str(cleanup_job.next_run_time) if cleanup_job.next_run_time else None,
            "last_result": metadata.get('last_result'),
            "execution_count": metadata.get('execution_count', 0),
            "success_count": metadata.get('total_success_count', 0),
            "failure_count": metadata.get('total_failure_count', 0),
            "config": {
                "enabled": self.settings.job_cleanup_enabled,
                "retention_days": self.settings.job_retention_days,
                "interval_hours": self.settings.cleanup_interval_hours,
                "batch_size": self.settings.cleanup_batch_size
            }
        }

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
                if job_info.type == JobType.REPORT:
                    continue  # 跳过报告任务
                await self.add_crawl_job(job_info)
            except Exception as e:
                self.logger.error(f"加载预定义任务失败 {job_id}: {e}")

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
            type=metadata.get('job_type', JobType.CRAWL),
            status=(
                metadata.get('status', JobStatus.PENDING),
                metadata.get('status_message', '未知状态')
            ),
            page_ids=metadata.get('page_ids', []),
            desc=metadata.get('desc', ''),
            result=metadata.get('execution_results', []),  # 返回执行历史而不是单个结果
            # 可以扩展返回更多执行统计信息
            last_result=metadata.get('last_result'),
            execution_stats={
                'total_executions': metadata.get('execution_count', 0),
                'success_count': metadata.get('total_success_count', 0),
                'failure_count': metadata.get('total_failure_count', 0),
                'last_execution_time': metadata.get('last_execution_time')
            }
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
