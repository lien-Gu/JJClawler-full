"""
调度器服务

统一调度所有爬取任务
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from pytz import utc

from app.modules.service.crawl_service import get_crawl_service
from app.modules.service.task_monitor_service import get_task_monitor_service
from app.utils.log_utils import get_logger
from app.config import get_settings

logger = get_logger(__name__)


class SchedulerService:
    """统一调度器服务"""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.crawl_service = get_crawl_service()
        self.task_monitor = get_task_monitor_service()
        self._is_running = False
        self._stats = {"total_executed": 0, "total_failed": 0}

    async def start(self):
        """启动调度器"""
        if self._is_running:
            logger.warning("调度器已在运行中")
            return

        try:
            logger.info("启动调度器服务...")

            # 配置SQL JobStore
            settings = get_settings()
            jobstore = SQLAlchemyJobStore(url=settings.DATABASE_URL, tablename='apscheduler_jobs')
            
            self.scheduler = AsyncIOScheduler(
                jobstores={'default': jobstore},
                timezone=utc
            )
            self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
            self.scheduler.start()
            
            logger.info(f"调度器使用SQL JobStore: {settings.DATABASE_URL}")

            self._setup_scheduled_jobs()
            await self.task_monitor.start_monitoring()

            self._is_running = True
            logger.info("调度器服务启动成功")

        except Exception as e:
            logger.error(f"调度器启动失败: {e}")
            await self.stop()
            raise

    async def stop(self):
        """停止调度器"""
        if not self._is_running:
            return

        try:
            logger.info("停止调度器服务...")
            await self.task_monitor.stop_monitoring()

            if self.scheduler:
                self.scheduler.shutdown(wait=True)
                self.scheduler = None

            self._is_running = False
            logger.info("调度器服务已停止")

        except Exception as e:
            logger.error(f"停止调度器失败: {e}")

    def _setup_scheduled_jobs(self):
        """配置定时任务 - 统一使用CronTrigger + 5分钟偏移"""
        try:
            scheduled_tasks = self.crawl_service.get_scheduled_tasks()
            
            for task in scheduled_tasks:
                self.scheduler.add_job(
                    func=self._execute_crawl,
                    trigger=CronTrigger(timezone=utc, **task.get_trigger_config()),
                    args=[task.id],
                    id=f"scheduled_{task.id}",
                    max_instances=1,
                    replace_existing=True
                )
                
                logger.info(f"配置定时任务: {task.id} ({task.frequency}, interval={task.interval})")

            logger.info(f"配置了 {len(scheduled_tasks)} 个定时任务 (统一CronTrigger + 5分钟偏移)")

        except Exception as e:
            logger.error(f"配置定时任务失败: {e}")

    async def _execute_crawl(self, task_id: str):
        """执行爬取任务"""
        try:
            logger.info(f"开始执行定时爬取: {task_id}")

            # 方案A：使用execute_task包装器（提供统一的任务生命周期管理）
            # 包括：创建执行实例 → 开始 → 执行 → 完成/失败 → 状态跟踪
            async def crawl_func():
                return await self.crawl_service.crawl_and_save(task_id)

            await self.crawl_service.execute_task(
                task_id, 
                crawl_func, 
                {"trigger_source": "scheduled"}
            )
            
            # 方案B：直接调用（如果您希望简化）
            # 缺点：失去统一的任务状态管理、错误处理、进度跟踪
            # await self.crawl_service.crawl_and_save(task_id)

        except Exception as e:
            logger.error(f"定时爬取失败 ({task_id}): {e}")

    def trigger_manual_crawl(self, task_id: str) -> str:
        """手动触发爬取任务"""
        if not self.scheduler:
            raise RuntimeError("调度器未启动")

        job_id = f"manual_{task_id}_{datetime.now().strftime('%H%M%S')}"

        self.scheduler.add_job(
            func=self._execute_crawl,
            trigger='date',
            run_date=datetime.now(),
            args=[task_id],
            id=job_id,
            max_instances=1
        )

        logger.info(f"添加手动任务: {job_id}")
        return job_id

    def _on_job_executed(self, event):
        """任务执行成功回调"""
        self._stats['total_executed'] += 1
        logger.info(f"定时任务执行成功: {event.job_id}")

    def _on_job_error(self, event):
        """任务执行失败回调"""
        self._stats['total_executed'] += 1
        self._stats['total_failed'] += 1
        logger.error(f"定时任务执行失败: {event.job_id}, 错误: {event.exception}")

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "is_running": self._is_running,
            "active_jobs": len(self.scheduler.get_jobs()) if self.scheduler else 0,
            "statistics": self._stats
        }

    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """获取所有定时任务"""
        if not self.scheduler:
            return []

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'func_name': job.func.__name__
            })

        return jobs


# 全局实例
_scheduler_service = None


def get_scheduler_service() -> SchedulerService:
    """获取调度器服务实例"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service


# 便捷函数
async def start_scheduler():
    """启动调度器"""
    await get_scheduler_service().start()


async def stop_scheduler():
    """停止调度器"""
    await get_scheduler_service().stop()


def trigger_manual_crawl(task_id: str) -> str:
    """手动触发爬取"""
    return get_scheduler_service().trigger_manual_crawl(task_id)


def get_scheduler_stats() -> Dict[str, Any]:
    """获取调度器统计信息"""
    service = get_scheduler_service()
    return {
        "status": service.get_status(),
        "jobs": service.get_scheduled_jobs(),
        "task_summary": get_crawl_service().get_all_tasks()
    }