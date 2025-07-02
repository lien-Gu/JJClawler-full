"""
任务调度器

使用APScheduler管理任务调度，简化设计
"""
from datetime import datetime
from typing import Dict, List, Optional, Any

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from pytz import utc

from app.config import get_settings
from app.utils.log_utils import get_logger
from app.modules.task.manager import get_task_manager
from app.modules.crawler.crawler import get_crawl_service

logger = get_logger(__name__)


class TaskScheduler:
    """任务调度器 - 基于APScheduler"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.task_manager = get_task_manager()
        self.crawl_service = get_crawl_service()
        self._is_running = False
        self._stats = {"total_executed": 0, "total_failed": 0}
    
    async def start(self):
        """启动调度器"""
        if self._is_running:
            logger.warning("调度器已在运行")
            return
        
        try:
            logger.info("启动任务调度器...")
            
            # 配置SQLAlchemy JobStore
            settings = get_settings()
            jobstore = SQLAlchemyJobStore(url=settings.DATABASE_URL, tablename='apscheduler_jobs')
            
            self.scheduler = AsyncIOScheduler(
                jobstores={'default': jobstore},
                timezone=utc
            )
            
            # 添加事件监听
            self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
            
            self.scheduler.start()
            
            # 配置定时任务
            self._setup_scheduled_jobs()
            
            self._is_running = True
            logger.info("任务调度器启动成功")
            
        except Exception as e:
            logger.error(f"调度器启动失败: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """停止调度器"""
        if not self._is_running:
            return
        
        try:
            logger.info("停止任务调度器...")
            
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
                self.scheduler = None
            
            self._is_running = False
            logger.info("任务调度器已停止")
            
        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
    
    def _setup_scheduled_jobs(self):
        """配置定时任务"""
        try:
            scheduled_configs = self.task_manager.get_scheduled_configs()
            
            for config in scheduled_configs:
                self.scheduler.add_job(
                    func=self._execute_crawl,
                    trigger=CronTrigger(timezone=utc, **config.get_cron_config()),
                    args=[config.id],
                    id=f"scheduled_{config.id}",
                    max_instances=1,
                    replace_existing=True
                )
                
                logger.info(f"配置定时任务: {config.name} ({config.frequency})")
            
            logger.info(f"配置了 {len(scheduled_configs)} 个定时任务")
            
        except Exception as e:
            logger.error(f"配置定时任务失败: {e}")
    
    async def _execute_crawl(self, task_id: str):
        """执行爬取任务"""
        try:
            logger.info(f"开始执行定时爬取: {task_id}")
            
            # 直接执行爬取 - APScheduler负责调度管理
            result = await self.crawl_service.crawl_and_save(task_id)
            
            if result.get('success'):
                logger.info(f"定时爬取成功: {task_id}, 抓取 {result.get('total_books', 0)} 条")
            else:
                logger.warning(f"定时爬取失败: {task_id}, 错误: {result.get('error', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"定时爬取异常 ({task_id}): {e}")
    
    def trigger_manual_crawl(self, task_id: str) -> str:
        """手动触发爬取"""
        if not self.scheduler or not self._is_running:
            # 如果调度器未启动，直接执行爬取
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在async上下文中，创建任务
                asyncio.create_task(self._execute_crawl(task_id))
            else:
                # 否则直接运行
                asyncio.run(self._execute_crawl(task_id))
            
            job_id = f"direct_{task_id}_{datetime.now().strftime('%H%M%S')}"
            logger.info(f"直接执行任务: {job_id}")
            return job_id
        
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
        logger.info(f"任务执行成功: {event.job_id}")
    
    def _on_job_error(self, event):
        """任务执行失败回调"""
        self._stats['total_executed'] += 1
        self._stats['total_failed'] += 1
        logger.error(f"任务执行失败: {event.job_id}, 错误: {event.exception}")
    
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
_task_scheduler = None


def get_task_scheduler() -> TaskScheduler:
    """获取任务调度器实例"""
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler()
    return _task_scheduler


# 便捷函数
async def start_scheduler():
    """启动调度器"""
    await get_task_scheduler().start()


async def stop_scheduler():
    """停止调度器"""
    await get_task_scheduler().stop()


def trigger_manual_crawl(task_id: str) -> str:
    """手动触发爬取"""
    return get_task_scheduler().trigger_manual_crawl(task_id)