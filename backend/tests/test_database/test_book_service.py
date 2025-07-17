"""
书籍服务测试文件
测试app.database.service.book_service模块的所有服务方法
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from app.database.service.book_service import BookService
from app.database.db.book import Book, BookSnapshot


class TestBookService:
    """测试BookService类"""
    
    @pytest.fixture
    def book_service(self):
        """BookService实例fixture"""
        return BookService()
    
    @pytest.fixture
    def mock_book_dao(self, mocker):
        """模拟BookDAO"""
        mock_dao = mocker.Mock()
        return mock_dao
    
    @pytest.fixture
    def mock_book_snapshot_dao(self, mocker):
        """模拟BookSnapshotDAO"""
        mock_dao = mocker.Mock()
        return mock_dao
    
    @pytest.fixture
    def book_service_with_mocks(self, mocker, mock_book_dao, mock_book_snapshot_dao):
        """使用模拟DAO的BookService"""
        service = BookService()
        service.book_dao = mock_book_dao
        service.book_snapshot_dao = mock_book_snapshot_dao
        return service
    
    @pytest.fixture
    def sample_book(self):
        """样本书籍数据"""
        return Book(
            id=1,
            novel_id=12345,
            title="测试小说",
            author_id=101,
            novel_class="现代言情",
            tags="现代,都市",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0)
        )
    
    @pytest.fixture
    def sample_snapshot(self):
        """样本快照数据"""
        return BookSnapshot(
            id=1,
            novel_id=12345,
            clicks=50000,
            favorites=1500,
            comments=800,
            recommendations=120,
            snapshot_time=datetime(2024, 1, 15, 12, 0, 0)
        )
    
    def test_get_book_by_id_success(self, book_service_with_mocks, mock_book_dao, sample_book, db_session):
        """测试成功根据ID获取书籍"""
        # Arrange
        mock_book_dao.get_by_id.return_value = sample_book
        
        # Act
        result = book_service_with_mocks.get_book_by_id(db_session, 1)
        
        # Assert
        assert result == sample_book
        mock_book_dao.get_by_id.assert_called_once_with(db_session, 1)
    
    def test_get_book_by_id_not_found(self, book_service_with_mocks, mock_book_dao, db_session):
        """测试书籍不存在时返回None"""
        # Arrange
        mock_book_dao.get_by_id.return_value = None
        
        # Act
        result = book_service_with_mocks.get_book_by_id(db_session, 999)
        
        # Assert
        assert result is None
        mock_book_dao.get_by_id.assert_called_once_with(db_session, 999)
    
    def test_get_book_by_novel_id_success(self, book_service_with_mocks, mock_book_dao, sample_book, db_session):
        """测试成功根据novel_id获取书籍"""
        # Arrange
        mock_book_dao.get_by_novel_id.return_value = sample_book
        
        # Act
        result = book_service_with_mocks.get_book_by_novel_id(db_session, 12345)
        
        # Assert
        assert result == sample_book
        mock_book_dao.get_by_novel_id.assert_called_once_with(db_session, 12345)
    
    def test_search_books_success(self, book_service_with_mocks, mock_book_dao, sample_book, db_session):
        """测试成功搜索书籍"""
        # Arrange
        mock_book_dao.search_by_title.return_value = [sample_book]
        
        # Act
        results = book_service_with_mocks.search_books(db_session, "测试", page=1, size=20)
        
        # Assert
        assert len(results) == 1
        assert results[0] == sample_book
        mock_book_dao.search_by_title.assert_called_once_with(db_session, "测试", limit=20)
    
    def test_search_books_with_pagination(self, book_service_with_mocks, mock_book_dao, sample_book, db_session):
        """测试搜索书籍分页功能"""
        # Arrange
        books = [sample_book] * 5  # 5本书
        mock_book_dao.search_by_title.return_value = books
        
        # Act - 获取第2页，每页2条
        results = book_service_with_mocks.search_books(db_session, "测试", page=2, size=2)
        
        # Assert
        assert len(results) == 2  # 第2页应该有2条记录
        mock_book_dao.search_by_title.assert_called_once_with(db_session, "测试", limit=4)  # skip=2, size=2, 所以limit=4
    
    def test_get_books_with_pagination_success(self, book_service_with_mocks, mock_book_dao, sample_book, db_session):
        """测试成功获取分页书籍列表"""
        # Arrange
        books = [sample_book] * 2
        mock_book_dao.get_multi.return_value = books
        mock_book_dao.count.return_value = 30
        
        # Act
        result = book_service_with_mocks.get_books_with_pagination(db_session, page=1, size=2)
        
        # Assert
        assert result["books"] == books
        assert result["total"] == 30
        assert result["page"] == 1
        assert result["size"] == 2
        assert result["total_pages"] == 15  # (30 + 2 - 1) // 2
        
        # 验证DAO调用
        mock_book_dao.get_multi.assert_called_once_with(db_session, skip=0, limit=2, filters=None)
        mock_book_dao.count.assert_called_once_with(db_session, filters=None)
    
    def test_get_book_detail_with_latest_snapshot_success(self, book_service_with_mocks, mock_book_dao, mock_book_snapshot_dao, sample_book, sample_snapshot, db_session):
        """测试成功获取书籍详情和最新快照"""
        # Arrange
        mock_book_dao.get_by_id.return_value = sample_book
        mock_book_snapshot_dao.get_latest_by_book_id.return_value = sample_snapshot
        mock_book_snapshot_dao.get_statistics_by_book_id.return_value = {"total_snapshots": 10}
        
        # Act
        result = book_service_with_mocks.get_book_detail_with_latest_snapshot(db_session, 1)
        
        # Assert
        assert result is not None
        assert result["book"] == sample_book
        assert result["latest_snapshot"] == sample_snapshot
        assert result["statistics"] == {"total_snapshots": 10}
        
        # 验证DAO调用 - 使用sample_book的novel_id
        mock_book_dao.get_by_id.assert_called_once_with(db_session, 1)
        mock_book_snapshot_dao.get_latest_by_book_id.assert_called_once_with(db_session, sample_book.novel_id)
        mock_book_snapshot_dao.get_statistics_by_book_id.assert_called_once_with(db_session, sample_book.novel_id)
    
    def test_get_book_detail_with_latest_snapshot_book_not_found(self, book_service_with_mocks, mock_book_dao, db_session):
        """测试书籍不存在时返回None"""
        # Arrange
        mock_book_dao.get_by_id.return_value = None
        
        # Act
        result = book_service_with_mocks.get_book_detail_with_latest_snapshot(db_session, 999)
        
        # Assert
        assert result is None
        mock_book_dao.get_by_id.assert_called_once_with(db_session, 999)
    
    @patch('app.database.service.book_service.datetime')
    def test_get_book_trend_success(self, mock_datetime, book_service_with_mocks, mock_book_dao, mock_book_snapshot_dao, sample_book, sample_snapshot, db_session):
        """测试成功获取书籍趋势数据"""
        # Arrange
        now = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.now.return_value = now
        mock_book_dao.get_by_id.return_value = sample_book
        mock_book_snapshot_dao.get_trend_by_book_id.return_value = [sample_snapshot]
        
        # Act
        results = book_service_with_mocks.get_book_trend(db_session, 1, days=7)
        
        # Assert
        assert len(results) == 1
        assert results[0] == sample_snapshot
        
        # 验证调用参数
        expected_start_time = now - timedelta(days=7)
        mock_book_dao.get_by_id.assert_called_once_with(db_session, 1)
        mock_book_snapshot_dao.get_trend_by_book_id.assert_called_once_with(
            db_session, sample_book.novel_id, start_time=expected_start_time, limit=168  # 7 * 24
        )
    
    @patch('app.database.service.book_service.datetime')
    def test_get_book_trend_hourly_success(self, mock_datetime, book_service_with_mocks, mock_book_dao, mock_book_snapshot_dao, sample_book, db_session):
        """测试成功获取小时级趋势数据"""
        # Arrange
        now = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.now.return_value = now
        trend_data = [{"time_period": "2024-01-15 11", "avg_clicks": 50000.0}]
        mock_book_dao.get_by_id.return_value = sample_book
        mock_book_snapshot_dao.get_trend_by_book_id_with_interval.return_value = trend_data
        
        # Act
        results = book_service_with_mocks.get_book_trend_hourly(db_session, 1, hours=24)
        
        # Assert
        assert results == trend_data
        
        # 验证调用参数
        expected_start_time = now - timedelta(hours=24)
        mock_book_dao.get_by_id.assert_called_once_with(db_session, 1)
        mock_book_snapshot_dao.get_trend_by_book_id_with_interval.assert_called_once_with(
            db_session, sample_book.novel_id, expected_start_time, now, "hour"
        )
    
    @patch('app.database.service.book_service.datetime')
    def test_get_book_trend_daily_success(self, mock_datetime, book_service_with_mocks, mock_book_dao, mock_book_snapshot_dao, sample_book, db_session):
        """测试成功获取天级趋势数据"""
        # Arrange
        now = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.now.return_value = now
        trend_data = [{"time_period": "2024-01-14", "avg_clicks": 50000.0}]
        mock_book_dao.get_by_id.return_value = sample_book
        mock_book_snapshot_dao.get_trend_by_book_id_with_interval.return_value = trend_data
        
        # Act
        results = book_service_with_mocks.get_book_trend_daily(db_session, 1, days=7)
        
        # Assert
        assert results == trend_data
        
        # 验证调用参数
        expected_start_time = now - timedelta(days=7)
        mock_book_dao.get_by_id.assert_called_once_with(db_session, 1)
        mock_book_snapshot_dao.get_trend_by_book_id_with_interval.assert_called_once_with(
            db_session, sample_book.novel_id, expected_start_time, now, "day"
        )
    
    @patch('app.database.service.book_service.datetime')
    def test_get_book_trend_weekly_success(self, mock_datetime, book_service_with_mocks, mock_book_dao, mock_book_snapshot_dao, sample_book, db_session):
        """测试成功获取周级趋势数据"""
        # Arrange
        now = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.now.return_value = now
        trend_data = [{"time_period": "2024-W02", "avg_clicks": 50000.0}]
        mock_book_dao.get_by_id.return_value = sample_book
        mock_book_snapshot_dao.get_trend_by_book_id_with_interval.return_value = trend_data
        
        # Act
        results = book_service_with_mocks.get_book_trend_weekly(db_session, 1, weeks=4)
        
        # Assert
        assert results == trend_data
        
        # 验证调用参数
        expected_start_time = now - timedelta(weeks=4)
        mock_book_dao.get_by_id.assert_called_once_with(db_session, 1)
        mock_book_snapshot_dao.get_trend_by_book_id_with_interval.assert_called_once_with(
            db_session, sample_book.novel_id, expected_start_time, now, "week"
        )
    
    @patch('app.database.service.book_service.datetime')
    def test_get_book_trend_monthly_success(self, mock_datetime, book_service_with_mocks, mock_book_dao, mock_book_snapshot_dao, sample_book, db_session):
        """测试成功获取月级趋势数据"""
        # Arrange
        now = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.now.return_value = now
        trend_data = [{"time_period": "2024-01", "avg_clicks": 50000.0}]
        mock_book_dao.get_by_id.return_value = sample_book
        mock_book_snapshot_dao.get_trend_by_book_id_with_interval.return_value = trend_data
        
        # Act
        results = book_service_with_mocks.get_book_trend_monthly(db_session, 1, months=3)
        
        # Assert
        assert results == trend_data
        
        # 验证调用参数
        expected_start_time = now - timedelta(days=90)  # 3 * 30
        mock_book_dao.get_by_id.assert_called_once_with(db_session, 1)
        mock_book_snapshot_dao.get_trend_by_book_id_with_interval.assert_called_once_with(
            db_session, sample_book.novel_id, expected_start_time, now, "month"
        )
    
    def test_get_book_trend_with_interval_hour(self, book_service_with_mocks, mocker, db_session):
        """测试使用统一接口获取小时级趋势"""
        # Arrange
        mock_hourly = mocker.patch.object(book_service_with_mocks, 'get_book_trend_hourly')
        trend_data = [{"time_period": "2024-01-15 11", "avg_clicks": 50000.0}]
        mock_hourly.return_value = trend_data
        
        # Act
        results = book_service_with_mocks.get_book_trend_with_interval(db_session, 1, 24, "hour")
        
        # Assert
        assert results == trend_data
        mock_hourly.assert_called_once_with(db_session, 1, 24)
    
    def test_get_book_trend_with_interval_day(self, book_service_with_mocks, mocker, db_session):
        """测试使用统一接口获取天级趋势"""
        # Arrange
        mock_daily = mocker.patch.object(book_service_with_mocks, 'get_book_trend_daily')
        trend_data = [{"time_period": "2024-01-14", "avg_clicks": 50000.0}]
        mock_daily.return_value = trend_data
        
        # Act
        results = book_service_with_mocks.get_book_trend_with_interval(db_session, 1, 7, "day")
        
        # Assert
        assert results == trend_data
        mock_daily.assert_called_once_with(db_session, 1, 7)
    
    def test_get_book_trend_with_interval_invalid(self, book_service_with_mocks, db_session):
        """测试使用无效时间间隔"""
        # Act & Assert
        with pytest.raises(ValueError, match="不支持的时间间隔"):
            book_service_with_mocks.get_book_trend_with_interval(db_session, 1, 7, "invalid")
    
    def test_create_or_update_book_success(self, book_service_with_mocks, mock_book_dao, sample_book, db_session):
        """测试成功创建或更新书籍"""
        # Arrange
        book_data = {"novel_id": 12345, "title": "新书籍", "author_id": 201}
        mock_book_dao.create_or_update_by_novel_id.return_value = sample_book
        
        # Act
        result = book_service_with_mocks.create_or_update_book(db_session, book_data)
        
        # Assert
        assert result == sample_book
        mock_book_dao.create_or_update_by_novel_id.assert_called_once_with(db_session, book_data)
    
    def test_create_book_snapshot_success(self, book_service_with_mocks, mock_book_snapshot_dao, sample_snapshot, db_session):
        """测试成功创建书籍快照"""
        # Arrange
        snapshot_data = {"novel_id": 12345, "clicks": 50000, "favorites": 1500}
        mock_book_snapshot_dao.create.return_value = sample_snapshot
        
        # Act
        result = book_service_with_mocks.create_book_snapshot(db_session, snapshot_data)
        
        # Assert
        assert result == sample_snapshot
        mock_book_snapshot_dao.create.assert_called_once_with(db_session, snapshot_data)
    
    def test_batch_create_book_snapshots_success(self, book_service_with_mocks, mock_book_snapshot_dao, sample_snapshot, db_session):
        """测试成功批量创建书籍快照"""
        # Arrange
        snapshots_data = [
            {"novel_id": 12345, "clicks": 50000, "favorites": 1500},
            {"novel_id": 12345, "clicks": 52000, "favorites": 1600}
        ]
        mock_book_snapshot_dao.bulk_create.return_value = [sample_snapshot, sample_snapshot]
        
        # Act
        results = book_service_with_mocks.batch_create_book_snapshots(db_session, snapshots_data)
        
        # Assert
        assert len(results) == 2
        mock_book_snapshot_dao.bulk_create.assert_called_once_with(db_session, snapshots_data)
    
    @patch('app.database.service.book_service.datetime')
    def test_cleanup_old_snapshots_success(self, mock_datetime, book_service_with_mocks, mock_book_snapshot_dao, db_session):
        """测试成功清理旧快照"""
        # Arrange
        now = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.now.return_value = now
        mock_book_snapshot_dao.delete_old_snapshots.return_value = 5  # 删除了5个快照
        
        # Act
        deleted_count = book_service_with_mocks.cleanup_old_snapshots(db_session, 1, keep_days=30, keep_count=100)
        
        # Assert
        assert deleted_count == 5
        
        # 验证调用参数
        expected_cutoff_time = now - timedelta(days=30)
        mock_book_snapshot_dao.delete_old_snapshots.assert_called_once_with(
            db_session, 1, expected_cutoff_time, 100
        )
    
    def test_get_book_statistics_success(self, book_service_with_mocks, mock_book_dao, mock_book_snapshot_dao, sample_book, db_session):
        """测试成功获取书籍统计信息"""
        # Arrange
        stats = {"total_snapshots": 10, "max_clicks": 60000}
        mock_book_dao.get_by_id.return_value = sample_book
        mock_book_snapshot_dao.get_statistics_by_book_id.return_value = stats
        
        # Act
        result = book_service_with_mocks.get_book_statistics(db_session, 1)
        
        # Assert
        assert result == stats
        mock_book_dao.get_by_id.assert_called_once_with(db_session, 1)
        mock_book_snapshot_dao.get_statistics_by_book_id.assert_called_once_with(db_session, sample_book.novel_id)
    
    def test_get_books_by_ids_success(self, book_service_with_mocks, mock_book_dao, sample_book, db_session):
        """测试成功根据ID列表获取书籍"""
        # Arrange
        book2 = Book(id=2, novel_id=54321, title="第二本书", author_id=202)
        mock_book_dao.get_by_id.side_effect = [sample_book, book2, None]  # 第三个ID不存在
        
        # Act
        results = book_service_with_mocks.get_books_by_ids(db_session, [1, 2, 999])
        
        # Assert
        assert len(results) == 2  # 只返回存在的书籍
        assert results[0] == sample_book
        assert results[1] == book2
        
        # 验证DAO调用
        assert mock_book_dao.get_by_id.call_count == 3
        mock_book_dao.get_by_id.assert_any_call(db_session, 1)
        mock_book_dao.get_by_id.assert_any_call(db_session, 2)
        mock_book_dao.get_by_id.assert_any_call(db_session, 999)
    
    def test_get_books_by_ids_empty_list(self, book_service_with_mocks, mock_book_dao, db_session):
        """测试空ID列表"""
        # Act
        results = book_service_with_mocks.get_books_by_ids(db_session, [])
        
        # Assert
        assert results == []
        mock_book_dao.get_by_id.assert_not_called()


class TestBookServiceIntegration:
    """BookService集成测试"""
    
    @pytest.fixture
    def book_service(self):
        """BookService实例"""
        return BookService()
    
    def test_book_lifecycle_integration(self, db_session, book_service):
        """测试书籍完整生命周期（集成测试）"""
        # 1. 创建书籍
        book_data = {
            "novel_id": 77777,
            "title": "集成测试小说",
            "author_id": 301,
            "novel_class": "现代言情",
            "tags": "都市,甜文"
        }
        
        book = book_service.create_or_update_book(db_session, book_data)
        assert book.novel_id == 77777
        assert book.title == "集成测试小说"
        
        # 2. 根据novel_id获取书籍
        found_book = book_service.get_book_by_novel_id(db_session, 77777)
        assert found_book is not None
        assert found_book.id == book.id
        
        # 3. 创建快照
        snapshot_data = {
            "novel_id": 77777,
            "clicks": 10000,
            "favorites": 500,
            "comments": 200,
            "recommendations": 50,
            "snapshot_time": datetime.now()
        }
        
        snapshot = book_service.create_book_snapshot(db_session, snapshot_data)
        assert snapshot.novel_id == 77777
        assert snapshot.clicks == 10000
        
        # 4. 获取书籍详情和最新快照
        detail = book_service.get_book_detail_with_latest_snapshot(db_session, book.id)
        assert detail is not None
        assert detail["book"].id == book.id
        assert detail["latest_snapshot"] is not None
        assert detail["latest_snapshot"].clicks == 10000
        
        # 5. 搜索书籍
        search_results = book_service.search_books(db_session, "集成测试")
        assert len(search_results) >= 1
        found_in_search = any(b.id == book.id for b in search_results)
        assert found_in_search
        
        # 6. 获取统计信息
        stats = book_service.get_book_statistics(db_session, book.id)
        assert stats["total_snapshots"] >= 1
    
    def test_pagination_integration(self, db_session, book_service):
        """测试分页功能集成测试"""
        # 创建多本书籍
        books_data = [
            {"novel_id": 88881 + i, "title": f"分页测试书籍{i}", "author_id": 401 + i}
            for i in range(5)
        ]
        
        created_books = []
        for book_data in books_data:
            book = book_service.create_or_update_book(db_session, book_data)
            created_books.append(book)
        
        # 测试分页
        page1 = book_service.get_books_with_pagination(db_session, page=1, size=2)
        assert len(page1["books"]) <= 2
        assert page1["page"] == 1
        assert page1["size"] == 2
        assert page1["total"] >= 5
        
        page2 = book_service.get_books_with_pagination(db_session, page=2, size=2)
        assert len(page2["books"]) <= 2
        assert page2["page"] == 2
        
        # 验证不同页面的书籍不重复
        page1_ids = {book.id for book in page1["books"]}
        page2_ids = {book.id for book in page2["books"]}
        assert page1_ids.isdisjoint(page2_ids)  # 两个集合没有交集
    
    def test_search_integration(self, db_session, book_service):
        """测试搜索功能集成测试"""
        # 创建具有特定关键词的书籍
        book_data = {
            "novel_id": 99999,
            "title": "搜索测试专用小说",
            "author_id": 501,
            "novel_class": "现代言情"
        }
        
        book = book_service.create_or_update_book(db_session, book_data)
        
        # 搜索测试
        search_results = book_service.search_books(db_session, "搜索测试")
        assert len(search_results) >= 1
        
        found_book = next((b for b in search_results if b.id == book.id), None)
        assert found_book is not None
        assert "搜索测试" in found_book.title
        
        # 搜索不存在的关键词
        no_results = book_service.search_books(db_session, "不存在的关键词xyz")
        assert len(no_results) == 0