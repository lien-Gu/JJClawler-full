"""
书籍业务逻辑服务
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from ..dao.book_dao import BookDAO, BookSnapshotDAO
from ..db.book import Book, BookSnapshot


class BookService:
    """书籍业务逻辑服务"""
    
    def __init__(self):
        self.book_dao = BookDAO()
        self.book_snapshot_dao = BookSnapshotDAO()
    
    def get_book_by_id(self, db: Session, book_id: int) -> Optional[Book]:
        """根据ID获取书籍"""
        return self.book_dao.get_by_id(db, book_id)
    
    def get_book_by_novel_id(self, db: Session, novel_id: int) -> Optional[Book]:
        """根据小说ID获取书籍"""
        return self.book_dao.get_by_novel_id(db, novel_id)
    
    def search_books(
        self, 
        db: Session, 
        keyword: str, 
        page: int = 1, 
        size: int = 20
    ) -> List[Book]:
        """搜索书籍"""
        skip = (page - 1) * size
        
        # 先按标题搜索
        books_by_title = self.book_dao.search_by_title(db, keyword, limit=size)
        
        # 如果结果不够，再按作者搜索
        if len(books_by_title) < size:
            remaining = size - len(books_by_title)
            books_by_author = self.book_dao.search_by_author(db, keyword, limit=remaining)
            
            # 合并结果，去重
            book_ids = {book.id for book in books_by_title}
            for book in books_by_author:
                if book.id not in book_ids:
                    books_by_title.append(book)
                    if len(books_by_title) >= size:
                        break
        
        return books_by_title[skip:skip + size]
    
    def get_book_detail_with_latest_snapshot(
        self, 
        db: Session, 
        book_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取书籍详情和最新快照数据"""
        book = self.book_dao.get_by_id(db, book_id)
        if not book:
            return None
        
        latest_snapshot = self.book_snapshot_dao.get_latest_by_book_id(db, book_id)
        
        return {
            "book": book,
            "latest_snapshot": latest_snapshot,
            "statistics": self.book_snapshot_dao.get_statistics_by_book_id(db, book_id)
        }
    
    def get_book_trend(
        self, 
        db: Session, 
        book_id: int, 
        days: int = 7
    ) -> List[BookSnapshot]:
        """获取书籍趋势数据（原始快照数据）"""
        start_time = datetime.now() - timedelta(days=days)
        return self.book_snapshot_dao.get_trend_by_book_id(
            db, book_id, start_time=start_time, limit=days * 24  # 假设每小时一个快照
        )

    def get_book_trend_hourly(
        self,
        db: Session,
        book_id: int,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        按小时获取书籍趋势数据
        
        Args:
            db: 数据库会话
            book_id: 书籍ID
            hours: 统计小时数
            
        Returns:
            List[Dict]: 按小时聚合的趋势数据
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        return self.book_snapshot_dao.get_trend_by_book_id_with_interval(
            db, book_id, start_time, end_time, "hour"
        )

    def get_book_trend_daily(
        self,
        db: Session,
        book_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        按天获取书籍趋势数据
        
        Args:
            db: 数据库会话
            book_id: 书籍ID
            days: 统计天数
            
        Returns:
            List[Dict]: 按天聚合的趋势数据
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        return self.book_snapshot_dao.get_trend_by_book_id_with_interval(
            db, book_id, start_time, end_time, "day"
        )

    def get_book_trend_weekly(
        self,
        db: Session,
        book_id: int,
        weeks: int = 4
    ) -> List[Dict[str, Any]]:
        """
        按周获取书籍趋势数据
        
        Args:
            db: 数据库会话
            book_id: 书籍ID
            weeks: 统计周数
            
        Returns:
            List[Dict]: 按周聚合的趋势数据
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(weeks=weeks)
        
        return self.book_snapshot_dao.get_trend_by_book_id_with_interval(
            db, book_id, start_time, end_time, "week"
        )

    def get_book_trend_monthly(
        self,
        db: Session,
        book_id: int,
        months: int = 3
    ) -> List[Dict[str, Any]]:
        """
        按月获取书籍趋势数据
        
        Args:
            db: 数据库会话
            book_id: 书籍ID
            months: 统计月数
            
        Returns:
            List[Dict]: 按月聚合的趋势数据
        """
        end_time = datetime.now()
        # 使用更精确的月份计算
        start_time = end_time - timedelta(days=months * 30)  # 近似计算
        
        return self.book_snapshot_dao.get_trend_by_book_id_with_interval(
            db, book_id, start_time, end_time, "month"
        )

    def get_book_trend_with_interval(
        self,
        db: Session,
        book_id: int,
        period_count: int = 7,
        interval: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        按指定时间间隔获取书籍趋势数据（统一入口函数）
        
        Args:
            db: 数据库会话
            book_id: 书籍ID
            period_count: 时间周期数量
            interval: 时间间隔 ('hour', 'day', 'week', 'month')
            
        Returns:
            List[Dict]: 按时间间隔聚合的趋势数据
        """
        if interval == "hour":
            return self.get_book_trend_hourly(db, book_id, period_count)
        elif interval == "day":
            return self.get_book_trend_daily(db, book_id, period_count)
        elif interval == "week":
            return self.get_book_trend_weekly(db, book_id, period_count)
        elif interval == "month":
            return self.get_book_trend_monthly(db, book_id, period_count)
        else:
            raise ValueError(f"不支持的时间间隔: {interval}")
    
    def create_or_update_book(self, db: Session, book_data: Dict[str, Any]) -> Book:
        """创建或更新书籍"""
        return self.book_dao.create_or_update_by_novel_id(db, book_data)
    
    def create_book_snapshot(self, db: Session, snapshot_data: Dict[str, Any]) -> BookSnapshot:
        """创建书籍快照"""
        return self.book_snapshot_dao.create(db, snapshot_data)
    
    def batch_create_book_snapshots(
        self, 
        db: Session, 
        snapshots: List[Dict[str, Any]]
    ) -> List[BookSnapshot]:
        """批量创建书籍快照"""
        return self.book_snapshot_dao.bulk_create(db, snapshots)
    
    def cleanup_old_snapshots(
        self, 
        db: Session, 
        book_id: int, 
        keep_days: int = 30,
        keep_count: int = 100
    ) -> int:
        """清理旧快照"""
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        return self.book_snapshot_dao.delete_old_snapshots(
            db, book_id, cutoff_time, keep_count
        )
    
    def get_book_statistics(self, db: Session, book_id: int) -> Dict[str, Any]:
        """获取书籍统计信息"""
        return self.book_snapshot_dao.get_statistics_by_book_id(db, book_id)
    
    def get_books_with_pagination(
        self, 
        db: Session, 
        page: int = 1, 
        size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分页获取书籍列表"""
        skip = (page - 1) * size
        
        books = self.book_dao.get_multi(db, skip=skip, limit=size, filters=filters)
        total = self.book_dao.count(db, filters=filters)
        
        return {
            "books": books,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": (total + size - 1) // size
        }
    
    def get_books_by_ids(self, db: Session, book_ids: List[int]) -> List[Book]:
        """根据ID列表获取书籍"""
        return [
            book for book_id in book_ids 
            if (book := self.book_dao.get_by_id(db, book_id)) is not None
        ]