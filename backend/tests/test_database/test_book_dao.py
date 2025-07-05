"""
测试 BookDAO 和 BookSnapshotDAO
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database.dao.book_dao import BookDAO, BookSnapshotDAO
from app.database.db.book import Book, BookSnapshot


class TestBookDAO:
    """测试 BookDAO"""
    
    def test_get_by_novel_id(self, test_db: Session, sample_book: Book):
        """测试根据novel_id获取书籍"""
        book_dao = BookDAO()
        result = book_dao.get_by_novel_id(test_db, sample_book.novel_id)
        assert result is not None
        assert result.novel_id == sample_book.novel_id
        assert result.title == sample_book.title
    
    def test_search_by_title(self, test_db: Session, sample_books: list[Book]):
        """测试根据标题搜索书籍"""
        book_dao = BookDAO()
        results = book_dao.search_by_title(test_db, "测试小说")
        assert len(results) > 0
        assert all("测试小说" in book.title for book in results)
    
    def test_search_by_author(self, test_db: Session, sample_books: list[Book]):
        """测试根据作者搜索书籍"""
        book_dao = BookDAO()
        results = book_dao.search_by_author(test_db, "作者1")
        assert len(results) == 1
        assert results[0].author == "作者1"
    
    def test_get_all(self, test_db: Session, sample_books: list[Book]):
        """测试获取所有书籍"""
        book_dao = BookDAO()
        results = book_dao.get_all(test_db, limit=10)
        assert len(results) == len(sample_books)
    
    def test_create_or_update_by_novel_id(self, test_db: Session):
        """测试根据novel_id创建或更新书籍"""
        book_dao = BookDAO()
        
        # 创建新书籍
        book_data = {
            "novel_id": 99999,
            "title": "新书籍",
            "author": "新作者"
        }
        book = book_dao.create_or_update_by_novel_id(test_db, book_data)
        assert book.novel_id == 99999
        assert book.title == "新书籍"
        
        # 更新现有书籍
        update_data = {
            "novel_id": 99999,
            "title": "更新的书籍",
            "author": "新作者"
        }
        updated_book = book_dao.create_or_update_by_novel_id(test_db, update_data)
        assert updated_book.id == book.id
        assert updated_book.title == "更新的书籍"


class TestBookSnapshotDAO:
    """测试 BookSnapshotDAO"""
    
    def test_get_latest_by_book_id(self, test_db: Session, sample_book_snapshots: list[BookSnapshot]):
        """测试获取书籍最新快照"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        result = snapshot_dao.get_latest_by_book_id(test_db, book_id)
        assert result is not None
        assert result.book_id == book_id
        # 应该是最新的快照
        assert result.snapshot_time == max(s.snapshot_time for s in sample_book_snapshots)
    
    def test_get_trend_by_book_id(self, test_db: Session, sample_book_snapshots: list[BookSnapshot]):
        """测试获取书籍趋势数据"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        results = snapshot_dao.get_trend_by_book_id(test_db, book_id)
        assert len(results) > 0
        assert all(snapshot.book_id == book_id for snapshot in results)
    
    def test_get_hourly_trend_by_book_id(self, test_db: Session, sample_book_snapshots: list[BookSnapshot]):
        """测试获取书籍小时趋势数据"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now()
        
        results = snapshot_dao.get_hourly_trend_by_book_id(test_db, book_id, start_time, end_time)
        assert isinstance(results, list)
        # 即使没有数据，也应该返回空列表
        assert results is not None
    
    def test_get_daily_trend_by_book_id(self, test_db: Session, sample_book_snapshots: list[BookSnapshot]):
        """测试获取书籍日趋势数据"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        
        results = snapshot_dao.get_daily_trend_by_book_id(test_db, book_id, start_time, end_time)
        assert isinstance(results, list)
        assert results is not None
    
    def test_get_weekly_trend_by_book_id(self, test_db: Session, sample_book_snapshots: list[BookSnapshot]):
        """测试获取书籍周趋势数据"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        start_time = datetime.now() - timedelta(weeks=4)
        end_time = datetime.now()
        
        results = snapshot_dao.get_weekly_trend_by_book_id(test_db, book_id, start_time, end_time)
        assert isinstance(results, list)
        assert results is not None
    
    def test_get_monthly_trend_by_book_id(self, test_db: Session, sample_book_snapshots: list[BookSnapshot]):
        """测试获取书籍月趋势数据"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        start_time = datetime.now() - timedelta(days=90)
        end_time = datetime.now()
        
        results = snapshot_dao.get_monthly_trend_by_book_id(test_db, book_id, start_time, end_time)
        assert isinstance(results, list)
        assert results is not None
    
    def test_get_trend_by_book_id_with_interval(self, test_db: Session, sample_book_snapshots: list[BookSnapshot]):
        """测试按指定间隔获取趋势数据"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        
        # 测试不同间隔
        for interval in ["hour", "day", "week", "month"]:
            results = snapshot_dao.get_trend_by_book_id_with_interval(
                test_db, book_id, start_time, end_time, interval
            )
            assert isinstance(results, list)
    
    def test_get_statistics_by_book_id(self, test_db: Session, sample_book_snapshots: list[BookSnapshot]):
        """测试获取书籍统计信息"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        stats = snapshot_dao.get_statistics_by_book_id(test_db, book_id)
        assert isinstance(stats, dict)
        assert "total_snapshots" in stats
        assert stats["total_snapshots"] > 0
    
    def test_bulk_create(self, test_db: Session, sample_book: Book):
        """测试批量创建快照"""
        snapshot_dao = BookSnapshotDAO()
        
        snapshots_data = [
            {
                "book_id": sample_book.id,
                "favorites": 1000,
                "clicks": 5000,
                "comments": 100,
                "recommendations": 50,
                "snapshot_time": datetime.now() - timedelta(minutes=i)
            }
            for i in range(3)
        ]
        
        results = snapshot_dao.bulk_create(test_db, snapshots_data)
        assert len(results) == 3
        assert all(snapshot.book_id == sample_book.id for snapshot in results)
    
    def test_delete_old_snapshots(self, test_db: Session, sample_book_snapshots: list[BookSnapshot]):
        """测试删除旧快照"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        before_time = datetime.now() - timedelta(days=3)
        deleted_count = snapshot_dao.delete_old_snapshots(test_db, book_id, before_time, keep_count=2)
        assert deleted_count >= 0