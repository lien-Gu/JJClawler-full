"""
书籍业务逻辑服务 - 集成DAO功能的简化版本
"""

from datetime import datetime, timedelta
from typing import Any
from typing import Tuple

from fastapi import HTTPException
from sqlalchemy import desc, func, select, text
from sqlalchemy.orm import Session

from app.database.sql.book_queries import (
    BOOK_HISTORY_QUERY,
)
from ..db.book import Book, BookSnapshot


class BookService:
    """书籍业务逻辑服务 - 直接操作数据库"""

    # ==================== 爬虫使用的方法 ====================
    @staticmethod
    def get_book_by_novel_id(db: Session, novel_id: int | str) -> Book | None:
        """
        根据novel_id获取书籍

        :param db: 数据库会话
        :param novel_id: 书籍novel_id，支持字符串和整数
        :return: Book对象或None
        """
        try:
            novel_id_int = int(novel_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=404, detail=f"无效的novel_id: {novel_id}")
        book = db.scalar(select(Book).where(Book.novel_id == novel_id_int))
        if not book:
            raise HTTPException(status_code=404, detail=f"书籍不存在: {novel_id}")
        return book

    @staticmethod
    def create_book(db: Session, book_data: dict[str, Any]) -> Book:
        """
        创建书籍

        :param db: 数据库会话
        :param book_data: 书籍数据
        :return: 书籍数据库对象
        """
        book = Book(**book_data)
        db.add(book)
        db.commit()
        db.refresh(book)
        return book

    @staticmethod
    def update_book(db: Session, book: Book, book_data: dict[str, Any]) -> Book:
        """
        更新书籍

        :param db: 数据库会话
        :param book: 书籍数据库对象
        :param book_data: 书籍数据
        :return: 更新后的书籍数据库对象
        """
        for key, value in book_data.items():
            if hasattr(book, key):
                setattr(book, key, value)
        book.updated_at = datetime.now()
        db.add(book)
        db.commit()
        db.refresh(book)
        return book

    def create_or_update_book(self, db: Session, book_data: dict[str, Any]) -> Book:
        """
        根据novel_id创建或更新书籍
        :param db:
        :param book_data:
        :return:
        """
        novel_id = book_data.get("novel_id")
        if not novel_id:
            raise ValueError("novel_id is required")
        book = self.get_book_by_novel_id(db, novel_id)
        if book:
            return self.update_book(db, book, book_data)
        else:
            return self.create_book(db, book_data)

    @staticmethod
    def batch_create_book_snapshots(db: Session, snapshots: list[dict[str, Any]]) -> list[BookSnapshot]:
        """
        批量创建书籍快照

        :param db:
        :param snapshots:
        :return:
        """
        snapshot_objs = [BookSnapshot(**snapshot) for snapshot in snapshots]
        db.add_all(snapshot_objs)
        db.commit()
        return snapshot_objs

    @staticmethod
    def get_book_by_id(db: Session, book_id: int) -> Book | None:
        """
        根据ID获取书籍

        :param db:
        :param book_id:
        :return:
        """
        return db.get(Book, book_id)

    @staticmethod
    def get_books_by_novel_ids(db: Session, novel_ids: list[int]) -> list[Book]:
        """
        根据novel_id列表获取书籍列表
        :param db:
        :param novel_ids:
        :return:
        """
        if not novel_ids:
            return []
        return list(db.scalars(select(Book).where(Book.novel_id.in_(novel_ids))).all())

    @staticmethod
    def get_books_with_pagination(
            db: Session,
            page: int = 1,
            size: int = 20,
            filters: dict[str, Any] | None = None,
    ) -> tuple[list[Book], int]:
        """
        分页获取书籍列表
        :param db:
        :param page:
        :param size:
        :param filters:
        :return:
        """
        # 构建查询
        query = select(Book)
        count_query = select(func.count(Book.id))
        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(Book, key):
                    query = query.where(getattr(Book, key) == value)
                    count_query = count_query.where(getattr(Book, key) == value)
        # 获取数据
        books = list(
            db.execute(
                query.order_by(desc(Book.created_at)).offset((page - 1) * size).limit(size)
            ).scalars()
        )

        total = db.scalar(count_query)
        total_pages = (total + size - 1) // size if total > 0 else 0

        return books, total_pages

    @staticmethod
    def get_latest_snapshot_by_book_id(db: Session, book_id: int) -> BookSnapshot | None:
        """
        获取书籍最新快照

        :param db:
        :param book_id:
        :return:
        """
        return db.scalar(
            select(BookSnapshot)
            .where(BookSnapshot.book_id == book_id)
            .order_by(desc(BookSnapshot.snapshot_time))
            .limit(1)
        )

    def get_book_detail_with_latest_snapshot(
            self, db: Session, book_id: int
    ) -> Tuple[Book, BookSnapshot]:
        """
        获取书籍详情和最新快照数据

        :param db:
        :param book_id:
        :return:
        """
        book = self.get_book_by_id(db, book_id)
        if not book:
            return None
        latest_snapshot = self.get_latest_snapshot_by_book_id(db, book.id)
        return book, latest_snapshot

    @staticmethod
    def get_snapshots_by_book_id(
            db: Session,
            book_id: int,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
            limit: int = 30,
    ) -> list[BookSnapshot]:
        """
        获取书籍快照列表

        :param db:
        :param book_id:
        :param start_time:
        :param end_time:
        :param limit:
        :return:
        """
        query = select(BookSnapshot).where(BookSnapshot.book_id == book_id)

        if start_time:
            query = query.where(BookSnapshot.snapshot_time >= start_time)
        if end_time:
            query = query.where(BookSnapshot.snapshot_time <= end_time)

        result = db.execute(
            query.order_by(desc(BookSnapshot.snapshot_time)).limit(limit)
        )
        return list(result.scalars())

    @staticmethod
    def get_historical_snapshots(
            db: Session, book_id: int, interval: str, count: int
    ) -> list[BookSnapshot]:
        """
        获取历史快照

        :param db: 数据库会话
        :param book_id: 书籍ID
        :param interval: 时间间隔 (hour/day/week/month)
        :param count: 数量
        :return: 每个时间间隔的第一个快照列表
        """
        # 计算查询时间范围
        end_time = datetime.now()
        time_deltas = {
            "hour": timedelta(hours=count),
            "day": timedelta(days=count),
            "week": timedelta(weeks=count),
            "month": timedelta(days=count * 30),
        }

        if interval not in time_deltas:
            raise ValueError(f"不支持的时间间隔: {interval}")

        start_time = end_time - time_deltas[interval]

        result = db.execute(
            text(BOOK_HISTORY_QUERY),
            {
                "book_id": book_id,
                "interval": interval,
                "start_time": start_time,
                "end_time": end_time,
            }
        )

        # 转换为BookSnapshot对象
        return [
            BookSnapshot(
                id=row.id,
                book_id=row.book_id,
                favorites=row.favorites,
                clicks=row.clicks,
                comments=row.comments,
                word_count=row.word_count,
                status=row.status,
                snapshot_time=row.snapshot_time
            )
            for row in result
        ]
