"""
Book业务服务

封装Book相关的业务逻辑
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from app.modules.dao import BookDAO, RankingDAO
from app.modules.models import (
    BookDetail, BookInRanking, BookRankingHistory, 
    BookTrendData, Book, BookSnapshot
)

logger = logging.getLogger(__name__)


class BookService:
    """Book业务服务类"""
    
    def __init__(self):
        self.book_dao = BookDAO()
        self.ranking_dao = RankingDAO()
    
    def close(self):
        """关闭服务"""
        self.book_dao.close()
        self.ranking_dao.close()
    
    def get_book_detail(self, book_id: str) -> Optional[BookDetail]:
        """获取书籍详细信息（包含最新动态数据）"""
        book = self.book_dao.get_by_id(book_id)
        if not book:
            return None
        
        # 获取最新快照数据
        latest_snapshot = self.book_dao.get_latest_snapshot(book_id)
        
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
        books, total = self.book_dao.search(
            title=title, 
            author=author, 
            novel_class=novel_class,
            limit=limit, 
            offset=offset
        )
        
        # 转换为BookDetail
        book_details = []
        for book in books:
            latest_snapshot = self.book_dao.get_latest_snapshot(book.book_id)
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
    
    def get_book_ranking_history(
        self, 
        book_id: str, 
        days: int = 30
    ) -> tuple[Optional[BookDetail], List[BookRankingHistory], List[BookRankingHistory]]:
        """获取书籍榜单历史"""
        # 获取书籍基本信息
        book_detail = self.get_book_detail(book_id)
        if not book_detail:
            return None, [], []
        
        # 获取当前在榜情况
        current_rankings_data = self.ranking_dao.get_current_book_rankings(book_id)
        current_rankings = []
        for ranking_snapshot, ranking in current_rankings_data:
            current_rankings.append(BookRankingHistory(
                ranking_id=ranking.ranking_id,
                ranking_name=ranking.name,
                position=ranking_snapshot.position,
                snapshot_time=ranking_snapshot.snapshot_time
            ))
        
        # 获取历史记录
        history_data = self.ranking_dao.get_book_ranking_history(book_id, days)
        history_rankings = []
        for ranking_snapshot, ranking in history_data:
            history_rankings.append(BookRankingHistory(
                ranking_id=ranking.ranking_id,
                ranking_name=ranking.name,
                position=ranking_snapshot.position,
                snapshot_time=ranking_snapshot.snapshot_time
            ))
        
        return book_detail, current_rankings, history_rankings
    
    def get_book_trend_data(self, book_id: str, days: int = 7) -> List[BookTrendData]:
        """获取书籍趋势数据"""
        snapshots = self.book_dao.get_trend_data(book_id, days)
        
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
    
    def create_or_update_book(self, book_data: Dict[str, Any]) -> Book:
        """创建或更新书籍信息"""
        return self.book_dao.create_or_update(book_data)
    
    def create_book_snapshot(self, snapshot_data: Dict[str, Any]) -> BookSnapshot:
        """创建书籍快照"""
        return self.book_dao.create_snapshot(snapshot_data)
    
    def batch_create_book_snapshots(self, snapshots_data: List[Dict[str, Any]]) -> List[BookSnapshot]:
        """批量创建书籍快照"""
        return self.book_dao.batch_create_snapshots(snapshots_data)
    
    def get_books_by_author(self, author_id: str) -> List[BookDetail]:
        """获取指定作者的所有书籍"""
        books = self.book_dao.get_books_by_author(author_id)
        
        book_details = []
        for book in books:
            latest_snapshot = self.book_dao.get_latest_snapshot(book.book_id)
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
        
        return book_details