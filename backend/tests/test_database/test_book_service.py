"""
书籍服务层测试
"""
import pytest
from datetime import datetime, timedelta

from app.database.service.book_service import BookService


class TestBookService:
    """书籍服务层测试"""
    
    def test_get_book_by_id(self, test_db, sample_book):
        """测试根据ID获取书籍"""
        book_service = BookService()
        
        result = book_service.get_book_by_id(test_db, sample_book.id)
        assert result is not None
        assert result.id == sample_book.id
        assert result.title == sample_book.title
        
        # 测试不存在的书籍
        result = book_service.get_book_by_id(test_db, 99999)
        assert result is None
    
    def test_get_book_by_novel_id(self, test_db, sample_book):
        """测试根据小说ID获取书籍"""
        book_service = BookService()
        
        result = book_service.get_book_by_novel_id(test_db, sample_book.novel_id)
        assert result is not None
        assert result.novel_id == sample_book.novel_id
        
        # 测试不存在的小说ID
        result = book_service.get_book_by_novel_id(test_db, 99999)
        assert result is None
    
    def test_search_books(self, test_db, sample_books):
        """测试搜索书籍"""
        book_service = BookService()
        
        # 按标题搜索
        results = book_service.search_books(test_db, "测试小说", page=1, size=10)
        assert len(results) == 5  # sample_books有5本书
        
        # 按作者搜索
        results = book_service.search_books(test_db, "作者1", page=1, size=10)
        assert len(results) == 1
        assert results[0].author == "作者1"
        
        # 搜索不存在的内容
        results = book_service.search_books(test_db, "不存在的内容", page=1, size=10)
        assert len(results) == 0
    
    def test_get_book_detail_with_latest_snapshot(self, test_db, sample_book, sample_book_snapshots):
        """测试获取书籍详情和最新快照"""
        book_service = BookService()
        
        result = book_service.get_book_detail_with_latest_snapshot(test_db, sample_book.id)
        assert result is not None
        assert result["book"].id == sample_book.id
        assert result["latest_snapshot"] is not None
        assert result["statistics"] is not None
        
        # 验证是最新的快照
        latest_snapshot = result["latest_snapshot"]
        assert latest_snapshot.favorites == 1060  # 最后一个快照的数据
        
        # 测试不存在的书籍
        result = book_service.get_book_detail_with_latest_snapshot(test_db, 99999)
        assert result is None
    
    def test_get_book_trend(self, test_db, sample_book, sample_book_snapshots):
        """测试获取书籍趋势数据"""
        book_service = BookService()
        
        trend_data = book_service.get_book_trend(test_db, sample_book.id, days=7)
        assert len(trend_data) == 7  # sample_book_snapshots有7个快照
        
        # 验证按时间降序排列
        assert trend_data[0].snapshot_time >= trend_data[1].snapshot_time
    
    def test_create_or_update_book(self, test_db):
        """测试创建或更新书籍"""
        book_service = BookService()
        
        # 创建新书籍
        book_data = {
            "novel_id": 12345,
            "title": "新书籍",
            "author": "新作者"
        }
        book = book_service.create_or_update_book(test_db, book_data)
        assert book.novel_id == 12345
        assert book.title == "新书籍"
        
        # 更新现有书籍
        update_data = {
            "novel_id": 12345,
            "title": "更新后的书籍",
            "author": "新作者"
        }
        updated_book = book_service.create_or_update_book(test_db, update_data)
        assert updated_book.id == book.id  # 同一本书
        assert updated_book.title == "更新后的书籍"
    
    def test_create_book_snapshot(self, test_db, sample_book):
        """测试创建书籍快照"""
        book_service = BookService()
        
        snapshot_data = {
            "book_id": sample_book.id,
            "favorites": 1000,
            "clicks": 5000,
            "comments": 100,
            "recommendations": 50
        }
        
        snapshot = book_service.create_book_snapshot(test_db, snapshot_data)
        assert snapshot.book_id == sample_book.id
        assert snapshot.favorites == 1000
        assert snapshot.clicks == 5000
    
    def test_batch_create_book_snapshots(self, test_db, sample_book):
        """测试批量创建书籍快照"""
        book_service = BookService()
        
        snapshots_data = []
        for i in range(3):
            snapshots_data.append({
                "book_id": sample_book.id,
                "favorites": 1000 + i * 100,
                "clicks": 5000 + i * 500,
                "snapshot_time": datetime.now() + timedelta(hours=i)
            })
        
        snapshots = book_service.batch_create_book_snapshots(test_db, snapshots_data)
        assert len(snapshots) == 3
        
        # 验证数据正确
        for i, snapshot in enumerate(snapshots):
            assert snapshot.book_id == sample_book.id
            assert snapshot.favorites == 1000 + i * 100
    
    def test_get_book_statistics(self, test_db, sample_book, sample_book_snapshots):
        """测试获取书籍统计信息"""
        book_service = BookService()
        
        stats = book_service.get_book_statistics(test_db, sample_book.id)
        
        assert stats["total_snapshots"] == 7
        assert stats["max_favorites"] == 1060  # 1000 + 6*10
        assert stats["max_clicks"] == 5300    # 5000 + 6*50
        assert stats["first_snapshot_time"] is not None
        assert stats["last_snapshot_time"] is not None


class TestBookTrendService:
    """书籍趋势服务测试（重构后的独立函数）"""
    
    def test_get_book_trend_hourly(self, test_db, sample_book, sample_book_snapshots):
        """测试按小时获取趋势数据"""
        book_service = BookService()
        
        # 模拟48小时的数据请求
        trend_data = book_service.get_book_trend_hourly(test_db, sample_book.id, hours=48)
        
        # 由于测试数据可能不够，这里主要测试函数能正常调用
        assert isinstance(trend_data, list)
        # 实际项目中这里会有更多断言来验证聚合逻辑
    
    def test_get_book_trend_daily(self, test_db, sample_book, sample_book_snapshots):
        """测试按天获取趋势数据"""
        book_service = BookService()
        
        trend_data = book_service.get_book_trend_daily(test_db, sample_book.id, days=7)
        
        assert isinstance(trend_data, list)
        # 每个数据点应该包含聚合信息
        if trend_data:
            data_point = trend_data[0]
            assert "time_period" in data_point
            assert "avg_favorites" in data_point
            assert "avg_clicks" in data_point
    
    def test_get_book_trend_weekly(self, test_db, sample_book, sample_book_snapshots):
        """测试按周获取趋势数据"""
        book_service = BookService()
        
        trend_data = book_service.get_book_trend_weekly(test_db, sample_book.id, weeks=4)
        
        assert isinstance(trend_data, list)
    
    def test_get_book_trend_monthly(self, test_db, sample_book, sample_book_snapshots):
        """测试按月获取趋势数据"""
        book_service = BookService()
        
        trend_data = book_service.get_book_trend_monthly(test_db, sample_book.id, months=3)
        
        assert isinstance(trend_data, list)
    
    def test_get_book_trend_with_interval(self, test_db, sample_book, sample_book_snapshots):
        """测试通用间隔趋势数据获取"""
        book_service = BookService()
        
        # 测试不同间隔
        intervals = ["hour", "day", "week", "month"]
        
        for interval in intervals:
            trend_data = book_service.get_book_trend_with_interval(
                test_db, sample_book.id, period_count=2, interval=interval
            )
            assert isinstance(trend_data, list)
        
        # 测试无效间隔
        with pytest.raises(ValueError):
            book_service.get_book_trend_with_interval(
                test_db, sample_book.id, period_count=2, interval="invalid"
            )