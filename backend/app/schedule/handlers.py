"""
任务处理器 - 重构后负责多页面管理和调用爬虫模块
"""
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from app.config import get_settings
from app.crawl.base import CrawlConfig
from app.crawl.crawl_flow import CrawlFlow
from app.models.schedule import JobContextModel, JobResultModel


class BaseJobHandler(ABC):
    """任务处理器基类"""
    
    def __init__(self, scheduler=None):
        self.scheduler = scheduler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.settings = get_settings()
        self.max_retries = self.settings.crawler.retry_times
    
    async def execute_with_retry(self, context: JobContextModel, page_ids: List = None) -> JobResultModel:
        """带重试机制的任务执行"""
        start_time = time.time()
        last_exception = None
        job_id = context.job_id

        # max_retries=3 表示最多重试3次: 1次初始执行 + 3次重试 = 总共4次尝试
        for attempt in range(self.max_retries + 1):
            try:
                if attempt == 0:
                    self.logger.info(f"开始执行任务 {job_id}")
                else:
                    self.logger.info(f"开始重试任务 {job_id}，第 {attempt} 次重试")

                # 执行任务
                result = await self.execute(page_ids)

                # 记录执行时间
                result.execution_time = time.time() - start_time

                if result.success:
                    # 执行成功
                    self.logger.info(f"任务 {job_id} 执行成功: {result.message}")
                    return result
                else:
                    # 执行失败，但没有异常
                    last_exception = result.exception
                    if attempt < self.max_retries:
                        self.logger.warning(f"任务 {job_id} 将进行第 {attempt + 1} 次重试")
                        continue
                    else:
                        self.logger.error(f"任务 {job_id} 执行失败: {last_exception}")
                        return result

            except Exception as e:
                last_exception = e
                self.logger.error(f"任务 {job_id} 执行异常 (尝试 {attempt + 1}): {e}")

                # 判断是否需要重试
                if attempt < self.max_retries:
                    self.logger.warning(f"任务 {job_id} 将进行第 {attempt + 1} 次重试")

                    # 重试延迟
                    retry_delay = self.settings.crawler.retry_delay
                    if retry_delay > 0:
                        await asyncio.sleep(retry_delay)
                    continue
                else:
                    # 达到最大重试次数
                    break

        # 所有重试都失败了
        result = JobResultModel.error_result(
            f"任务执行失败，已重试 {self.max_retries} 次",
            last_exception
        )
        result.execution_time = time.time() - start_time

        self.logger.error(f"任务 {job_id} 执行失败: {last_exception}")
        return result
    
    @abstractmethod
    async def execute(self, page_ids: List[str] = None) -> JobResultModel:
        """
        执行任务的抽象方法，子类必须实现
        
        Args:
            page_ids: 页面列表
            
        Returns:
            JobResultModel: 任务执行结果
        """
        pass


class CrawlJobHandler(BaseJobHandler):
    """爬虫任务处理器 - 重构后负责多页面管理"""

    def __init__(self, scheduler=None):
        super().__init__(scheduler)
        self.config = CrawlConfig()

    async def execute(self, page_ids: List[str] = None) -> JobResultModel:
        """
        执行爬虫任务（重构后支持多页面管理）
        
        Args:
            page_ids: 页面列表
                
        Returns:
            JobResultModel: 任务执行结果
        """
        if page_ids is None:
            return JobResultModel.error_result("任务数据为空")

        try:
            # 确定要爬取的页面列表
            page_ids = await self._determine_page_ids(page_ids)

            if not page_ids:
                return JobResultModel.error_result("没有找到需要爬取的页面")

            # 执行多页面爬取（调度模块负责并发控制）
            results = await self._crawl_multiple_pages(page_ids)

            # 统计结果
            total_pages = len(page_ids)
            successful_pages = len([r for r in results if r.get('success', False)])
            total_books = sum(r.get('books_crawled', 0) for r in results if r.get('success', False))

            if successful_pages > 0:
                return JobResultModel.success_result(
                    f"完成 {total_pages} 个页面爬取，成功 {successful_pages} 个，共爬取 {total_books} 本书籍",
                    {
                        "total_pages": total_pages,
                        "successful_pages": successful_pages,
                        "failed_pages": total_pages - successful_pages,
                        "total_books": total_books,
                        "results": results
                    }
                )
            else:
                return JobResultModel.error_result(f"所有 {total_pages} 个页面爬取都失败")

        except Exception as e:
            return JobResultModel.error_result(f"爬虫任务执行异常: {str(e)}", e)

    async def _determine_page_ids(self, page_ids: List[str]) -> List[str]:
        """
        根据任务数据确定需要爬取的页面ID列表
        
        Args:
            page_ids: 任务数据
            
        Returns:
            List[str]: 页面ID列表
        """
        # 特殊字符任务类型
        if len(page_ids) == 1 and page_ids[0] in ["all", "jiazi", "category"]:
            special_word = page_ids[0]
            if special_word == "jiazi":
                # 夹子榜任务
                return ["jiazi"]
            elif special_word == "category":
                # 所有分类任务
                return self._get_category_page_ids()
            else:
                return self._get_all_page_ids()
        return [pid for pid in page_ids if self._validate_page_id(pid)]


    def _get_category_page_ids(self) -> List[str]:
        """获取所有分类页面ID列表（排除夹子榜）"""
        all_tasks = self.config.get_all_tasks()
        category_ids = []
        
        for task in all_tasks:
            task_id = task.get('id', '')
            if not ('jiazi' in task_id.lower() or task.get('category') == 'jiazi'):
                category_ids.append(task_id)
        
        self.logger.info(f"找到分类页面 {len(category_ids)} 个")
        return category_ids

    def _get_all_page_ids(self) -> List[str]:
        """获取所欧页面id"""
        all_tasks = self.config.get_all_tasks()
        return [i.get("id") for i in all_tasks]

    def _validate_page_id(self, page_id: str) -> bool:
        """验证页面ID是否在配置中"""
        all_tasks = self.config.get_all_tasks()
        available_ids = {task.get('id', '') for task in all_tasks}
        return page_id in available_ids

    async def _crawl_multiple_pages(self, page_ids: List[str]) -> List[Dict[str, Any]]:
        """
        并发爬取多个页面（调度模块负责并发控制）

        Args:
            page_ids: 页面ID列表

        Returns:
            List[Dict[str, Any]]: 爬取结果列表
        """
        semaphore = asyncio.Semaphore(self.settings.scheduler.max_workers)

        async def crawl_single_page_with_semaphore(page_id: str) -> Dict[str, Any]:
            async with semaphore:
                crawler = CrawlFlow()
                try:
                    crawl_result = await crawler.execute_crawl_task(page_id)
                    return crawl_result
                finally:
                    await crawler.close()

        # 并发执行所有页面爬取
        tasks = [crawl_single_page_with_semaphore(page_id) for page_id in page_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "page_id": page_ids[i],
                    "books_crawled": 0,
                    "error_message": f"页面爬取异常: {str(result)}"
                })
            else:
                processed_results.append(result)

        return processed_results


class ReportJobHandler(BaseJobHandler):
    """报告任务处理器 - 暂时不实现具体功能"""

    def __init__(self, scheduler=None):
        super().__init__(scheduler)
        # 报告相关的配置可以在这里初始化
        
    async def execute(self, page_ids: List[str] = None) -> JobResultModel:
        """
        执行报告任务（暂时不实现）
        
        Args:
            page_ids: 页面列表（报告任务可能不需要这个参数）
            
        Returns:
            JobResultModel: 任务执行结果
        """
        # 暂时返回未实现的错误
        return JobResultModel.error_result("报告任务处理器暂时未实现")
