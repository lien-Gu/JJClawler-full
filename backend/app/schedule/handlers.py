"""
任务处理器 - 重构后负责多页面管理和调用爬虫模块
"""

import asyncio
import time
from abc import ABC, abstractmethod

from app.config import get_settings
from app.crawl_config import CrawlConfig
from app.crawl.crawl_flow import CrawlFlow
from app.logger import get_logger
from app.models.schedule import , JobResultModel


class BaseJobHandler(ABC):
    """任务处理器基类"""

    def __init__(self, scheduler=None):
        self.scheduler = scheduler
        self.logger = get_logger(self.__class__.__name__)
        self.settings = get_settings()
        self.max_retries = self.settings.crawler.retry_times

    async def execute_with_retry(
        self, job_id: str, page_ids: list = None
    ) -> JobResultModel:
        """带重试机制的任务执行"""
        start_time = time.time()
        last_exception = None

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
                        self.logger.warning(
                            f"任务 {job_id} 将进行第 {attempt + 1} 次重试"
                        )
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
            f"任务执行失败，已重试 {self.max_retries} 次", last_exception
        )
        result.execution_time = time.time() - start_time

        self.logger.error(f"任务 {job_id} 执行失败: {last_exception}")
        return result

    @abstractmethod
    async def execute(self, page_ids: list[str] = None) -> JobResultModel:
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

    async def execute(self, page_ids: list[str] = None) -> JobResultModel:
        """
        执行单页面爬虫任务（重构后只处理单个页面）

        Args:
            page_ids: 页面列表，应该只包含一个页面ID

        Returns:
            JobResultModel: 任务执行结果
        """
        if not page_ids:
            return JobResultModel.error_result("任务数据为空")

        if len(page_ids) != 1:
            return JobResultModel.error_result(
                f"单页面任务应该只包含一个页面ID，但收到了 {len(page_ids)} 个"
            )

        page_id = page_ids[0]

        try:
            # 验证页面ID是否有效
            if not self.config.validate_page_id(page_id):
                return JobResultModel.error_result(f"无效的页面ID: {page_id}")

            # 执行单页面爬取
            crawler = CrawlFlow()
            try:
                self.logger.info(f"开始爬取页面: {page_id}")
                crawl_result = await crawler.execute_crawl_task(page_id)

                if crawl_result.get("success", False):
                    books_crawled = crawl_result.get("books_crawled", 0)
                    self.logger.info(
                        f"页面 {page_id} 爬取成功，共爬取 {books_crawled} 本书籍"
                    )

                    return JobResultModel.success_result(
                        f"页面 {page_id} 爬取成功，共爬取 {books_crawled} 本书籍",
                        {
                            "page_id": page_id,
                            "books_crawled": books_crawled,
                            "crawl_result": crawl_result,
                        },
                    )
                else:
                    error_msg = crawl_result.get("error_message", "未知错误")
                    return JobResultModel.error_result(
                        f"页面 {page_id} 爬取失败: {error_msg}"
                    )

            finally:
                await crawler.close()

        except Exception as e:
            self.logger.error(f"页面 {page_id} 爬取异常: {str(e)}")
            return JobResultModel.error_result(f"页面 {page_id} 爬取异常: {str(e)}", e)


class ReportJobHandler(BaseJobHandler):
    """报告任务处理器 - 暂时不实现具体功能"""

    def __init__(self, scheduler=None):
        super().__init__(scheduler)
        # 报告相关的配置可以在这里初始化

    async def execute(self, page_ids: list[str] = None) -> JobResultModel:
        """
        执行报告任务（暂时不实现）

        Args:
            page_ids: 页面列表（报告任务可能不需要这个参数）

        Returns:
            JobResultModel: 任务执行结果
        """
        # 暂时返回未实现的错误
        return JobResultModel.error_result("报告任务处理器暂时未实现")
