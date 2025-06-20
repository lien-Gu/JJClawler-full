"""
数据访问服务模块

提供数据库CRUD操作和业务查询方法
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func, and_, or_
from app.modules.database import get_session_sync
from app.modules.models import (
    Ranking, Book, BookSnapshot, RankingSnapshot,
    BookDetail, BookInRanking, BookRankingHistory, 
    BookTrendData, RankingSnapshotSummary
)

logger = logging.getLogger(__name__)


class DataService:
    """数据访问服务类"""
    
    def __init__(self):
        self._session = None
    
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

    # ==================== 榜单相关操作 ====================
    
    def get_ranking_by_id(self, ranking_id: str) -> Optional[Ranking]:
        """根据榜单ID获取榜单信息"""
        statement = select(Ranking).where(Ranking.ranking_id == ranking_id)
        return self.session.exec(statement).first()
    
    def get_all_rankings(self) -> List[Ranking]:
        """获取所有榜单配置"""
        statement = select(Ranking).order_by(Ranking.ranking_id)
        return list(self.session.exec(statement))
    
    def create_ranking(self, ranking_data: Dict[str, Any]) -> Ranking:
        """创建新榜单配置"""
        ranking = Ranking(**ranking_data)
        self.session.add(ranking)
        self.session.commit()
        self.session.refresh(ranking)
        return ranking
    
    def update_ranking(self, ranking_id: str, update_data: Dict[str, Any]) -> Optional[Ranking]:
        """更新榜单配置"""
        ranking = self.get_ranking_by_id(ranking_id)
        if ranking:
            for field, value in update_data.items():
                if hasattr(ranking, field):
                    setattr(ranking, field, value)
            self.session.commit()
            self.session.refresh(ranking)
        return ranking

    # ==================== 书籍相关操作 ====================
    
    def get_book_by_id(self, book_id: str) -> Optional[Book]:
        """根据书籍ID获取书籍信息"""
        statement = select(Book).where(Book.book_id == book_id)
        return self.session.exec(statement).first()
    
    def get_book_detail(self, book_id: str) -> Optional[BookDetail]:
        """获取书籍详细信息（包含最新动态数据）"""
        book = self.get_book_by_id(book_id)
        if not book:
            return None
        
        # 获取最新快照数据
        latest_snapshot = self.get_latest_book_snapshot(book_id)
        
        # 构建BookDetail对象
        book_detail = BookDetail(
            id=book.id,
            book_id=book.book_id,
            title=book.title,
            author_id=book.author_id,
            author_name=book.author_name,
            novel_class=book.novel_class,
            tags=book.tags,
            first_seen=book.first_seen,
            last_updated=book.last_updated,
            latest_clicks=latest_snapshot.total_clicks if latest_snapshot else None,
            latest_favorites=latest_snapshot.total_favorites if latest_snapshot else None,
            latest_comments=latest_snapshot.comment_count if latest_snapshot else None,
            latest_chapters=latest_snapshot.chapter_count if latest_snapshot else None
        )
        return book_detail
    
    def search_books(
        self, 
        title: Optional[str] = None,
        author: Optional[str] = None,
        novel_class: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[BookDetail], int]:
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
        
        # 转换为BookDetail
        book_details = []
        for book in books:
            latest_snapshot = self.get_latest_book_snapshot(book.book_id)
            book_detail = BookDetail(
                id=book.id,
                book_id=book.book_id,
                title=book.title,
                author_id=book.author_id,
                author_name=book.author_name,
                novel_class=book.novel_class,
                tags=book.tags,
                first_seen=book.first_seen,
                last_updated=book.last_updated,
                latest_clicks=latest_snapshot.total_clicks if latest_snapshot else None,
                latest_favorites=latest_snapshot.total_favorites if latest_snapshot else None,
                latest_comments=latest_snapshot.comment_count if latest_snapshot else None,
                latest_chapters=latest_snapshot.chapter_count if latest_snapshot else None
            )
            book_details.append(book_detail)
        
        return book_details, total
    
    def create_or_update_book(self, book_data: Dict[str, Any]) -> Book:
        """创建或更新书籍信息"""
        book_id = book_data["book_id"]
        existing_book = self.get_book_by_id(book_id)
        
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
            book = Book(**book_data)
            self.session.add(book)
            self.session.commit()
            self.session.refresh(book)
            return book

    # ==================== 书籍快照相关操作 ====================
    
    def get_latest_book_snapshot(self, book_id: str) -> Optional[BookSnapshot]:
        """获取书籍最新快照"""
        statement = (
            select(BookSnapshot)
            .where(BookSnapshot.book_id == book_id)
            .order_by(BookSnapshot.snapshot_time.desc())
            .limit(1)
        )
        return self.session.exec(statement).first()
    
    def get_book_trend_data(self, book_id: str, days: int = 7) -> List[BookTrendData]:
        """获取书籍趋势数据"""
        start_date = datetime.now() - timedelta(days=days)
        
        statement = (
            select(BookSnapshot)
            .where(
                and_(
                    BookSnapshot.book_id == book_id,
                    BookSnapshot.snapshot_time >= start_date
                )
            )
            .order_by(BookSnapshot.snapshot_time.asc())
        )
        
        snapshots = list(self.session.exec(statement))
        
        # 按日期聚合数据（取每日最新记录）
        daily_data = {}
        for snapshot in snapshots:
            date_key = snapshot.snapshot_time.date().isoformat()
            if date_key not in daily_data or snapshot.snapshot_time > daily_data[date_key].snapshot_time:
                daily_data[date_key] = snapshot
        
        # 转换为趋势数据
        trend_data = []
        for date_str, snapshot in sorted(daily_data.items()):
            trend_data.append(BookTrendData(
                date=date_str,
                total_clicks=snapshot.total_clicks,
                total_favorites=snapshot.total_favorites,
                comment_count=snapshot.comment_count,
                chapter_count=snapshot.chapter_count
            ))
        
        return trend_data
    
    def create_book_snapshot(self, snapshot_data: Dict[str, Any]) -> BookSnapshot:
        """创建书籍快照"""
        snapshot = BookSnapshot(**snapshot_data)
        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot

    # ==================== 榜单快照相关操作 ====================
    
    def get_ranking_books(
        self, 
        ranking_id: str, 
        snapshot_time: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[BookInRanking], Optional[datetime]]:
        """获取榜单书籍列表"""
        # 如果没有指定时间，使用最新快照
        if snapshot_time is None:
            latest_snapshot_stmt = (
                select(RankingSnapshot.snapshot_time)
                .where(RankingSnapshot.ranking_id == ranking_id)
                .order_by(RankingSnapshot.snapshot_time.desc())
                .limit(1)
            )
            snapshot_time = self.session.exec(latest_snapshot_stmt).first()
            
            if not snapshot_time:
                return [], None
        
        # 获取指定时间的榜单数据
        statement = (
            select(RankingSnapshot, Book)
            .join(Book, RankingSnapshot.book_id == Book.book_id)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time == snapshot_time
                )
            )
            .order_by(RankingSnapshot.position.asc())
            .offset(offset)
            .limit(limit)
        )
        
        results = list(self.session.exec(statement))
        
        # 转换为BookInRanking
        books_in_ranking = []
        for ranking_snapshot, book in results:
            book_in_ranking = BookInRanking(
                book_id=book.book_id,
                title=book.title,
                author_name=book.author_name,
                author_id=book.author_id,
                novel_class=book.novel_class,
                tags=book.tags,
                position=ranking_snapshot.position,
                position_change=None  # TODO: 计算排名变化
            )
            books_in_ranking.append(book_in_ranking)
        
        return books_in_ranking, snapshot_time
    
    def get_book_ranking_history(self, book_id: str, days: int = 30) -> List[BookRankingHistory]:
        """获取书籍榜单历史"""
        start_date = datetime.now() - timedelta(days=days)
        
        statement = (
            select(RankingSnapshot, Ranking)
            .join(Ranking, RankingSnapshot.ranking_id == Ranking.ranking_id)
            .where(
                and_(
                    RankingSnapshot.book_id == book_id,
                    RankingSnapshot.snapshot_time >= start_date
                )
            )
            .order_by(RankingSnapshot.snapshot_time.desc())
        )
        
        results = list(self.session.exec(statement))
        
        # 转换为历史记录
        history = []
        for ranking_snapshot, ranking in results:
            history.append(BookRankingHistory(
                ranking_id=ranking.ranking_id,
                ranking_name=ranking.name,
                position=ranking_snapshot.position,
                snapshot_time=ranking_snapshot.snapshot_time
            ))
        
        return history
    
    def get_ranking_history_summary(
        self, 
        ranking_id: str, 
        days: int = 7
    ) -> List[RankingSnapshotSummary]:
        """获取榜单历史摘要"""
        start_date = datetime.now() - timedelta(days=days)
        
        # 按快照时间分组统计
        statement = (
            select(
                RankingSnapshot.snapshot_time,
                func.count(RankingSnapshot.id).label("total_books"),
                func.min(RankingSnapshot.position).label("min_position")
            )
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time >= start_date
                )
            )
            .group_by(RankingSnapshot.snapshot_time)
            .order_by(RankingSnapshot.snapshot_time.desc())
        )
        
        results = list(self.session.exec(statement))
        
        # 获取每个快照的第一名书籍
        summaries = []
        for row in results:
            # 查询第一名书籍
            top_book_stmt = (
                select(Book.title)
                .join(RankingSnapshot, Book.book_id == RankingSnapshot.book_id)
                .where(
                    and_(
                        RankingSnapshot.ranking_id == ranking_id,
                        RankingSnapshot.snapshot_time == row.snapshot_time,
                        RankingSnapshot.position == 1
                    )
                )
                .limit(1)
            )
            top_book_title = self.session.exec(top_book_stmt).first()
            
            summaries.append(RankingSnapshotSummary(
                snapshot_time=row.snapshot_time,
                total_books=row.total_books,
                top_book_title=top_book_title
            ))
        
        return summaries
    
    def create_ranking_snapshot(self, snapshot_data: Dict[str, Any]) -> RankingSnapshot:
        """创建榜单快照"""
        snapshot = RankingSnapshot(**snapshot_data)
        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot
    
    def batch_create_ranking_snapshots(self, snapshots_data: List[Dict[str, Any]]) -> List[RankingSnapshot]:
        """批量创建榜单快照"""
        snapshots = [RankingSnapshot(**data) for data in snapshots_data]
        self.session.add_all(snapshots)
        self.session.commit()
        for snapshot in snapshots:
            self.session.refresh(snapshot)
        return snapshots


# 全局数据服务实例
_data_service = None


def get_data_service() -> DataService:
    """获取数据服务实例"""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service


def close_data_service():
    """关闭数据服务"""
    global _data_service
    if _data_service:
        _data_service.close()
        _data_service = None