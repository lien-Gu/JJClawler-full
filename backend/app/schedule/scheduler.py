"""
任务调度器 - 使用APScheduler 4.0
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from apscheduler import AsyncScheduler, current_job
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.logger import get_logger
from app.models.schedule import (
    PREDEFINED_JOB_INFO,
    JobHandlerType,
    JobInfo,
    JobStatus,
    TriggerType,
)

from .handlers import BaseJobHandler, CrawlJobHandler, ReportJobHandler


class TaskScheduler:
    """任务调度器主类 - 基于APScheduler 4.0"""

    def __init__(self):
        """初始化调度器"""
        self.settings = get_settings()
        self.scheduler: Optional[AsyncScheduler] = None
        self.job_handlers: Dict[str, type[BaseJobHandler]] = {}
        self.logger = get_logger(__name__)
        self.start_time: Optional[datetime] = None
        self._job_store: Dict[str, JobInfo] = {}  # 内存中存储任务信息

        # 注册默认任务处理器
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """注册默认任务处理器"""
        self.job_handlers = {
            JobHandlerType.CRAWL: CrawlJobHandler,
            JobHandlerType.REPORT: ReportJobHandler,
        }

    def _create_scheduler(self) -> AsyncScheduler:
        """创建APScheduler 4.0实例"""
        # 使用SQLite数据库存储调度任务，从配置中获取数据库URL
        scheduler_config = self.settings.scheduler
        db_url = scheduler_config.job_store_url or self.settings.database.url

        # 配置数据存储 - 使用SQLAlchemyDataStore
        data_store = SQLAlchemyDataStore(url=db_url)

        # 创建调度器
        scheduler = AsyncScheduler(data_store=data_store)

        self.logger.info(f"调度器配置完成，任务存储URL: {db_url}")

        return scheduler

    async def start(self) -> None:
        """启动调度器"""
        if self.scheduler is not None:
            self.logger.warning("调度器已经启动")
            return

        self.logger.info("正在启动任务调度器...")
        self.scheduler = self._create_scheduler()
        self.start_time = datetime.now()

        # 启动调度器
        await self.scheduler.start_in_background()
        
        # 加载预定义任务
        await self._load_predefined_jobs()
        self.logger.info("任务调度器启动成功")

    async def shutdown(self) -> None:
        """关闭调度器"""
        if self.scheduler is None:
            return

        self.logger.info("正在关闭任务调度器...")
        await self.scheduler.stop()
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
            # 指定日期触发
            run_time = trigger_time.get("run_time")
            return DateTrigger(run_date=run_time)
        elif trigger_type == TriggerType.CRON:
            # Cron表达式触发
            return CronTrigger(**trigger_time)
        elif trigger_type == TriggerType.INTERVAL:
            # 间隔触发
            return IntervalTrigger(**trigger_time)
        else:
            raise ValueError(f"不支持的触发器类型: {trigger_type}")

    async def _load_predefined_jobs(self) -> None:
        """加载预定义任务（支持多子任务）"""
        for job_id, job_info in PREDEFINED_JOB_INFO.items():
            try:
                if job_info.handler == JobHandlerType.REPORT:
                    continue  # 跳过报告任务
                await self.add_job(job_info)
            except Exception as e:
                self.logger.error(f"加载预定义任务失败 {job_id}: {e}")

    async def add_job(self, job_info: JobInfo) -> JobInfo:
        """
        根据调度任务信息来添加一个调度任务
        如果是爬虫类任务，并且page id不是单个，就需要调用add_batch_jobs来处理
        """
        # 如果没有job_id，生成一个
        if not job_info.job_id:
            job_info.job_id = self._generate_job_id(job_info.handler)

        # 获取完整的page_ids
        if job_info.page_ids:
            page_ids = self.get_full_page_ids(job_info.page_ids)
            job_info.page_ids = page_ids

        # 存储任务信息
        self._job_store[job_info.job_id] = job_info

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
            
            handler = handler_class(self)
            
            # 添加任务到调度器
            await self.scheduler.add_schedule(
                handler.execute_with_retry,
                trigger,
                id=job_info.job_id,
                args=[job_info.job_id, job_info.page_ids or []]
            )
            
            # 更新状态
            job_info.status = (JobStatus.PENDING, "任务已添加到调度器")
            job_info.desc = job_info.desc or f"{job_info.handler}任务"
            
            self.logger.info(f"单个任务添加成功: {job_info.job_id}")
            return job_info
            
        except Exception as e:
            self.logger.error(f"添加单个任务失败 {job_info.job_id}: {e}")
            job_info.status = (JobStatus.FAILED, f"添加任务失败: {str(e)}")
            raise

    async def add_batch_jobs(self, job_info: JobInfo) -> JobInfo:
        """
        添加多个调度任务，将job_info中的page_ids中的每个页面都生成一个爬虫调度任务，然后添加到调度器中
        """
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
                job_info.status = (JobStatus.PENDING, f"批次任务部分添加成功 ({success_jobs}/{total_jobs}), 失败: {failed_count}")
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

    async def get_job_info(self, job_id: str) -> Optional[JobInfo]:
        """获取任务信息"""
        job_info = self._job_store.get(job_id)
        if not job_info:
            return None
        
        # 查询调度器中的任务状态
        if self.scheduler:
            try:
                schedules = await self.scheduler.get_schedules()
                for schedule in schedules:
                    if schedule.id == job_id:
                        # 更新任务状态（这里可以根据实际情况更新）
                        break
            except Exception as e:
                self.logger.error(f"查询任务状态失败 {job_id}: {e}")
        
        return job_info

    async def get_scheduler_info(self) -> Dict[str, Any]:
        """获取调度器状态信息"""
        if not self.scheduler:
            return {
                "status": "stopped",
                "job_wait": [],
                "job_running": [],
                "run_time": "0天0小时0分钟0秒"
            }
        
        try:
            # 获取调度器中的任务
            schedules = await self.scheduler.get_schedules()
            
            job_wait = []
            job_running = []
            
            for schedule in schedules:
                job_data = {
                    "id": schedule.id,
                    "next_run_time": str(schedule.next_fire_time) if schedule.next_fire_time else None,
                    "trigger": str(schedule.trigger)
                }
                
                # 这里简单地将所有任务归类为等待状态
                # 实际实现中可能需要更复杂的状态判断
                job_wait.append(job_data)
            
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
                "job_wait": job_wait,
                "job_running": job_running,
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
