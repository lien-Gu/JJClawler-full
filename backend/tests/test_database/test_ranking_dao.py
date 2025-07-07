"""
测试 RankingDAO 和 RankingSnapshotDAO
"""
import pytest
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session

from app.database.dao.ranking_dao import RankingDAO, RankingSnapshotDAO
from app.database.db.ranking import Ranking, RankingSnapshot


class TestRankingDAO:
    """测试 RankingDAO"""
    
    def test_get_by_rank_id(self, test_db: Session, sample_ranking: Ranking):
        """测试根据rank_id获取榜单"""
        ranking_dao = RankingDAO()
        result = ranking_dao.get_by_rank_id(test_db, sample_ranking.rank_id)
        assert result is not None
        assert result.rank_id == sample_ranking.rank_id
        assert result.rank_name == sample_ranking.rank_name
    
    def test_get_by_page_id(self, test_db: Session, sample_rankings: list[Ranking]):
        """测试根据page_id获取榜单列表"""
        ranking_dao = RankingDAO()
        page_id = sample_rankings[0].page_id
        results = ranking_dao.get_by_page_id(test_db, page_id)
        assert len(results) > 0
        assert all(ranking.page_id == page_id for ranking in results)
    
    def test_get_by_group_type(self, test_db: Session, sample_rankings: list[Ranking]):
        """测试根据榜单分组类型获取榜单"""
        ranking_dao = RankingDAO()
        results = ranking_dao.get_by_group_type(test_db, "romance")
        assert len(results) > 0
        assert all(ranking.rank_group_type == "romance" for ranking in results)
    
    def test_create_or_update_by_rank_id(self, test_db: Session):
        """测试根据rank_id创建或更新榜单"""
        ranking_dao = RankingDAO()
        
        # 创建新榜单
        ranking_data = {
            "rank_id": 99999,
            "rank_name": "新榜单",
            "page_id": "new_page",
            "rank_group_type": "fantasy"
        }
        ranking = ranking_dao.create_or_update_by_rank_id(test_db, ranking_data)
        assert ranking.rank_id == 99999
        assert ranking.rank_name == "新榜单"
        
        # 更新现有榜单
        update_data = {
            "rank_id": 99999,
            "rank_name": "更新的榜单",
            "page_id": "new_page",
            "rank_group_type": "fantasy"
        }
        updated_ranking = ranking_dao.create_or_update_by_rank_id(test_db, update_data)
        assert updated_ranking.id == ranking.id
        assert updated_ranking.rank_name == "更新的榜单"


class TestRankingSnapshotDAO:
    """测试 RankingSnapshotDAO"""
    
    def test_get_latest_by_ranking_id(self, test_db: Session, sample_ranking_snapshots: list[RankingSnapshot]):
        """测试获取榜单最新快照"""
        snapshot_dao = RankingSnapshotDAO()
        ranking_id = sample_ranking_snapshots[0].ranking_id
        
        results = snapshot_dao.get_latest_by_ranking_id(test_db, ranking_id)
        assert len(results) > 0
        assert all(snapshot.ranking_id == ranking_id for snapshot in results)
        # 验证按位置排序
        positions = [snapshot.position for snapshot in results]
        assert positions == sorted(positions)
    
    def test_get_by_ranking_and_date(self, test_db: Session, sample_ranking_snapshots: list[RankingSnapshot]):
        """测试获取指定日期的榜单快照"""
        snapshot_dao = RankingSnapshotDAO()
        ranking_id = sample_ranking_snapshots[0].ranking_id
        target_date = date.today()
        
        results = snapshot_dao.get_by_ranking_and_date(test_db, ranking_id, target_date)
        # 即使没有数据，也应该返回空列表
        assert isinstance(results, list)
    
    def test_get_book_ranking_history(self, test_db: Session, sample_ranking_snapshots: list[RankingSnapshot]):
        """测试获取书籍排名历史"""
        snapshot_dao = RankingSnapshotDAO()
        book_id = sample_ranking_snapshots[0].book_id
        ranking_id = sample_ranking_snapshots[0].ranking_id
        
        results = snapshot_dao.get_book_ranking_history(test_db, book_id, ranking_id)
        assert isinstance(results, list)
        if results:
            assert all(snapshot.book_id == book_id for snapshot in results)
    
    def test_get_ranking_statistics(self, test_db: Session, sample_ranking_snapshots: list[RankingSnapshot]):
        """测试获取榜单统计信息"""
        snapshot_dao = RankingSnapshotDAO()
        ranking_id = sample_ranking_snapshots[0].ranking_id
        
        stats = snapshot_dao.get_ranking_statistics(test_db, ranking_id)
        assert isinstance(stats, dict)
        if stats:
            assert "total_snapshots" in stats
            assert "unique_books" in stats
    
    def test_get_ranking_trend(self, test_db: Session, sample_ranking_snapshots: list[RankingSnapshot]):
        """测试获取榜单变化趋势"""
        snapshot_dao = RankingSnapshotDAO()
        ranking_id = sample_ranking_snapshots[0].ranking_id
        
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        
        results = snapshot_dao.get_ranking_trend(test_db, ranking_id, start_time, end_time)
        assert isinstance(results, list)
        if results:
            assert all(len(item) == 2 for item in results)  # (datetime, int) 元组
    
    def test_bulk_create(self, test_db: Session, sample_ranking: Ranking, sample_books: list):
        """测试批量创建快照"""
        snapshot_dao = RankingSnapshotDAO()
        
        snapshots_data = [
            {
                "ranking_id": sample_ranking.id,
                "book_id": sample_books[i].id,
                "position": i + 1,
                "score": 100.0 - i * 10,
                "snapshot_time": datetime.now()
            }
            for i in range(min(3, len(sample_books)))
        ]
        
        results = snapshot_dao.bulk_create(test_db, snapshots_data)
        assert len(results) == len(snapshots_data)
        assert all(snapshot.ranking_id == sample_ranking.id for snapshot in results)
    
    def test_delete_old_snapshots(self, test_db: Session, sample_ranking_snapshots: list[RankingSnapshot]):
        """测试删除旧快照"""
        snapshot_dao = RankingSnapshotDAO()
        ranking_id = sample_ranking_snapshots[0].ranking_id
        
        before_time = datetime.now() - timedelta(days=3)
        deleted_count = snapshot_dao.delete_old_snapshots(test_db, ranking_id, before_time, keep_days=2)
        assert deleted_count >= 0
    
    def test_get_books_comparison(self, test_db: Session, sample_rankings: list[Ranking]):
        """测试获取多个榜单的书籍对比数据"""
        snapshot_dao = RankingSnapshotDAO()
        ranking_ids = [ranking.id for ranking in sample_rankings[:2]]
        
        # 测试最新数据对比
        results = snapshot_dao.get_books_comparison(test_db, ranking_ids)
        assert isinstance(results, dict)
        assert all(ranking_id in results for ranking_id in ranking_ids)
        
        # 测试指定日期对比
        target_date = date.today()
        results_by_date = snapshot_dao.get_books_comparison(test_db, ranking_ids, target_date)
        assert isinstance(results_by_date, dict)
        assert all(ranking_id in results_by_date for ranking_id in ranking_ids)