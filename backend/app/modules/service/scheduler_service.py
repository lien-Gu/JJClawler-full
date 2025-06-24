"""
调度器服务 - 简化版本

使用APScheduler实现定时爬取功能：
- 集成AsyncIOScheduler到FastAPI应用
- 实现定时任务配置（夹子榜每小时，其他榜单每日）
- 简化的错误处理和任务状态监控
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from pytz import utc

from app.modules.service.crawler_service import CrawlerService
from app.modules.service.task_service import get_task_manager, TaskType, execute_with_task
from app.modules.service.page_service import get_page_service
from app.utils.log_utils import get_logger

logger = get_logger(__name__)


class SchedulerService:
    """简化的调度器服务"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.task_manager = get_task_manager()
        self.page_service = get_page_service()
        self._is_running = False
        self._stats = {"total_executed": 0, "total_failed": 0}
    
    async def start(self):
        """启动调度器"""
        if self._is_running:
            logger.warning("调度器已在运行中")
            return
        
        try:
            logger.info("启动调度器服务...")
            
            # 初始化调度器
            self.scheduler = AsyncIOScheduler(timezone=utc)
            
            # 设置事件监听
            self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
            
            # 启动调度器
            self.scheduler.start()
            
            # 配置定时任务
            self._setup_jobs()
            
            self._is_running = True
            logger.info("调度器服务启动成功")
            
        except Exception as e:
            logger.error(f"调度器启动失败: {e}")
            self.stop()
            raise
    
    def stop(self):
        """停止调度器"""
        if not self._is_running:
            return
        
        try:
            logger.info("停止调度器服务...")
            
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
                self.scheduler = None
            
            self._is_running = False
            logger.info("调度器服务已停止")
            
        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
    
    def _setup_jobs(self):
        """配置定时任务"""
        # 夹子榜每小时
        self.scheduler.add_job(
            func=self._execute_jiazi_crawl,
            trigger=CronTrigger(minute=0),
            id="jiazi_hourly",
            max_instances=1,
            replace_existing=True
        )
        
        # 分类页面每日
        self._setup_daily_jobs()
        
        logger.info("定时任务配置完成")
    
    def _setup_daily_jobs(self):
        """配置每日爬取任务"""
        try:
            channels = self.page_service.get_ranking_channels()
            
            for i, channel_info in enumerate(channels):
                channel = channel_info['channel']
                if channel == 'jiazi':
                    continue
                
                # 错开执行时间
                hour = 1 + (i % 6)
                minute = (i * 10) % 60
                
                self.scheduler.add_job(
                    func=self._execute_page_crawl,
                    trigger=CronTrigger(hour=hour, minute=minute),
                    args=[channel],
                    id=f"page_daily_{channel}",
                    max_instances=1,
                    replace_existing=True
                )
            
            logger.info(f"配置了 {len(channels)-1} 个每日爬取任务")
            
        except Exception as e:
            logger.error(f"配置每日任务失败: {e}")
    
    async def _execute_jiazi_crawl(self):
        """执行夹子榜爬取"""
        try:
            task_id = self.task_manager.create_task(
                TaskType.JIAZI,
                {"trigger_source": "scheduled"}
            )
            
            logger.info("开始执行夹子榜定时爬取")
            
            async def crawl_func():
                crawler_service = CrawlerService()
                try:
                    return await crawler_service.crawl_and_save_jiazi()
                finally:
                    crawler_service.close()
            
            await execute_with_task(task_id, crawl_func)
            
        except Exception as e:
            logger.error(f"夹子榜定时爬取失败: {e}")
    
    async def _execute_page_crawl(self, channel: str):
        """执行分类页面爬取"""
        try:
            task_id = self.task_manager.create_task(
                TaskType.PAGE,
                {"trigger_source": "scheduled", "channel": channel}
            )
            
            logger.info(f"开始执行分类页面定时爬取: {channel}")
            
            async def crawl_func():
                crawler_service = CrawlerService()
                try:
                    return await crawler_service.crawl_and_save_page(channel)
                finally:
                    crawler_service.close()
            
            await execute_with_task(task_id, crawl_func)
            
        except Exception as e:
            logger.error(f"分类页面定时爬取失败 ({channel}): {e}")
    
    def _on_job_executed(self, event):
        """任务执行成功回调"""
        self._stats['total_executed'] += 1
        logger.info(f"定时任务执行成功: {event.job_id}")
    
    def _on_job_error(self, event):
        """任务执行失败回调"""
        self._stats['total_executed'] += 1
        self._stats['total_failed'] += 1
        logger.error(f"定时任务执行失败: {event.job_id}, 错误: {event.exception}")
    
    def trigger_manual_crawl(self, target: str) -> str:
        """手动触发爬取任务"""
        if not self.scheduler:
            raise RuntimeError("调度器未启动")
        
        job_id = f"manual_{target}_{datetime.now().strftime('%H%M%S')}"
        
        if target == "jiazi":
            func = self._execute_jiazi_crawl
            args = []
        else:
            func = self._execute_page_crawl
            args = [target]
        
        self.scheduler.add_job(
            func=func,
            trigger='date',
            run_date=datetime.now(),
            args=args,
            id=job_id,
            max_instances=1
        )
        
        logger.info(f"添加手动任务: {job_id}")
        return job_id
    
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
    scheduler_service = get_scheduler_service()
    await scheduler_service.start()


def stop_scheduler():
    """停止调度器"""
    scheduler_service = get_scheduler_service()
    scheduler_service.stop()


def trigger_manual_crawl(target: str) -> str:
    """手动触发爬取"""
    scheduler_service = get_scheduler_service()
    return scheduler_service.trigger_manual_crawl(target)


def get_scheduler_stats() -> Dict[str, Any]:
    """获取调度器统计信息"""
    scheduler_service = get_scheduler_service()
    return {
        "status": scheduler_service.get_status(),
        "jobs": scheduler_service.get_scheduled_jobs(),
        "task_summary": get_task_manager().get_task_summary()
    }