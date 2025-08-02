"""
爬取流程管理器 - 高效的并发爬取架构
"""

import asyncio
import dataclasses
import itertools
import logging
import time
from typing import Dict, List, Tuple, Union

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.database.service.book_service import BookService
from app.database.service.ranking_service import RankingService
from app.logger import get_logger
from app.crawl_config import CrawlConfig
from app.config import get_settings
from .http import HttpClient
from .parser import NovelPageParser, PageParser, RankingParser
from .result_models import PageResult, PagesResult, BooksResult, SaveResult, TaskStats, CrawlTaskResult
from ..utils import generate_batch_id
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential, retry_if_exception, before_sleep, \
    before_sleep_log

logger = get_logger(__name__)


class CrawlFlow:
    """
    统一并发爬取流程管理器 - 两阶段处理架构
    
    阶段 1: 获取所有页面内容
    阶段 2: 获取所有书籍内容  
    全局统一并发控制
    """

    def __init__(self) -> None:
        """
        初始化爬取流程管理器
        """
        self.config = CrawlConfig()
        self.crawler_config = get_settings().crawler
        self.book_service = BookService()
        self.ranking_service = RankingService()
        self.client = HttpClient()

        # 统一并发控制 - 所有HTTP请求由此信号量管理
        self.request_semaphore = asyncio.Semaphore(self.crawler_config.max_concurrent_requests)

        # 统计信息 - 使用类型安全的数据类
        self.task_stats = TaskStats()

    async def execute_crawl_task(self, page_ids: List[str]) -> Tuple[bool, Dict]:
        """
        执行统一并发爬取任务 - 两阶段处理架构
        
        Args:
            page_ids: 页面ID或页面ID列表
            
        Returns:
            爬取结果
        """
        # 兼容性处理：支持单页面字符串输入
        if isinstance(page_ids, str):
            page_ids = [page_ids]

        self.task_stats.start_time = time.time()

        logger.info(f"开始统一并发爬取 {len(page_ids)} 个页面: {page_ids}")

        try:
            # 阶段 1: 获取所有页面内容
            page_data = await self._fetch_pages(page_ids)

            # 阶段 2: 获取所有书籍内容
            book_data = await self._fetch_books(page_data)

            # 阶段 3: 保存数据
            save_results = await self._save_data(page_data, book_data)

            # 更新统计信息
            self.task_stats.end_time = time.time()
            self.task_stats.successful_pages = self.task_stats.total_pages  # 所有页面都有效处理
            self.task_stats.failed_pages = 0
            self.task_stats.total_rankings = save_results.rankings_saved
            self.task_stats.total_books = save_results.books_saved
            self.task_stats.failed_books = 0  # 暂时设为0，后续可从 books_result 中获取

            # 使用类型安全的结果类
            message = f"成功爬取页面{len(page_ids)}个，榜单{save_result.rankings_saved}个，书籍{save_result.books_saved}个。"
            task_result = CrawlTaskResult.success_res(
                stats=self.task_stats,
                message=message
            )

            logger.info(f"统一并发爬取总结: {message},总耗时 {self.task_stats.execution_time:.2f}s")

            # 使用类型安全的结果构建
            return self._build_success_result(save_results, page_ids)

        except Exception as e:
            logger.error(f"爬取任务执行失败: {e}")
            return self._build_error_result(str(e))

    async def _fetch_pages(self, page_ids: List[str]) -> PagesResult:
        """
        阶段 1: 并发获取所有页面内容
        
        Args:
            page_ids: 页面ID列表
            
        Returns:
            类型安全的页面结果
        """
        logger.info(f"阶段 1: 开始获取 {len(page_ids)} 个页面内容")

        # 创建所有页面的获取任务
        tasks = [self._fetch_and_parse_page(page_id) for page_id in page_ids]
        page_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 使用类型安全的结果类
        pages_result = PagesResult()

        for page_id, result in zip(page_ids, page_results):
            if isinstance(result, Exception):
                pages_result.page_data[page_id] = result

        logger.info(f"阶段 1 完成: 成功 {pages_result.successful_pages}/{pages_result.total_pages} 个页面")
        return pages_result

    @retry(stop=stop_after_attempt(5),
           wait=wait_exponential(multiplier=5, min=1, max=10),
           retry=retry_if_exception(Exception),
           before_sleep=before_sleep_log(logger, logging.WARN), )
    async def _fetch_and_parse_page(self, page_id: str) -> PageResult:
        async with self.request_semaphore:
            start_time = time.time()
            try:
                logger.info(f"开始爬取页面: {page_id}")

                # 生成页面URL
                page_url = self.config.build_url(page_id)
                if not page_url:
                    raise Exception("无法生成页面地址")

                # 获取页面内容
                page_content = await self.client.run(page_url)

                if not page_content or page_content.get("status") == "error":
                    raise Exception(f"页面内容获取失败: {page_content.get('error', '未知错误')}")

                # 解析榜单信息
                page_parser = PageParser(page_content, page_id=page_id)

                # 使用类型安全的结果构建
                result = PageResult.success_res(
                    page_id=page_id,
                    rankings=page_parser.rankings,
                )

                logger.info(
                    f"页面 {page_id} 内容获取完成: 榜单 {len(result.rankings)}个, 书籍 {len(result.novel_ids)}个")

                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"页面 {page_id} 内容获取异常: {e}")
                return PageResult.failed_res(page_id, str(e))

    async def _fetch_books(self, pages_result: PagesResult) -> BooksResult:
        """
        阶段 2: 并发获取所有书籍内容
        
        Args:
            pages_result: 类型安全的页面结果
            
        Returns:
            类型安全的书籍结果
        """
        # 收集所有成功页面的书籍ID
        all_novel_ids = set()
        for page_result in pages_result.page_data.values():
            if page_result.success and page_result.novel_ids:
                all_novel_ids.update(page_result.novel_ids)
        all_novel_ids = list(all_novel_ids)
        if not all_novel_ids:
            logger.info("阶段 2: 无书籍ID需要获取")
            return BooksResult()

        logger.info(f"阶段 2: 开始获取 {len(all_novel_ids)} 个书籍内容")

        # 并发获取所有书籍内容
        book_tasks = [self._fetch_and_parse_book(book_id) for book_id in all_novel_ids]
        book_results = await asyncio.gather(*book_tasks, return_exceptions=True)

        # 使用类型安全的结果类
        books_result = BooksResult()

        for novel_id, result in zip(all_novel_ids, book_results):
            if isinstance(result, Exception):
                logger.error(f"书籍 {novel_id} 获取失败: {result}")
                books_result.failed_novels.append(novel_id)
            elif result and result.get("status") != "error":
                try:
                    book_parser = NovelPageParser(result)
                    books_result.books.append(book_parser)
                except Exception as e:
                    logger.error(f"书籍 {novel_id} 解析失败: {e}")
                    books_result.failed_novels.append(novel_id)
            else:
                books_result.failed_novels.append(novel_id)

        logger.info(f"阶段 2 完成: 成功 {books_result.successful_novels}/{books_result.total_novels} 个书籍")

        return books_result

    @retry(stop=stop_after_attempt(5),
           wait=wait_exponential(multiplier=5, min=1, max=10),
           retry=retry_if_exception(Exception),
           before_sleep=before_sleep_log(logger, logging.WARN), )
    async def _fetch_and_parse_book(self, novel_id: str) -> Dict:
        """
        书籍获取

        :param novel_id: 书籍ID
        :return: 书籍响应数据
        """
        async with self.request_semaphore:
            book_url = self.config.build_novel_url(novel_id)
            result = await self.client.run(book_url)
            if not result.get("success"):
                error_msg = result.get("error", "unknown error during book content fetch")
                raise Exception(f"Book {book_url} fetch failed with status: {error_msg}")
            return result

    async def _save_data(self, pages_result: PagesResult, books_result: BooksResult) -> SaveResult:
        """
        阶段 3: 保存所有数据
        
        Args:
            pages_result: 类型安全的页面结果
            books_result: 类型安全的书籍结果
            
        Returns:
            类型安全的保存结果
        """
        logger.info("阶段 3: 开始保存所有数据")

        # 收集所有榜单数据
        all_rankings = []
        for page_result in pages_result.page_data.values():
            if not page_result.exception and page_result.rankings:
                all_rankings.extend(page_result.rankings)

        books = books_result.books

        # 创建独立的数据库会话并保存数据
        db = SessionLocal()
        try:
            # 使用现有的Service方法保存数据
            if all_rankings:
                self.save_ranking_parsers(all_rankings, db)
                logger.info(f"保存了 {len(all_rankings)} 个榜单")

            if books:
                self.save_novel_parsers(books, db)
                logger.info(f"保存了 {len(books)} 个书籍")

            db.commit()
            logger.info("阶段 3 完成: 所有数据保存成功")

            return SaveResult.success_res(
                rankings_saved=len(all_rankings),
                books_saved=len(books)
            )

        except Exception as db_error:
            db.rollback()
            logger.error(f"数据库操作失败: {db_error}")
            return SaveResult.failed_res(db_error)
        finally:
            db.close()

    def _build_success_result(self, save_result: SaveResult, page_ids: List[str]) -> dataclasses:
        """
        构建成功结果 - 使用类型安全的结果类
        
        Args:
            save_result: 类型安全的保存结果
            page_ids: 页面ID列表
            
        Returns:
            向后兼容的元组格式
        """
        # 更新统计信息
        self.task_stats.end_time = time.time()
        self.task_stats.successful_pages = self.task_stats.total_pages  # 所有页面都有效处理
        self.task_stats.failed_pages = 0
        self.task_stats.total_rankings = save_result.rankings_saved
        self.task_stats.total_books = save_result.books_saved
        self.task_stats.failed_books = 0  # 暂时设为0，后续可从 books_result 中获取

        # 使用类型安全的结果类
        message = f"成功爬取页面{len(page_ids)}个，榜单{save_result.rankings_saved}个，书籍{save_result.books_saved}个。"
        task_result = CrawlTaskResult.success_res(
            stats=self.task_stats,
            message=message
        )

        logger.info(f"统一并发爬取总结: {message},总耗时 {self.task_stats.execution_time:.2f}s")

        # 返回向后兼容的元组格式
        return task_result

    def _build_error_result(self, error_msg: str) -> Tuple[bool, Dict]:
        """
        构建错误结果 - 使用类型安全的结果类
        
        Args:
            error_msg: 错误消息
            
        Returns:
            向后兼容的元组格式
        """
        self.task_stats.end_time = time.time()

        # 使用类型安全的结果类
        task_result = CrawlTaskResult.failed(
            error=error_msg,
            stats=self.task_stats
        )

        # 返回向后兼容的元组格式
        return task_result.to_tuple()

    def save_ranking_parsers(self, rankings: List[RankingParser], db: Session):
        """
        保存从榜单网页中爬取的榜单记录、榜单中的书籍记录、榜单快照记录
        :param rankings:
        :param db:
        :return:
        """
        for ranking in rankings:
            # 保存或更新榜单信息
            rank_record = self.ranking_service.create_or_update_ranking(
                db, ranking.ranking_info
            )
            ranking_snapshots = []
            batch_id = generate_batch_id()

            for book in ranking.book_snapshots:
                # 保存书籍
                book_record = self.book_service.create_or_update_book(db, book)
                # 创建榜单快照记录
                snapshot_data = {
                    "ranking_id": rank_record.id,
                    "book_id": book_record.id,
                    "batch_id": batch_id,
                    **book
                }
                ranking_snapshots.append(snapshot_data)

            # 批量保存榜单快照
            if ranking_snapshots:
                self.ranking_service.batch_create_ranking_snapshots(
                    db, ranking_snapshots, batch_id
                )

    def save_novel_parsers(self, books: List[NovelPageParser], db: Session):
        """
        保存书籍快照
        :param books:
        :param db:
        :return:
        """
        # 保存书籍快照
        book_snapshots = []
        for book_data in books:
            # 保存或更新书籍基本信息
            book_info = book_data.book_detail
            book_record = self.book_service.create_or_update_book(db, book_info)

            # 创建书籍快照记录
            snapshot_data = {
                "book_id": book_record.id,
                **book_info
            }
            book_snapshots.append(snapshot_data)
        # 批量保存书籍快照
        if book_snapshots:
            self.book_service.batch_create_book_snapshots(db, book_snapshots)

    def _build_result(self, is_success: bool = True, msg: str = None) -> Tuple[bool, Dict]:
        """
        构造运行结果 - 保持向后兼容
        :param is_success:
        :param msg:
        :return:
        """
        res = self.stats.copy()
        if msg:
            res["message"] = msg
        if is_success:
            res["execution_time"] = res.get("end_time", time.time()) - res["start_time"]
        else:
            res["execution_time"] = time.time() - res["start_time"]
        return is_success, res

    async def close(self) -> None:
        """关闭资源"""
        await self.client.close()
