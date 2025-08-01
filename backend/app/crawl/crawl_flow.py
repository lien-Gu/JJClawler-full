"""
爬取流程管理器 - 高效的并发爬取架构
"""

import asyncio
import itertools
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

logger = get_logger(__name__)


class CrawlFlow:
    """
    并发爬取流程管理器 - 使用现有Service，支持多页面并发
    """

    def __init__(self) -> None:
        """
        初始化爬取流程管理器
        """
        self.config = CrawlConfig()
        self.crawler_config = get_settings().crawler
        self.book_service = BookService()
        self.ranking_service = RankingService()
        self.client = HttpClient(concurrent=True)
        
        # 并发控制
        self.page_semaphore = asyncio.Semaphore(self.crawler_config.max_concurrent_pages)
        
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
        执行并发爬取任务 - 支持单页面和多页面
        
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
        
        logger.info(f"开始并发爬取 {len(page_ids)} 个页面: {page_ids}")
        
        # 并发爬取所有页面
        tasks = [self._crawl_single_page_with_retry(page_id) for page_id in page_ids]
        page_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 聚合结果
        return self._aggregate_results(page_results, page_ids)

    async def _crawl_single_page_with_retry(self, page_id: str) -> Dict:
        """
        带重试机制的单页面爬取
        
        Args:
            page_id: 页面ID
            
        Returns:
            页面爬取结果
        """
        async with self.page_semaphore:  # 控制并发页面数
            for attempt in range(self.crawler_config.page_retry_times + 1):
                try:
                    result = await self._crawl_single_page(page_id)
                    if result["success"]:
                        return result
                    else:
                        raise Exception(result.get("error", "页面爬取失败"))
                        
                except Exception as e:
                    if attempt < self.crawler_config.page_retry_times:
                        retry_delay = self.crawler_config.page_retry_delay * (attempt + 1)
                        logger.warning(f"页面 {page_id} 第 {attempt + 1} 次重试，延迟 {retry_delay}s, 错误: {e}")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"页面 {page_id} 最终爬取失败: {e}")
                        return {
                            "page_id": page_id,
                            "success": False,
                            "error": str(e),
                            "rankings_count": 0,
                            "books_count": 0,
                            "requests_count": 0,
                            "execution_time": 0
                        }

    async def _crawl_single_page(self, page_id: str) -> Dict:
        """
        爬取单个页面的核心逻辑 - 使用现有Service
        
        Args:
            page_id: 页面ID
            
        Returns:
            页面爬取结果
        """
        start_time = time.time()
        page_stats = {
            "page_id": page_id,
            "success": False,
            "rankings_count": 0,
            "books_count": 0,
            "requests_count": 0,
            "execution_time": 0
        }
        
        try:
            logger.info(f"开始爬取页面: {page_id}")

            # 生成页面URL
            page_url = self.config.build_url(page_id)
            if not page_url:
                raise Exception("无法生成页面地址")

            # 爬取页面内容
            page_stats["requests_count"] += 1
            page_content = await self.client.run(page_url)
            
            if not page_content or page_content.get("status") == "error":
                raise Exception(f"页面内容爬取失败: {page_content.get('error', '未知错误')}")

            # 解析榜单
            page_parser = PageParser(page_content, page_id=page_id)
            rankings: List[RankingParser] = page_parser.rankings
            page_stats["rankings_count"] = len(rankings)
            
            logger.debug(f"页面 {page_id} 发现 {len(rankings)} 个榜单")

            # 爬取书籍详情
            novel_id_list = list(
                set(itertools.chain.from_iterable(ranking.get_novel_ids() for ranking in rankings))
            )
            
            books = []
            if novel_id_list:
                page_stats["requests_count"] += 1
                book_urls = [self.config.build_novel_url(novel_id) for novel_id in novel_id_list]
                book_responses = await self.client.run(book_urls)
                
                # 过滤成功的书籍响应
                valid_book_responses = [
                    resp for resp in book_responses 
                    if resp and resp.get("status") != "error"
                ]
                
                page_stats["books_count"] = len(valid_book_responses)
                logger.debug(f"页面 {page_id} 成功爬取 {len(valid_book_responses)} 个书籍详情")

                # 解析书籍信息
                if valid_book_responses:
                    books = [NovelPageParser(resp) for resp in valid_book_responses]

            # 创建独立的数据库会话并保存数据
            db = SessionLocal()
            try:
                # 使用现有的Service方法保存数据
                self.save_ranking_parsers(rankings, db)
                self.save_novel_parsers(books, db)
                
            except Exception as db_error:
                db.rollback()
                raise Exception(f"数据库操作失败: {db_error}")
            finally:
                db.close()

            # 计算执行时间
            page_stats["execution_time"] = time.time() - start_time
            page_stats["success"] = True
            
            logger.info(f"页面 {page_id} 爬取完成: 榜单 {page_stats['rankings_count']}, "
                       f"书籍 {page_stats['books_count']}, 耗时 {page_stats['execution_time']:.2f}s")
            
            return page_stats
            
        except Exception as e:
            page_stats["execution_time"] = time.time() - start_time
            page_stats["error"] = str(e)
            logger.error(f"页面 {page_id} 爬取异常: {e}")
            return page_stats

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
