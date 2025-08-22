"""
书籍业务逻辑服务 - 集成DAO功能的简化版本
"""

from datetime import datetime, timedelta
from typing import Any, Optional, cast

from sqlalchemy import desc, func, select, text
from sqlalchemy.orm import Session

from app.database.sql.book_queries import (
    BOOK_HISTORY_QUERY,
)
from app.database.db.book import Book, BookSnapshot
from app.models import book
from app.utils import filter_dict, get_model_fields


class BookService:
    """书籍业务逻辑服务 - 直接操作数据库"""

    # ==================== 基础CRUD操作 ====================

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

        # 确保novel_id是整数类型
        try:
            novel_id = int(novel_id)
            book_data["novel_id"] = novel_id
        except (ValueError, TypeError):
            raise ValueError(f"Invalid novel_id format: {novel_id}")

        # 尝试获取已存在的书籍
        book = self.get_book_by_novel_id(db, novel_id)
        if book:
            return self.update_book(db, book, book_data)

        # 如果不存在，尝试创建新书籍
        try:
            return self.create_book(db, book_data)
        except Exception as e:
            # 如果创建失败（可能是并发导致的重复插入），再次尝试获取并更新
            error_str = str(e).lower()
            if "unique constraint failed" in error_str or "duplicate" in error_str:
                # 刷新会话，重新获取可能已经被其他事务创建的记录
                db.rollback()
                book = self.get_book_by_novel_id(db, novel_id)
                if book:
                    return self.update_book(db, book, book_data)
            # 如果仍然失败，重新抛出异常
            raise e

    @staticmethod
    def batch_create_book_snapshots(db: Session, snapshots: list[dict[str, Any]]) -> list[BookSnapshot]:
        """
        批量创建书籍快照

        :param db: 数据库会话对象，用于执行数据库操作
        :param snapshots: 快照数据列表，每个元素为包含BookSnapshot字段的字典
        :return: 创建后的BookSnapshot对象列表，包含自动生成的ID等信息
        """
        filtered_snapshots = [filter_dict(snapshot, BookSnapshot) for snapshot in snapshots]
        snapshot_objs = [BookSnapshot(**snapshot) for snapshot in filtered_snapshots]
        db.add_all(snapshot_objs)
        db.commit()
        return snapshot_objs

    # ==================== API操作 ====================

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
        ).scalars().first()
        if not book_record or not latest_snapshot:
            return None
        book_dict = {
            "novel_id": book_record.novel_id,
            "title": book_record.title
        }
        # 将SQLAlchemy对象转换为字典
        snapshot_dict = {
            "snapshot_time": latest_snapshot.snapshot_time,
            "favorites": latest_snapshot.favorites,
            "clicks": latest_snapshot.clicks,
            "comments": latest_snapshot.comments,
            "nutrition": latest_snapshot.nutrition,
            "word_counts": latest_snapshot.word_counts,
            "chapter_counts": latest_snapshot.chapter_counts,
            "status": latest_snapshot.status,
            "vip_chapter_id": getattr(latest_snapshot, 'vip_chapter_id', None) or 0
        }
        return book.BookDetail.model_validate({**book_dict, **snapshot_dict})




if __name__ == '__main__':
    from app.models.base import DataResponse
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from pathlib import Path
    import os

    # 构建数据库文件路径
    db_path = Path(__file__).parent.parent.parent.parent / "data" / "jjcrawler.db"
    db_url = f"sqlite:///{db_path.absolute()}"

    print(f"连接到爬虫数据库: {db_url}")

    # 检查数据库文件是否损坏，如果损坏则删除
    if db_path.exists():
        try:
            # 尝试简单的连接测试
            from sqlalchemy import text

            test_engine = create_engine(db_url, echo=False)
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("数据库文件正常")
        except Exception as e:
            print(f"数据库文件不存在: {e}")

    # 创建引擎和会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=create_engine(db_url, echo=False))
    db = SessionLocal()

    novel_id = 8953663
    book = BookService.get_book_by_novel_id(db, novel_id)

    # 通过novel_id获取详细信息
    book_detail = BookService.get_book_detail_by_novel_id(db, book.novel_id)

    res =  DataResponse(
        data=book_detail,
        message="获取书籍详情成功"
    )
    print(res)

