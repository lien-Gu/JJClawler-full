"""
调度器服务模块 - T4.3任务调度器集成实现

使用APScheduler 3.x AsyncIOScheduler实现定时爬取功能，完善任务管理系统：
- 集成AsyncIOScheduler到FastAPI应用
- 实现定时任务配置（夹子榜每小时，其他榜单每日）
- 实现任务重试和错误处理机制
- 完善任务状态监控和日志记录

设计原则：
1. 异步优先：使用AsyncIOScheduler适配FastAPI异步架构
2. 资源管理：正确的生命周期管理和资源清理
3. 错误恢复：完善的错误处理和重试机制
4. 监控完备：详细的日志记录和状态监控
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from contextlib import asynccontextmanager

# 使用成熟的APScheduler 3.x库
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED
from pytz import utc

from app.modules.service.crawler_service import CrawlerService
from app.modules.service.task_service import get_task_manager, TaskType
from app.modules.service.page_service import get_page_service
from app.utils.log_utils import get_logger

logger = get_logger(__name__)


class SchedulerService:
    """
    调度器服务类
    
    集成APScheduler实现自动化任务调度：
    - 定时爬取任务管理
    - 任务状态监控
    - 错误处理和重试
    - 资源生命周期管理
    """
    
    def __init__(self):
        """初始化调度器服务"""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.crawler_service = None
        self.task_manager = get_task_manager()
        self.page_service = get_page_service()
        self._is_running = False
        self._startup_complete = False
        
        # 任务统计
        self._job_stats = {
            'total_executed': 0,
            'total_failed': 0,
            'total_succeeded': 0,
            'last_execution': None
        }
    
    async def start(self) -> None:
        """
        启动调度器服务
        
        初始化AsyncIOScheduler并配置所有定时任务
        """
        if self._is_running:
            logger.warning("调度器已在运行中")
            return
        
        try:
            logger.info("正在启动调度器服务...")
            
            # 初始化AsyncIOScheduler
            self.scheduler = AsyncIOScheduler(timezone=utc)
            
            # 订阅调度器事件
            self._setup_event_listeners()
            
            # 启动调度器
            self.scheduler.start()
            
            # 配置定时任务
            self._configure_scheduled_jobs()
            
            self._is_running = True
            self._startup_complete = True
            
            logger.info("调度器服务启动成功")
            
        except Exception as e:
            logger.error(f"调度器服务启动失败: {e}")
            self.stop()
            raise
    
    def stop(self) -> None:
        """
        停止调度器服务
        
        清理资源并优雅关闭
        """
        if not self._is_running:
            return
        
        try:
            logger.info("正在停止调度器服务...")
            
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
                self.scheduler = None
            
            if self.crawler_service:
                self.crawler_service.close()
                self.crawler_service = None
            
            self._is_running = False
            logger.info("调度器服务已停止")
            
        except Exception as e:
            logger.error(f"停止调度器服务时出错: {e}")
    
    def _setup_event_listeners(self) -> None:
        """设置事件监听器"""
        
        def job_executed_listener(event):
            """任务执行成功事件监听器"""
            logger.info(f"任务执行成功: {event.job_id}")
            self._job_stats['total_executed'] += 1
            self._job_stats['total_succeeded'] += 1
            self._job_stats['last_execution'] = datetime.now()
        
        def job_error_listener(event):
            """任务执行错误事件监听器"""
            logger.error(f"任务执行失败: {event.job_id}, 错误: {event.exception}")
            self._job_stats['total_executed'] += 1
            self._job_stats['total_failed'] += 1
            self._job_stats['last_execution'] = datetime.now()
        
        def job_added_listener(event):
            """任务添加事件监听器"""
            logger.info(f"任务已添加: {event.job_id}")
        
        # 订阅事件
        self.scheduler.add_listener(job_executed_listener, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)
        self.scheduler.add_listener(job_added_listener, EVENT_JOB_ADDED)
    
    def _configure_scheduled_jobs(self) -> None:
        """配置所有定时任务"""
        
        # 配置夹子榜定时任务（每小时）
        self.scheduler.add_job(
            func=self._execute_jiazi_crawl,
            trigger=CronTrigger(minute=0),  # 每小时整点执行
            id="jiazi_hourly",
            max_instances=1,  # 防止重复执行
            misfire_grace_time=300,  # 5分钟容错时间
            replace_existing=True
        )
        
        # 配置分类页面定时任务（每日）
        self._configure_daily_crawl_jobs()
        
        # 配置任务清理定时任务（每周）
        self.scheduler.add_job(
            func=self._cleanup_old_tasks,
            trigger=CronTrigger(day_of_week=0, hour=2),  # 每周日凌晨2点
            id="task_cleanup_weekly",
            max_instances=1,
            replace_existing=True
        )
        
        logger.info("定时任务配置完成")
    
    def _configure_daily_crawl_jobs(self) -> None:
        """配置每日爬取任务"""
        try:
            # 获取所有可用频道
            channels = self.page_service.get_ranking_channels()
            
            for i, channel_info in enumerate(channels):
                channel = channel_info['channel']
                if channel == 'jiazi':  # 夹子榜已单独配置
                    continue
                
                # 错开执行时间，避免同时爬取
                hour = 1 + (i % 6)  # 分布在1-6点
                minute = (i * 10) % 60  # 错开分钟
                
                self.scheduler.add_job(
                    func=self._execute_page_crawl,
                    trigger=CronTrigger(hour=hour, minute=minute),
                    args=[channel],
                    id=f"page_daily_{channel}",
                    max_instances=1,
                    misfire_grace_time=1800,  # 30分钟容错时间
                    replace_existing=True
                )
            
            logger.info(f"配置了 {len(channels)-1} 个每日爬取任务")
            
        except Exception as e:
            logger.error(f"配置每日爬取任务失败: {e}")
    
    async def _execute_jiazi_crawl(self) -> None:
        """执行夹子榜爬取任务"""
        task_id = None
        
        try:
            logger.info("开始执行夹子榜定时爬取")
            
            # 创建任务记录
            task_id = self.task_manager.create_task(
                TaskType.JIAZI,
                metadata={"trigger_source": "scheduled", "job_id": "jiazi_hourly"}
            )
            
            # 执行爬取
            crawler_service = CrawlerService()
            result = await crawler_service.crawl_and_save_jiazi()
            
            # 完成任务
            self.task_manager.complete_task(
                task_id, 
                items_crawled=result.get('books_new', 0) + result.get('books_updated', 0),
                metadata=result
            )
            
            self._job_stats['total_succeeded'] += 1
            logger.info(f"夹子榜定时爬取完成: {result}")
            
        except Exception as e:
            self._job_stats['total_failed'] += 1
            error_msg = f"夹子榜定时爬取失败: {e}"
            logger.error(error_msg)
            
            if task_id:
                self.task_manager.fail_task(task_id, str(e))
            
            # 重试逻辑
            await self._handle_crawl_error("jiazi", e)
        
        finally:
            if 'crawler_service' in locals():
                crawler_service.close()
    
    async def _execute_page_crawl(self, channel: str) -> None:
        """执行分类页面爬取任务"""
        task_id = None
        
        try:
            logger.info(f"开始执行分类页面定时爬取: {channel}")
            
            # 创建任务记录
            task_id = self.task_manager.create_task(
                TaskType.PAGE,
                metadata={
                    "trigger_source": "scheduled", 
                    "channel": channel,
                    "job_id": f"page_daily_{channel}"
                }
            )
            
            # 执行爬取
            crawler_service = CrawlerService()
            result = await crawler_service.crawl_and_save_page(channel)
            
            # 完成任务
            self.task_manager.complete_task(
                task_id,
                items_crawled=result.get('books_new', 0) + result.get('books_updated', 0),
                metadata=result
            )
            
            self._job_stats['total_succeeded'] += 1
            logger.info(f"分类页面定时爬取完成 ({channel}): {result}")
            
        except Exception as e:
            self._job_stats['total_failed'] += 1
            error_msg = f"分类页面定时爬取失败 ({channel}): {e}"
            logger.error(error_msg)
            
            if task_id:
                self.task_manager.fail_task(task_id, str(e))
            
            # 重试逻辑
            await self._handle_crawl_error(channel, e)
        
        finally:
            if 'crawler_service' in locals():
                crawler_service.close()
    
    def _cleanup_old_tasks(self) -> None:
        """清理旧任务记录"""
        try:
            logger.info("开始清理旧任务记录")
            
            # 清理7天前的任务
            self.task_manager.cleanup_old_tasks(days=7)
            
            logger.info("旧任务记录清理完成")
            
        except Exception as e:
            logger.error(f"清理旧任务记录失败: {e}")
    
    async def _handle_crawl_error(self, target: str, error: Exception) -> None:
        """
        处理爬取错误
        
        Args:
            target: 爬取目标（jiazi或频道名）
            error: 错误信息
        """
        # 这里可以实现重试逻辑
        # 例如：网络错误可以短时间后重试，其他错误记录日志
        error_type = type(error).__name__
        
        if "network" in str(error).lower() or "timeout" in str(error).lower():
            # 网络错误，可以考虑重试
            logger.warning(f"网络错误，暂不重试: {target} - {error}")
        else:
            # 其他错误，记录详细日志
            logger.error(f"爬取错误，需要人工检查: {target} - {error}")
    
    def add_manual_job(self, job_func: Callable, *args, **kwargs) -> str:
        """
        添加手动任务
        
        Args:
            job_func: 任务函数
            *args, **kwargs: 任务参数
            
        Returns:
            任务ID
        """
        if not self.scheduler:
            raise RuntimeError("调度器未启动")
        
        # 生成唯一任务ID
        job_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 添加一次性任务
        self.scheduler.add_job(
            func=job_func,
            trigger='date',  # 立即执行
            run_date=datetime.now(),
            args=args,
            kwargs=kwargs,
            id=job_id,
            max_instances=1,
            replace_existing=True
        )
        
        logger.info(f"添加手动任务: {job_id}")
        return job_id
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        return {
            **self._job_stats,
            'is_running': self._is_running,
            'startup_complete': self._startup_complete,
            'active_jobs': len(self.scheduler.get_jobs()) if self.scheduler else 0
        }
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """获取所有定时任务信息"""
        if not self.scheduler:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'func_ref': str(job.func_ref),
                'max_instances': job.max_instances,
                'misfire_grace_time': job.misfire_grace_time
            })
        
        return jobs
    
    def trigger_manual_crawl(self, target: str) -> str:
        """
        手动触发爬取任务
        
        Args:
            target: 爬取目标（"jiazi"或频道名）
            
        Returns:
            任务ID
        """
        if target == "jiazi":
            return self.add_manual_job(self._execute_jiazi_crawl)
        else:
            return self.add_manual_job(self._execute_page_crawl, target)


# 全局调度器服务实例
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    """
    获取全局调度器服务实例
    
    Returns:
        SchedulerService: 调度器服务实例
    """
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service


@asynccontextmanager
async def scheduler_lifespan():
    """
    调度器生命周期管理器
    
    用于FastAPI应用的lifespan事件
    """
    scheduler_service = await get_scheduler_service()
    try:
        await scheduler_service.start()
        yield scheduler_service
    finally:
        await scheduler_service.stop()


# 便捷函数
async def start_scheduler() -> None:
    """启动调度器服务"""
    scheduler_service = get_scheduler_service()
    await scheduler_service.start()


def stop_scheduler() -> None:
    """停止调度器服务"""
    scheduler_service = get_scheduler_service()
    scheduler_service.stop()


def get_scheduler_stats() -> Dict[str, Any]:
    """获取调度器统计信息"""
    scheduler_service = get_scheduler_service()
    return scheduler_service.get_job_statistics()


def trigger_manual_crawl(target: str) -> str:
    """手动触发爬取任务"""
    scheduler_service = get_scheduler_service()
    return scheduler_service.trigger_manual_crawl(target)