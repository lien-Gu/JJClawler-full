"""
书籍DAO测试文件
测试app.database.dao.book_dao模块的所有DAO方法
"""
import pytest
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.exc import IntegrityError

from app.database.dao.book_dao import BookDAO, BookSnapshotDAO
from app.database.db.book import Book, BookSnapshot


class TestBookDAO:
    """测试BookDAO类"""
    
    @pytest.fixture
    def book_dao(self):
        """BookDAO实例fixture"""
        return BookDAO()
    
    @pytest.fixture
    def book_entity(self, create_test_book):
        """书籍实体fixture"""
        return create_test_book
    
    def test_get_by_novel_id_success(self, db_session, book_dao, book_entity):
        """测试成功根据novel_id获取书籍"""
        # Act
        result = book_dao.get_by_novel_id(db_session, book_entity.novel_id)
        
        # Assert
        assert result is not None
        assert result.novel_id == book_entity.novel_id
        assert result.title == book_entity.title
        assert result.author_id == book_entity.author_id
    
    def test_get_by_novel_id_not_found(self, db_session, book_dao):
        """测试novel_id不存在时返回None"""
        # Act
        result = book_dao.get_by_novel_id(db_session, 99999)
        
        # Assert
        assert result is None
    
    def test_search_by_title_success(self, db_session, book_dao, create_multiple_books):
        """测试成功根据标题搜索书籍"""
        # Act
        results = book_dao.search_by_title(db_session, "测试", limit=10)
        
        # Assert
        assert len(results) >= 2  # 至少找到包含"测试"的书籍
        for book in results:
            assert "测试" in book.title
    
    def test_search_by_title_partial_match(self, db_session, book_dao, create_multiple_books):
        """测试部分匹配搜索"""
        # Act
        results = book_dao.search_by_title(db_session, "小说", limit=10)
        
        # Assert
        assert len(results) >= 1
        for book in results:
            assert "小说" in book.title
    
    def test_search_by_title_no_results(self, db_session, book_dao, create_multiple_books):
        """测试搜索无结果"""
        # Act
        results = book_dao.search_by_title(db_session, "不存在的标题xyz", limit=10)
        
        # Assert
        assert len(results) == 0
    
    def test_search_by_title_with_limit(self, db_session, book_dao, create_multiple_books):
        """测试搜索结果限制"""
        # Act
        results = book_dao.search_by_title(db_session, "测试", limit=1)
        
        # Assert
        assert len(results) == 1
    
    def test_get_all_success(self, db_session, book_dao, create_multiple_books):
        """测试成功获取所有书籍"""
        # Act
        results = book_dao.get_all(db_session, skip=0, limit=10)
        
        # Assert
        assert len(results) == 3  # create_multiple_books创建了3本书
        # 验证按创建时间倒序排列
        assert results[0].created_at >= results[1].created_at
        assert results[1].created_at >= results[2].created_at
    
    def test_get_all_with_pagination(self, db_session, book_dao, create_multiple_books):
        """测试分页获取书籍"""
        # Act - 获取第二页，每页1条
        results = book_dao.get_all(db_session, skip=1, limit=1)
        
        # Assert
        assert len(results) == 1
        
        # Act - 获取第三页，每页1条
        results_page3 = book_dao.get_all(db_session, skip=2, limit=1)
        
        # Assert
        assert len(results_page3) == 1
        assert results[0].novel_id != results_page3[0].novel_id
    
    def test_create_or_update_by_novel_id_create_new(self, db_session, book_dao):
        """测试创建新书籍"""
        # Arrange
        book_data = {
            "novel_id": 54321,
            "title": "新创建的小说",
            "author_id": 201,
            "novel_class": "现代言情",
            "tags": "现代,都市"
        }
        
        # Act
        result = book_dao.create_or_update_by_novel_id(db_session, book_data)
        
        # Assert
        assert result is not None
        assert result.novel_id == 54321
        assert result.title == "新创建的小说"
        assert result.author_id == 201
        assert result.novel_class == "现代言情"
        assert result.tags == "现代,都市"
        assert result.created_at is not None
        assert result.updated_at is not None
    
    def test_create_or_update_by_novel_id_update_existing(self, db_session, book_dao, book_entity):
        """测试更新已存在的书籍"""
        # Arrange
        original_updated_at = book_entity.updated_at
        update_data = {
            "novel_id": book_entity.novel_id,
            "title": "更新后的标题",
            "novel_class": "古代言情",
            "tags": "宫廷,重生,甜文"
        }
        
        # Act
        result = book_dao.create_or_update_by_novel_id(db_session, update_data)
        
        # Assert
        assert result is not None
        assert result.novel_id == book_entity.novel_id
        assert result.title == "更新后的标题"
        assert result.novel_class == "古代言情"
        assert result.tags == "宫廷,重生,甜文"
        assert result.updated_at > original_updated_at
        assert result.created_at == book_entity.created_at  # 创建时间不变
    
    def test_create_or_update_by_novel_id_missing_novel_id(self, db_session, book_dao):
        """测试缺少novel_id时抛出异常"""
        # Arrange
        book_data = {
            "title": "缺少ID的小说",
            "author_id": 301
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="novel_id is required"):
            book_dao.create_or_update_by_novel_id(db_session, book_data)
    
    def test_create_with_duplicate_novel_id(self, db_session, book_dao, book_entity):
        """测试创建重复novel_id的书籍（应该通过update处理）"""
        # Arrange
        duplicate_data = {
            "novel_id": book_entity.novel_id,
            "title": "重复ID测试",
            "author_id": 999
        }
        
        # Act
        result = book_dao.create_or_update_by_novel_id(db_session, duplicate_data)
        
        # Assert - 应该是更新操作，不是创建新记录
        assert result.novel_id == book_entity.novel_id
        assert result.title == "重复ID测试"
        assert result.author_id == 999
        
        # 验证数据库中只有一条记录
        all_books = book_dao.get_all(db_session, skip=0, limit=100)
        books_with_this_id = [b for b in all_books if b.novel_id == book_entity.novel_id]
        assert len(books_with_this_id) == 1


class TestBookSnapshotDAO:
    """测试BookSnapshotDAO类"""
    
    @pytest.fixture
    def snapshot_dao(self):
        """BookSnapshotDAO实例fixture"""
        return BookSnapshotDAO()
    
    @pytest.fixture
    def book_entity(self, create_test_book):
        """书籍实体fixture"""
        return create_test_book
    
    @pytest.fixture
    def snapshot_entity(self, create_test_book_snapshot):
        """快照实体fixture"""
        return create_test_book_snapshot
    
    def test_get_latest_by_book_id_success(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试成功获取书籍最新快照"""
        # Act
        result = snapshot_dao.get_latest_by_book_id(db_session, book_entity.id)
        
        # Assert
        assert result is not None
        assert result.book_id == book_entity.id
        # 应该是最新的快照（时间最大）
        assert result.snapshot_time == datetime(2024, 1, 15, 12, 0, 0)
        assert result.clicks == 52000  # 最新快照的点击数
    
    def test_get_latest_by_book_id_not_found(self, db_session, snapshot_dao):
        """测试获取不存在书籍的最新快照"""
        # Act
        result = snapshot_dao.get_latest_by_book_id(db_session, 99999)
        
        # Assert
        assert result is None
    
    def test_get_trend_by_book_id_success(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试成功获取书籍趋势数据"""
        # Act
        results = snapshot_dao.get_trend_by_book_id(db_session, book_entity.id, limit=10)
        
        # Assert
        assert len(results) >= 2  # 至少有2个快照
        # 验证按时间倒序排列
        for i in range(len(results) - 1):
            assert results[i].snapshot_time >= results[i + 1].snapshot_time
    
    def test_get_trend_by_book_id_with_time_range(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试指定时间范围获取趋势数据"""
        # Arrange
        start_time = datetime(2024, 1, 14, 0, 0, 0)
        end_time = datetime(2024, 1, 15, 23, 59, 59)
        
        # Act
        results = snapshot_dao.get_trend_by_book_id(
            db_session, book_entity.id, start_time, end_time, limit=10
        )
        
        # Assert
        assert len(results) >= 2
        for snapshot in results:
            assert start_time <= snapshot.snapshot_time <= end_time
    
    def test_get_trend_by_book_id_with_limit(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试限制返回数量"""
        # Act
        results = snapshot_dao.get_trend_by_book_id(db_session, book_entity.id, limit=1)
        
        # Assert
        assert len(results) == 1
    
    def test_get_hourly_trend_by_book_id(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试按小时获取趋势数据"""
        # Arrange
        start_time = datetime(2024, 1, 14, 0, 0, 0)
        end_time = datetime(2024, 1, 15, 23, 59, 59)
        
        # Act
        results = snapshot_dao.get_hourly_trend_by_book_id(db_session, book_entity.id, start_time, end_time)
        
        # Assert
        assert isinstance(results, list)
        if results:  # 如果有数据
            for trend_item in results:
                assert "time_period" in trend_item
                assert "avg_clicks" in trend_item
                assert "avg_favorites" in trend_item
                assert "max_clicks" in trend_item
                assert "min_clicks" in trend_item
                assert "snapshot_count" in trend_item
    
    def test_get_daily_trend_by_book_id(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试按天获取趋势数据"""
        # Arrange
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 31, 23, 59, 59)
        
        # Act
        results = snapshot_dao.get_daily_trend_by_book_id(db_session, book_entity.id, start_time, end_time)
        
        # Assert
        assert isinstance(results, list)
        if results:
            for trend_item in results:
                assert "time_period" in trend_item
                assert "avg_clicks" in trend_item
                assert "avg_favorites" in trend_item
    
    def test_get_weekly_trend_by_book_id(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试按周获取趋势数据"""
        # Arrange
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 31, 23, 59, 59)
        
        # Act
        results = snapshot_dao.get_weekly_trend_by_book_id(db_session, book_entity.id, start_time, end_time)
        
        # Assert
        assert isinstance(results, list)
    
    def test_get_monthly_trend_by_book_id(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试按月获取趋势数据"""
        # Arrange
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 3, 31, 23, 59, 59)
        
        # Act
        results = snapshot_dao.get_monthly_trend_by_book_id(db_session, book_entity.id, start_time, end_time)
        
        # Assert
        assert isinstance(results, list)
    
    def test_get_trend_by_book_id_with_interval_hour(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试使用统一接口获取小时级趋势"""
        # Arrange
        start_time = datetime(2024, 1, 14, 0, 0, 0)
        end_time = datetime(2024, 1, 15, 23, 59, 59)
        
        # Act
        results = snapshot_dao.get_trend_by_book_id_with_interval(
            db_session, book_entity.id, start_time, end_time, "hour"
        )
        
        # Assert
        assert isinstance(results, list)
    
    def test_get_trend_by_book_id_with_interval_day(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试使用统一接口获取天级趋势"""
        # Arrange
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 31, 23, 59, 59)
        
        # Act
        results = snapshot_dao.get_trend_by_book_id_with_interval(
            db_session, book_entity.id, start_time, end_time, "day"
        )
        
        # Assert
        assert isinstance(results, list)
    
    def test_get_trend_by_book_id_with_interval_invalid(self, db_session, snapshot_dao, book_entity):
        """测试使用无效时间间隔"""
        # Arrange
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 31, 23, 59, 59)
        
        # Act & Assert
        with pytest.raises(ValueError, match="不支持的时间间隔"):
            snapshot_dao.get_trend_by_book_id_with_interval(
                db_session, book_entity.id, start_time, end_time, "invalid"
            )
    
    def test_get_statistics_by_book_id_success(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试成功获取书籍统计信息"""
        # Act
        stats = snapshot_dao.get_statistics_by_book_id(db_session, book_entity.id)
        
        # Assert
        assert isinstance(stats, dict)
        assert "total_snapshots" in stats
        assert "max_favorites" in stats
        assert "max_clicks" in stats
        assert "max_comments" in stats
        assert "first_snapshot_time" in stats
        assert "last_snapshot_time" in stats
        
        assert stats["total_snapshots"] >= 2  # 至少有2个快照
        assert stats["max_clicks"] >= 50000   # 最大点击数
        assert stats["max_favorites"] >= 1500 # 最大收藏数
    
    def test_get_statistics_by_book_id_no_snapshots(self, db_session, snapshot_dao):
        """测试获取无快照书籍的统计信息"""
        # Act
        stats = snapshot_dao.get_statistics_by_book_id(db_session, 99999)
        
        # Assert
        assert stats == {}
    
    def test_bulk_create_success(self, db_session, snapshot_dao, book_entity):
        """测试批量创建快照"""
        # Arrange
        snapshots_data = [
            {
                "book_id": book_entity.id,
                "clicks": 60000,
                "favorites": 2000,
                "comments": 1000,
                "snapshot_time": datetime(2024, 1, 16, 12, 0, 0)
            },
            {
                "book_id": book_entity.id,
                "clicks": 65000,
                "favorites": 2100,
                "comments": 1050,
                "snapshot_time": datetime(2024, 1, 17, 12, 0, 0)
            }
        ]
        
        # Act
        results = snapshot_dao.bulk_create(db_session, snapshots_data)
        
        # Assert
        assert len(results) == 2
        for i, snapshot in enumerate(results):
            assert snapshot.book_id == book_entity.id
            assert snapshot.clicks == snapshots_data[i]["clicks"]
            assert snapshot.favorites == snapshots_data[i]["favorites"]
    
    def test_delete_old_snapshots_success(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试删除旧快照"""
        # Arrange - 创建更多快照
        old_snapshots_data = [
            {
                "book_id": book_entity.id,
                "clicks": 40000 + i * 1000,
                "favorites": 1000 + i * 50,
                "comments": 500 + i * 20,
                "snapshot_time": datetime(2024, 1, 10, 12, 0, 0) + timedelta(hours=i)
            }
            for i in range(5)
        ]
        snapshot_dao.bulk_create(db_session, old_snapshots_data)
        
        # 验证快照总数
        all_snapshots = snapshot_dao.get_trend_by_book_id(db_session, book_entity.id, limit=100)
        initial_count = len(all_snapshots)
        assert initial_count >= 7  # 至少有7个快照
        
        # Act - 删除2024-1-13之前的快照，但保留最新的3个
        before_time = datetime(2024, 1, 13, 0, 0, 0)
        deleted_count = snapshot_dao.delete_old_snapshots(
            db_session, book_entity.id, before_time, keep_count=3
        )
        
        # Assert
        assert deleted_count >= 0  # 删除了一些快照
        
        # 验证剩余快照数量
        remaining_snapshots = snapshot_dao.get_trend_by_book_id(db_session, book_entity.id, limit=100)
        # 应该保留至少3个最新快照，加上2024-1-13之后的快照
        assert len(remaining_snapshots) >= 3
    
    def test_delete_old_snapshots_keep_recent(self, db_session, snapshot_dao, book_entity, create_multiple_snapshots):
        """测试删除旧快照时保留最新记录"""
        # Arrange
        before_time = datetime(2024, 1, 20, 0, 0, 0)  # 删除所有快照之前的时间
        
        # Act
        deleted_count = snapshot_dao.delete_old_snapshots(
            db_session, book_entity.id, before_time, keep_count=2
        )
        
        # Assert
        remaining_snapshots = snapshot_dao.get_trend_by_book_id(db_session, book_entity.id, limit=100)
        assert len(remaining_snapshots) == 2  # 应该保留2个最新快照
        
        # 验证保留的是最新的快照
        assert remaining_snapshots[0].snapshot_time >= remaining_snapshots[1].snapshot_time


class TestBookDAOIntegration:
    """BookDAO和BookSnapshotDAO集成测试"""
    
    @pytest.fixture
    def book_dao(self):
        return BookDAO()
    
    @pytest.fixture
    def snapshot_dao(self):
        return BookSnapshotDAO()
    
    def test_book_with_snapshots_lifecycle(self, db_session, book_dao, snapshot_dao):
        """测试书籍与快照的完整生命周期"""
        # 1. 创建书籍
        book_data = {
            "novel_id": 88888,
            "title": "生命周期测试小说",
            "author_id": 401,
            "novel_class": "现代言情"
        }
        book = book_dao.create_or_update_by_novel_id(db_session, book_data)
        assert book.novel_id == 88888
        
        # 2. 创建快照
        snapshot_data = {
            "book_id": book.id,
            "clicks": 10000,
            "favorites": 500,
            "comments": 200,
            "snapshot_time": datetime.now()
        }
        snapshot = snapshot_dao.create(db_session, snapshot_data)
        assert snapshot.book_id == book.id
        
        # 3. 获取书籍的最新快照
        latest_snapshot = snapshot_dao.get_latest_by_book_id(db_session, book.id)
        assert latest_snapshot is not None
        assert latest_snapshot.book_id == book.id
        assert latest_snapshot.clicks == 10000
        
        # 4. 更新书籍信息
        update_data = {
            "novel_id": book.novel_id,
            "novel_class": "现代言情",
            "tags": "都市,完结"
        }
        updated_book = book_dao.create_or_update_by_novel_id(db_session, update_data)
        assert updated_book.novel_class == "现代言情"
        assert updated_book.tags == "都市,完结"
        
        # 5. 获取统计信息
        stats = snapshot_dao.get_statistics_by_book_id(db_session, book.id)
        assert stats["total_snapshots"] == 1
        assert stats["max_clicks"] == 10000