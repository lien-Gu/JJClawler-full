"""
测试 BookService
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database.service.book_service import BookService
from app.database.db.book import Book, BookSnapshot


class TestBookService:
    """测试 BookService"""
    
    def test_get_book_by_id(self, test_db: Session, sample_book: Book):
        """测试根据ID获取书籍"""
        service = BookService()
        result = service.get_book_by_id(test_db, sample_book.id)
        assert result is not None
        assert result.id == sample_book.id
        assert result.title == sample_book.title
    
    def test_get_book_by_novel_id(self, test_db: Session, sample_book: Book):
        """测试根据小说ID获取书籍"""
        service = BookService()
        result = service.get_book_by_novel_id(test_db, sample_book.novel_id)
        assert result is not None
        assert result.novel_id == sample_book.novel_id
        assert result.title == sample_book.title
    
    def test_search_books(self, test_db: Session, sample_books: list[Book]):
        """测试搜索书籍"""
        service = BookService()
        results = service.search_books(test_db, "测试小说", page=1, size=5)
        assert len(results) > 0
        assert all("测试小说" in book.title for book in results)
    
    def test_get_book_detail_with_latest_snapshot(self, test_db: Session, sample_book: Book, sample_book_snapshots: list[BookSnapshot]):
        """测试获取书籍详情和最新快照数据"""
        service = BookService()
        result = service.get_book_detail_with_latest_snapshot(test_db, sample_book.id)
        assert result is not None
        assert "book" in result
        assert "latest_snapshot" in result
        assert "statistics" in result
        assert result["book"].id == sample_book.id
    
    def test_get_book_trend(self, test_db: Session, sample_book: Book, sample_book_snapshots: list[BookSnapshot]):
        """测试获取书籍趋势数据"""
        service = BookService()
        results = service.get_book_trend(test_db, sample_book.id, days=7)
        assert isinstance(results, list)
        if results:
            assert all(snapshot.novel_id == sample_book.id for snapshot in results)
    
    def test_get_book_trend_hourly(self, test_db: Session, sample_book: Book, sample_book_snapshots: list[BookSnapshot]):
        """测试按小时获取书籍趋势数据"""
        service = BookService()
        results = service.get_book_trend_hourly(test_db, sample_book.id, hours=24)
        assert isinstance(results, list)
    
    def test_get_book_trend_daily(self, test_db: Session, sample_book: Book, sample_book_snapshots: list[BookSnapshot]):
        """测试按天获取书籍趋势数据"""
        service = BookService()
        results = service.get_book_trend_daily(test_db, sample_book.id, days=7)
        assert isinstance(results, list)
    
    def test_get_book_trend_weekly(self, test_db: Session, sample_book: Book, sample_book_snapshots: list[BookSnapshot]):
        """测试按周获取书籍趋势数据"""
        service = BookService()
        results = service.get_book_trend_weekly(test_db, sample_book.id, weeks=4)
        assert isinstance(results, list)
    
    def test_get_book_trend_monthly(self, test_db: Session, sample_book: Book, sample_book_snapshots: list[BookSnapshot]):
        """测试按月获取书籍趋势数据"""
        service = BookService()
        results = service.get_book_trend_monthly(test_db, sample_book.id, months=3)
        assert isinstance(results, list)
    
    def test_get_book_trend_with_interval(self, test_db: Session, sample_book: Book, sample_book_snapshots: list[BookSnapshot]):
        """测试按指定时间间隔获取书籍趋势数据"""
        service = BookService()
        
        # 测试不同间隔
        for interval in ["hour", "day", "week", "month"]:
            results = service.get_book_trend_with_interval(test_db, sample_book.id, 5, interval)
            assert isinstance(results, list)
    
    def test_create_or_update_book(self, test_db: Session):
        """测试创建或更新书籍"""
        service = BookService()
        
        book_data = {
            "novel_id": 88888,
            "title": "服务测试书籍"
        }
        
        book = service.create_or_update_book(test_db, book_data)
        assert book.novel_id == 88888
        assert book.title == "服务测试书籍"
        
        # 测试更新
        update_data = {
            "novel_id": 88888,
            "title": "更新的服务测试书籍"
        }
        
        updated_book = service.create_or_update_book(test_db, update_data)
        assert updated_book.id == book.id
        assert updated_book.title == "更新的服务测试书籍"
    
    def test_create_book_snapshot(self, test_db: Session, sample_book: Book):
        """测试创建书籍快照"""
        service = BookService()
        
        snapshot_data = {
            "novel_id": sample_book.id,
            "favorites": 2000,
            "clicks": 10000,
            "comments": 200,
            "recommendations": 100,
            "snapshot_time": datetime.now()
        }
        
        snapshot = service.create_book_snapshot(test_db, snapshot_data)
        assert snapshot.novel_id == sample_book.id
        assert snapshot.favorites == 2000
    
    def test_batch_create_book_snapshots(self, test_db: Session, sample_book: Book):
        """测试批量创建书籍快照"""
        service = BookService()
        
        snapshots_data = [
            {
                "novel_id": sample_book.id,
                "favorites": 1000 + i * 100,
                "clicks": 5000 + i * 500,
                "comments": 100 + i * 10,
                "recommendations": 50 + i * 5,
                "snapshot_time": datetime.now() - timedelta(minutes=i)
            }
            for i in range(3)
        ]
        
        snapshots = service.batch_create_book_snapshots(test_db, snapshots_data)
        assert len(snapshots) == 3
        assert all(snapshot.novel_id == sample_book.id for snapshot in snapshots)
    
    def test_cleanup_old_snapshots(self, test_db: Session, sample_book: Book, sample_book_snapshots: list[BookSnapshot]):
        """测试清理旧快照"""
        service = BookService()
        
        deleted_count = service.cleanup_old_snapshots(test_db, sample_book.id, keep_days=1, keep_count=2)
        assert deleted_count >= 0
    
    def test_get_book_statistics(self, test_db: Session, sample_book: Book, sample_book_snapshots: list[BookSnapshot]):
        """测试获取书籍统计信息"""
        service = BookService()
        
        stats = service.get_book_statistics(test_db, sample_book.id)
        assert isinstance(stats, dict)
        if stats:
            assert "total_snapshots" in stats
            assert stats["total_snapshots"] > 0
    
    def test_get_books_with_pagination(self, test_db: Session, sample_books: list[Book]):
        """测试分页获取书籍列表"""
        service = BookService()
        
        result = service.get_books_with_pagination(test_db, page=1, size=3)
        assert "books" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert "total_pages" in result
        assert len(result["books"]) <= 3
        assert result["page"] == 1
        assert result["size"] == 3
    
    def test_get_books_by_ids(self, test_db: Session, sample_books: list[Book]):
        """测试根据ID列表获取书籍"""
        service = BookService()
        
        book_ids = [book.id for book in sample_books[:2]]
        results = service.get_books_by_ids(test_db, book_ids)
        assert len(results) == 2
        assert all(book.id in book_ids for book in results)
    
    def test_get_book_detail_with_latest_snapshot_not_found(self, test_db: Session):
        """测试获取不存在的书籍详情"""
        service = BookService()
        result = service.get_book_detail_with_latest_snapshot(test_db, 99999)
        assert result is None
    
    def test_get_book_by_id_not_found(self, test_db: Session):
        """测试获取不存在的书籍"""
        service = BookService()
        result = service.get_book_by_id(test_db, 99999)
        assert result is None