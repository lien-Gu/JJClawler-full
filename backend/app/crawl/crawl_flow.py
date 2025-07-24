"""
爬取流程管理器 - 高效的并发爬取架构
"""

import itertools
import logging
import time
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.database.service.book_service import BookService
from app.database.service.ranking_service import RankingService
from .base import CrawlConfig
from .http import HttpClient
from .parser import NovelPageParser, PageParser, RankingParser
from ..utils import generate_batch_id

logger = logging.getLogger(__name__)


class CrawlFlow:
    """
    爬取流程管理器

    """

    def __init__(self) -> None:
        """
        初始化爬取流程管理器
        """
        self.config = CrawlConfig()
        self.book_service = BookService()
        self.ranking_service = RankingService()
        self.client = HttpClient(concurrent=True)  # 配置HTTP客户端
        self._reset_data()  # 初始化数据容器

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

    async def execute_crawl_task(self, page_id: str) -> Tuple[bool, Dict]:
        """
        执行完整的爬取任务

        Args:
            page_id: 页面任务ID

        Returns:
            爬取结果
        """
        self.stats["start_time"] = time.time()
        try:
            logger.info(f"开始爬取页面: {page_id}")

            # 生成页面URL
            page_url = self.config.build_url(page_id)
            if not page_url:
                return self._build_result(False, "无法生成页面地址")

            # 爬取页面内容
            self.stats["total_requests"] += 1
            page_content = await self.client.run(page_url)
            if not page_content:
                return self._build_result(False, "页面内容爬取失败")
            # 解析榜单并且保存
            page_parser = PageParser(page_content, page_id=page_id)
            rankings: List[RankingParser] = page_parser.rankings
            logger.debug(f"发现 {len(rankings)} 个榜单")
            self.save_ranking_parsers(rankings)

            # 爬取书籍详情
            novel_id_list = list(set(itertools.chain.from_iterable(ranking.get_novel_ids() for ranking in rankings)))
            book_responses = await self.client.run(
                [self.config.build_novel_url(novel_id) for novel_id in novel_id_list])
            logger.debug(f"成功爬取 {len(book_responses)} 个书籍详情")

            # 解析书籍信息并且保存
            books = [NovelPageParser(i) for i in book_responses]
            self.save_novel_parsers(books)

            # 返回结果
            self.stats["end_time"] = time.time()

            return self._build_result(True)
        except Exception as e:
            logger.error(f"页面 {page_id} 爬取异常: {e}")
            return self._build_result(False, f"爬取异常: {str(e)}")

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
        构造运行结果
        :param is_success:
        :param msg:
        :return:
        """
        res = self.stats
        if msg:
            res["msg"] = msg
        if is_success:
            res["execution_time"] = res.get("end_time") - res["start_time"]
            return is_success, res

        res["execution_time"] = time.time() - res["start_time"]
        return is_success, res

    async def close(self) -> None:
        """关闭资源"""
        await self.client.close()
