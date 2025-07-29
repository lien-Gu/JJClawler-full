"""
RankingService业务逻辑的Mock测试
使用pytest-mock进行单元测试，专注于业务逻辑验证
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from app.database.service.ranking_service import RankingService
from app.models import ranking


class TestRankingServiceMock:
    """使用Mock的RankingService测试类"""

    @pytest.fixture
    def ranking_service(self):
        return RankingService()

    @pytest.fixture
    def mock_db_session(self, mocker: MockerFixture):
        """模拟数据库会话"""
        return mocker.MagicMock()

    def test_get_ranking_detail_by_day_success(self, ranking_service, mock_db_session, mocker: MockerFixture):
        """测试按天获取榜单详情 - 成功场景"""
        # Mock数据准备
        mock_ranking = MagicMock()
        mock_ranking.id = 1
        mock_ranking.channel_name = "测试频道"
        mock_ranking.sub_channel_name = "测试子频道"
        mock_ranking.page_id = "test_page"
        mock_ranking.rank_group_type = "test_type"

        mock_snapshot = MagicMock()
        mock_snapshot.novel_id = 123
        mock_snapshot.position = 1
        mock_snapshot.snapshot_time = datetime(2024, 1, 1, 12, 0, 0)

        # Mock方法调用
        mock_db_session.get.return_value = mock_ranking
        mocker.patch.object(ranking_service, 'get_snapshots_by_day', return_value=[mock_snapshot])

        # 执行测试
        target_date = date(2024, 1, 1)
        result = ranking_service.get_ranking_detail_by_day(mock_db_session, 1, target_date)

        # 验证结果
        assert result is not None
        assert result.id == 1
        assert result.channel_name == "测试频道"
        assert len(result.books) == 1
        assert result.books[0].novel_id == 123
        assert result.books[0].position == 1

        # 验证调用
        mock_db_session.get.assert_called_once_with(mocker.ANY, 1)
        ranking_service.get_snapshots_by_day.assert_called_once_with(mock_db_session, 1, target_date)

    def test_get_ranking_detail_by_day_not_found(self, ranking_service, mock_db_session, mocker: MockerFixture):
        """测试按天获取榜单详情 - 榜单不存在"""
        # Mock方法调用
        mock_db_session.get.return_value = None

        # 执行测试
        target_date = date(2024, 1, 1)
        result = ranking_service.get_ranking_detail_by_day(mock_db_session, 999, target_date)

        # 验证结果
        assert result is None

    def test_get_ranking_detail_by_hour_success(self, ranking_service, mock_db_session, mocker: MockerFixture):
        """测试按小时获取榜单详情 - 成功场景"""
        # Mock数据准备
        mock_ranking = MagicMock()
        mock_ranking.id = 1
        mock_ranking.channel_name = "测试频道"
        mock_ranking.sub_channel_name = "测试子频道"
        mock_ranking.page_id = "test_page"
        mock_ranking.rank_group_type = "test_type"

        mock_snapshot = MagicMock()
        mock_snapshot.novel_id = 123
        mock_snapshot.position = 1
        mock_snapshot.snapshot_time = datetime(2024, 1, 1, 14, 30, 0)

        # Mock方法调用
        mock_db_session.get.return_value = mock_ranking
        mocker.patch.object(ranking_service, 'get_snapshots_by_hour', return_value=[mock_snapshot])

        # 执行测试
        target_date = date(2024, 1, 1)
        target_hour = 14
        result = ranking_service.get_ranking_detail_by_hour(mock_db_session, 1, target_date, target_hour)

        # 验证结果
        assert result is not None
        assert result.id == 1
        assert result.channel_name == "测试频道"
        assert len(result.books) == 1
        assert result.books[0].novel_id == 123

        # 验证调用
        ranking_service.get_snapshots_by_hour.assert_called_once_with(mock_db_session, 1, target_date, target_hour)

    def test_get_ranking_history_by_day_success(self, ranking_service, mock_db_session, mocker: MockerFixture):
        """测试按天获取榜单历史 - 成功场景"""
        # Mock数据准备
        mock_ranking = MagicMock()
        mock_ranking.id = 1
        mock_ranking.channel_name = "测试频道"
        mock_ranking.sub_channel_name = "测试子频道"
        mock_ranking.page_id = "test_page"
        mock_ranking.rank_group_type = "test_type"

        # Mock数据库执行结果
        mock_batch_row = MagicMock()
        mock_batch_row.batch_id = "batch_001"
        mock_batch_row.snapshot_date = date(2024, 1, 1)

        mock_snapshot = MagicMock()
        mock_snapshot.batch_id = "batch_001"
        mock_snapshot.novel_id = 123
        mock_snapshot.position = 1
        mock_snapshot.snapshot_time = datetime(2024, 1, 1, 12, 0, 0)

        # Mock方法调用
        mocker.patch.object(ranking_service, 'get_ranking_by_id', return_value=mock_ranking)
        
        # Mock数据库查询
        mock_db_session.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[mock_batch_row])),  # 第一次查询batch_ids
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_snapshot]))))  # 第二次查询snapshots
        ]

        # 执行测试
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 3)
        result = ranking_service.get_ranking_history_by_day(mock_db_session, 1, start_date, end_date)

        # 验证结果
        assert result is not None
        assert result.id == 1
        assert result.channel_name == "测试频道"
        assert len(result.snapshots) == 1
        assert len(result.snapshots[0].books) == 1

        # 验证调用
        ranking_service.get_ranking_by_id.assert_called_once_with(mock_db_session, 1)
        assert mock_db_session.execute.call_count == 2

    def test_get_ranking_history_by_day_ranking_not_found(self, ranking_service, mock_db_session, mocker: MockerFixture):
        """测试按天获取榜单历史 - 榜单不存在"""
        # Mock方法调用
        mocker.patch.object(ranking_service, 'get_ranking_by_id', return_value=None)

        # 执行测试
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 3)
        result = ranking_service.get_ranking_history_by_day(mock_db_session, 999, start_date, end_date)

        # 验证结果
        assert result is None

    def test_get_ranking_history_by_hour_success(self, ranking_service, mock_db_session, mocker: MockerFixture):
        """测试按小时获取榜单历史 - 成功场景"""
        # Mock数据准备
        mock_ranking = MagicMock()
        mock_ranking.id = 1
        mock_ranking.channel_name = "测试频道"
        mock_ranking.sub_channel_name = "测试子频道"
        mock_ranking.page_id = "test_page"
        mock_ranking.rank_group_type = "test_type"

        # Mock数据库执行结果
        mock_batch_row = MagicMock()
        mock_batch_row.batch_id = "batch_001"
        mock_batch_row.snapshot_hour = "2024-01-01 14:00:00"

        mock_snapshot = MagicMock()
        mock_snapshot.batch_id = "batch_001"
        mock_snapshot.novel_id = 123
        mock_snapshot.position = 1
        mock_snapshot.snapshot_time = datetime(2024, 1, 1, 14, 30, 0)

        # Mock方法调用
        mocker.patch.object(ranking_service, 'get_ranking_by_id', return_value=mock_ranking)
        
        # Mock数据库查询
        mock_db_session.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[mock_batch_row])),  # 第一次查询batch_ids
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_snapshot]))))  # 第二次查询snapshots
        ]

        # 执行测试
        start_time = datetime(2024, 1, 1, 14, 0, 0)
        end_time = datetime(2024, 1, 1, 16, 0, 0)
        result = ranking_service.get_ranking_history_by_hour(mock_db_session, 1, start_time, end_time)

        # 验证结果
        assert result is not None
        assert result.id == 1
        assert result.channel_name == "测试频道"
        assert len(result.snapshots) == 1
        assert len(result.snapshots[0].books) == 1

        # 验证调用
        ranking_service.get_ranking_by_id.assert_called_once_with(mock_db_session, 1)
        assert mock_db_session.execute.call_count == 2

    def test_get_rankings_by_name_with_pagination_success(self, ranking_service, mock_db_session, mocker: MockerFixture):
        """测试按名称分页查询榜单 - 成功场景"""
        # Mock数据准备
        mock_ranking = MagicMock()
        mock_ranking.id = 1
        mock_ranking.channel_name = "测试频道"
        mock_ranking.sub_channel_name = "测试子频道"
        mock_ranking.page_id = "test_page"
        mock_ranking.rank_group_type = "test_type"

        # Mock数据库查询结果
        mock_db_session.execute.return_value = MagicMock(scalars=MagicMock(return_value=[mock_ranking]))
        mock_db_session.scalar.return_value = 5  # 总数

        # Mock ranking.RankingBasic.model_validate
        mock_ranking_basic = MagicMock()
        mock_ranking_basic.id = 1
        mock_ranking_basic.channel_name = "测试频道"
        mocker.patch('app.models.ranking.RankingBasic.model_validate', return_value=mock_ranking_basic)

        # 执行测试
        rankings, total_pages = ranking_service.get_rankings_by_name_with_pagination(
            mock_db_session, "测试", page=1, size=2
        )

        # 验证结果
        assert len(rankings) == 1
        assert rankings[0].id == 1
        assert rankings[0].channel_name == "测试频道"
        assert total_pages == 3  # ceil(5/2) = 3

        # 验证调用
        assert mock_db_session.execute.call_count == 1
        assert mock_db_session.scalar.call_count == 1

    def test_create_or_update_ranking_create_new(self, ranking_service, mock_db_session, mocker: MockerFixture):
        """测试创建或更新榜单 - 创建新榜单场景"""
        # Mock数据准备
        ranking_data = {
            "rank_id": "new_ranking",
            "rank_name": "新榜单",
            "channel_name": "新频道"
        }

        mock_new_ranking = MagicMock()
        mock_new_ranking.id = 1
        mock_new_ranking.rank_id = "new_ranking"

        # Mock方法调用
        mocker.patch.object(ranking_service, 'get_rankings_by_rank_id', return_value=[])
        mocker.patch.object(ranking_service, 'create_ranking', return_value=mock_new_ranking)

        # 执行测试
        result = ranking_service.create_or_update_ranking(mock_db_session, ranking_data)

        # 验证结果
        assert result.id == 1
        assert result.rank_id == "new_ranking"

        # 验证调用
        ranking_service.get_rankings_by_rank_id.assert_called_once_with(mock_db_session, "new_ranking")
        ranking_service.create_ranking.assert_called_once_with(mock_db_session, ranking_data)

    def test_create_or_update_ranking_update_existing(self, ranking_service, mock_db_session, mocker: MockerFixture):
        """测试创建或更新榜单 - 更新已存在榜单场景"""
        # Mock数据准备
        ranking_data = {
            "rank_id": "existing_ranking",
            "rank_name": "更新榜单",
            "channel_name": "更新频道"
        }

        mock_existing_ranking = MagicMock()
        mock_existing_ranking.id = 1
        mock_existing_ranking.rank_id = "existing_ranking"

        mock_updated_ranking = MagicMock()
        mock_updated_ranking.id = 1
        mock_updated_ranking.rank_name = "更新榜单"

        # Mock方法调用
        mocker.patch.object(ranking_service, 'get_rankings_by_rank_id', return_value=[mock_existing_ranking])
        mocker.patch.object(ranking_service, 'update_ranking', return_value=mock_updated_ranking)

        # 执行测试
        result = ranking_service.create_or_update_ranking(mock_db_session, ranking_data)

        # 验证结果
        assert result.id == 1
        assert result.rank_name == "更新榜单"

        # 验证调用
        ranking_service.get_rankings_by_rank_id.assert_called_once_with(mock_db_session, "existing_ranking")
        ranking_service.update_ranking.assert_called_once_with(mock_db_session, mock_existing_ranking, ranking_data)

    def test_batch_create_ranking_snapshots_success(self, ranking_service, mock_db_session, mocker: MockerFixture):
        """测试批量创建榜单快照 - 成功场景"""
        # Mock数据准备
        snapshots_data = [
            {
                "ranking_id": 1,
                "book_id": 123,
                "position": 1,
                "snapshot_time": datetime.now()
            },
            {
                "ranking_id": 1,
                "book_id": 124,
                "position": 2,
                "snapshot_time": datetime.now()
            }
        ]

        batch_id = "test_batch_001"
        
        # Mock RankingSnapshot创建
        mock_snapshot1 = MagicMock()
        mock_snapshot2 = MagicMock()
        
        # Mock filter_dict和RankingSnapshot
        mocker.patch('app.database.service.ranking_service.filter_dict', side_effect=lambda x, y: x)
        mock_ranking_snapshot = mocker.patch('app.database.service.ranking_service.RankingSnapshot')
        mock_ranking_snapshot.side_effect = [mock_snapshot1, mock_snapshot2]

        # 执行测试
        result = ranking_service.batch_create_ranking_snapshots(mock_db_session, snapshots_data, batch_id)

        # 验证结果
        assert len(result) == 2
        assert result[0] == mock_snapshot1
        assert result[1] == mock_snapshot2

        # 验证所有快照数据都添加了batch_id
        for snapshot in snapshots_data:
            assert snapshot['batch_id'] == batch_id

        # 验证数据库操作
        mock_db_session.add_all.assert_called_once()
        mock_db_session.commit.assert_called_once()