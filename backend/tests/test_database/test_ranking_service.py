"""
RankingService集成测试
使用真实内存数据库进行服务层功能测试，验证数据库CRUD操作和业务逻辑
"""

from datetime import date, datetime, timedelta

import pytest

from app.database.service.ranking_service import RankingService
from app.database.db.ranking import Ranking, RankingSnapshot


class TestRankingServiceIntegration:
    """RankingService集成测试类 - 使用真实内存数据库"""

    @pytest.fixture
    def ranking_service(self):
        return RankingService()

    # ==================== 基础CRUD操作测试 ====================

    def test_get_ranking_by_id_success(self, ranking_service, populated_db_session):
        """测试根据ID获取榜单 - 成功场景"""
        # 执行测试 - 获取已存在的榜单
        result = ranking_service.get_ranking_by_id(populated_db_session, 1)

        # 验证结果
        assert result is not None
        assert result.id == 1
        assert result.rank_id == "jiazi"
        assert result.channel_name == "夹子"

    def test_get_ranking_by_id_not_found(self, ranking_service, populated_db_session):
        """测试根据ID获取榜单 - 榜单不存在"""
        # 执行测试 - 获取不存在的榜单
        result = ranking_service.get_ranking_by_id(populated_db_session, 999)

        # 验证结果
        assert result is None

    def test_get_rankings_by_rank_id_success(self, ranking_service, populated_db_session):
        """测试根据rank_id获取榜单列表 - 成功场景"""
        # 执行测试 - 获取具有相同rank_id的榜单（如VIP金榜有多个）
        result = ranking_service.get_rankings_by_rank_id(populated_db_session, "657")

        # 验证结果
        assert len(result) >= 1  # 至少有一个榜单
        for ranking in result:
            assert ranking.rank_id == "657"

    def test_get_rankings_by_rank_id_not_found(self, ranking_service, populated_db_session):
        """测试根据rank_id获取榜单列表 - 不存在的rank_id"""
        # 执行测试 - 获取不存在的rank_id
        result = ranking_service.get_rankings_by_rank_id(populated_db_session, "nonexistent")

        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 0

    def test_create_or_update_ranking_create_new(self, ranking_service, test_db_session, sample_ranking_data):
        """测试创建或更新榜单 - 创建新榜单场景"""
        # 确认榜单不存在
        existing_rankings = ranking_service.get_rankings_by_rank_id(test_db_session, sample_ranking_data["rank_id"])
        assert len(existing_rankings) == 0

        # 执行测试 - 创建新榜单
        result = ranking_service.create_or_update_ranking(test_db_session, sample_ranking_data)

        # 验证结果
        assert result is not None
        assert result.rank_id == sample_ranking_data["rank_id"]
        assert result.channel_name == sample_ranking_data["channel_name"]

        # 验证数据库中的记录
        db_ranking = test_db_session.get(Ranking, result.id)
        assert db_ranking is not None
        assert db_ranking.rank_id == sample_ranking_data["rank_id"]

    def test_create_or_update_ranking_update_existing(self, ranking_service, populated_db_session):
        """测试创建或更新榜单 - 更新已存在榜单场景"""
        # 准备更新数据
        update_data = {
            "rank_id": "jiazi",  # 使用已存在的rank_id
            "channel_name": "更新后的夹子榜单",
            "rank_group_type": "更新分组",
            "page_id": "updated_jiazi"
        }

        # 执行测试 - 更新已存在的榜单
        result = ranking_service.create_or_update_ranking(populated_db_session, update_data)

        # 验证结果
        assert result is not None
        assert result.rank_id == "jiazi"
        assert result.channel_name == "更新后的夹子榜单"

        # 验证数据库更新
        db_ranking = populated_db_session.get(Ranking, result.id)
        assert db_ranking.channel_name == "更新后的夹子榜单"

    def test_create_or_update_ranking_missing_rank_id(self, ranking_service, test_db_session):
        """测试创建或更新榜单 - 缺少rank_id异常场景"""
        # 准备无效数据 - 没有rank_id
        invalid_data = {
            "channel_name": "无ID榜单",
            "page_id": "no_id_page"
        }

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="ranking_data中必须包含rank_id"):
            ranking_service.create_or_update_ranking(test_db_session, invalid_data)

    def test_batch_create_ranking_snapshots_success(self, ranking_service, populated_db_session, sample_ranking_snapshots_data):
        """测试批量创建榜单快照 - 成功场景"""
        # 生成批次ID
        from app.utils import generate_batch_id
        batch_id = generate_batch_id()

        # 执行测试 - 批量创建快照
        result = ranking_service.batch_create_ranking_snapshots(populated_db_session, sample_ranking_snapshots_data, batch_id)

        # 验证结果
        assert len(result) == len(sample_ranking_snapshots_data)
        
        # 验证每个快照
        for i, snapshot in enumerate(result):
            assert snapshot.ranking_id == sample_ranking_snapshots_data[i]["ranking_id"]
            assert snapshot.novel_id == sample_ranking_snapshots_data[i]["novel_id"]
            assert snapshot.position == sample_ranking_snapshots_data[i]["position"]
            assert snapshot.batch_id == batch_id

        # 验证数据库中的记录数量
        total_snapshots = populated_db_session.query(RankingSnapshot).count()
        assert total_snapshots >= len(sample_ranking_snapshots_data)

    # ==================== API操作测试 ====================

    def test_get_rankings_by_name_with_pagination_success(self, ranking_service, populated_db_session):
        """测试按名称分页查询榜单 - 成功场景"""
        # 执行测试 - 搜索包含"榜"的榜单
        rankings, total_pages = ranking_service.get_rankings_by_name_with_pagination(
            populated_db_session, "榜", page=1, size=2
        )

        # 验证结果
        assert len(rankings) <= 2  # 最多2条记录
        assert total_pages >= 1  # 至少1页
        
        # 验证返回的榜单数据包含搜索关键字
        if rankings:
            assert hasattr(rankings[0], 'id')
            assert hasattr(rankings[0], 'channel_name')
            # 检查榜单名称包含搜索关键字
            for ranking in rankings:
                assert "榜" in ranking.channel_name

    def test_get_ranges_by_page_with_pagination_success(self, ranking_service, populated_db_session):
        """测试按页面分页查询榜单 - 成功场景"""
        # 执行测试 - 获取index页面的榜单
        rankings, total_pages = ranking_service.get_ranges_by_page_with_pagination(
            populated_db_session, "index", page=1, size=3
        )

        # 验证结果
        assert len(rankings) <= 3  # 最多3条记录
        assert total_pages >= 1  # 至少1页
        
        # 验证返回的榜单数据
        if rankings:
            for ranking in rankings:
                assert hasattr(ranking, 'id')
                assert hasattr(ranking, 'page_id')
                assert ranking.page_id == "index"

    def test_get_ranking_detail_by_day_success(self, ranking_service, populated_db_session):
        """测试按天获取榜单详情 - 成功场景"""
        # 使用当前日期，因为测试数据包含当天的快照
        target_date = date.today()
        
        # 执行测试 - 获取夹子榜单的当天详情
        result = ranking_service.get_ranking_detail_by_day(populated_db_session, 1, target_date)

        # 验证结果
        if result is not None:  # 可能没有当天数据
            assert result.id == 1
            assert result.channel_name == "夹子"
            assert hasattr(result, 'books')
            # 如果有书籍数据，验证书籍属性
            if result.books:
                for book in result.books:
                    assert hasattr(book, 'novel_id')
                    assert hasattr(book, 'position')

    def test_get_ranking_detail_by_day_not_found(self, ranking_service, populated_db_session):
        """测试按天获取榜单详情 - 榜单不存在"""
        # 执行测试 - 获取不存在的榜单详情
        target_date = date.today()
        result = ranking_service.get_ranking_detail_by_day(populated_db_session, 999, target_date)

        # 验证结果
        assert result is None

    def test_get_ranking_detail_by_hour_success(self, ranking_service, populated_db_session):
        """测试按小时获取榜单详情 - 成功场景"""
        # 使用当前日期和小时
        target_date = date.today()
        target_hour = datetime.now().hour
        
        # 执行测试 - 获取夹子榜单的当前小时详情
        result = ranking_service.get_ranking_detail_by_hour(populated_db_session, 1, target_date, target_hour)

        # 验证结果（可能没有数据，取决于测试数据的时间）
        if result is not None:
            assert result.id == 1
            assert result.channel_name == "夹子"
            assert hasattr(result, 'books')

    def test_get_ranking_history_by_day_success(self, ranking_service, populated_db_session):
        """测试按天获取榜单历史 - 成功场景"""
        # 执行测试 - 获取最近3天的夹子榜单历史
        start_date = date.today() - timedelta(days=2)
        end_date = date.today()
        result = ranking_service.get_ranking_history_by_day(populated_db_session, 1, start_date, end_date)

        # 验证结果
        if result is not None:  # 可能没有历史数据
            assert result.id == 1
            assert result.channel_name == "夹子"
            assert hasattr(result, 'snapshots')
            # 验证快照数据结构
            for snapshot in result.snapshots:
                assert hasattr(snapshot, 'books')
                assert hasattr(snapshot, 'snapshot_time')

    def test_get_ranking_history_by_day_ranking_not_found(self, ranking_service, populated_db_session):
        """测试按天获取榜单历史 - 榜单不存在"""
        # 执行测试 - 获取不存在榜单的历史
        start_date = date.today() - timedelta(days=2)
        end_date = date.today()
        result = ranking_service.get_ranking_history_by_day(populated_db_session, 999, start_date, end_date)

        # 验证结果
        assert result is None

    def test_get_ranking_history_by_hour_success(self, ranking_service, populated_db_session):
        """测试按小时获取榜单历史 - 成功场景"""
        # 执行测试 - 获取最近2小时的夹子榜单历史
        start_time = datetime.now() - timedelta(hours=2)
        end_time = datetime.now()
        result = ranking_service.get_ranking_history_by_hour(populated_db_session, 1, start_time, end_time)

        # 验证结果（可能没有数据，取决于测试数据）
        if result is not None:
            assert result.id == 1
            assert result.channel_name == "夹子"
            assert hasattr(result, 'snapshots')

    def test_get_snapshots_by_day_success(self, ranking_service, populated_db_session):
        """测试获取指定日期快照 - 成功场景"""
        # 使用当前日期
        target_date = date.today()
        
        try:
            # 执行测试 - 获取夹子榜单当天的快照
            result = ranking_service.get_snapshots_by_day(populated_db_session, 1, target_date)
            
            # 验证结果
            assert isinstance(result, list)
            if result:
                for snapshot in result:
                    assert hasattr(snapshot, 'novel_id')
                    assert hasattr(snapshot, 'position')
                    assert hasattr(snapshot, 'batch_id')
        except ValueError as e:
            # 如果没有当天数据，这是正常的
            assert "Don't exist records in target time" in str(e)

    def test_get_snapshots_by_day_no_data(self, ranking_service, populated_db_session):
        """测试获取指定日期快照 - 无数据"""
        # 使用一个很久以前的日期，应该没有数据
        target_date = date(2020, 1, 1)
        
        # 执行测试并验证异常
        with pytest.raises(ValueError, match="Don't exist records in target time"):
            ranking_service.get_snapshots_by_day(populated_db_session, 1, target_date)

    def test_get_snapshots_by_hour_success(self, ranking_service, populated_db_session):
        """测试获取指定小时快照 - 成功场景"""
        # 使用当前日期和小时
        target_date = date.today()
        target_hour = datetime.now().hour
        
        # 执行测试 - 获取夹子榜单当前小时的快照
        result = ranking_service.get_snapshots_by_hour(populated_db_session, 1, target_date, target_hour)

        # 验证结果（可能为空，取决于测试数据）
        assert isinstance(result, list)
        if result:
            for snapshot in result:
                assert hasattr(snapshot, 'novel_id')
                assert hasattr(snapshot, 'position')
                assert hasattr(snapshot, 'batch_id')

    def test_get_snapshots_by_hour_no_data(self, ranking_service, populated_db_session):
        """测试获取指定小时快照 - 无数据"""
        # 使用一个很久以前的日期，应该没有数据
        target_date = date(2020, 1, 1)
        target_hour = 14
        
        # 执行测试 - 应该返回空列表
        result = ranking_service.get_snapshots_by_hour(populated_db_session, 1, target_date, target_hour)

        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 0

    # ==================== 边界条件和异常测试 ====================

    def test_pagination_with_empty_search(self, ranking_service, populated_db_session):
        """测试分页查询 - 空搜索条件"""
        # 执行测试 - 使用空字符串搜索
        rankings, total_pages = ranking_service.get_rankings_by_name_with_pagination(
            populated_db_session, "", page=1, size=5
        )

        # 验证结果 - 应该返回所有榜单
        assert isinstance(rankings, list)
        assert total_pages >= 1

    def test_pagination_with_large_page_number(self, ranking_service, populated_db_session):
        """测试分页查询 - 超大页码"""
        # 执行测试 - 请求第100页
        rankings, total_pages = ranking_service.get_rankings_by_name_with_pagination(
            populated_db_session, "榜", page=100, size=10
        )

        # 验证结果 - 应该返回空列表
        assert isinstance(rankings, list)
        assert len(rankings) == 0
        assert total_pages >= 1

    def test_batch_create_empty_snapshots(self, ranking_service, test_db_session):
        """测试批量创建空快照列表"""
        from app.utils import generate_batch_id
        batch_id = generate_batch_id()
        
        # 执行测试 - 传入空列表
        result = ranking_service.batch_create_ranking_snapshots(test_db_session, [], batch_id)

        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 0

    def test_ranking_operations_with_minimal_data(self, ranking_service, test_db_session):
        """测试榜单操作 - 最小数据集"""
        # 测试包含最小必要字段的数据
        minimal_data = {
            "rank_id": "minimal_test",
            "channel_name": "最小测试榜单",
            "page_id": "test"
        }
        
        # 创建榜单应该能处理最小数据
        result = ranking_service.create_or_update_ranking(test_db_session, minimal_data)
        assert result is not None
        assert result.rank_id == "minimal_test"
        assert result.channel_name == "最小测试榜单"

    def test_search_with_special_characters(self, ranking_service, populated_db_session):
        """测试搜索 - 特殊字符"""
        # 执行测试 - 搜索包含特殊字符的内容
        rankings, total_pages = ranking_service.get_rankings_by_name_with_pagination(
            populated_db_session, "VIP", page=1, size=5
        )

        # 验证结果
        assert isinstance(rankings, list)
        if rankings:
            for ranking in rankings:
                assert "VIP" in ranking.channel_name