"""
任务处理器
"""
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from .context import JobContext
from .result import JobResult


class BaseJobHandler(ABC):
    """任务处理器基类"""
    
    def __init__(self, scheduler=None):
        self.scheduler = scheduler
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def execute(self, context: JobContext) -> JobResult:
        """执行任务（子类必须实现）"""
        pass
    
    async def execute_with_retry(self, context: JobContext) -> JobResult:
        """带重试机制的任务执行"""
        start_time = time.time()
        last_exception = None
        
        for attempt in range(context.max_retries + 1):
            context.retry_count = attempt
            
            try:
                self.logger.info(f"开始执行任务 {context.job_id}，第 {attempt + 1} 次尝试")
                
                # 执行任务
                result = await self.execute(context)
                
                # 记录执行时间
                result.execution_time = time.time() - start_time
                result.retry_count = attempt
                
                if result.success:
                    # 执行成功
                    await self.on_success(context, result)
                    self.logger.info(f"任务 {context.job_id} 执行成功")
                    return result
                else:
                    # 执行失败，但没有异常
                    last_exception = result.exception
                    if attempt < context.max_retries and self.should_retry(last_exception, attempt):
                        await self.on_retry(context, attempt + 1)
                        continue
                    else:
                        await self.on_failure(context, last_exception)
                        return result
                        
            except Exception as e:
                last_exception = e
                self.logger.error(f"任务 {context.job_id} 执行异常 (尝试 {attempt + 1}): {e}")
                
                # 判断是否需要重试
                if attempt < context.max_retries and self.should_retry(e, attempt):
                    await self.on_retry(context, attempt + 1)
                    
                    # 计算重试延迟
                    retry_delay = self.get_retry_delay(attempt + 1)
                    if retry_delay > 0:
                        await asyncio.sleep(retry_delay)
                    
                    continue
                else:
                    # 达到最大重试次数或不应重试
                    break
        
        # 所有重试都失败了
        result = JobResult.error_result(
            f"任务执行失败，已重试 {context.max_retries} 次",
            last_exception
        )
        result.execution_time = time.time() - start_time
        result.retry_count = context.max_retries
        
        await self.on_failure(context, last_exception)
        return result
    
    async def on_success(self, context: JobContext, result: JobResult) -> None:
        """任务执行成功时的回调"""
        self.logger.debug(f"任务 {context.job_id} 执行成功: {result.message}")
    
    async def on_failure(self, context: JobContext, exception: Optional[Exception]) -> None:
        """任务执行失败时的回调"""
        self.logger.error(f"任务 {context.job_id} 执行失败: {exception}")
    
    async def on_retry(self, context: JobContext, attempt: int) -> None:
        """任务重试时的回调"""
        self.logger.warning(f"任务 {context.job_id} 将进行第 {attempt} 次重试")
    
    def should_retry(self, exception: Optional[Exception], attempt: int) -> bool:
        """判断是否应该重试"""
        if exception is None:
            return False
        
        retryable_exceptions = (
            ConnectionError,
            TimeoutError,
        )
        
        return isinstance(exception, retryable_exceptions)
    
    def get_retry_delay(self, attempt: int) -> int:
        """获取重试延迟时间（秒）"""
        # 指数退避策略：1, 2, 4, 8, ... 秒，最大60秒
        delay = min(2 ** (attempt - 1), 60)
        return delay


class CrawlJobHandler(BaseJobHandler):
    """爬虫任务处理器"""
    
    async def execute(self, context: JobContext) -> JobResult:
        """执行爬虫任务"""
        try:
            job_type = context.job_data.get('type', 'unknown')
            task_id = context.job_data.get('task_id', context.job_id)
            
            # 导入实际的爬虫管理器
            from app.crawl.manager import CrawlerManager
            crawler_manager = CrawlerManager()
            
            try:
                if job_type == 'jiazi':
                    # 执行夹子榜爬取任务
                    results = await crawler_manager.crawl_tasks_by_category('jiazi')
                    crawled_count = sum(r.get('books_crawled', 0) for r in results if r.get('success'))
                    
                    # 更新任务状态
                    await self._update_task_status(task_id, "completed", f"夹子榜爬取完成，共爬取 {crawled_count} 本书籍")
                    
                    return JobResult.success_result(f"夹子榜爬取完成", {"crawled_count": crawled_count, "task_id": task_id})
                    
                elif job_type == 'category':
                    # 执行分类榜单爬取任务
                    results = await crawler_manager.crawl_all_tasks()
                    crawled_count = sum(r.get('books_crawled', 0) for r in results if r.get('success'))
                    
                    # 更新任务状态
                    await self._update_task_status(task_id, "completed", f"分类榜单爬取完成，共爬取 {crawled_count} 本书籍")
                    
                    return JobResult.success_result(f"分类榜单爬取完成", {"crawled_count": crawled_count, "task_id": task_id})
                    
                elif job_type == 'pages':
                    # 执行指定页面爬取任务
                    page_ids = context.job_data.get('page_ids', [])
                    if not page_ids:
                        return JobResult.error_result("页面ID列表为空")
                    
                    # 执行指定页面爬取
                    results = await crawler_manager.crawl(page_ids)
                    crawled_count = sum(r.get('books_crawled', 0) for r in results if r.get('success'))
                    
                    # 更新任务状态
                    await self._update_task_status(task_id, "completed", f"指定页面爬取完成，共爬取 {crawled_count} 本书籍")
                    
                    return JobResult.success_result(f"指定页面爬取完成", {"crawled_count": crawled_count, "page_ids": page_ids, "task_id": task_id})
                    
                else:
                    await self._update_task_status(task_id, "failed", f"未知的爬虫任务类型: {job_type}")
                    return JobResult.error_result(f"未知的爬虫任务类型: {job_type}")
                    
            finally:
                # 确保关闭爬虫管理器
                await crawler_manager.close()
                
        except Exception as e:
            # 更新任务状态为失败
            task_id = context.job_data.get('task_id', context.job_id)
            await self._update_task_status(task_id, "failed", f"爬虫任务执行失败: {str(e)}")
            return JobResult.error_result(f"爬虫任务执行失败: {str(e)}", e)
    
    async def _update_task_status(self, task_id: str, status: str, message: str):
        """更新任务状态到数据库"""
        try:
            from app.database.async_connection import get_session
            from app.database.service.crawl_task_service import CrawlTaskService
            
            # 使用异步上下文管理器获取数据库会话
            async for session in get_session():
                try:
                    task_service = CrawlTaskService(session)
                    await task_service.update_task_status(task_id, status, message)
                    self.logger.info(f"任务 {task_id} 状态更新为: {status}")
                    break  # 只使用第一个会话
                except Exception as e:
                    self.logger.error(f"更新任务状态失败 {task_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"获取数据库会话失败: {e}")


class MaintenanceJobHandler(BaseJobHandler):
    """维护任务处理器"""
    
    async def execute(self, context: JobContext) -> JobResult:
        """执行维护任务"""
        try:
            job_type = context.job_data.get('type', 'unknown')
            
            if job_type == 'database_cleanup':
                # 执行数据库清理
                await asyncio.sleep(0.5)  # 模拟任务执行
                return JobResult.success_result("数据库清理完成", {"cleaned_records": 1000})
                
            elif job_type == 'log_rotation':
                # 执行日志轮转
                await asyncio.sleep(0.5)  # 模拟任务执行
                return JobResult.success_result("日志轮转完成", {"rotated_files": 5})
                
            elif job_type == 'health_check':
                # 执行健康检查
                await asyncio.sleep(0.3)  # 模拟任务执行
                return JobResult.success_result("系统健康检查完成", {"status": "healthy"})
                
            else:
                return JobResult.error_result(f"未知的维护任务类型: {job_type}")
                
        except Exception as e:
            return JobResult.error_result(f"维护任务执行失败: {str(e)}", e)


class ReportJobHandler(BaseJobHandler):
    """报告任务处理器"""
    
    async def execute(self, context: JobContext) -> JobResult:
        """执行报告任务"""
        try:
            job_type = context.job_data.get('type', 'unknown')
            
            if job_type == 'data_analysis':
                # 执行数据分析报告
                await asyncio.sleep(3)  # 模拟任务执行
                return JobResult.success_result("数据分析报告生成完成", {"report_size": "2.5MB"})
                
            else:
                return JobResult.error_result(f"未知的报告任务类型: {job_type}")
                
        except Exception as e:
            return JobResult.error_result(f"报告任务执行失败: {str(e)}", e)