"""
任务处理器 - 重构后的简化版本
"""
import asyncio
import logging
import time

from app.config import get_settings
from app.crawl.single_crawler import SinglePageCrawler
from app.models.schedule import JobContextModel, JobResultModel


class CrawlJobHandler:
    """爬虫任务处理器 - 只处理单个页面爬取（重构后）"""

    def __init__(self, scheduler=None):
        self.scheduler = scheduler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.settings = get_settings()
        self.max_retries = self.settings.crawler.retry_times

    async def execute_with_retry(self, context: JobContextModel, job_data: dict = None) -> JobResultModel:
        """带重试机制的任务执行"""
        start_time = time.time()
        last_exception = None

        # max_retries=3 表示最多重试3次: 1次初始执行 + 3次重试 = 总共4次尝试
        # attempt: 0=初始执行, 1-3=重试
        for attempt in range(self.max_retries + 1):
            try:
                if attempt == 0:
                    self.logger.info(f"开始执行任务 {context.job_id}")
                else:
                    self.logger.info(f"开始重试任务 {context.job_id}，第 {attempt} 次重试")

                # 执行任务
                result = await self.execute(context, job_data)

                # 记录执行时间
                result.execution_time = time.time() - start_time

                if result.success:
                    # 执行成功
                    self.logger.info(f"任务 {context.job_id} 执行成功: {result.message}")
                    return result
                else:
                    # 执行失败，但没有异常
                    last_exception = result.exception
                    if attempt < self.max_retries:
                        self.logger.warning(f"任务 {context.job_id} 将进行第 {attempt + 1} 次重试")
                        continue
                    else:
                        self.logger.error(f"任务 {context.job_id} 执行失败: {last_exception}")
                        return result

            except Exception as e:
                last_exception = e
                self.logger.error(f"任务 {context.job_id} 执行异常 (尝试 {attempt + 1}): {e}")

                # 判断是否需要重试
                if attempt < self.max_retries:
                    self.logger.warning(f"任务 {context.job_id} 将进行第 {attempt + 1} 次重试")
                    
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

        self.logger.error(f"任务 {context.job_id} 执行失败: {last_exception}")
        return result

    async def execute(self, context: JobContextModel, job_data: dict = None) -> JobResultModel:
        """
        执行单个页面爬虫任务（重构后）
        
        Args:
            context: 任务上下文
            job_data: 任务数据，应包含 page_id 字段
            
        Returns:
            JobResultModel: 任务执行结果
        """
        crawler = None
        try:
            if job_data is None:
                return JobResultModel.error_result("任务数据为空")

            page_id = job_data.get('page_id')
            if not page_id:
                return JobResultModel.error_result("缺少页面ID (page_id)")

            # 创建单页面爬虫
            crawler = SinglePageCrawler()

            # 执行单页面爬取
            result = await crawler.crawl_page(page_id)

            if result.get('success', False):
                books_crawled = result.get('books_crawled', 0)
                execution_time = result.get('execution_time', 0)
                
                return JobResultModel.success_result(
                    f"页面 {page_id} 爬取完成，爬取书籍 {books_crawled} 本",
                    {
                        "page_id": page_id,
                        "books_crawled": books_crawled,
                        "execution_time": execution_time
                    }
                )
            else:
                error_msg = result.get('error_message', '未知错误')
                return JobResultModel.error_result(f"页面 {page_id} 爬取失败: {error_msg}")

        except Exception as e:
            return JobResultModel.error_result(f"爬虫任务执行异常: {str(e)}", e)
        finally:
            # 确保关闭爬虫资源
            if crawler:
                try:
                    await crawler.close()
                except Exception as e:
                    self.logger.warning(f"关闭爬虫资源失败: {e}")


# 为了保持向后兼容，保留BaseJobHandler别名
BaseJobHandler = CrawlJobHandler