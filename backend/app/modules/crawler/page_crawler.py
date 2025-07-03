"""
页面爬虫模块

专门负责晋江文学城分类页面的数据抓取和解析
"""

import json
from typing import Dict, Any, Tuple, List
from datetime import datetime

from app.utils.http_client import HTTPClient
from app.utils.log_utils import get_logger
from app.modules.models import Book, BookSnapshot, Ranking, RankingSnapshot
from app.modules.dao import BookDAO, RankingDAO
from app.modules.database.connection import get_session

logger = get_logger(__name__)


class PageCrawler:
    """分类页面爬虫"""

    def __init__(self):
        self.http_client = HTTPClient(timeout=30.0, rate_limit_delay=1.0)

    async def crawl(self, task_id: str) -> Dict[str, Any]:
        """执行分类页面爬取"""
        try:
            logger.info(f"开始爬取分类页面: {task_id}")

            # 构建URL（这里需要根据task_id构建实际的URL）
            url = self._build_url(task_id)

            # 获取数据
            response = await self.http_client.get(url)
            response.raise_for_status()

            # 解析JSON响应
            data = response.json()

            # 解析书籍数据和排行榜数据
            books, snapshots, rankings = self._parse_page_data(data, task_id)

            # 保存到数据库
            saved_books, saved_snapshots, saved_rankings = await self._save_data(
                books, snapshots, rankings, task_id
            )

            result = {
                "success": True,
                "books_new": len([b for b in saved_books if b]),
                "books_updated": len(saved_books) - len([b for b in saved_books if b]),
                "total_books": len(books),
                "snapshots_created": len(saved_snapshots),
                "rankings_created": len(saved_rankings),
            }

            logger.info(f"分类页面爬取完成 {task_id}: {result}")
            return result

        except Exception as e:
            logger.error(f"分类页面爬取失败 {task_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "books_new": 0,
                "books_updated": 0,
                "total_books": 0,
            }

    def _build_url(self, task_id: str) -> str:
        """根据task_id构建页面URL"""
        # 基础URL模板
        base_url = "https://app-cdn.jjwxc.com/bookstore/getFullPageV1"

        # 根据不同的task_id构建不同的参数
        if task_id == "index":
            return f"{base_url}?channel=index&version=19"
        else:
            # 其他分类页面
            return f"{base_url}?channel={task_id}&version=19"

    def _parse_page_data(
        self, data: Dict[str, Any], task_id: str
    ) -> Tuple[List[Book], List[BookSnapshot], List[RankingSnapshot]]:
        """解析分类页面API响应数据"""
        books = []
        snapshots = []
        rankings = []

        try:
            # 检查API响应状态
            if data.get("code") != "200":
                raise ValueError(f"API响应错误: {data.get('message', '未知错误')}")

            data_sections = data.get("data", [])
            current_time = datetime.now()

            # 处理不同的数据结构
            for section in data_sections:
                ranking_id = section.get("rankid", "")
                ranking_name = section.get("channelName", "")
                section_books = section.get("data", [])

                # 处理每个排行榜的书籍
                for position, item in enumerate(section_books, 1):
                    try:
                        # 解析书籍基本信息
                        book = self._parse_book_info(item)
                        books.append(book)

                        # 解析书籍快照数据
                        snapshot = self._parse_book_snapshot(item, current_time)
                        snapshots.append(snapshot)

                        # 创建排行榜快照
                        if ranking_id:
                            ranking_snapshot = RankingSnapshot(
                                ranking_id=ranking_id,
                                book_id=book.book_id,
                                position=position,
                                snapshot_time=current_time,
                            )
                            rankings.append(ranking_snapshot)

                    except Exception as e:
                        logger.warning(
                            f"解析单本书籍失败: {e}, 书籍数据: {item.get('novelId', 'unknown')}"
                        )
                        continue

        except Exception as e:
            logger.error(f"分类页面数据解析失败 {task_id}: {e}")
            raise

        logger.info(
            f"分类页面数据解析完成 {task_id}: {len(books)} 本书籍, {len(rankings)} 个排名"
        )
        return books, snapshots, rankings

    def _parse_book_info(self, item: Dict[str, Any]) -> Book:
        """解析单本书籍的基本信息"""
        # 处理字段名的多种变体（API返回可能不一致）
        book_id = str(item.get("novelId") or item.get("novelid", ""))
        title = item.get("novelName") or item.get("novelname", "")
        author_id = str(item.get("authorId") or item.get("authorid", ""))
        author_name = item.get("authorName") or item.get("authorname", "")
        novel_class = item.get("novelClass") or item.get("novelclass", "")
        tags = item.get("tags", "")

        # 数据清洗
        if not book_id or not title:
            raise ValueError(f"书籍数据不完整: ID={book_id}, Title={title}")

        return Book(
            book_id=book_id,
            title=title.strip(),
            author_id=author_id,
            author_name=author_name.strip() if author_name else "",
            novel_class=novel_class.strip() if novel_class else "",
            tags=tags.strip() if tags else "",
            first_seen=datetime.now(),
            last_updated=datetime.now(),
        )

    def _parse_book_snapshot(
        self, item: Dict[str, Any], snapshot_time: datetime
    ) -> BookSnapshot:
        """解析书籍快照数据"""
        book_id = str(item.get("novelId") or item.get("novelid", ""))

        # 解析统计数据
        total_clicks = self._parse_numeric_field(item, ["novelScore"], 0)
        total_favorites = self._parse_numeric_field(
            item, ["favCount", "totalFavorites"], 0
        )
        comment_count = self._parse_numeric_field(item, ["commentCount"], 0)
        chapter_count = self._parse_numeric_field(item, ["chapterCount"], 0)
        word_count = self._parse_word_count(item.get("novelSizeformat", ""))

        return BookSnapshot(
            book_id=book_id,
            total_clicks=total_clicks,
            total_favorites=total_favorites,
            comment_count=comment_count,
            chapter_count=chapter_count,
            word_count=word_count,
            snapshot_time=snapshot_time,
        )

    def _parse_numeric_field(
        self, item: Dict[str, Any], field_names: List[str], default: int = 0
    ) -> int:
        """解析数值字段（处理字符串格式的数字）"""
        for field_name in field_names:
            value = item.get(field_name)
            if value is not None:
                try:
                    # 处理字符串格式的数字
                    if isinstance(value, str):
                        # 去除逗号
                        value = value.replace(",", "")

                        # 处理"亿"单位
                        if "亿" in value:
                            base_num = float(value.replace("亿", ""))
                            return int(base_num * 100000000)

                        # 处理"万"单位
                        if "万" in value:
                            base_num = float(value.replace("万", ""))
                            return int(base_num * 10000)

                        # 处理"千"单位
                        if "千" in value:
                            base_num = float(value.replace("千", ""))
                            return int(base_num * 1000)

                    return int(float(value))
                except (ValueError, TypeError):
                    continue

        return default

    def _parse_word_count(self, size_format: str) -> int:
        """解析字数格式，如 '10.14万' -> 101400"""
        if not size_format:
            return 0

        try:
            # 去除多余空格
            size_format = size_format.strip()

            # 处理"万"单位
            if "万" in size_format:
                base_num = float(size_format.replace("万", ""))
                return int(base_num * 10000)

            # 处理纯数字
            return int(float(size_format))

        except (ValueError, TypeError):
            logger.warning(f"无法解析字数格式: {size_format}")
            return 0

    async def _save_data(
        self,
        books: List[Book],
        snapshots: List[BookSnapshot],
        rankings: List[RankingSnapshot],
        task_id: str,
    ) -> Tuple[List[Book], List[BookSnapshot], List[RankingSnapshot]]:
        """保存数据到数据库"""
        saved_books = []
        saved_snapshots = []
        saved_rankings = []

        try:
            async with get_session() as session:
                book_dao = BookDAO(session)
                ranking_dao = RankingDAO(session)

                # 保存或更新书籍信息
                for book in books:
                    try:
                        book_data = {
                            "book_id": book.book_id,
                            "title": book.title,
                            "author_id": book.author_id,
                            "author_name": book.author_name,
                            "novel_class": book.novel_class,
                            "tags": book.tags,
                            "first_seen": book.first_seen,
                            "last_updated": book.last_updated,
                        }
                        saved_book = book_dao.create_or_update(book_data)
                        saved_books.append(saved_book)
                    except Exception as e:
                        logger.error(f"保存书籍失败 {book.book_id}: {e}")
                        saved_books.append(None)

                # 批量保存书籍快照
                try:
                    snapshots_data = []
                    for snapshot in snapshots:
                        snapshot_data = {
                            "book_id": snapshot.book_id,
                            "total_clicks": snapshot.total_clicks,
                            "total_favorites": snapshot.total_favorites,
                            "comment_count": snapshot.comment_count,
                            "chapter_count": snapshot.chapter_count,
                            "word_count": snapshot.word_count,
                            "snapshot_time": snapshot.snapshot_time,
                        }
                        snapshots_data.append(snapshot_data)

                    saved_snapshots = book_dao.batch_create_snapshots(snapshots_data)
                except Exception as e:
                    logger.error(f"批量保存书籍快照失败: {e}")

                # 批量保存排行榜快照
                try:
                    rankings_data = []
                    for ranking in rankings:
                        ranking_data = {
                            "ranking_id": ranking.ranking_id,
                            "book_id": ranking.book_id,
                            "position": ranking.position,
                            "snapshot_time": ranking.snapshot_time,
                        }
                        rankings_data.append(ranking_data)

                    saved_rankings = ranking_dao.batch_create_snapshots(rankings_data)
                except Exception as e:
                    logger.error(f"批量保存排行榜快照失败: {e}")

                session.commit()

        except Exception as e:
            logger.error(f"数据保存失败 {task_id}: {e}")
            raise

        logger.info(
            f"数据保存完成 {task_id}: {len(saved_books)} 本书籍, {len(saved_snapshots)} 个书籍快照, {len(saved_rankings)} 个排行榜快照"
        )
        return saved_books, saved_snapshots, saved_rankings

    async def close(self):
        """关闭资源"""
        await self.http_client.close()
