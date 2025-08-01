"""
爬取流程管理器 - 高效的并发爬取架构
"""

import asyncio
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

        # 统计信息
        self.stats = {
            "total_pages": 0,
            "successful_pages": 0,
            "failed_pages": 0,
            "total_books": 0,
            "total_rankings": 0,
            "total_requests": 0,
            "start_time": 0.0,
            "end_time": 0.0,
        }

    async def execute_crawl_task(self, page_ids: Union[str, List[str]]) -> Tuple[bool, Dict]:
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

        self.stats["start_time"] = time.time()
        self.stats["total_pages"] = len(page_ids)

        logger.info(f"开始统一并发爬取 {len(page_ids)} 个页面: {page_ids}")

        try:
            # 阶段 1: 获取所有页面内容
            page_data = await self._fetch_pages(page_ids)

            # 阶段 2: 获取所有书籍内容
            book_data = await self._fetch_books(page_data)

            # 阶段 3: 保存数据
            results = await self._save_data(page_data, book_data)

            return self._aggregate_final_results(results, page_ids)

        except Exception as e:
            logger.error(f"爬取任务执行失败: {e}")
            return self._build_error_result(str(e))

    async def _fetch_pages(self, page_ids: List[str]) -> Dict[str, Dict]:
        """
        阶段 1: 并发获取所有页面内容
        
        Args:
            page_ids: 页面ID列表
            
        Returns:
            页面数据字典 {page_id: page_result}
        """
        logger.info(f"阶段 1: 开始获取 {len(page_ids)} 个页面内容")

        # 创建所有页面的获取任务
        tasks = [self._fetch_and_parse_page(page_id) for page_id in page_ids]
        page_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        page_data = {}
        for page_id, result in zip(page_ids, page_results):
            if isinstance(result, Exception):
                logger.error(f"页面 {page_id} 获取失败: {result}")
                page_data[page_id] = {"success": False, "error": str(result)}
            else:
                page_data[page_id] = result

        successful_pages = sum(1 for data in page_data.values() if data.get("success"))
        logger.info(f"阶段 1 完成: 成功 {successful_pages}/{len(page_ids)} 个页面")
        return page_data

    @retry(stop=stop_after_attempt(5),
           wait=wait_exponential(multiplier=5, min=1, max=10),
           retry=retry_if_exception(Exception),
           before_sleep=before_sleep_log(logger, logging.WARN), )
    async def _fetch_and_parse_page(self, page_id: str) -> Dict[str, Dict]:
        async with self.request_semaphore:
            result = await self._fetch_single_page_content(page_id)
            if not result.get("success"):
                error_msg = result.get("error", "unknown error during page content fetch")
                raise Exception(f"Page {page_id} fetch failed with status: {error_msg}")
            logger.info(f"Page {page_id} fetch succeeded")
            return result

    async def _fetch_books(self, page_data: Dict[str, Dict]) -> Dict[str, List]:
        """
        阶段 2: 并发获取所有书籍内容
        
        Args:
            page_data: 页面数据字典
            
        Returns:
            书籍数据字典 {"books": [NovelPageParser, ...], "failed_urls": [...]}
        """
        # 收集所有成功页面的书籍ID
        all_novel_ids = set()
        for page_result in page_data.values():
            if page_result.get("success") and page_result.get("novel_ids"):
                all_novel_ids.update(page_result["novel_ids"])

        all_novel_ids = list(all_novel_ids)
        if not all_novel_ids:
            logger.info("阶段 2: 无书籍ID需要获取")
            return {"books": [], "failed_urls": []}

        logger.info(f"阶段 2: 开始获取 {len(all_novel_ids)} 个书籍内容")

        # 生成所有书籍URL
        book_urls = [self.config.build_novel_url(novel_id) for novel_id in all_novel_ids]

        # 并发获取所有书籍内容
        book_tasks = [self._fetch_and_parse_book(url) for url in book_urls]
        book_results = await asyncio.gather(*book_tasks, return_exceptions=True)

        # 处理结果
        books = []
        failed_urls = []

        for url, result in zip(book_urls, book_results):
            if isinstance(result, Exception):
                logger.error(f"书籍 {url} 获取失败: {result}")
                failed_urls.append(url)
            elif result and result.get("status") != "error":
                try:
                    book_parser = NovelPageParser(result)
                    books.append(book_parser)
                except Exception as e:
                    logger.error(f"书籍 {url} 解析失败: {e}")
                    failed_urls.append(url)
            else:
                failed_urls.append(url)

        success_count = len(books)
        logger.info(f"阶段 2 完成: 成功 {success_count}/{len(all_novel_ids)} 个书籍")

        return {"books": books, "failed_urls": failed_urls}

    @retry(stop=stop_after_attempt(5),
           wait=wait_exponential(multiplier=5, min=1, max=10),
           retry=retry_if_exception(Exception),
           before_sleep=before_sleep_log(logger, logging.WARN), )
    async def _fetch_and_parse_book(self, book_url: str) -> Dict:
        """
        书籍获取

        :param book_url: 书籍地址
        :return: 书籍响应数据
        """
        async with self.request_semaphore:
            result = await self.client.run(book_url)
            if not result.get("success"):
                error_msg = result.get("error", "unknown error during book content fetch")
                raise Exception(f"Book {book_url} fetch failed with status: {error_msg}")
            return result

    async def _fetch_single_book_with_retry(self, book_url: str) -> Dict:
        """
        带重试的单书籍获取
        
        Args:
            book_url: 书籍URL
            
        Returns:
            书籍响应数据
        """
        async with self.request_semaphore:  # 统一并发控制
            for attempt in range(self.crawler_config.retry_times + 1):
                try:
                    result = await self.client.run(book_url)
                    if result and result.get("status") != "error":
                        return result
                    else:
                        raise Exception(result.get("error", "书籍内容获取失败"))

                except Exception as e:
                    if attempt < self.crawler_config.retry_times:
                        retry_delay = self._calculate_retry_delay(e, attempt)
                        logger.debug(f"书籍 {book_url} 第 {attempt + 1} 次重试，延迟 {retry_delay:.1f}s")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"书籍 {book_url} 最终获取失败: {e}")
                        return {"status": "error", "url": book_url, "error": str(e)}

    async def _save_data(self, page_data: Dict[str, Dict], book_data: Dict[str, List]) -> Dict:
        """
        阶段 3: 保存所有数据
        
        Args:
            page_data: 页面数据
            book_data: 书籍数据
            
        Returns:
            保存结果
        """
        logger.info("阶段 3: 开始保存所有数据")

        # 收集所有榜单数据
        all_rankings = []
        for page_result in page_data.values():
            if page_result.get("success") and page_result.get("rankings"):
                all_rankings.extend(page_result["rankings"])

        books = book_data.get("books", [])

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

            return {
                "success": True,
                "rankings_saved": len(all_rankings),
                "books_saved": len(books),
                "failed_books": len(book_data.get("failed_urls", []))
            }

        except Exception as db_error:
            db.rollback()
            logger.error(f"数据库操作失败: {db_error}")
            raise Exception(f"数据库操作失败: {db_error}")
        finally:
            db.close()

    async def _fetch_single_page_content(self, page_id: str) -> Dict:
        """
        获取单个页面内容和书籍ID列表
        
        Args:
            page_id: 页面ID
            
        Returns:
            页面内容结果
        """
        start_time = time.time()
        page_result = {
            "page_id": page_id,
            "success": False,
            "rankings": [],
            "novel_ids": [],
            "execution_time": 0
        }

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
            rankings: List[RankingParser] = page_parser.rankings

            # 提取所有书籍ID
            novel_id_list = list(
                set(itertools.chain.from_iterable(ranking.get_novel_ids() for ranking in rankings))
            )

            logger.debug(f"页面 {page_id} 发现 {len(rankings)} 个榜单, {len(novel_id_list)} 个书籍")

            # 返回页面数据，不在此阶段处理书籍请求
            page_result["rankings"] = rankings
            page_result["novel_ids"] = novel_id_list

            # 计算执行时间
            page_result["execution_time"] = time.time() - start_time
            page_result["success"] = True

            logger.info(f"页面 {page_id} 内容获取完成: 榜单 {len(rankings)}, "
                        f"书籍ID {len(novel_id_list)}, 耗时 {page_result['execution_time']:.2f}s")

            return page_result

        except Exception as e:
            page_result["execution_time"] = time.time() - start_time
            page_result["error"] = str(e)
            logger.error(f"页面 {page_id} 内容获取异常: {e}")
            return page_result

    def _aggregate_results(self, page_results: List[Dict], page_ids: List[str]) -> Tuple[bool, Dict]:
        """
        聚合所有页面的爬取结果
        
        Args:
            page_results: 各页面的爬取结果
            page_ids: 页面ID列表
            
        Returns:
            聚合后的最终结果
        """
        self.stats["end_time"] = time.time()
        execution_time = self.stats["end_time"] - self.stats["start_time"]

        # 统计成功和失败的页面
        successful_pages = []
        failed_pages = []

        total_rankings = 0
        total_books = 0
        total_requests = 0

        for result in page_results:
            if isinstance(result, Exception):
                # 处理异常情况
                failed_pages.append({
                    "page_id": "unknown",
                    "error": str(result),
                    "success": False
                })
            elif result.get("success", False):
                successful_pages.append(result)
                total_rankings += result.get("rankings_count", 0)
                total_books += result.get("books_count", 0)
                total_requests += result.get("requests_count", 0)
            else:
                failed_pages.append(result)

        # 更新统计信息
        self.stats.update({
            "successful_pages": len(successful_pages),
            "failed_pages": len(failed_pages),
            "total_rankings": total_rankings,
            "total_books": total_books,
            "total_requests": total_requests,
            "execution_time": execution_time
        })

        # 判断整体是否成功
        overall_success = len(successful_pages) > 0  # 至少有一个页面成功

        # 构建详细结果
        result_data = {
            **self.stats,
            "page_results": {
                "successful": successful_pages,
                "failed": failed_pages
            }
        }

        if failed_pages:
            failed_page_ids = [p.get("page_id", "unknown") for p in failed_pages]
            result_data["message"] = f"部分页面爬取失败: {failed_page_ids}"
        else:
            result_data["message"] = "所有页面爬取成功"

        logger.info(f"并发爬取总结: 成功 {len(successful_pages)}/{len(page_ids)} 页面, "
                    f"榜单 {total_rankings}, 书籍 {total_books}, 总耗时 {execution_time:.2f}s")

        return overall_success, result_data

    def _aggregate_final_results(self, save_result: Dict, page_ids: List[str]) -> Tuple[bool, Dict]:
        """
        聚合最终结果 - 统一并发架构的结果汇总
        
        Args:
            save_result: 数据保存结果
            page_ids: 页面ID列表
            
        Returns:
            最终的爬取结果
        """
        self.stats["end_time"] = time.time()
        execution_time = self.stats["end_time"] - self.stats["start_time"]

        # 更新统计信息
        self.stats.update({
            "successful_pages": self.stats["total_pages"],  # 所有页面都有效处理
            "failed_pages": 0,
            "total_rankings": save_result.get("rankings_saved", 0),
            "total_books": save_result.get("books_saved", 0),
            "failed_books": save_result.get("failed_books", 0),
            "execution_time": execution_time
        })

        # 构建详细结果
        result_data = {
            **self.stats,
            "message": f"统一并发爬取完成: 页面 {len(page_ids)}, 榜单 {save_result.get('rankings_saved', 0)}, 书籍 {save_result.get('books_saved', 0)}"
        }

        if save_result.get("failed_books", 0) > 0:
            result_data["message"] += f", 失败书籍 {save_result['failed_books']}"

        logger.info(f"统一并发爬取总结: 页面 {len(page_ids)}, "
                    f"榜单 {save_result.get('rankings_saved', 0)}, 书籍 {save_result.get('books_saved', 0)}, "
                    f"总耗时 {execution_time:.2f}s")

        return True, result_data  # 只要数据保存成功就返回true

    def _build_error_result(self, error_msg: str) -> Tuple[bool, Dict]:
        """
        构建错误结果
        
        Args:
            error_msg: 错误消息
            
        Returns:
            错误结果
        """
        self.stats["end_time"] = time.time()
        execution_time = self.stats["end_time"] - self.stats["start_time"]

        result_data = {
            **self.stats,
            "execution_time": execution_time,
            "success": False,
            "error": error_msg,
            "message": f"统一并发爬取失败: {error_msg}"
        }

        return False, result_data

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
