"""
爬取流程管理器 - 高效的并发爬取架构
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List
from typing import Tuple

import httpx
from sqlalchemy.orm import Session
from tenacity import before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.crawl_config import CrawlConfig
from app.database.connection import SessionLocal
from app.database.service.book_service import BookService
from app.database.service.ranking_service import RankingService
from app.logger import get_logger
from .http import HttpClient
from .parser import NovelPageParser, PageParser, RankingParser
from ..models.base import BaseResult
from ..utils import generate_batch_id


@dataclass
class PagesResult(BaseResult[PageParser]):
    """多页面爬取结果"""

    @property
    def rankings(self) -> List[RankingParser]:
        res = []
        for page in self.success_items:
            res.extend(page.rankings)
        return res

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_pages_num": self.total_num,
            "failed_pages": self.failed_ids
        }


@dataclass
class NovelsResult(BaseResult[NovelPageParser]):
    """
    多书籍页面爬取结果
    """

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_novels_num": self.total_num,
            "failed_novels": self.failed_ids
        }


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

    async def execute_crawl_task(self, page_ids: List[str]) -> Dict[str, Any]:
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

        start_time = time.time()
        logger.info(f"开始统一并发爬取 {len(page_ids)} 个页面: {page_ids}")
        try:
            # 阶段 1: 获取所有页面内容
            page_data = await self._fetch_pages(page_ids)

            # 阶段 2: 获取所有书籍内容
            book_data = await self._fetch_books(page_data)

            # 阶段 3: 保存数据
            save_results = await self._save_data(page_data, book_data)

            execution_time = time.time() - start_time
            logger.info(f"统一并发爬取总耗时 {execution_time:.2f}s")

            # 使用类型安全的结果构建
            return {
                "success": True,
                "page_results": page_data.to_dict(),
                "book_results": book_data.to_dict(),
                "store_results": save_results,
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(f"爬取任务执行失败: {e}")
            return {
                "success": False,
                "exception": e
            }

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
        pages = await asyncio.gather(*tasks, return_exceptions=True)

        # 使用类型安全的结果类
        pages_result = PagesResult()

        for page_id, result in zip(page_ids, pages):
            if isinstance(result, Exception):
                pages_result.failed_items[page_id] = result
            else:
                pages_result.success_items.append(result)

        logger.info(f"阶段 1 完成: 成功 {len(pages_result.success_items)}/{pages_result.total_num} 个页面")
        return pages_result

    @retry(stop=stop_after_attempt(5),
           wait=wait_exponential(multiplier=5, min=1, max=10),
           retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError, httpx.TimeoutException, json.JSONDecodeError)),
           before_sleep=before_sleep_log(logger, logging.WARN), )
    async def _fetch_and_parse_page(self, page_id: str) -> PageParser | Exception:
        async with self.request_semaphore:
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

                logger.info(
                    f"页面 {page_id} 内容获取完成: 解析榜单 {len(page_parser.rankings)}个")

                return page_parser
            except Exception as e:
                logger.error(f"页面 {page_id} 内容获取异常: {e}")
                return e

    async def _fetch_books(self, pages_result: PagesResult) -> NovelsResult:
        """
        阶段 2: 并发获取所有书籍内容
        
        Args:
            pages_result: 类型安全的页面结果
            
        Returns:
            类型安全的书籍结果
        """
        # 收集所有成功页面的书籍ID
        all_novel_ids = set()
        for page_result in pages_result.success_items:
            all_novel_ids.add(page_result.get_novel_ids())
        all_novel_ids = list(all_novel_ids)
        if not all_novel_ids:
            logger.info("阶段 2: 无书籍ID需要获取")
            return NovelsResult()

        logger.info(f"阶段 2: 开始获取 {len(all_novel_ids)} 个书籍内容")

        # 并发获取所有书籍内容
        book_tasks = [self._fetch_and_parse_book(book_id) for book_id in all_novel_ids]
        book_results = await asyncio.gather(*book_tasks, return_exceptions=True)

        # 使用类型安全的结果类
        books_result = NovelsResult()
        for novel_id, result in zip(all_novel_ids, book_results):
            if isinstance(result, Exception):
                books_result.failed_items[novel_id] = result
            else:
                logger.error(f"书籍 {novel_id} 获取失败: {result}")
                books_result.success_items.append(result)

        logger.info(f"阶段 2 完成: 成功 {len(books_result.success_items)}/{books_result.total_num} 个书籍")

        return books_result

    @retry(stop=stop_after_attempt(5),
           wait=wait_exponential(multiplier=5, min=1, max=10),
           retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError, httpx.TimeoutException, json.JSONDecodeError)),
           before_sleep=before_sleep_log(logger, logging.WARN), )
    async def _fetch_and_parse_book(self, novel_id: str) -> NovelPageParser | Exception:
        """
        书籍获取

        :param novel_id: 书籍ID
        :return: 书籍响应数据
        """
        async with self.request_semaphore:
            try:
                book_url = self.config.build_novel_url(novel_id)
                result = await self.client.run(book_url)
                if not result.get("success"):
                    error_msg = result.get("error", "unknown error during book content fetch")
                    raise Exception(f"Book {book_url} fetch failed with status: {error_msg}")
                novel_parser = NovelPageParser(result)
                return novel_parser
            except Exception as e:
                logger.error(f"书籍页面 {novel_id} 内容获取异常: {e}")
                return e

    async def _save_data(self, pages_result: PagesResult, novels_result: NovelsResult) -> Dict[str, int] | Exception:
        """
        阶段 3: 保存所有数据
        
        Args:
            pages_result: 类型安全的页面结果
            novels_result: 类型安全的书籍结果
            
        Returns:
            类型安全的保存结果
        """
        logger.info("阶段 3: 开始保存所有数据")

        # 收集所有榜单数据
        all_rankings = pages_result.rankings
        books = novels_result.success_items

        ranking_snapshots_num = 0
        books_snapshots_num = 0

        # 创建独立的数据库会话并保存数据
        db = SessionLocal()
        try:
            # 使用现有的Service方法保存数据
            if all_rankings:
                _, ranking_snapshots_num = self.save_ranking_parsers(all_rankings, db)
                logger.info(f"保存了 {len(all_rankings)} 个榜单")

            if books:
                books_snapshots_num = self.save_novel_parsers(books, db)
                logger.info(f"保存了 {len(books)} 个书籍")

            db.commit()
            logger.info("阶段 3 完成: 所有数据保存成功")

            return {
                "rankings": len(all_rankings),
                "ranking_snapshots": ranking_snapshots_num,
                "books": len(books),
                "books_snapshots": books_snapshots_num,
            }
        except Exception as db_error:
            db.rollback()
            logger.error(f"数据库操作失败: {db_error}")
            return db_error
        finally:
            db.close()

    def save_ranking_parsers(self, rankings: List[RankingParser], db: Session) -> Tuple[int, int]:
        """
        保存从榜单网页中爬取的榜单记录、榜单中的书籍记录、榜单快照记录
        :param rankings:
        :param db:
        :return: 保存的榜单数量，保存的榜单快照数量
        """
        stored_ranking_snapshots = 0
        for ranking in rankings:
            # 保存或更新榜单信息
            rank_record = self.ranking_service.create_or_update_ranking(
                db, ranking.ranking_info
            )
            ranking_snapshots = []
            batch_id = generate_batch_id()
            stored_ranking_snapshots += len(ranking.book_snapshots)
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
        return len(rankings), stored_ranking_snapshots

    def save_novel_parsers(self, books: List[NovelPageParser], db: Session) -> int:
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
        return len(book_snapshots)

    async def close(self) -> None:
        """关闭资源"""
        await self.client.close()
