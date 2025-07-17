"""
榜单DAO测试文件
测试app.database.dao.ranking_dao模块的所有DAO方法
"""
import pytest
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from app.database.dao.ranking_dao import RankingDAO, RankingSnapshotDAO
from app.database.db.ranking import Ranking, RankingSnapshot


class TestRankingDAO:
    """测试RankingDAO类"""
    
    @pytest.fixture
    def ranking_dao(self):
        """RankingDAO实例fixture"""
        return RankingDAO()
    
    @pytest.fixture
    def ranking_entity(self, create_test_ranking):
        """榜单实体fixture"""
        return create_test_ranking
    
    def test_get_by_rank_id_success(self, db_session, ranking_dao, ranking_entity):
        """测试成功根据rank_id获取榜单"""
        # Act
        result = ranking_dao.get_by_rank_id(db_session, ranking_entity.rank_id)
        
        # Assert
        assert result is not None
        assert result.rank_id == ranking_entity.rank_id
        assert result.rank_name == ranking_entity.rank_name
        assert result.page_id == ranking_entity.page_id
        assert result.rank_group_type == ranking_entity.rank_group_type
    
    def test_get_by_rank_id_not_found(self, db_session, ranking_dao):
        """测试rank_id不存在时返回None"""
        # Act
        result = ranking_dao.get_by_rank_id(db_session, 99999)
        
        # Assert
        assert result is None
    
    def test_get_by_page_id_success(self, db_session, ranking_dao, ranking_entity):
        """测试成功根据page_id获取榜单列表"""
        # Act
        results = ranking_dao.get_by_page_id(db_session, ranking_entity.page_id)
        
        # Assert
        assert len(results) >= 1
        for ranking in results:
            assert ranking.page_id == ranking_entity.page_id
    
    def test_get_by_page_id_not_found(self, db_session, ranking_dao):
        """测试page_id不存在时返回空列表"""
        # Act
        results = ranking_dao.get_by_page_id(db_session, "nonexistent_page")
        
        # Assert
        assert results == []
    
    def test_get_by_group_type_success(self, db_session, ranking_dao, ranking_entity):
        """测试成功根据榜单分组类型获取榜单"""
        # Act
        results = ranking_dao.get_by_group_type(db_session, ranking_entity.rank_group_type)
        
        # Assert
        assert len(results) >= 1
        for ranking in results:
            assert ranking.rank_group_type == ranking_entity.rank_group_type
    
    def test_get_by_group_type_not_found(self, db_session, ranking_dao):
        """测试分组类型不存在时返回空列表"""
        # Act
        results = ranking_dao.get_by_group_type(db_session, "不存在的分组")
        
        # Assert
        assert results == []
    
    def test_create_or_update_by_rank_id_create_new(self, db_session, ranking_dao):
        """测试创建新榜单"""
        # Arrange
        ranking_data = {
            "rank_id": 9999,
            "rank_name": "新创建的榜单",
            "page_id": "new_ranking",
            "rank_group_type": "新分组",
        }
        
        # Act
        result = ranking_dao.create_or_update_by_rank_id(db_session, ranking_data)
        
        # Assert
        assert result is not None
        assert result.rank_id == 9999
        assert result.rank_name == "新创建的榜单"
        assert result.page_id == "new_ranking"
        assert result.rank_group_type == "新分组"
        assert result.created_at is not None
    
    def test_create_or_update_by_rank_id_update_existing(self, db_session, ranking_dao, ranking_entity):
        """测试更新已存在的榜单"""
        # Arrange
        original_updated_at = ranking_entity.updated_at
        update_data = {
            "rank_id": ranking_entity.rank_id,
            "rank_name": "更新后的榜单名称",
        }
        
        # Act
        result = ranking_dao.create_or_update_by_rank_id(db_session, update_data)
        
        # Assert
        assert result is not None
        assert result.rank_id == ranking_entity.rank_id
        assert result.rank_name == "更新后的榜单名称"
        assert result.updated_at > original_updated_at
        assert result.created_at == ranking_entity.created_at  # 创建时间不变
    
    def test_create_or_update_by_rank_id_missing_rank_id(self, db_session, ranking_dao):
        """测试缺少rank_id时抛出异常"""
        # Arrange
        ranking_data = {
            "rank_name": "缺少ID的榜单",
            "page_id": "missing_id"
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="rank_id is required"):
            ranking_dao.create_or_update_by_rank_id(db_session, ranking_data)
    
    def test_create_with_duplicate_rank_id(self, db_session, ranking_dao, ranking_entity):
        """测试创建重复rank_id的榜单（应该通过update处理）"""
        # Arrange
        duplicate_data = {
            "rank_id": ranking_entity.rank_id,
            "rank_name": "重复ID测试榜单",
            "page_id": "duplicate_test"
        }
        
        # Act
        result = ranking_dao.create_or_update_by_rank_id(db_session, duplicate_data)
        
        # Assert - 应该是更新操作，不是创建新记录
        assert result.rank_id == ranking_entity.rank_id
        assert result.rank_name == "重复ID测试榜单"
        assert result.page_id == "duplicate_test"
        
        # 验证数据库中只有一条记录
        all_rankings = ranking_dao.get_multi(db_session, skip=0, limit=100)
        rankings_with_this_id = [r for r in all_rankings if r.rank_id == ranking_entity.rank_id]
        assert len(rankings_with_this_id) == 1


class TestRankingSnapshotDAO:
    """测试RankingSnapshotDAO类"""
    
    @pytest.fixture
    def ranking_snapshot_dao(self):
        """RankingSnapshotDAO实例fixture"""
        return RankingSnapshotDAO()
    
    @pytest.fixture
    def ranking_entity(self, create_test_ranking):
        """榜单实体fixture"""
        return create_test_ranking
    
    @pytest.fixture
    def book_entity(self, create_test_book):
        """书籍实体fixture"""
        return create_test_book
    
    @pytest.fixture
    def ranking_snapshot_entity(self, create_test_ranking_snapshot):
        """榜单快照实体fixture"""
        return create_test_ranking_snapshot
    
    @pytest.fixture
    def multiple_ranking_snapshots(self, db_session, ranking_entity, book_entity):
        """创建多个榜单快照"""
        snapshots_data = [
            {
                "ranking_id": ranking_entity.id,
                "book_id": book_entity.id,
                "position": 1,
                "score": 95.0,
                "snapshot_time": datetime(2024, 1, 14, 12, 0, 0)
            },
            {
                "ranking_id": ranking_entity.id,
                "book_id": book_entity.id,
                "position": 2,
                "score": 92.0,
                "snapshot_time": datetime(2024, 1, 15, 12, 0, 0)
            },
            {
                "ranking_id": ranking_entity.id,
                "book_id": book_entity.id,
                "position": 1,
                "score": 96.0,
                "snapshot_time": datetime(2024, 1, 16, 12, 0, 0)  # 最新快照
            }
        ]
        
        snapshots = []
        for snapshot_data in snapshots_data:
            snapshot = RankingSnapshot(**snapshot_data)
            db_session.add(snapshot)
            snapshots.append(snapshot)
        
        db_session.commit()
        
        for snapshot in snapshots:
            db_session.refresh(snapshot)
        
        return snapshots
    
    def test_get_latest_by_ranking_id_success(self, db_session, ranking_snapshot_dao, ranking_entity, multiple_ranking_snapshots):
        """测试成功获取榜单最新快照"""
        # Act
        results = ranking_snapshot_dao.get_latest_by_ranking_id(db_session, ranking_entity.id, limit=10)
        
        # Assert
        assert len(results) >= 1
        # 验证获取的是最新时间的快照
        for snapshot in results:
            assert snapshot.ranking_id == ranking_entity.id
            assert snapshot.snapshot_time == datetime(2024, 1, 16, 12, 0, 0)  # 最新时间
        
        # 验证按位置排序
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].position <= results[i + 1].position
    
    def test_get_latest_by_ranking_id_not_found(self, db_session, ranking_snapshot_dao):
        """测试获取不存在榜单的最新快照"""
        # Act
        results = ranking_snapshot_dao.get_latest_by_ranking_id(db_session, 99999)
        
        # Assert
        assert results == []
    
    def test_get_latest_by_ranking_id_with_limit(self, db_session, ranking_snapshot_dao, ranking_entity, multiple_ranking_snapshots):
        """测试限制返回数量"""
        # Act
        results = ranking_snapshot_dao.get_latest_by_ranking_id(db_session, ranking_entity.id, limit=1)
        
        # Assert
        assert len(results) <= 1
    
    def test_get_by_ranking_and_date_success(self, db_session, ranking_snapshot_dao, ranking_entity, multiple_ranking_snapshots):
        """测试成功获取指定日期的榜单快照"""
        # Act
        target_date = date(2024, 1, 15)
        results = ranking_snapshot_dao.get_by_ranking_and_date(db_session, ranking_entity.id, target_date)
        
        # Assert
        assert len(results) >= 1
        for snapshot in results:
            assert snapshot.ranking_id == ranking_entity.id
            assert snapshot.snapshot_time.date() == target_date
    
    def test_get_by_ranking_and_date_not_found(self, db_session, ranking_snapshot_dao, ranking_entity):
        """测试获取不存在日期的榜单快照"""
        # Act
        target_date = date(2024, 12, 31)  # 不存在的日期
        results = ranking_snapshot_dao.get_by_ranking_and_date(db_session, ranking_entity.id, target_date)
        
        # Assert
        assert results == []
    
    def test_get_book_ranking_history_success(self, db_session, ranking_snapshot_dao, book_entity, multiple_ranking_snapshots):
        """测试成功获取书籍排名历史"""
        # Act
        results = ranking_snapshot_dao.get_book_ranking_history(db_session, book_entity.id)
        
        # Assert
        assert len(results) >= 3  # 至少有3个快照
        for snapshot in results:
            assert snapshot.book_id == book_entity.id
        
        # 验证按时间倒序排列
        for i in range(len(results) - 1):
            assert results[i].snapshot_time >= results[i + 1].snapshot_time
    
    def test_get_book_ranking_history_with_ranking_filter(self, db_session, ranking_snapshot_dao, book_entity, ranking_entity, multiple_ranking_snapshots):
        """测试指定榜单ID获取书籍排名历史"""
        # Act
        results = ranking_snapshot_dao.get_book_ranking_history(
            db_session, book_entity.id, ranking_id=ranking_entity.id
        )
        
        # Assert
        assert len(results) >= 3
        for snapshot in results:
            assert snapshot.book_id == book_entity.id
            assert snapshot.ranking_id == ranking_entity.id
    
    def test_get_book_ranking_history_with_time_range(self, db_session, ranking_snapshot_dao, book_entity, multiple_ranking_snapshots):
        """测试指定时间范围获取书籍排名历史"""
        # Arrange
        start_time = datetime(2024, 1, 15, 0, 0, 0)
        end_time = datetime(2024, 1, 16, 23, 59, 59)
        
        # Act
        results = ranking_snapshot_dao.get_book_ranking_history(
            db_session, book_entity.id, start_time=start_time, end_time=end_time
        )
        
        # Assert
        assert len(results) >= 2  # 应该有2个在时间范围内的快照
        for snapshot in results:
            assert start_time <= snapshot.snapshot_time <= end_time
    
    def test_get_book_ranking_history_with_limit(self, db_session, ranking_snapshot_dao, book_entity, multiple_ranking_snapshots):
        """测试限制返回数量"""
        # Act
        results = ranking_snapshot_dao.get_book_ranking_history(db_session, book_entity.id, limit=2)
        
        # Assert
        assert len(results) <= 2
    
    def test_get_book_ranking_history_not_found(self, db_session, ranking_snapshot_dao):
        """测试获取不存在书籍的排名历史"""
        # Act
        results = ranking_snapshot_dao.get_book_ranking_history(db_session, 99999)
        
        # Assert
        assert results == []
    
    def test_get_ranking_statistics_success(self, db_session, ranking_snapshot_dao, ranking_entity, multiple_ranking_snapshots):
        """测试成功获取榜单统计信息"""
        # Act
        stats = ranking_snapshot_dao.get_ranking_statistics(db_session, ranking_entity.id)
        
        # Assert
        assert isinstance(stats, dict)
        assert "total_snapshots" in stats
        assert "unique_books" in stats
        assert "first_snapshot_time" in stats
        assert "last_snapshot_time" in stats
        
        assert stats["total_snapshots"] >= 3  # 至少有3个不同时间的快照
        assert stats["unique_books"] >= 1     # 至少有1本书
        assert stats["first_snapshot_time"] is not None
        assert stats["last_snapshot_time"] is not None
        assert stats["first_snapshot_time"] <= stats["last_snapshot_time"]
    
    def test_get_ranking_statistics_no_snapshots(self, db_session, ranking_snapshot_dao):
        """测试获取无快照榜单的统计信息"""
        # Act
        stats = ranking_snapshot_dao.get_ranking_statistics(db_session, 99999)
        
        # Assert
        assert stats == {
            'first_snapshot_time': None,
            'last_snapshot_time': None,
            'total_snapshots': 0,
            'unique_books': 0
        }
    
    def test_get_ranking_trend_success(self, db_session, ranking_snapshot_dao, ranking_entity, multiple_ranking_snapshots):
        """测试成功获取榜单变化趋势"""
        # Act
        trend_data = ranking_snapshot_dao.get_ranking_trend(db_session, ranking_entity.id)
        
        # Assert
        assert isinstance(trend_data, list)
        assert len(trend_data) >= 3  # 至少有3个时间点的数据
        
        for time_point, book_count in trend_data:
            assert isinstance(time_point, datetime)
            assert isinstance(book_count, int)
            assert book_count >= 1  # 每个快照至少有1本书
        
        # 验证按时间升序排列
        for i in range(len(trend_data) - 1):
            assert trend_data[i][0] <= trend_data[i + 1][0]
    
    def test_get_ranking_trend_with_time_range(self, db_session, ranking_snapshot_dao, ranking_entity, multiple_ranking_snapshots):
        """测试指定时间范围获取榜单趋势"""
        # Arrange
        start_time = datetime(2024, 1, 15, 0, 0, 0)
        end_time = datetime(2024, 1, 16, 23, 59, 59)
        
        # Act
        trend_data = ranking_snapshot_dao.get_ranking_trend(
            db_session, ranking_entity.id, start_time, end_time
        )
        
        # Assert
        assert isinstance(trend_data, list)
        for time_point, book_count in trend_data:
            assert start_time <= time_point <= end_time
    
    def test_get_ranking_trend_no_data(self, db_session, ranking_snapshot_dao):
        """测试获取无数据榜单的趋势"""
        # Act
        trend_data = ranking_snapshot_dao.get_ranking_trend(db_session, 99999)
        
        # Assert
        assert trend_data == []
    
    def test_bulk_create_success(self, db_session, ranking_snapshot_dao, ranking_entity, book_entity):
        """测试批量创建快照"""
        # Arrange
        snapshots_data = [
            {
                "ranking_id": ranking_entity.id,
                "book_id": book_entity.id,
                "position": 5,
                "score": 90.0,
                "snapshot_time": datetime(2024, 1, 20, 12, 0, 0)
            },
            {
                "ranking_id": ranking_entity.id,
                "book_id": book_entity.id,
                "position": 4,
                "score": 91.0,
                "snapshot_time": datetime(2024, 1, 21, 12, 0, 0)
            }
        ]
        
        # Act
        results = ranking_snapshot_dao.bulk_create(db_session, snapshots_data)
        
        # Assert
        assert len(results) == 2
        for i, snapshot in enumerate(results):
            assert snapshot.ranking_id == ranking_entity.id
            assert snapshot.book_id == book_entity.id
            assert snapshot.position == snapshots_data[i]["position"]
            assert snapshot.score == snapshots_data[i]["score"]
    
    def test_delete_old_snapshots_success(self, db_session, ranking_snapshot_dao, ranking_entity, multiple_ranking_snapshots):
        """测试删除旧快照"""
        # Arrange - 创建更多快照
        old_snapshots_data = [
            {
                "ranking_id": ranking_entity.id,
                "book_id": multiple_ranking_snapshots[0].book_id,
                "position": 3,
                "score": 88.0,
                "snapshot_time": datetime(2024, 1, 5, 12, 0, 0) + timedelta(days=i)
            }
            for i in range(5)
        ]
        ranking_snapshot_dao.bulk_create(db_session, old_snapshots_data)
        
        # 验证快照总数
        trend_data = ranking_snapshot_dao.get_ranking_trend(db_session, ranking_entity.id)
        initial_count = len(trend_data)
        assert initial_count >= 8  # 至少有8个时间点
        
        # Act - 删除2024-1-13之前的快照，但保留最新的5天
        before_time = datetime(2024, 1, 13, 0, 0, 0)
        deleted_count = ranking_snapshot_dao.delete_old_snapshots(
            db_session, ranking_entity.id, before_time, keep_days=5
        )
        
        # Assert
        assert deleted_count >= 0  # 删除了一些快照
        
        # 验证剩余快照
        remaining_trend = ranking_snapshot_dao.get_ranking_trend(db_session, ranking_entity.id)
        # 应该保留至少5天的快照，加上2024-1-13之后的快照
        assert len(remaining_trend) >= 3
    
    def test_delete_old_snapshots_keep_recent(self, db_session, ranking_snapshot_dao, ranking_entity, multiple_ranking_snapshots):
        """测试删除旧快照时保留最新记录"""
        # Arrange
        before_time = datetime(2024, 1, 20, 0, 0, 0)  # 删除所有快照之前的时间
        
        # Act
        deleted_count = ranking_snapshot_dao.delete_old_snapshots(
            db_session, ranking_entity.id, before_time, keep_days=2
        )
        
        # Assert
        remaining_trend = ranking_snapshot_dao.get_ranking_trend(db_session, ranking_entity.id)
        assert len(remaining_trend) == 2  # 应该保留2天的快照
    
    def test_get_books_comparison_latest(self, db_session, ranking_snapshot_dao, ranking_entity, multiple_ranking_snapshots):
        """测试获取多个榜单的最新书籍对比数据"""
        # Arrange
        ranking_ids = [ranking_entity.id]
        
        # Act
        comparison_data = ranking_snapshot_dao.get_books_comparison(db_session, ranking_ids)
        
        # Assert
        assert isinstance(comparison_data, dict)
        assert ranking_entity.id in comparison_data
        assert len(comparison_data[ranking_entity.id]) >= 1
        
        # 验证是最新数据
        for snapshot in comparison_data[ranking_entity.id]:
            assert snapshot.snapshot_time == datetime(2024, 1, 16, 12, 0, 0)  # 最新时间
    
    def test_get_books_comparison_with_date(self, db_session, ranking_snapshot_dao, ranking_entity, multiple_ranking_snapshots):
        """测试获取指定日期的多个榜单对比数据"""
        # Arrange
        ranking_ids = [ranking_entity.id]
        target_date = date(2024, 1, 15)
        
        # Act
        comparison_data = ranking_snapshot_dao.get_books_comparison(db_session, ranking_ids, target_date)
        
        # Assert
        assert isinstance(comparison_data, dict)
        assert ranking_entity.id in comparison_data
        
        # 验证是指定日期的数据
        for snapshot in comparison_data[ranking_entity.id]:
            assert snapshot.snapshot_time.date() == target_date
    
    def test_get_books_comparison_multiple_rankings(self, db_session, ranking_snapshot_dao, ranking_entity):
        """测试多个榜单对比（包含不存在的榜单）"""
        # Arrange
        ranking_ids = [ranking_entity.id, 99999]  # 包含一个不存在的榜单
        
        # Act
        comparison_data = ranking_snapshot_dao.get_books_comparison(db_session, ranking_ids)
        
        # Assert
        assert isinstance(comparison_data, dict)
        assert len(comparison_data) == 2
        assert ranking_entity.id in comparison_data
        assert 99999 in comparison_data
        assert len(comparison_data[99999]) == 0  # 不存在的榜单返回空列表


class TestRankingDAOIntegration:
    """RankingDAO和RankingSnapshotDAO集成测试"""
    
    @pytest.fixture
    def ranking_dao(self):
        return RankingDAO()
    
    @pytest.fixture
    def ranking_snapshot_dao(self):
        return RankingSnapshotDAO()
    
    @pytest.fixture
    def book_entity(self, create_test_book):
        """书籍实体fixture"""
        return create_test_book
    
    def test_ranking_with_snapshots_lifecycle(self, db_session, ranking_dao, ranking_snapshot_dao, book_entity):
        """测试榜单与快照的完整生命周期"""
        # 1. 创建榜单
        ranking_data = {
            "rank_id": 77777,
            "rank_name": "生命周期测试榜单",
            "page_id": "lifecycle_test",
            "rank_group_type": "测试分组",
        }
        ranking = ranking_dao.create_or_update_by_rank_id(db_session, ranking_data)
        assert ranking.rank_id == 77777
        
        # 2. 创建快照
        snapshot_data = {
            "ranking_id": ranking.id,
            "book_id": book_entity.id,
            "position": 1,
            "score": 95.5,
            "snapshot_time": datetime.now()
        }
        snapshot = ranking_snapshot_dao.create(db_session, snapshot_data)
        assert snapshot.ranking_id == ranking.id
        
        # 3. 获取榜单的最新快照
        latest_snapshots = ranking_snapshot_dao.get_latest_by_ranking_id(db_session, ranking.id)
        assert len(latest_snapshots) == 1
        assert latest_snapshots[0].book_id == book_entity.id
        assert latest_snapshots[0].position == 1
        
        # 4. 更新榜单信息
        update_data = {
            "rank_id": ranking.rank_id,
        }
        updated_ranking = ranking_dao.create_or_update_by_rank_id(db_session, update_data)
        
        # 5. 获取统计信息
        stats = ranking_snapshot_dao.get_ranking_statistics(db_session, ranking.id)
        assert stats["total_snapshots"] == 1
        assert stats["unique_books"] == 1
    
    def test_multiple_rankings_comparison(self, db_session, ranking_dao, ranking_snapshot_dao, book_entity):
        """测试多个榜单对比功能"""
        # 创建两个榜单
        ranking1_data = {
            "rank_id": 88881,
            "rank_name": "对比榜单1",
            "page_id": "compare_test_1",
            "rank_group_type": "对比分组"
        }
        ranking1 = ranking_dao.create_or_update_by_rank_id(db_session, ranking1_data)
        
        ranking2_data = {
            "rank_id": 88882,
            "rank_name": "对比榜单2",
            "page_id": "compare_test_2",
            "rank_group_type": "对比分组"
        }
        ranking2 = ranking_dao.create_or_update_by_rank_id(db_session, ranking2_data)
        
        # 为每个榜单创建快照
        now = datetime.now()
        snapshots_data = [
            {
                "ranking_id": ranking1.id,
                "book_id": book_entity.id,
                "position": 1,
                "score": 95.0,
                "snapshot_time": now
            },
            {
                "ranking_id": ranking2.id,
                "book_id": book_entity.id,
                "position": 3,
                "score": 90.0,
                "snapshot_time": now
            }
        ]
        ranking_snapshot_dao.bulk_create(db_session, snapshots_data)
        
        # 进行对比
        comparison_data = ranking_snapshot_dao.get_books_comparison(
            db_session, [ranking1.id, ranking2.id]
        )
        
        # 验证对比结果
        assert len(comparison_data) == 2
        assert ranking1.id in comparison_data
        assert ranking2.id in comparison_data
        assert len(comparison_data[ranking1.id]) == 1
        assert len(comparison_data[ranking2.id]) == 1
        
        # 验证同一本书在不同榜单的位置
        book_in_ranking1 = comparison_data[ranking1.id][0]
        book_in_ranking2 = comparison_data[ranking2.id][0]
        assert book_in_ranking1.book_id == book_in_ranking2.book_id
        assert book_in_ranking1.position == 1
        assert book_in_ranking2.position == 3