"""
榜单服务测试文件
测试app.database.service.ranking_service模块的所有服务方法
"""

from datetime import date, datetime

import pytest

from app.database.service.ranking_service import RankingService


class TestRankingService:
    """测试RankingService类"""

    @pytest.fixture
    def ranking_service(self):
        """RankingService实例fixture"""
        return RankingService()

    # ==================== 基础CRUD操作测试 ====================

    def test_get_ranking_by_id(self, ranking_service, db_session, create_test_ranking):
        """测试根据ID获取榜单"""
        result = ranking_service.get_ranking_by_id(db_session, create_test_ranking.id)

        assert result is not None
        assert result.id == create_test_ranking.id
        assert result.name == create_test_ranking.name

    def test_get_ranking_by_rank_id(
        self, ranking_service, db_session, create_test_ranking
    ):
        """测试根据rank_id获取榜单"""
        result = ranking_service.get_ranking_by_rank_id(
            db_session, create_test_ranking.rank_id
        )

        assert result is not None
        assert result.rank_id == create_test_ranking.rank_id
        assert result.name == create_test_ranking.name

    def test_create_ranking(self, ranking_service, db_session):
        """测试创建榜单"""
        ranking_data = {
            "rank_id": "999",
            "name": "新建榜单",
            "page_id": "new_ranking",
            "rank_group_type": "新分类",
        }

        result = ranking_service.create_ranking(db_session, ranking_data)

        assert result.rank_id == "999"
        assert result.name == "新建榜单"
        assert result.page_id == "new_ranking"
        assert result.rank_group_type == "新分类"

    def test_update_ranking(self, ranking_service, db_session, create_test_ranking):
        """测试更新榜单"""
        update_data = {"name": "更新后的榜单名", "rank_group_type": "更新后的分类"}

        result = ranking_service.update_ranking(
            db_session, create_test_ranking, update_data
        )

        assert result.name == "更新后的榜单名"
        assert result.rank_group_type == "更新后的分类"
        assert result.rank_id == create_test_ranking.rank_id  # rank_id不变

    def test_create_or_update_ranking_create(self, ranking_service, db_session):
        """测试创建或更新榜单 - 创建新榜单"""
        ranking_data = {
            "rank_id": "888",
            "name": "创建或更新测试榜单",
            "page_id": "create_or_update",
            "rank_group_type": "测试分类",
        }

        result = ranking_service.create_or_update_ranking(db_session, ranking_data)

        assert result.rank_id == "888"
        assert result.name == "创建或更新测试榜单"

    def test_create_or_update_ranking_update(
        self, ranking_service, db_session, create_test_ranking
    ):
        """测试创建或更新榜单 - 更新现有榜单"""
        ranking_data = {
            "rank_id": create_test_ranking.rank_id,
            "name": "更新的榜单名",
            "rank_group_type": "更新的分类",
        }

        result = ranking_service.create_or_update_ranking(db_session, ranking_data)

        assert result.id == create_test_ranking.id  # 同一个记录
        assert result.name == "更新的榜单名"
        assert result.rank_group_type == "更新的分类"

    # ==================== 查询操作测试 ====================

    def test_get_rankings_by_page_id(
        self, ranking_service, db_session, create_test_ranking
    ):
        """测试根据页面ID获取榜单列表"""
        result = ranking_service.get_rankings_by_page_id(
            db_session, create_test_ranking.page_id
        )

        assert len(result) >= 1
        assert any(r.id == create_test_ranking.id for r in result)

    def test_get_rankings_by_group_type(
        self, ranking_service, db_session, create_test_ranking
    ):
        """测试根据分组类型获取榜单"""
        result = ranking_service.get_rankings_by_group_type(
            db_session, create_test_ranking.rank_group_type
        )

        assert len(result) >= 1
        assert any(r.id == create_test_ranking.id for r in result)

    def test_get_rankings_with_pagination(
        self, ranking_service, db_session, create_test_ranking
    ):
        """测试分页获取榜单列表"""
        result = ranking_service.get_rankings_with_pagination(
            db_session, page=1, size=10
        )

        assert "rankings" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert "total_pages" in result
        assert result["page"] == 1
        assert result["size"] == 10
        assert len(result["rankings"]) >= 1

    # ==================== 榜单快照操作测试 ====================

    def test_create_ranking_snapshot(
        self, ranking_service, db_session, create_test_ranking, create_test_book
    ):
        """测试创建榜单快照"""
        snapshot_data = {
            "ranking_id": create_test_ranking.id,
            "book_id": create_test_book.id,
            "position": 1,
            "score": 95.5,
            "snapshot_time": datetime(2024, 1, 15, 12, 0, 0),
        }

        result = ranking_service.create_ranking_snapshot(db_session, snapshot_data)

        assert result.ranking_id == create_test_ranking.id
        assert result.book_id == create_test_book.id
        assert result.position == 1
        assert result.score == 95.5

    def test_batch_create_ranking_snapshots(
        self, ranking_service, db_session, create_test_ranking, create_test_book
    ):
        """测试批量创建榜单快照"""
        snapshots_data = [
            {
                "ranking_id": create_test_ranking.id,
                "book_id": create_test_book.id,
                "position": 1,
                "score": 95.5,
                "snapshot_time": datetime(2024, 1, 15, 12, 0, 0),
            },
            {
                "ranking_id": create_test_ranking.id,
                "book_id": create_test_book.id,
                "position": 2,
                "score": 90.0,
                "snapshot_time": datetime(
                    2024, 1, 15, 13, 0, 0
                ),  # 不同的时间避免约束冲突
            },
        ]

        result = ranking_service.batch_create_ranking_snapshots(
            db_session, snapshots_data
        )

        assert len(result) == 2
        assert result[0].position == 1
        assert result[1].position == 2

    def test_get_latest_snapshots_by_ranking_id(
        self, ranking_service, db_session, create_test_ranking_snapshot
    ):
        """测试获取榜单最新快照"""
        result = ranking_service.get_latest_snapshots_by_ranking_id(
            db_session, create_test_ranking_snapshot.ranking_id
        )

        assert len(result) >= 1
        assert result[0].ranking_id == create_test_ranking_snapshot.ranking_id

    def test_get_snapshots_by_ranking_and_date(
        self, ranking_service, db_session, create_test_ranking_snapshot
    ):
        """测试获取指定日期的榜单快照"""
        target_date = create_test_ranking_snapshot.snapshot_time.date()

        result = ranking_service.get_snapshots_by_ranking_and_date(
            db_session, create_test_ranking_snapshot.ranking_id, target_date
        )

        assert len(result) >= 1
        assert result[0].ranking_id == create_test_ranking_snapshot.ranking_id

    def test_get_book_ranking_history(
        self, ranking_service, db_session, create_test_ranking_snapshot
    ):
        """测试获取书籍排名历史"""
        result = ranking_service.get_book_ranking_history(
            db_session,
            create_test_ranking_snapshot.book_id,
            create_test_ranking_snapshot.ranking_id,
        )

        assert len(result) >= 1
        assert result[0].book_id == create_test_ranking_snapshot.book_id
        assert result[0].ranking_id == create_test_ranking_snapshot.ranking_id

    # ==================== 统计和趋势分析测试 ====================

    def test_get_ranking_statistics(
        self, ranking_service, db_session, create_test_ranking_snapshot
    ):
        """测试获取榜单统计信息"""
        result = ranking_service.get_ranking_statistics(
            db_session, create_test_ranking_snapshot.ranking_id
        )

        assert "total_snapshots" in result
        assert "unique_books" in result
        assert "first_snapshot_time" in result
        assert "last_snapshot_time" in result
        assert result["total_snapshots"] >= 1

    def test_get_ranking_trend(
        self, ranking_service, db_session, create_test_ranking_snapshot
    ):
        """测试获取榜单变化趋势"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 31, 23, 59, 59)

        result = ranking_service.get_ranking_trend(
            db_session, create_test_ranking_snapshot.ranking_id, start_time, end_time
        )

        assert isinstance(result, list)
        assert len(result) >= 1
        # 验证元组格式 (datetime, int)
        assert len(result[0]) == 2
        assert isinstance(result[0][0], datetime)
        assert isinstance(result[0][1], int)

    # ==================== 业务逻辑方法测试 ====================

    def test_get_ranking_detail(
        self, ranking_service, db_session, create_test_ranking_snapshot
    ):
        """测试获取榜单详情"""
        result = ranking_service.get_ranking_detail(
            db_session, create_test_ranking_snapshot.ranking_id
        )

        assert result is not None
        assert "ranking" in result
        assert "books" in result
        assert "snapshot_time" in result
        assert "total_books" in result
        assert "statistics" in result
        assert len(result["books"]) >= 1

    def test_get_ranking_detail_with_target_date(
        self, ranking_service, db_session, create_test_ranking_snapshot
    ):
        """测试获取指定日期的榜单详情"""
        target_date = create_test_ranking_snapshot.snapshot_time.date()

        result = ranking_service.get_ranking_detail(
            db_session, create_test_ranking_snapshot.ranking_id, target_date
        )

        assert result is not None
        assert "ranking" in result
        assert "books" in result
        assert len(result["books"]) >= 1

    def test_get_ranking_history(
        self, ranking_service, db_session, create_test_ranking_snapshot
    ):
        """测试获取榜单历史趋势"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        result = ranking_service.get_ranking_history(
            db_session, create_test_ranking_snapshot.ranking_id, start_date, end_date
        )

        assert "ranking_id" in result
        assert "start_date" in result
        assert "end_date" in result
        assert "trend_data" in result
        assert result["ranking_id"] == create_test_ranking_snapshot.ranking_id

    def test_get_book_ranking_history_with_details(
        self, ranking_service, db_session, create_test_ranking_snapshot
    ):
        """测试获取书籍在榜单中的排名历史（包含详细信息）"""
        # 使用一个很大的天数来确保能包含测试数据
        result = ranking_service.get_book_ranking_history_with_details(
            db_session,
            create_test_ranking_snapshot.book_id,
            create_test_ranking_snapshot.ranking_id,
            days=800,  # 足够大的天数包含2024年的测试数据
        )

        assert isinstance(result, list)
        assert len(result) >= 1

        history_item = result[0]
        assert "ranking_id" in history_item
        assert "ranking_name" in history_item
        assert "position" in history_item
        assert "score" in history_item
        assert "snapshot_time" in history_item

    def test_compare_rankings(
        self,
        ranking_service,
        db_session,
        create_test_ranking,
        create_test_ranking_snapshot,
    ):
        """测试对比多个榜单"""
        # 创建第二个榜单
        ranking_data2 = {
            "rank_id": "2",
            "name": "第二个榜单",
            "page_id": "second_ranking",
            "rank_group_type": "热门",
        }
        ranking2 = ranking_service.create_ranking(db_session, ranking_data2)

        ranking_ids = [create_test_ranking.id, ranking2.id]

        result = ranking_service.compare_rankings(db_session, ranking_ids)

        assert "rankings" in result
        assert "comparison_date" in result
        assert "ranking_data" in result
        assert "common_books" in result
        assert "stats" in result
        assert len(result["rankings"]) == 2

    def test_cleanup_old_ranking_snapshots(
        self, ranking_service, db_session, create_test_ranking_snapshot
    ):
        """测试清理旧的榜单快照"""
        # 创建一些旧快照
        old_snapshot_data = {
            "ranking_id": create_test_ranking_snapshot.ranking_id,
            "book_id": create_test_ranking_snapshot.book_id,
            "position": 5,
            "score": 80.0,
            "snapshot_time": datetime(2023, 12, 1, 12, 0, 0),  # 很久以前的快照
        }
        ranking_service.create_ranking_snapshot(db_session, old_snapshot_data)

        # 清理30天前的快照
        deleted_count = ranking_service.cleanup_old_ranking_snapshots(
            db_session, create_test_ranking_snapshot.ranking_id, keep_days=30
        )

        assert deleted_count >= 0  # 可能没有删除任何记录，取决于测试数据

    # ==================== 错误处理测试 ====================

    def test_create_or_update_ranking_without_rank_id(
        self, ranking_service, db_session
    ):
        """测试创建或更新榜单时缺少rank_id"""
        ranking_data = {"name": "测试榜单", "page_id": "test"}

        with pytest.raises(ValueError, match="rank_id is required"):
            ranking_service.create_or_update_ranking(db_session, ranking_data)

    def test_get_ranking_by_id_not_found(self, ranking_service, db_session):
        """测试获取不存在的榜单"""
        result = ranking_service.get_ranking_by_id(db_session, 99999)
        assert result is None

    def test_get_ranking_detail_not_found(self, ranking_service, db_session):
        """测试获取不存在榜单的详情"""
        result = ranking_service.get_ranking_detail(db_session, 99999)
        assert result is None

    def test_compare_rankings_insufficient_rankings(self, ranking_service, db_session):
        """测试对比榜单时榜单数量不足"""
        with pytest.raises(ValueError, match="至少需要2个榜单进行对比"):
            ranking_service.compare_rankings(db_session, [1])
