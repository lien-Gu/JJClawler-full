"""
任务处理器 - 重构为专注于任务执行，不处理调度状态管理

本模块的处理器类只负责执行具体的业务逻辑，状态管理由Scheduler通过事件系统处理。
这样设计实现了关注点分离和松耦合架构。
"""

from abc import ABC, abstractmethod

from app.config import get_settings
from app.crawl_config import CrawlConfig
from app.crawl.crawl_flow import CrawlFlow
from app.logger import get_logger
from app.models.schedule import JobResultModel


class BaseJobHandler(ABC):
    """任务处理器基类
    
    重构后的处理器专注于任务执行逻辑，不再处理调度状态管理。
    状态管理由Scheduler通过事件系统统一处理。
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.settings = get_settings()


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
    """爬虫任务处理器
    
    重构后专注于爬虫业务逻辑执行，支持单页面和多页面任务。
    重试机制和状态管理由Scheduler通过事件系统处理。
    """

    def __init__(self):
        super().__init__()
        self.config = CrawlConfig()

    async def execute(self, page_ids: list[str] = None) -> JobResultModel:
        """
        执行爬虫任务（支持单页面和多页面）

        Args:
            page_ids: 页面列表

        Returns:
            JobResultModel: 任务执行结果
        """
        if not page_ids:
            return JobResultModel.error_result("任务数据为空")

        # 处理单页面任务
        if len(page_ids) == 1:
            return await self._execute_single_page(page_ids[0])
        
        # 处理多页面任务
        return await self._execute_multiple_pages(page_ids)

    async def _execute_single_page(self, page_id: str) -> JobResultModel:
        """执行单个页面的爬取任务"""
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
                    rankings_crawled = crawl_result.get("rankings_crawled", 0)
                    
                    self.logger.info(
                        f"页面 {page_id} 爬取成功，共爬取 {books_crawled} 本书籍，{rankings_crawled} 个榜单"
                    )

                    return JobResultModel.success_result(
                        f"页面 {page_id} 爬取成功，共爬取 {books_crawled} 本书籍",
                        {
                            "page_id": page_id,
                            "books_crawled": books_crawled,
                            "rankings_crawled": rankings_crawled,
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

    async def _execute_multiple_pages(self, page_ids: list[str]) -> JobResultModel:
        """执行多个页面的爬取任务"""
        total_books = 0
        total_rankings = 0
        success_pages = []
        failed_pages = []
        
        for page_id in page_ids:
            try:
                result = await self._execute_single_page(page_id)
                if result.success:
                    success_pages.append(page_id)
                    if result.data:
                        total_books += result.data.get("books_crawled", 0)
                        total_rankings += result.data.get("rankings_crawled", 0)
                else:
                    failed_pages.append(page_id)
            except Exception as e:
                self.logger.error(f"页面 {page_id} 处理异常: {e}")
                failed_pages.append(page_id)
        
        # 汇总结果
        success_count = len(success_pages)
        total_count = len(page_ids)
        
        if success_count == total_count:
            return JobResultModel.success_result(
                f"多页面爬取完全成功: {success_count}/{total_count} 页面，共 {total_books} 本书籍，{total_rankings} 个榜单",
                {
                    "total_pages": total_count,
                    "success_pages": success_pages,
                    "failed_pages": failed_pages,
                    "total_books": total_books,
                    "total_rankings": total_rankings
                }
            )
        elif success_count > 0:
            return JobResultModel.success_result(
                f"多页面爬取部分成功: {success_count}/{total_count} 页面，共 {total_books} 本书籍，{total_rankings} 个榜单",
                {
                    "total_pages": total_count,
                    "success_pages": success_pages,
                    "failed_pages": failed_pages,
                    "total_books": total_books,
                    "total_rankings": total_rankings
                }
            )
        else:
            return JobResultModel.error_result(
                f"多页面爬取全部失败: 0/{total_count} 页面成功",
                None
            )


class ReportJobHandler(BaseJobHandler):
    """报告任务处理器
    
    重构后专注于报告生成逻辑，暂时不实现具体功能。
    """

    def __init__(self):
        super().__init__()
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
