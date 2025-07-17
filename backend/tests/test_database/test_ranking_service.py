"""
榜单服务测试文件
测试app.database.service.ranking_service模块的所有服务方法
"""
import pytest
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from app.database.service.ranking_service import RankingService
from app.database.db.ranking import Ranking, RankingSnapshot
from app.database.db.book import Book


class TestRankingService:
    """测试RankingService类"""
    
    @pytest.fixture
    def ranking_service(self):
        """RankingService实例fixture"""
        return RankingService()
    
    @pytest.fixture
    def mock_ranking_dao(self, mocker):
        """模拟RankingDAO"""
        return mocker.Mock()
    
    @pytest.fixture
    def mock_ranking_snapshot_dao(self, mocker):
        """模拟RankingSnapshotDAO"""
        return mocker.Mock()
    
    @pytest.fixture
    def mock_book_dao(self, mocker):
        """模拟BookDAO"""
        return mocker.Mock()
    
    @pytest.fixture
    def ranking_service_with_mocks(self, mocker, mock_ranking_dao, mock_ranking_snapshot_dao, mock_book_dao):
        """使用模拟DAO的RankingService"""
        service = RankingService()
        service.ranking_dao = mock_ranking_dao
        service.ranking_snapshot_dao = mock_ranking_snapshot_dao
        service.book_dao = mock_book_dao
        return service
    
    @pytest.fixture
    def sample_ranking(self):
        """样本榜单数据"""
        return Ranking(
            id=1,
            rank_id=100,
            rank_name="测试榜单",
            page_id="test_ranking",
            rank_group_type="热门",
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
    
    @pytest.fixture
    def sample_book(self):
        """样本书籍数据"""
        return Book(
            id=1,
            novel_id=12345,
            title="测试小说",
            author_name="测试作者",
            status="连载中"
        )
    
    @pytest.fixture
    def sample_ranking_snapshot(self, sample_book):
        """样本榜单快照数据"""
        snapshot = RankingSnapshot(
            id=1,
            ranking_id=1,
            novel_id=12345,
            position=1,
            score=95.5,
            snapshot_time=datetime(2024, 1, 15, 12, 0, 0)
        )
        snapshot.book = sample_book
        return snapshot
    
    def test_get_ranking_by_id_success(self, ranking_service_with_mocks, mock_ranking_dao, sample_ranking, db_session):
        """测试成功根据ID获取榜单"""
        # Arrange
        mock_ranking_dao.get_by_id.return_value = sample_ranking
        
        # Act
        result = ranking_service_with_mocks.get_ranking_by_id(db_session, 1)
        
        # Assert
        assert result == sample_ranking
        mock_ranking_dao.get_by_id.assert_called_once_with(db_session, 1)
    
    def test_get_ranking_by_id_not_found(self, ranking_service_with_mocks, mock_ranking_dao, db_session):
        """测试榜单不存在时返回None"""
        # Arrange
        mock_ranking_dao.get_by_id.return_value = None
        
        # Act
        result = ranking_service_with_mocks.get_ranking_by_id(db_session, 999)
        
        # Assert
        assert result is None
        mock_ranking_dao.get_by_id.assert_called_once_with(db_session, 999)
    
    def test_get_ranking_by_rank_id_success(self, ranking_service_with_mocks, mock_ranking_dao, sample_ranking, db_session):
        """测试成功根据rank_id获取榜单"""
        # Arrange
        mock_ranking_dao.get_by_rank_id.return_value = sample_ranking
        
        # Act
        result = ranking_service_with_mocks.get_ranking_by_rank_id(db_session, 100)
        
        # Assert
        assert result == sample_ranking
        mock_ranking_dao.get_by_rank_id.assert_called_once_with(db_session, 100)
    
    def test_get_rankings_by_page_id_success(self, ranking_service_with_mocks, mock_ranking_dao, sample_ranking, db_session):
        """测试成功根据页面ID获取榜单列表"""
        # Arrange
        mock_ranking_dao.get_by_page_id.return_value = [sample_ranking]
        
        # Act
        results = ranking_service_with_mocks.get_rankings_by_page_id(db_session, "test_page")
        
        # Assert
        assert len(results) == 1
        assert results[0] == sample_ranking
        mock_ranking_dao.get_by_page_id.assert_called_once_with(db_session, "test_page")
    
    def test_get_rankings_by_group_type_success(self, ranking_service_with_mocks, mock_ranking_dao, sample_ranking, db_session):
        """测试成功根据分组类型获取榜单"""
        # Arrange
        mock_ranking_dao.get_by_group_type.return_value = [sample_ranking]
        
        # Act
        results = ranking_service_with_mocks.get_rankings_by_group_type(db_session, "热门")
        
        # Assert
        assert len(results) == 1
        assert results[0] == sample_ranking
        mock_ranking_dao.get_by_group_type.assert_called_once_with(db_session, "热门")
    
    def test_get_all_rankings_success(self, ranking_service_with_mocks, mock_ranking_dao, sample_ranking, db_session):
        """测试成功分页获取所有榜单"""
        # Arrange
        mock_ranking_dao.get_multi.return_value = [sample_ranking]
        mock_ranking_dao.count.return_value = 1
        
        # Act
        result = ranking_service_with_mocks.get_all_rankings(db_session, page=1, size=20)
        
        # Assert
        assert result["rankings"] == [sample_ranking]
        assert result["total"] == 1
        assert result["page"] == 1
        assert result["size"] == 20
        assert result["total_pages"] == 1
        
        # 验证DAO调用
        mock_ranking_dao.get_multi.assert_called_once_with(db_session, skip=0, limit=20, filters=None)
        mock_ranking_dao.count.assert_called_once_with(db_session, filters=None)
    
    def test_get_all_rankings_with_filters(self, ranking_service_with_mocks, mock_ranking_dao, sample_ranking, db_session):
        """测试使用过滤条件分页获取榜单"""
        # Arrange
        filters = {"rank_group_type": "热门"}
        mock_ranking_dao.get_multi.return_value = [sample_ranking]
        mock_ranking_dao.count.return_value = 1
        
        # Act
        result = ranking_service_with_mocks.get_all_rankings(db_session, page=2, size=10, filters=filters)
        
        # Assert
        assert result["page"] == 2
        assert result["size"] == 10
        
        # 验证DAO调用
        mock_ranking_dao.get_multi.assert_called_once_with(db_session, skip=10, limit=10, filters=filters)
        mock_ranking_dao.count.assert_called_once_with(db_session, filters=filters)
    
    def test_get_ranking_detail_success_latest(self, ranking_service_with_mocks, mock_ranking_dao, mock_ranking_snapshot_dao, sample_ranking, sample_ranking_snapshot, sample_book, db_session):
        """测试成功获取榜单详情（最新数据）"""
        # Arrange
        mock_ranking_dao.get_by_id.return_value = sample_ranking
        mock_ranking_snapshot_dao.get_latest_by_ranking_id.return_value = [sample_ranking_snapshot]
        mock_ranking_snapshot_dao.get_ranking_statistics.return_value = {"total_snapshots": 10}
        # Mock book_dao
        ranking_service_with_mocks.book_dao.get_by_novel_id.return_value = sample_book
        
        # Act
        result = ranking_service_with_mocks.get_ranking_detail(db_session, 1)
        
        # Assert
        assert result is not None
        assert result["ranking"] == sample_ranking
        assert len(result["books"]) == 1
        assert result["books"][0]["title"] == "测试小说"
        assert result["books"][0]["novel_id"] == 12345
        assert result["books"][0]["position"] == 1
        assert result["total_books"] == 1
        assert result["statistics"] == {"total_snapshots": 10}
        
        # 验证DAO调用
        mock_ranking_dao.get_by_id.assert_called_once_with(db_session, 1)
        mock_ranking_snapshot_dao.get_latest_by_ranking_id.assert_called_once_with(db_session, 1, 50)
        mock_ranking_snapshot_dao.get_ranking_statistics.assert_called_once_with(db_session, 1)
    
    def test_get_ranking_detail_success_with_date(self, ranking_service_with_mocks, mock_ranking_dao, mock_ranking_snapshot_dao, sample_ranking, sample_ranking_snapshot, db_session):
        """测试成功获取榜单详情（指定日期）"""
        # Arrange
        target_date = date(2024, 1, 15)
        mock_ranking_dao.get_by_id.return_value = sample_ranking
        mock_ranking_snapshot_dao.get_by_ranking_and_date.return_value = [sample_ranking_snapshot]
        mock_ranking_snapshot_dao.get_ranking_statistics.return_value = {"total_snapshots": 10}
        
        # Act
        result = ranking_service_with_mocks.get_ranking_detail(db_session, 1, target_date, limit=30)
        
        # Assert
        assert result is not None
        assert result["ranking"] == sample_ranking
        assert len(result["books"]) == 1
        
        # 验证DAO调用
        mock_ranking_snapshot_dao.get_by_ranking_and_date.assert_called_once_with(db_session, 1, target_date, 30)
    
    def test_get_ranking_detail_ranking_not_found(self, ranking_service_with_mocks, mock_ranking_dao, db_session):
        """测试榜单不存在时返回None"""
        # Arrange
        mock_ranking_dao.get_by_id.return_value = None
        
        # Act
        result = ranking_service_with_mocks.get_ranking_detail(db_session, 999)
        
        # Assert
        assert result is None
        mock_ranking_dao.get_by_id.assert_called_once_with(db_session, 999)
    
    def test_get_ranking_detail_no_snapshots(self, ranking_service_with_mocks, mock_ranking_dao, mock_ranking_snapshot_dao, sample_ranking, db_session):
        """测试榜单无快照时的处理"""
        # Arrange
        mock_ranking_dao.get_by_id.return_value = sample_ranking
        mock_ranking_snapshot_dao.get_latest_by_ranking_id.return_value = []
        mock_ranking_snapshot_dao.get_ranking_statistics.return_value = {}
        
        # Act
        result = ranking_service_with_mocks.get_ranking_detail(db_session, 1)
        
        # Assert
        assert result is not None
        assert result["ranking"] == sample_ranking
        assert result["books"] == []
        assert result["total_books"] == 0
        assert result["snapshot_time"] is None
    
    def test_get_ranking_history_success(self, ranking_service_with_mocks, mock_ranking_snapshot_dao, db_session):
        """测试成功获取榜单历史趋势"""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 15)
        trend_data = [
            (datetime(2024, 1, 1, 12, 0, 0), 20),
            (datetime(2024, 1, 15, 12, 0, 0), 25)
        ]
        mock_ranking_snapshot_dao.get_ranking_trend.return_value = trend_data
        
        # Act
        result = ranking_service_with_mocks.get_ranking_history(db_session, 1, start_date, end_date)
        
        # Assert
        assert result["ranking_id"] == 1
        assert result["start_date"] == start_date
        assert result["end_date"] == end_date
        assert len(result["trend_data"]) == 2
        assert result["trend_data"][0]["book_count"] == 20
        assert result["trend_data"][1]["book_count"] == 25
        
        # 验证DAO调用
        expected_start_time = datetime.combine(start_date, datetime.min.time())
        expected_end_time = datetime.combine(end_date, datetime.max.time())
        mock_ranking_snapshot_dao.get_ranking_trend.assert_called_once_with(
            db_session, 1, expected_start_time, expected_end_time
        )
    
    def test_get_ranking_history_no_dates(self, ranking_service_with_mocks, mock_ranking_snapshot_dao, db_session):
        """测试不指定日期获取榜单历史"""
        # Arrange
        mock_ranking_snapshot_dao.get_ranking_trend.return_value = []
        
        # Act
        result = ranking_service_with_mocks.get_ranking_history(db_session, 1)
        
        # Assert
        assert result["ranking_id"] == 1
        assert result["start_date"] is None
        assert result["end_date"] is None
        assert result["trend_data"] == []
        
        # 验证DAO调用
        mock_ranking_snapshot_dao.get_ranking_trend.assert_called_once_with(db_session, 1, None, None)
    
    @patch('app.database.service.ranking_service.datetime')
    def test_get_book_ranking_history_success(self, mock_datetime, ranking_service_with_mocks, mock_ranking_snapshot_dao, sample_ranking, db_session):
        """测试成功获取书籍排名历史"""
        # Arrange
        now = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.now.return_value = now
        
        # 创建模拟快照数据
        mock_snapshot = Mock()
        mock_snapshot.ranking_id = 1
        mock_snapshot.position = 1
        mock_snapshot.score = 95.5
        mock_snapshot.snapshot_time = datetime(2024, 1, 14, 12, 0, 0)
        
        mock_ranking_snapshot_dao.get_book_ranking_history.return_value = [mock_snapshot]
        # Mock ranking_dao
        ranking_service_with_mocks.ranking_dao.get_by_id.return_value = sample_ranking
        
        # Act
        result = ranking_service_with_mocks.get_book_ranking_history(db_session, 12345, ranking_id=1, days=30)
        
        # Assert
        assert len(result) == 1
        assert result[0]["ranking_id"] == 1
        assert result[0]["ranking_name"] == "测试榜单"
        assert result[0]["position"] == 1
        assert result[0]["score"] == 95.5
        
        # 验证DAO调用
        expected_start_time = now - timedelta(days=30)
        mock_ranking_snapshot_dao.get_book_ranking_history.assert_called_once_with(
            db_session, 12345, 1, expected_start_time
        )
    
    def test_create_or_update_ranking_success(self, ranking_service_with_mocks, mock_ranking_dao, sample_ranking, db_session):
        """测试成功创建或更新榜单"""
        # Arrange
        ranking_data = {"rank_id": 100, "rank_name": "新榜单", "page_id": "new_ranking"}
        mock_ranking_dao.create_or_update_by_rank_id.return_value = sample_ranking
        
        # Act
        result = ranking_service_with_mocks.create_or_update_ranking(db_session, ranking_data)
        
        # Assert
        assert result == sample_ranking
        mock_ranking_dao.create_or_update_by_rank_id.assert_called_once_with(db_session, ranking_data)
    
    def test_create_ranking_snapshot_success(self, ranking_service_with_mocks, mock_ranking_snapshot_dao, sample_ranking_snapshot, db_session):
        """测试成功创建榜单快照"""
        # Arrange
        snapshot_data = {"ranking_id": 1, "novel_id": 12345, "position": 1, "score": 95.5}
        mock_ranking_snapshot_dao.create.return_value = sample_ranking_snapshot
        
        # Act
        result = ranking_service_with_mocks.create_ranking_snapshot(db_session, snapshot_data)
        
        # Assert
        assert result == sample_ranking_snapshot
        mock_ranking_snapshot_dao.create.assert_called_once_with(db_session, snapshot_data)
    
    def test_batch_create_ranking_snapshots_success(self, ranking_service_with_mocks, mock_ranking_snapshot_dao, sample_ranking_snapshot, db_session):
        """测试成功批量创建榜单快照"""
        # Arrange
        snapshots_data = [
            {"ranking_id": 1, "novel_id": 12345, "position": 1, "score": 95.5},
            {"ranking_id": 1, "novel_id": 54321, "position": 2, "score": 90.0}
        ]
        mock_ranking_snapshot_dao.bulk_create.return_value = [sample_ranking_snapshot, sample_ranking_snapshot]
        
        # Act
        results = ranking_service_with_mocks.batch_create_ranking_snapshots(db_session, snapshots_data)
        
        # Assert
        assert len(results) == 2
        mock_ranking_snapshot_dao.bulk_create.assert_called_once_with(db_session, snapshots_data)
    
    def test_compare_rankings_success(self, ranking_service_with_mocks, mock_ranking_dao, mock_ranking_snapshot_dao, sample_ranking, sample_ranking_snapshot, db_session):
        """测试成功对比多个榜单"""
        # Arrange
        ranking_ids = [1, 2]
        
        # 模拟榜单数据
        ranking1 = Mock()
        ranking1.id = 1
        ranking1.rank_name = "榜单1"
        ranking1.page_id = "ranking1"
        
        ranking2 = Mock()
        ranking2.id = 2
        ranking2.rank_name = "榜单2"
        ranking2.page_id = "ranking2"
        
        mock_ranking_dao.get_by_id.side_effect = [ranking1, ranking2]
        
        # 模拟快照数据
        snapshot1 = Mock()
        snapshot1.book_id = 12345
        snapshot1.book.id = 1
        snapshot1.book.title = "书籍1"
        snapshot1.position = 1
        snapshot1.score = 95.5
        
        snapshot2 = Mock()
        snapshot2.book_id = 54321
        snapshot2.book.id = 2
        snapshot2.book.title = "书籍2"
        snapshot2.position = 1
        snapshot2.score = 90.0
        
        comparison_data = {
            1: [snapshot1],
            2: [snapshot2]
        }
        mock_ranking_snapshot_dao.get_books_comparison.return_value = comparison_data
        
        # Act
        result = ranking_service_with_mocks.compare_rankings(db_session, ranking_ids)
        
        # Assert
        assert len(result["rankings"]) == 2
        assert result["rankings"][0]["ranking_id"] == 1
        assert result["rankings"][1]["ranking_id"] == 2
        assert 1 in result["ranking_data"]
        assert 2 in result["ranking_data"]
        assert result["stats"]["total_unique_books"] == 2
        assert result["stats"]["common_books_count"] == 0  # 没有共同书籍
        
        # 验证DAO调用
        mock_ranking_dao.get_by_id.assert_any_call(db_session, 1)
        mock_ranking_dao.get_by_id.assert_any_call(db_session, 2)
        mock_ranking_snapshot_dao.get_books_comparison.assert_called_once_with(db_session, ranking_ids, None)
    
    def test_compare_rankings_with_common_books(self, ranking_service_with_mocks, mock_ranking_dao, mock_ranking_snapshot_dao, sample_book, db_session):
        """测试对比榜单有共同书籍的情况"""
        # Arrange
        ranking_ids = [1, 2]
        
        ranking1 = Mock()
        ranking1.id = 1
        ranking1.rank_name = "榜单1"
        ranking1.page_id = "ranking1"
        
        ranking2 = Mock()
        ranking2.id = 2
        ranking2.rank_name = "榜单2"
        ranking2.page_id = "ranking2"
        
        mock_ranking_dao.get_by_id.side_effect = [ranking1, ranking2]
        
        # 两个榜单都有同一本书
        snapshot1 = Mock()
        snapshot1.novel_id = 12345
        snapshot1.position = 1
        snapshot1.score = 95.5
        
        snapshot2 = Mock()
        snapshot2.novel_id = 12345  # 同一本书
        snapshot2.position = 3
        snapshot2.score = 90.0
        
        comparison_data = {
            1: [snapshot1],
            2: [snapshot2]
        }
        mock_ranking_snapshot_dao.get_books_comparison.return_value = comparison_data
        
        # Mock book_dao to return the same book for the shared novel_id
        ranking_service_with_mocks.book_dao.get_by_novel_id.return_value = sample_book
        
        # Act
        result = ranking_service_with_mocks.compare_rankings(db_session, ranking_ids)
        
        # Assert
        assert result["stats"]["total_unique_books"] == 1
        assert result["stats"]["common_books_count"] == 1
        assert len(result["common_books"]) == 1
        assert result["common_books"][0]["title"] == "测试小说"
    
    def test_compare_rankings_insufficient_rankings(self, ranking_service_with_mocks, db_session):
        """测试榜单数量不足时抛出异常"""
        # Act & Assert
        with pytest.raises(ValueError, match="至少需要2个榜单进行对比"):
            ranking_service_with_mocks.compare_rankings(db_session, [1])
    
    def test_compare_rankings_nonexistent_ranking(self, ranking_service_with_mocks, mock_ranking_dao, db_session):
        """测试部分榜单不存在时抛出异常"""
        # Arrange
        ranking_ids = [1, 999]
        mock_ranking_dao.get_by_id.side_effect = [Mock(), None]  # 第二个榜单不存在
        
        # Act & Assert
        with pytest.raises(ValueError, match="部分榜单不存在"):
            ranking_service_with_mocks.compare_rankings(db_session, ranking_ids)
    
    @patch('app.database.service.ranking_service.datetime')
    def test_cleanup_old_ranking_snapshots_success(self, mock_datetime, ranking_service_with_mocks, mock_ranking_snapshot_dao, db_session):
        """测试成功清理旧的榜单快照"""
        # Arrange
        now = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.now.return_value = now
        mock_ranking_snapshot_dao.delete_old_snapshots.return_value = 10  # 删除了10个快照
        
        # Act
        deleted_count = ranking_service_with_mocks.cleanup_old_ranking_snapshots(db_session, 1, keep_days=30)
        
        # Assert
        assert deleted_count == 10
        
        # 验证DAO调用
        expected_cutoff_time = now - timedelta(days=30)
        mock_ranking_snapshot_dao.delete_old_snapshots.assert_called_once_with(
            db_session, 1, expected_cutoff_time, 30
        )
    
    def test_get_ranking_statistics_success(self, ranking_service_with_mocks, mock_ranking_snapshot_dao, db_session):
        """测试成功获取榜单统计信息"""
        # Arrange
        stats = {"total_snapshots": 50, "unique_books": 25}
        mock_ranking_snapshot_dao.get_ranking_statistics.return_value = stats
        
        # Act
        result = ranking_service_with_mocks.get_ranking_statistics(db_session, 1)
        
        # Assert
        assert result == stats
        mock_ranking_snapshot_dao.get_ranking_statistics.assert_called_once_with(db_session, 1)


class TestRankingServiceIntegration:
    """RankingService集成测试"""
    
    @pytest.fixture
    def ranking_service(self):
        """RankingService实例"""
        return RankingService()
    
    def test_ranking_lifecycle_integration(self, db_session, ranking_service):
        """测试榜单完整生命周期（集成测试）"""
        # 1. 创建榜单
        ranking_data = {
            "rank_id": 88888,
            "rank_name": "集成测试榜单",
            "page_id": "integration_test",
            "rank_group_type": "测试分组"
        }
        
        ranking = ranking_service.create_or_update_ranking(db_session, ranking_data)
        assert ranking.rank_id == 88888
        assert ranking.rank_name == "集成测试榜单"
        
        # 2. 根据不同方式获取榜单
        found_by_id = ranking_service.get_ranking_by_id(db_session, ranking.id)
        assert found_by_id is not None
        assert found_by_id.id == ranking.id
        
        found_by_rank_id = ranking_service.get_ranking_by_rank_id(db_session, 88888)
        assert found_by_rank_id is not None
        assert found_by_rank_id.id == ranking.id
        
        found_by_page_id = ranking_service.get_rankings_by_page_id(db_session, "integration_test")
        assert len(found_by_page_id) >= 1
        assert any(r.id == ranking.id for r in found_by_page_id)
        
        found_by_group = ranking_service.get_rankings_by_group_type(db_session, "测试分组")
        assert len(found_by_group) >= 1
        assert any(r.id == ranking.id for r in found_by_group)
        
        # 3. 分页获取榜单
        all_rankings = ranking_service.get_all_rankings(db_session, page=1, size=10)
        assert all_rankings["total"] >= 1
        ranking_ids = [r.id for r in all_rankings["rankings"]]
        assert ranking.id in ranking_ids
        
        # 4. 获取榜单详情（无快照）
        detail = ranking_service.get_ranking_detail(db_session, ranking.id)
        assert detail is not None
        assert detail["ranking"].id == ranking.id
        assert detail["books"] == []
        assert detail["total_books"] == 0
        
        # 5. 获取统计信息
        stats = ranking_service.get_ranking_statistics(db_session, ranking.id)
        assert stats.get("total_snapshots", 0) == 0
    
    def test_ranking_with_snapshots_integration(self, db_session, ranking_service):
        """测试榜单与快照的集成测试"""
        # 创建榜单
        ranking_data = {
            "rank_id": 99999,
            "rank_name": "快照测试榜单",
            "page_id": "snapshot_test",
            "rank_group_type": "快照测试"
        }
        ranking = ranking_service.create_or_update_ranking(db_session, ranking_data)
        
        # 创建书籍（需要先有书籍才能创建快照）
        from app.database.service.book_service import BookService
        book_service = BookService()
        book_data = {
            "novel_id": 77777,
            "title": "快照测试小说",
            "author_name": "快照测试作者"
        }
        book = book_service.create_or_update_book(db_session, book_data)
        
        # 创建快照
        snapshot_data = {
            "ranking_id": ranking.id,
            "novel_id": book.novel_id,
            "position": 1,
            "score": 95.5,
            "snapshot_time": datetime.now()
        }
        snapshot = ranking_service.create_ranking_snapshot(db_session, snapshot_data)
        assert snapshot.ranking_id == ranking.id
        assert snapshot.novel_id == book.novel_id
        
        # 获取榜单详情（有快照）
        detail = ranking_service.get_ranking_detail(db_session, ranking.id)
        assert detail is not None
        assert detail["total_books"] == 1
        assert len(detail["books"]) == 1
        assert detail["books"][0]["title"] == book.title
        assert detail["books"][0]["position"] == 1
        
        # 获取书籍排名历史
        ranking_history = ranking_service.get_book_ranking_history(
            db_session, book.novel_id, ranking_id=ranking.id
        )
        assert len(ranking_history) >= 1
        assert ranking_history[0]["ranking_id"] == ranking.id
        assert ranking_history[0]["position"] == 1
        
        # 获取榜单历史趋势
        trend = ranking_service.get_ranking_history(db_session, ranking.id)
        assert trend["ranking_id"] == ranking.id
        assert len(trend["trend_data"]) >= 1
        
        # 获取统计信息
        stats = ranking_service.get_ranking_statistics(db_session, ranking.id)
        assert stats["total_snapshots"] >= 1
        assert stats["unique_books"] >= 1
    
    def test_compare_rankings_integration(self, db_session, ranking_service):
        """测试榜单对比功能集成测试"""
        # 创建两个榜单
        ranking1_data = {
            "rank_id": 11111,
            "rank_name": "对比榜单1",
            "page_id": "compare1",
            "rank_group_type": "对比测试"
        }
        ranking1 = ranking_service.create_or_update_ranking(db_session, ranking1_data)
        
        ranking2_data = {
            "rank_id": 22222,
            "rank_name": "对比榜单2",
            "page_id": "compare2",
            "rank_group_type": "对比测试"
        }
        ranking2 = ranking_service.create_or_update_ranking(db_session, ranking2_data)
        
        # 创建书籍
        from app.database.service.book_service import BookService
        book_service = BookService()
        
        book1_data = {"novel_id": 11111, "title": "对比书籍1", "author_name": "作者1"}
        book1 = book_service.create_or_update_book(db_session, book1_data)
        
        book2_data = {"novel_id": 22222, "title": "对比书籍2", "author_name": "作者2"}
        book2 = book_service.create_or_update_book(db_session, book2_data)
        
        # 为榜单创建快照
        now = datetime.now()
        snapshots_data = [
            {
                "ranking_id": ranking1.id,
                "novel_id": book1.novel_id,
                "position": 1,
                "score": 95.0,
                "snapshot_time": now
            },
            {
                "ranking_id": ranking1.id,
                "novel_id": book2.novel_id,
                "position": 2,
                "score": 90.0,
                "snapshot_time": now
            },
            {
                "ranking_id": ranking2.id,
                "novel_id": book2.novel_id,  # 共同书籍
                "position": 1,
                "score": 92.0,
                "snapshot_time": now
            }
        ]
        
        ranking_service.batch_create_ranking_snapshots(db_session, snapshots_data)
        
        # 进行榜单对比
        comparison = ranking_service.compare_rankings(db_session, [ranking1.id, ranking2.id])
        
        # 验证对比结果
        assert len(comparison["rankings"]) == 2
        assert comparison["stats"]["total_unique_books"] == 2
        assert comparison["stats"]["common_books_count"] == 1  # book2是共同书籍
        assert len(comparison["common_books"]) == 1
        assert comparison["common_books"][0]["title"] == "对比书籍2"
        
        # 验证榜单数据
        assert ranking1.id in comparison["ranking_data"]
        assert ranking2.id in comparison["ranking_data"]
        assert len(comparison["ranking_data"][ranking1.id]) == 2  # 榜单1有2本书
        assert len(comparison["ranking_data"][ranking2.id]) == 1  # 榜单2有1本书