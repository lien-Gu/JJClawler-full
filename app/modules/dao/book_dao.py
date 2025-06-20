"""
Book数据访问对象

封装Book和BookSnapshot的数据库操作
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func, and_, or_, desc
from app.modules.database import get_session_sync
from app.modules.models import Book, BookSnapshot

logger = logging.getLogger(__name__)


class BookDAO:
    """Book数据访问对象"""
    
    def __init__(self):
        self._session: Optional[Session] = None
    
    @property
    def session(self) -> Session:
        """获取数据库会话"""
        if self._session is None:
            self._session = get_session_sync()
        return self._session
    
    def close(self):
        """关闭数据库会话"""
        if self._session:
            self._session.close()
            self._session = None

    # ==================== Book基础CRUD ====================
    
    def get_by_id(self, book_id: str) -> Optional[Book]:
        """根据书籍ID获取书籍信息"""
        statement = select(Book).where(Book.book_id == book_id)
        return self.session.exec(statement).first()
    
    def create(self, book_data: Dict[str, Any]) -> Book:
        """创建新书籍"""
        book = Book(**book_data)
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book
    
    def update(self, book_id: str, update_data: Dict[str, Any]) -> Optional[Book]:
        """更新书籍信息"""
        book = self.get_by_id(book_id)
        if book:
            for field, value in update_data.items():
                if hasattr(book, field):
                    setattr(book, field, value)
            book.last_updated = datetime.now()
            self.session.commit()
            self.session.refresh(book)
        return book
    
    def create_or_update(self, book_data: Dict[str, Any]) -> Book:
        """创建或更新书籍信息"""
        book_id = book_data["book_id"]
        existing_book = self.get_by_id(book_id)
        
        if existing_book:
            # 更新现有书籍
            for field, value in book_data.items():
                if hasattr(existing_book, field) and field != "book_id":
                    setattr(existing_book, field, value)
            existing_book.last_updated = datetime.now()
            self.session.commit()
            self.session.refresh(existing_book)
            return existing_book
        else:
            # 创建新书籍
            return self.create(book_data)
    
    def search(
        self, 
        title: Optional[str] = None,
        author: Optional[str] = None,
        novel_class: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[Book], int]:
        """搜索书籍"""
        statement = select(Book)
        
        # 构建查询条件
        conditions = []
        if title:
            conditions.append(Book.title.contains(title))
        if author:
            conditions.append(or_(
                Book.author_name.contains(author),
                Book.author_id == author
            ))
        if novel_class:
            conditions.append(Book.novel_class == novel_class)
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        # 获取总数
        count_statement = select(func.count(Book.id))
        if conditions:
            count_statement = count_statement.where(and_(*conditions))
        total = self.session.exec(count_statement).one()
        
        # 分页查询
        statement = statement.offset(offset).limit(limit).order_by(Book.last_updated.desc())
        books = list(self.session.exec(statement))
        
        return books, total

    # ==================== BookSnapshot操作 ====================
    
    def get_latest_snapshot(self, book_id: str) -> Optional[BookSnapshot]:
        """获取书籍最新快照"""
        statement = (
            select(BookSnapshot)
            .where(BookSnapshot.book_id == book_id)
            .order_by(BookSnapshot.snapshot_time.desc())
            .limit(1)
        )
        return self.session.exec(statement).first()
    
    def get_snapshots_by_date_range(
        self, 
        book_id: str, 
        start_date: datetime, 
        end_date: Optional[datetime] = None
    ) -> List[BookSnapshot]:
        """获取指定日期范围的快照"""
        if end_date is None:
            end_date = datetime.now()
        
        statement = (
            select(BookSnapshot)
            .where(
                and_(
                    BookSnapshot.book_id == book_id,
                    BookSnapshot.snapshot_time >= start_date,
                    BookSnapshot.snapshot_time <= end_date
                )
            )
            .order_by(BookSnapshot.snapshot_time.asc())
        )
        
        return list(self.session.exec(statement))
    
    def get_trend_data(self, book_id: str, days: int = 7) -> List[BookSnapshot]:
        """获取书籍趋势数据"""
        start_date = datetime.now() - timedelta(days=days)
        return self.get_snapshots_by_date_range(book_id, start_date)
    
    def create_snapshot(self, snapshot_data: Dict[str, Any]) -> BookSnapshot:
        """创建书籍快照"""
        snapshot = BookSnapshot(**snapshot_data)
        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot
    
    def batch_create_snapshots(self, snapshots_data: List[Dict[str, Any]]) -> List[BookSnapshot]:
        """批量创建书籍快照"""
        snapshots = [BookSnapshot(**data) for data in snapshots_data]
        self.session.add_all(snapshots)
        self.session.commit()
        for snapshot in snapshots:
            self.session.refresh(snapshot)
        return snapshots

    # ==================== 业务查询方法 ====================
    
    def get_books_with_latest_data(
        self, 
        book_ids: List[str]
    ) -> List[tuple[Book, Optional[BookSnapshot]]]:
        """获取书籍及其最新快照数据"""
        results = []
        for book_id in book_ids:
            book = self.get_by_id(book_id)
            if book:
                latest_snapshot = self.get_latest_snapshot(book_id)
                results.append((book, latest_snapshot))
        return results
    
    def get_books_by_author(self, author_id: str) -> List[Book]:
        """获取指定作者的所有书籍"""
        statement = select(Book).where(Book.author_id == author_id)
        return list(self.session.exec(statement))