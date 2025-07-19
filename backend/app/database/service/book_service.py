"""
书籍业务逻辑服务 - 集成DAO功能的简化版本
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

from ..db.book import Book, BookSnapshot
from ...models import BookResponse


class BookService:
    """书籍业务逻辑服务 - 直接操作数据库"""

    # ==================== 爬虫使用的方法 ====================
    
    def get_book_by_novel_id(self, db: Session, novel_id: int) -> Optional[Book]:
        """根据novel_id获取书籍"""
        return db.scalar(select(Book).where(Book.novel_id == novel_id))
    
    def create_book(self, db: Session, book_data: Dict[str, Any]) -> Book:
        """创建书籍"""
        book = Book(**book_data)
        db.add(book)
        db.commit()
        db.refresh(book)
        return book
    
    def update_book(self, db: Session, book: Book, book_data: Dict[str, Any]) -> Book:
        """更新书籍"""
        for key, value in book_data.items():
            if hasattr(book, key):
                setattr(book, key, value)
        book.updated_at = datetime.now()
        db.add(book)
        db.commit()
        db.refresh(book)
        return book
    
    def create_or_update_book(self, db: Session, book_data: Dict[str, Any]) -> Book:
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
        self, 
        db: Session, 
        snapshots: List[Dict[str, Any]]
    ) -> List[BookSnapshot]:
        """批量创建书籍快照"""
        snapshot_objs = [BookSnapshot(**snapshot) for snapshot in snapshots]
        db.add_all(snapshot_objs)
        db.commit()
        return snapshot_objs

    # ==================== API使用的方法 ====================
    
    def get_book_by_id(self, db: Session, book_id: int) -> Optional[Book]:
        """根据ID获取书籍"""
        return db.get(Book, book_id)
    
    def get_books_by_novel_ids(self, db: Session, novel_ids: List[int]) -> List[Book]:
        """根据novel_id列表获取书籍"""
        if not novel_ids:
            return []
        return db.scalars(select(Book).where(Book.novel_id.in_(novel_ids))).all()

    def get_books_with_pagination(
        self, 
        db: Session, 
        page: int = 1, 
        size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Book], int]:
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
        books = list(db.execute(
            query.order_by(desc(Book.created_at))
            .offset(skip)
            .limit(size)
        ).scalars())
        
        total = db.scalar(count_query)
        total_pages = (total + size - 1) // size if total > 0 else 0
        
        return books, total_pages

    def search_books(
        self,
        db: Session,
        keyword: str,
        page: int = 1,
        size: int = 20
    ) -> List[Book]:
        """搜索书籍（API使用）"""
        result = db.execute(
            select(Book)
            .where(Book.title.like(f"%{keyword}%"))
            .limit(size)
        )
        return list(result.scalars())

    def get_latest_snapshot_by_book_id(
        self,
        db: Session,
        book_id: int
    ) -> Optional[BookSnapshot]:
        """获取书籍最新快照"""
        return db.scalar(
            select(BookSnapshot)
            .where(BookSnapshot.book_id == book_id)
            .order_by(desc(BookSnapshot.snapshot_time))
            .limit(1)
        )

    def get_book_statistics(self, db: Session, book_id: int) -> Dict[str, Any]:
        """获取书籍统计信息"""
        result = db.execute(
            select(
                func.count(BookSnapshot.id).label("total_snapshots"),
                func.max(BookSnapshot.favorites).label("max_favorites"),
                func.max(BookSnapshot.clicks).label("max_clicks"),
                func.max(BookSnapshot.comments).label("max_comments"),
                func.min(BookSnapshot.snapshot_time).label("first_snapshot_time"),
                func.max(BookSnapshot.snapshot_time).label("last_snapshot_time")
            ).where(BookSnapshot.book_id == book_id)
        ).first()

        if result and result.total_snapshots > 0:
            return {
                "total_snapshots": result.total_snapshots or 0,
                "max_favorites": result.max_favorites or 0,
                "max_clicks": result.max_clicks or 0,
                "max_comments": result.max_comments or 0,
                "first_snapshot_time": result.first_snapshot_time,
                "last_snapshot_time": result.last_snapshot_time
            }
        return {}

    def get_book_detail_with_latest_snapshot(
        self, 
        db: Session, 
        book_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取书籍详情和最新快照数据"""
        book = self.get_book_by_id(db, book_id)
        if not book:
            return None
        
        latest_snapshot = self.get_latest_snapshot_by_book_id(db, book.id)
        statistics = self.get_book_statistics(db, book.id)
        
        return {
            "book": book,
            "latest_snapshot": latest_snapshot,
            "statistics": statistics
        }

    def get_snapshots_by_book_id(
        self,
        db: Session,
        book_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 30
    ) -> List[BookSnapshot]:
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
        self,
        db: Session,
        book_id: int,
        days: int = 7
    ) -> List[BookSnapshot]:
        """获取书籍趋势数据（原始快照）"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        return self.get_snapshots_by_book_id(db, book_id, start_time, end_time)

    def _get_aggregated_trend_data(
        self,
        db: Session,
        book_id: int,
        start_time: datetime,
        end_time: datetime,
        time_format: str
    ) -> List[Dict[str, Any]]:
        """获取聚合趋势数据的通用方法"""
        from sqlalchemy import text
        
        query = text(f"""
            SELECT 
                strftime('{time_format}', snapshot_time) as time_period,
                AVG(favorites) as avg_favorites,
                AVG(clicks) as avg_clicks,
                AVG(comments) as avg_comments,
                MAX(favorites) as max_favorites,
                MAX(clicks) as max_clicks,
                MIN(favorites) as min_favorites,
                MIN(clicks) as min_clicks,
                COUNT(*) as snapshot_count,
                MIN(snapshot_time) as period_start,
                MAX(snapshot_time) as period_end
            FROM book_snapshots
            WHERE book_id = :book_id 
                AND snapshot_time >= :start_time 
                AND snapshot_time <= :end_time
            GROUP BY strftime('{time_format}', snapshot_time)
            ORDER BY period_start DESC
        """)

        result = db.execute(query, {
            "book_id": book_id,
            "start_time": start_time,
            "end_time": end_time
        })

        trend_data = []
        for row in result:
            trend_data.append({
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
                "period_end": row.period_end
            })

        return trend_data

    def get_book_trend_hourly(
        self,
        db: Session,
        book_id: int,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """按小时获取书籍趋势数据"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        return self._get_aggregated_trend_data(db, book_id, start_time, end_time, '%Y-%m-%d %H')
    
    def get_book_trend_daily(
        self,
        db: Session,
        book_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """按天获取书籍趋势数据"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        return self._get_aggregated_trend_data(db, book_id, start_time, end_time, '%Y-%m-%d')
    
    def get_book_trend_weekly(
        self,
        db: Session,
        book_id: int,
        weeks: int = 4
    ) -> List[Dict[str, Any]]:
        """按周获取书籍趋势数据"""
        end_time = datetime.now()
        start_time = end_time - timedelta(weeks=weeks)
        return self._get_aggregated_trend_data(db, book_id, start_time, end_time, '%Y-W%W')
    
    def get_book_trend_monthly(
        self,
        db: Session,
        book_id: int,
        months: int = 3
    ) -> List[Dict[str, Any]]:
        """按月获取书籍趋势数据"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=months * 30)
        return self._get_aggregated_trend_data(db, book_id, start_time, end_time, '%Y-%m')

    def get_book_trend_with_interval(
        self,
        db: Session,
        book_id: int,
        period_count: int,
        interval: str
    ) -> List[Dict[str, Any]]:
        """按指定时间间隔获取书籍趋势数据（API使用）"""
        end_time = datetime.now()
        
        time_formats = {
            "hour": ('%Y-%m-%d %H', timedelta(hours=period_count)),
            "day": ('%Y-%m-%d', timedelta(days=period_count)),
            "week": ('%Y-W%W', timedelta(weeks=period_count)),
            "month": ('%Y-%m', timedelta(days=period_count * 30))
        }
        
        if interval not in time_formats:
            raise ValueError(f"不支持的时间间隔: {interval}")
        
        time_format, time_delta = time_formats[interval]
        start_time = end_time - time_delta
        
        return self._get_aggregated_trend_data(db, book_id, start_time, end_time, time_format)