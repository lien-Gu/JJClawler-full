"""
书籍业务逻辑服务 - 集成DAO功能的简化版本
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select, text
from sqlalchemy.orm import Session

from ..db.book import Book, BookSnapshot
from app.database.sql.book_queries import (
    BOOK_HOURLY_SNAPSHOTS_QUERY,
    BOOK_DAILY_ONE_OCLOCK_SNAPSHOTS_QUERY,
    get_aggregated_trend_query,
)


class BookService:
    """书籍业务逻辑服务 - 直接操作数据库"""

    # ==================== 爬虫使用的方法 ====================

    def get_book_by_novel_id(self, db: Session, novel_id: int) -> Book | None:
        """根据novel_id获取书籍"""
        return db.scalar(select(Book).where(Book.novel_id == novel_id))

    def create_book(self, db: Session, book_data: dict[str, Any]) -> Book:
        """创建书籍"""
        book = Book(**book_data)
        db.add(book)
        db.commit()
        db.refresh(book)
        return book

    def update_book(self, db: Session, book: Book, book_data: dict[str, Any]) -> Book:
        """更新书籍"""
        for key, value in book_data.items():
            if hasattr(book, key):
                setattr(book, key, value)
        book.updated_at = datetime.now()
        db.add(book)
        db.commit()
        db.refresh(book)
        return book

    def create_or_update_book(self, db: Session, book_data: dict[str, Any]) -> Book:
        """根据novel_id创建或更新书籍"""
        novel_id = book_data.get("novel_id")
        if not novel_id:
            raise ValueError("novel_id is required")

        book = self.get_book_by_novel_id(db, novel_id)
        if book:
            return self.update_book(db, book, book_data)
        else:
            return self.create_book(db, book_data)

    def batch_create_book_snapshots(
        self, db: Session, snapshots: list[dict[str, Any]]
    ) -> list[BookSnapshot]:
        """批量创建书籍快照"""
        snapshot_objs = [BookSnapshot(**snapshot) for snapshot in snapshots]
        db.add_all(snapshot_objs)
        db.commit()
        return snapshot_objs

    # ==================== API使用的方法 ====================

    def get_book_by_id(self, db: Session, book_id: int) -> Book | None:
        """根据ID获取书籍"""
        return db.get(Book, book_id)

    def get_books_by_novel_ids(self, db: Session, novel_ids: list[int]) -> list[Book]:
        """根据novel_id列表获取书籍"""
        if not novel_ids:
            return []
        return db.scalars(select(Book).where(Book.novel_id.in_(novel_ids))).all()

    def get_books_with_pagination(
        self,
        db: Session,
        page: int = 1,
        size: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[Book], int]:
        """分页获取书籍列表"""
        skip = (page - 1) * size

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
                query.order_by(desc(Book.created_at)).offset(skip).limit(size)
            ).scalars()
        )

        total = db.scalar(count_query)
        total_pages = (total + size - 1) // size if total > 0 else 0

        return books, total_pages

    def search_books(
        self, db: Session, keyword: str, page: int = 1, size: int = 20
    ) -> list[Book]:
        """搜索书籍（API使用）"""
        result = db.execute(
            select(Book).where(Book.title.like(f"%{keyword}%")).limit(size)
        )
        return list(result.scalars())

    def get_latest_snapshot_by_book_id(
        self, db: Session, book_id: int
    ) -> BookSnapshot | None:
        """获取书籍最新快照"""
        return db.scalar(
            select(BookSnapshot)
            .where(BookSnapshot.book_id == book_id)
            .order_by(desc(BookSnapshot.snapshot_time))
            .limit(1)
        )

    def get_book_statistics(self, db: Session, book_id: int) -> dict[str, Any]:
        """获取书籍统计信息"""
        result = db.execute(
            select(
                func.count(BookSnapshot.id).label("total_snapshots"),
                func.max(BookSnapshot.favorites).label("max_favorites"),
                func.max(BookSnapshot.clicks).label("max_clicks"),
                func.max(BookSnapshot.comments).label("max_comments"),
                func.min(BookSnapshot.snapshot_time).label("first_snapshot_time"),
                func.max(BookSnapshot.snapshot_time).label("last_snapshot_time"),
            ).where(BookSnapshot.book_id == book_id)
        ).first()

        if result and result.total_snapshots > 0:
            return {
                "total_snapshots": result.total_snapshots or 0,
                "max_favorites": result.max_favorites or 0,
                "max_clicks": result.max_clicks or 0,
                "max_comments": result.max_comments or 0,
                "first_snapshot_time": result.first_snapshot_time,
                "last_snapshot_time": result.last_snapshot_time,
            }
        return {}

    def get_book_detail_with_latest_snapshot(
        self, db: Session, book_id: int
    ) -> dict[str, Any] | None:
        """获取书籍详情和最新快照数据"""
        book = self.get_book_by_id(db, book_id)
        if not book:
            return None

        latest_snapshot = self.get_latest_snapshot_by_book_id(db, book.id)
        statistics = self.get_book_statistics(db, book.id)

        return {
            "book": book,
            "latest_snapshot": latest_snapshot,
            "statistics": statistics,
        }

    def get_snapshots_by_book_id(
        self,
        db: Session,
        book_id: int,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 30,
    ) -> list[BookSnapshot]:
        """获取书籍快照列表"""
        query = select(BookSnapshot).where(BookSnapshot.book_id == book_id)

        if start_time:
            query = query.where(BookSnapshot.snapshot_time >= start_time)
        if end_time:
            query = query.where(BookSnapshot.snapshot_time <= end_time)

        result = db.execute(
            query.order_by(desc(BookSnapshot.snapshot_time)).limit(limit)
        )
        return list(result.scalars())

    def get_book_trend(
        self, db: Session, book_id: int, duration: str = "day"
    ) -> list[BookSnapshot]:
        """
        获取书籍趋势数据（智能快照选择）

        Args:
            db: 数据库会话
            book_id: 书籍ID
            duration: 时间范围
                - day: 返回24小时内每个小时的快照
                - week: 返回一周内每个小时的快照
                - month: 返回一个月内每天1点的快照（或最接近1点的快照）
                - half-year: 返回半年内每天1点的快照（或最接近1点的快照）

        Returns:
            List[BookSnapshot]: 快照列表
        """
        if duration == "day":
            return self._get_hourly_snapshots(db, book_id, hours=24)
        elif duration == "week":
            return self._get_hourly_snapshots(db, book_id, hours=168)  # 7 * 24
        elif duration == "month":
            return self._get_daily_one_oclock_snapshots(db, book_id, days=30)
        elif duration == "half-year":
            return self._get_daily_one_oclock_snapshots(db, book_id, days=180)  # 6 * 30
        else:
            raise ValueError(f"不支持的duration类型: {duration}")

    def _get_hourly_snapshots(
        self, db: Session, book_id: int, hours: int
    ) -> list[BookSnapshot]:
        """获取指定小时数内每个小时的快照"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        # 使用导入的SQL查询
        query = text(BOOK_HOURLY_SNAPSHOTS_QUERY)

        result = db.execute(
            query, {"book_id": book_id, "start_time": start_time, "end_time": end_time}
        )

        snapshots = []
        for row in result:
            snapshot = BookSnapshot()
            snapshot.id = row.id
            snapshot.book_id = row.book_id
            snapshot.favorites = row.favorites
            snapshot.clicks = row.clicks
            snapshot.comments = row.comments
            snapshot.recommendations = row.recommendations
            snapshot.word_count = row.word_count
            snapshot.status = row.status
            snapshot.snapshot_time = row.snapshot_time
            snapshots.append(snapshot)

        return snapshots

    def _get_daily_one_oclock_snapshots(
        self, db: Session, book_id: int, days: int
    ) -> list[BookSnapshot]:
        """获取指定天数内每天1点的快照（或最接近1点的快照）"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # 使用导入的SQL查询
        query = text(BOOK_DAILY_ONE_OCLOCK_SNAPSHOTS_QUERY)

        result = db.execute(
            query, {"book_id": book_id, "start_time": start_time, "end_time": end_time}
        )

        snapshots = []
        for row in result:
            snapshot = BookSnapshot()
            snapshot.id = row.id
            snapshot.book_id = row.book_id
            snapshot.favorites = row.favorites
            snapshot.clicks = row.clicks
            snapshot.comments = row.comments
            snapshot.recommendations = row.recommendations
            snapshot.word_count = row.word_count
            snapshot.status = row.status
            snapshot.snapshot_time = row.snapshot_time
            snapshots.append(snapshot)

        return snapshots

    def _get_aggregated_trend_data(
        self,
        db: Session,
        book_id: int,
        start_time: datetime,
        end_time: datetime,
        time_format: str,
    ) -> list[dict[str, Any]]:
        """获取聚合趋势数据的通用方法"""
        # 使用导入的查询函数
        query_string = get_aggregated_trend_query(time_format)
        query = text(query_string)

        result = db.execute(
            query, {"book_id": book_id, "start_time": start_time, "end_time": end_time}
        )

        trend_data = []
        for row in result:
            trend_data.append(
                {
                    "time_period": row.time_period,
                    "avg_favorites": round(row.avg_favorites or 0, 2),
                    "avg_clicks": round(row.avg_clicks or 0, 2),
                    "avg_comments": round(row.avg_comments or 0, 2),
                    "max_favorites": row.max_favorites or 0,
                    "max_clicks": row.max_clicks or 0,
                    "min_favorites": row.min_favorites or 0,
                    "min_clicks": row.min_clicks or 0,
                    "snapshot_count": row.snapshot_count,
                    "period_start": row.period_start,
                    "period_end": row.period_end,
                }
            )

        return trend_data

    def get_book_trend_hourly(
        self, db: Session, book_id: int, hours: int = 24
    ) -> list[dict[str, Any]]:
        """按小时获取书籍趋势数据"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        return self._get_aggregated_trend_data(
            db, book_id, start_time, end_time, "%Y-%m-%d %H"
        )

    def get_book_trend_daily(
        self, db: Session, book_id: int, days: int = 7
    ) -> list[dict[str, Any]]:
        """按天获取书籍趋势数据"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        return self._get_aggregated_trend_data(
            db, book_id, start_time, end_time, "%Y-%m-%d"
        )

    def get_book_trend_weekly(
        self, db: Session, book_id: int, weeks: int = 4
    ) -> list[dict[str, Any]]:
        """按周获取书籍趋势数据"""
        end_time = datetime.now()
        start_time = end_time - timedelta(weeks=weeks)
        return self._get_aggregated_trend_data(
            db, book_id, start_time, end_time, "%Y-W%W"
        )

    def get_book_trend_monthly(
        self, db: Session, book_id: int, months: int = 3
    ) -> list[dict[str, Any]]:
        """按月获取书籍趋势数据"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=months * 30)
        return self._get_aggregated_trend_data(
            db, book_id, start_time, end_time, "%Y-%m"
        )

    def get_book_trend_with_interval(
        self, db: Session, book_id: int, period_count: int, interval: str
    ) -> list[dict[str, Any]]:
        """按指定时间间隔获取书籍趋势数据（API使用）"""
        end_time = datetime.now()

        time_formats = {
            "hour": ("%Y-%m-%d %H", timedelta(hours=period_count)),
            "day": ("%Y-%m-%d", timedelta(days=period_count)),
            "week": ("%Y-W%W", timedelta(weeks=period_count)),
            "month": ("%Y-%m", timedelta(days=period_count * 30)),
        }

        if interval not in time_formats:
            raise ValueError(f"不支持的时间间隔: {interval}")

        time_format, time_delta = time_formats[interval]
        start_time = end_time - time_delta

        return self._get_aggregated_trend_data(
            db, book_id, start_time, end_time, time_format
        )
