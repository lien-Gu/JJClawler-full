"""
书籍业务逻辑服务 - 集成DAO功能的简化版本
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Tuple, cast

from fastapi import HTTPException
from sqlalchemy import desc, func, select, text
from sqlalchemy.orm import Session

from app.database.sql.book_queries import (
    BOOK_HISTORY_QUERY,
)
from ..db.book import Book, BookSnapshot
from ...models import book
from ...utils import filter_dict, get_model_fields


class BookService:
    """书籍业务逻辑服务 - 直接操作数据库"""

    # ==================== 基础查询操作 ====================

    @staticmethod
    def get_book_by_novel_id(db: Session, novel_id: int) -> Optional[Book]:
        """
        根据novel_id获取书籍（现在作为主键）

        :param db: 数据库会话对象，用于执行数据库操作
        :param novel_id: 书籍主键novel_id，数据库中的唯一标识符
        :return: Book对象，如果存在则返回书籍实例，不存在则返回None
        """
        if not isinstance(novel_id, int):
            novel_id = cast(int, novel_id)
        return db.get(Book, novel_id)

    # ==================== 批量查询操作 ====================

    @staticmethod
    def get_books_by_novel_ids(db: Session, novel_ids: list[int]) -> list[Book]:
        """
        根据novel_id列表批量获取书籍

        :param db: 数据库会话对象，用于执行数据库操作
        :param novel_ids: novel_id列表，包含多个晋江文学城小说ID的整数列表
        :return: Book对象列表，按照novel_ids的顺序返回找到的书籍实例
        """
        if not novel_ids:
            return []
        return list(db.scalars(select(Book).where(Book.novel_id.in_(novel_ids))).all())

    @staticmethod
    def get_books_with_pagination(
            db: Session,
            page: int = 1,
            size: int = 20,
    ) -> tuple[list[book.BookBasic], int]:
        """
        分页获取书籍列表

        :param db: 数据库会话对象，用于执行数据库操作
        :param page: 页码，从1开始的页面索引，默认为第1页
        :param size: 每页数量，单页返回的最大记录数，默认20条，建议1-100之间
        :return: 元组(书籍列表, 总页数)，第一个元素为Book对象列表，第二个元素为总页数
        """
        query = select(Book).order_by(desc(Book.created_at))
        book_records = db.execute(query.offset((page - 1) * size).limit(size)).scalars()

        # 计算页码数
        total_books = db.scalar(select(func.count(Book.novel_id))) or 0
        import math
        total_pages = math.ceil(total_books * 1.0 / size)

        return [book.BookBasic.model_validate(i) for i in book_records], total_pages

    # ==================== 书籍CRUD操作 ====================

    @staticmethod
    def create_book(db: Session, book_data: dict[str, Any]) -> Book:
        """
        创建新书籍

        :param db: 数据库会话对象，用于执行数据库操作
        :param book_data: 书籍数据字典，包含novel_id、title等Book模型字段的键值对
        :return: 创建后的Book对象，包含自动生成的ID和时间戳等信息
        """
        filtered_data = filter_dict(book_data, Book)
        book_record = Book(**filtered_data)
        db.add(book_record)
        db.commit()
        db.refresh(book_record)
        return book_record

    @staticmethod
    def update_book(db: Session, book_record: Book, book_data: dict[str, Any]) -> Book:
        """
        更新现有书籍

        :param db: 数据库会话对象，用于执行数据库操作
        :param book_record: 要更新的Book对象实例，必须是已存在于数据库中的对象
        :param book_data: 更新数据字典，包含要更新的字段名和新值的键值对
        :return: 更新后的Book对象，updated_at字段会被自动设置为当前时间
        """
        filtered_data = filter_dict(book_data, Book)
        for key, value in filtered_data.items():
            setattr(book_record, key, value)
        book_record.updated_at = datetime.now()
        db.add(book_record)
        db.commit()
        db.refresh(book_record)
        return book_record

    def create_or_update_book(self, db: Session, book_data: dict[str, Any]) -> Book:
        """
        根据novel_id创建或更新书籍（Upsert操作）

        :param db: 数据库会话对象，用于执行数据库操作
        :param book_data: 书籍数据字典，必须包含novel_id字段，其他字段为Book模型的属性
        :return: 创建或更新后的Book对象
        :raises ValueError: 当book_data中缺少novel_id字段时抛出
        """
        novel_id = book_data.get("novel_id")
        if not novel_id:
            raise ValueError("novel_id is required")
        book = self.get_book_by_novel_id(db, novel_id)
        if book:
            return self.update_book(db, book, book_data)
        return self.create_book(db, book_data)

    # ==================== 快照查询操作 ====================

    @staticmethod
    def get_latest_snapshot_by_novel_id(db: Session, novel_id: int) -> Optional[BookSnapshot]:
        """
        获取指定书籍的最新快照

        :param db: 数据库会话对象，用于执行数据库操作
        :param novel_id: 书籍主键novel_id，对应Book.novel_id字段
        :return: BookSnapshot对象，如果存在快照则返回最新的一个，不存在则返回None
        """
        return db.scalar(
            select(BookSnapshot)
            .where(BookSnapshot.novel_id == novel_id)
            .order_by(desc(BookSnapshot.snapshot_time))
            .limit(1)
        )

    @staticmethod
    def get_snapshots_by_novel_id(
            db: Session,
            novel_id: int,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            limit: int = 30,
    ) -> list[BookSnapshot]:
        """
        获取指定书籍的快照列表（支持时间范围过滤）

        :param db: 数据库会话对象，用于执行数据库操作
        :param novel_id: 书籍主键novel_id，对应Book.novel_id字段
        :param start_time: 开始时间，可选，如果指定则只返回此时间之后的快照
        :param end_time: 结束时间，可选，如果指定则只返回此时间之前的快照
        :param limit: 返回记录数限制，默认30条，按时间倒序排列
        :return: BookSnapshot对象列表，按snapshot_time倒序排列
        """
        query = select(BookSnapshot).where(BookSnapshot.novel_id == novel_id)
        if start_time:
            query = query.where(BookSnapshot.snapshot_time >= start_time)
        if end_time:
            query = query.where(BookSnapshot.snapshot_time <= end_time)

        result = db.execute(
            query.order_by(desc(BookSnapshot.snapshot_time)).limit(limit)
        )
        return list(result.scalars())

    @staticmethod
    def get_historical_snapshots_by_novel_id(
            db: Session, novel_id: int, interval: str, count: int
    ) -> list[book.BookSnapshot]:
        """
        获取指定时间间隔的历史快照

        :param db: 数据库会话对象，用于执行数据库操作
        :param novel_id: 书籍主键novel_id，对应Book.novel_id字段
        :param interval: 时间间隔类型，支持"hour"（小时）、"day"（天）、"week"（周）、"month"（月）
        :param count: 时间段数量，表示向前追溯多少个时间间隔单位
        :return: BookSnapshot对象列表，每个时间间隔的第一个快照，按时间倒序排列
        :raises ValueError: 当interval参数不在支持的值范围内时抛出
        """
        # 计算查询时间范围
        end_time = datetime.now()
        time_deltas = {
            "hour": timedelta(hours=count),
            "day": timedelta(days=count),
            "week": timedelta(weeks=count),
            "month": timedelta(days=count * 30),  # 近似月份计算
        }

        if interval not in time_deltas:
            raise ValueError(f"不支持的时间间隔: {interval}")

        start_time = end_time - time_deltas[interval]
        result = db.execute(
            text(BOOK_HISTORY_QUERY),
            {
                "novel_id": novel_id,
                "interval": interval,
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        return [book.BookSnapshot.model_validate(row._asdict()) for row in result]

    # ==================== 快照写入操作 ====================

    @staticmethod
    def batch_create_book_snapshots(db: Session, snapshots: list[dict[str, Any]]) -> list[BookSnapshot]:
        """
        批量创建书籍快照

        :param db: 数据库会话对象，用于执行数据库操作
        :param snapshots: 快照数据列表，每个元素为包含BookSnapshot字段的字典
        :return: 创建后的BookSnapshot对象列表，包含自动生成的ID等信息
        """
        valid_fields = get_model_fields(BookSnapshot)
        filtered_snapshots = [filter_dict(snapshot, valid_fields) for snapshot in snapshots]
        snapshot_objs = [BookSnapshot(**snapshot) for snapshot in filtered_snapshots]
        db.add_all(snapshot_objs)
        db.commit()
        return snapshot_objs

    # ==================== 复合查询操作 ====================

    @staticmethod
    def get_book_detail_by_novel_id(db: Session, novel_id: int) -> Optional[book.BookDetail]:
        """
        获取书籍详情和最新快照数据, 并聚合成一个Pydantic模型返回。

        :param db: 数据库会话对象，用于执行数据库操作
        :param novel_id: 书籍主键novel_id，对应Book.novel_id字段
        :return: BookDetail Pydantic模型实例，如果书籍不存在则返回None
        """
        book_record = db.get(Book, novel_id)
        latest_snapshot = db.execute(
            select(BookSnapshot)
            .where(BookSnapshot.novel_id == novel_id)
            .order_by(desc(BookSnapshot.snapshot_time))
            .limit(1)
        ).first()
        if not book_record or not latest_snapshot:
            return None
        book_dict = {
            "novel_id": book_record.novel_id,
            "title": book_record.title
        }
        return book.BookDetail.model_validate({**book_dict, **latest_snapshot._asdict()})
