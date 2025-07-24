"""
爬取流程管理器 - 高效的并发爬取架构
"""

import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Any, List
import itertools
from app.config import settings
from app.database.connection import get_db
from app.database.service.book_service import BookService
from app.database.service.ranking_service import RankingService
from .http import Crawler
from .base import CrawlConfig
from .parser import DataType, Parser, RankingParseInfo, BookParseInfo

logger = logging.getLogger(__name__)


class CrawlFlow:
    """
    爬取流程管理器

    功能：
    1. 并发爬取书籍详情，提升性能
    2. 创建书籍和榜单快照，记录变化
    3. 统一错误处理和日志记录
    4. 模块化设计，提高代码复用率
    """

    def __init__(self) -> None:
        """
        初始化爬取流程管理器
        """
        self.config = CrawlConfig()
        self.parser = Parser()
        self.book_service = BookService()
        self.ranking_service = RankingService()

        # 从配置文件获取设置
        crawler_config = settings.crawler



        # 配置HTTP客户端
        self.concurrent_requests = crawler_config.concurrent_requests
        self.concurrent_mode = self.concurrent_requests >= 1
        delay = crawler_config.request_delay
        timeout = crawler_config.timeout
        if self.concurrent_mode:
            # 并发时减少延迟和超时
            self.client = HttpClient(request_delay=delay/10, timeout=timeout/2)
        else:
            self.client = HttpClient(request_delay=delay, timeout=timeout)
        # 初始化数据容器
        self._reset_data()

        # 统计信息
        self.stats = {
            "books_crawled": 0,
            "total_requests": 0,
            "start_time": 0.0,
            "end_time": 0.0,
        }

    def _reset_data(self) -> None:
        """重置数据容器"""
        self.crawled_book_ids: set[str] = set()
        self.books_data: list[dict] = []
        self.rankings_data: list[dict] = []
        self.pages_data: list[dict] = []

    async def execute_crawl_task(self, page_id: str) -> dict[str, Any]:
        """
        执行完整的爬取任务

        Args:
            page_id: 页面任务ID

        Returns:
            爬取结果
        """
        start_time = time.time()
        self.stats["start_time"] = start_time

        try:
            logger.info(f"开始爬取页面: {page_id}")

            # 生成页面URL
            page_url = self.config.build_url(page_id)
            if not page_url:
                return self._create_error_result(
                    page_id, "无法生成页面地址", start_time
                )

            # 爬取页面内容
            self.stats["total_requests"] += 1
            page_content = await self.client.get(page_url)
            if not page_content:
                return self._create_error_result(
                    page_id, "页面内容爬取失败", start_time
                )

            # 解析榜单
            rankings: List[RankingParseInfo] = self.parser.parse(page_content, page_id=page_id)
            logger.debug(f"发现 {len(rankings)} 个榜单")

            # 爬取书籍详情
            book_list = BookParseInfo.unique_book_items(itertools.chain.from_iterable(ranking.books for ranking in rankings))
            book_responses = await self._crawl_books_details(book_list)
            logger.debug(f"成功爬取 {len(book_responses)} 个书籍详情")

            # 保存数据
            save_success = await self._save_crawl_result(rankings, books)

            # 返回结果
            execution_time = time.time() - start_time
            self.stats["end_time"] = time.time()

            if save_success:
                logger.info(f"页面 {page_id} 爬取成功，耗时 {execution_time:.2f} 秒")
                return self._create_success_result(page_id, len(books), execution_time)
            else:
                return self._create_error_result(page_id, "数据保存失败", start_time)

        except Exception as e:
            logger.error(f"页面 {page_id} 爬取异常: {e}")
            return self._create_error_result(page_id, f"爬取异常: {str(e)}", start_time)



    async def _crawl_page_content(self, url: str) -> dict | None:
        """爬取页面内容"""
        try:
            self.stats["total_requests"] += 1
            return await self.client.get(url)
        except Exception as e:
            logger.error(f"爬取页面内容失败: {e}")
            return None



    async def _save_crawl_result(self, rankings: list[dict], books: list[dict]) -> bool:
        """保存爬取结果到数据库 - 使用batch_id确保数据一致性"""
        try:
            for db in get_db():
                try:
                    snapshot_time = datetime.now()
                    await self._save_rankings(db, rankings, snapshot_time)
                    await self._save_books(db, books, snapshot_time)

                    db.commit()
                    logger.info(
                        f"成功保存 {len(rankings)} 个榜单和 {len(books)} 本书籍)"
                    )

                    return True

                except Exception as e:
                    db.rollback()
                    logger.error(f"保存数据失败: {e}")
                    raise
                break

        except Exception as e:
            logger.error(f"数据库操作失败: {e}")
            return False

    async def _save_rankings(
            self, db, rankings_data: list[dict], snapshot_time: datetime,
    ) -> None:
        """保存榜单数据和快照 - 使用batch_id确保一致性"""
        for ranking_data in rankings_data:
            try:
                # 保存或更新榜单基本信息
                ranking_info = {
                    "rank_id": ranking_data.get("rank_id"),
                    "name": ranking_data.get("rank_name", ""),
                    "page_id": ranking_data.get("page_id", ""),
                    "rank_group_type": ranking_data.get("rank_group_type", ""),
                    "sub_ranking_name": ranking_data.get("sub_ranking_name"),
                }

                ranking = self.ranking_service.create_or_update_ranking(
                    db, ranking_info
                )

                # 创建榜单快照
                books = ranking_data.get("books", [])
                ranking_snapshots = []
                # 导入batch管理工具
                from ..utils import generate_batch_id
                batch_id = generate_batch_id()

                for book in books:
                    # 确保书籍存在
                    book_info = {
                        "novel_id": int(book.get("book_id")),
                        "title": book.get("title", ""),
                    }
                    book_obj = self.book_service.create_or_update_book(db, book_info)

                    # 创建榜单快照记录
                    snapshot_data = {
                        "ranking_id": ranking.id,
                        "book_id": book_obj.id,
                        "batch_id": batch_id,
                        "position": book.get("position", 0),
                        "score": book.get("score", 0.0),
                        "snapshot_time": snapshot_time,
                    }
                    ranking_snapshots.append(snapshot_data)

                # 批量保存榜单快照 - 传递batch_id
                if ranking_snapshots:
                    self.ranking_service.batch_create_ranking_snapshots(
                        db, ranking_snapshots, batch_id
                    )

                logger.debug(
                    f"保存榜单 '{ranking_data.get('rank_name')}' "
                    f"及其 {len(books)} 个书籍快照"
                )

            except Exception as e:
                logger.error(f"保存榜单 '{ranking_data.get('rank_name')}' 失败: {e}")
                raise

    async def _save_books(
            self, db, books_data: list[dict], snapshot_time: datetime
    ) -> None:
        """保存书籍数据和快照"""
        if not books_data:
            return

        book_snapshots = []

        for book_data in books_data:
            try:
                # 保存或更新书籍基本信息
                book_info = {
                    "novel_id": int(book_data.get("book_id")),
                    "title": book_data.get("title", ""),
                }

                book = self.book_service.create_or_update_book(db, book_info)

                # 创建书籍快照记录
                snapshot_data = {
                    "book_id": book.id,
                    "clicks": self._parse_number(book_data.get("clicks", 0)),
                    "favorites": self._parse_number(book_data.get("favorites", 0)),
                    "comments": self._parse_number(book_data.get("comments", 0)),
                    "recommendations": self._parse_number(
                        book_data.get("nutrition", 0)
                    ),
                    "word_count": self._parse_number(book_data.get("word_count")),
                    "status": book_data.get("status"),
                    "snapshot_time": snapshot_time,
                }
                book_snapshots.append(snapshot_data)

            except Exception as e:
                logger.error(f"处理书籍 '{book_data.get('title')}' 数据失败: {e}")
                continue

        # 批量保存书籍快照
        if book_snapshots:
            self.book_service.batch_create_book_snapshots(db, book_snapshots)
            logger.debug(f"保存 {len(book_snapshots)} 个书籍快照")

    def _parse_number(self, value: Any) -> int | None:
        """
        解析数值字段，处理格式化字符串

        Args:
            value: 待解析的值

        Returns:
            解析后的整数，失败时返回None
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return int(value)

        if isinstance(value, str):
            # 提取数字，处理如 "85,221(章均)" -> "85221" 的格式
            numbers = re.findall(r"[\d,]+", value)
            if numbers:
                try:
                    number_str = numbers[0].replace(",", "")
                    return int(number_str)
                except ValueError:
                    pass

        return 0

    def _create_success_result(
            self, page_id: str, books_crawled: int, execution_time: float
    ) -> dict[str, Any]:
        """创建成功结果"""
        return {
            "success": True,
            "page_id": page_id,
            "books_crawled": books_crawled,
            "execution_time": execution_time,
        }

    def _create_error_result(
            self, page_id: str, error_msg: str, start_time: float
    ) -> dict[str, Any]:
        """创建错误结果"""
        execution_time = time.time() - start_time
        return {
            "success": False,
            "page_id": page_id,
            "books_crawled": 0,
            "execution_time": execution_time,
            "error_message": error_msg,
        }



    async def close(self) -> None:
        """关闭资源"""
        await self.client.close()
