"""
测试 RankingService
"""
import pytest
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session

from app.database.service.ranking_service import RankingService
from app.database.db.ranking import Ranking, RankingSnapshot


class TestRankingService:
    """测试 RankingService"""
    
    def test_get_ranking_by_id(self, test_db: Session, sample_ranking: Ranking):
        """测试根据ID获取榜单"""
        service = RankingService()
        result = service.get_ranking_by_id(test_db, sample_ranking.id)
        assert result is not None
        assert result.id == sample_ranking.id
        assert result.name == sample_ranking.name
    
    def test_get_ranking_by_rank_id(self, test_db: Session, sample_ranking: Ranking):
        """测试根据rank_id获取榜单"""
        service = RankingService()
        result = service.get_ranking_by_rank_id(test_db, sample_ranking.rank_id)
        assert result is not None
        assert result.rank_id == sample_ranking.rank_id
        assert result.name == sample_ranking.name
    
    def test_get_rankings_by_page_id(self, test_db: Session, sample_rankings: list[Ranking]):
        """测试根据页面ID获取榜单列表"""
        service = RankingService()
        page_id = sample_rankings[0].page_id
        results = service.get_rankings_by_page_id(test_db, page_id)
        assert len(results) > 0
        assert all(ranking.page_id == page_id for ranking in results)
    
    def test_get_rankings_by_group_type(self, test_db: Session, sample_rankings: list[Ranking]):
        """测试根据分组类型获取榜单"""
        service = RankingService()
        results = service.get_rankings_by_group_type(test_db, "romance")
        assert len(results) > 0
        assert all(ranking.rank_group_type == "romance" for ranking in results)
    
    def test_get_all_rankings(self, test_db: Session, sample_rankings: list[Ranking]):
        """测试分页获取所有榜单"""
        service = RankingService()
        result = service.get_all_rankings(test_db, page=1, size=2)
        
        assert "rankings" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert "total_pages" in result
        assert len(result["rankings"]) <= 2
        assert result["page"] == 1
        assert result["size"] == 2
    
    def test_get_ranking_detail(self, test_db: Session, sample_ranking: Ranking, sample_ranking_snapshots: list[RankingSnapshot]):
        """测试获取榜单详情"""
        service = RankingService()
        result = service.get_ranking_detail(test_db, sample_ranking.id)
        
        assert result is not None
        assert "ranking" in result
        assert "books" in result
        assert "snapshot_time" in result
        assert "total_books" in result
        assert "statistics" in result
        assert result["ranking"].id == sample_ranking.id
    
    def test_get_ranking_detail_with_date(self, test_db: Session, sample_ranking: Ranking):
        """测试获取指定日期的榜单详情"""
        service = RankingService()
        target_date = date.today()
        result = service.get_ranking_detail(test_db, sample_ranking.id, target_date)
        
        assert result is not None
        assert "ranking" in result
        assert "books" in result
    
    def test_get_ranking_history(self, test_db: Session, sample_ranking: Ranking):
        """测试获取榜单历史趋势"""
        service = RankingService()
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        result = service.get_ranking_history(test_db, sample_ranking.id, start_date, end_date)
        
        assert isinstance(result, dict)
        assert "ranking_id" in result
        assert "start_date" in result
        assert "end_date" in result
        assert "trend_data" in result
        assert result["ranking_id"] == sample_ranking.id
    
    def test_get_book_ranking_history(self, test_db: Session, sample_books: list, sample_ranking_snapshots: list[RankingSnapshot]):
        """测试获取书籍在榜单中的排名历史"""
        service = RankingService()
        book_id = sample_books[0].id
        
        results = service.get_book_ranking_history(test_db, book_id)
        
        assert isinstance(results, list)
        if results:
            assert all("ranking_id" in item for item in results)
            assert all("ranking_name" in item for item in results)
            assert all("position" in item for item in results)
    
    def test_create_or_update_ranking(self, test_db: Session):
        """测试创建或更新榜单"""
        service = RankingService()
        
        ranking_data = {
            "rank_id": 77777,
            "name": "服务测试榜单",
            "page_id": "service_test_page",
            "rank_group_type": "fantasy"
        }
        
        ranking = service.create_or_update_ranking(test_db, ranking_data)
        assert ranking.rank_id == 77777
        assert ranking.name == "服务测试榜单"
        
        # 测试更新
        update_data = {
            "rank_id": 77777,
            "name": "更新的服务测试榜单",
            "page_id": "service_test_page",
            "rank_group_type": "fantasy"
        }
        
        updated_ranking = service.create_or_update_ranking(test_db, update_data)
        assert updated_ranking.id == ranking.id
        assert updated_ranking.name == "更新的服务测试榜单"
    
    def test_create_ranking_snapshot(self, test_db: Session, sample_ranking: Ranking, sample_books: list):
        """测试创建榜单快照"""
        service = RankingService()
        
        snapshot_data = {
            "ranking_id": sample_ranking.id,
            "book_id": sample_books[0].id,
            "position": 1,
            "score": 95.5,
            "snapshot_time": datetime.now()
        }
        
        snapshot = service.create_ranking_snapshot(test_db, snapshot_data)
        assert snapshot.ranking_id == sample_ranking.id
        assert snapshot.book_id == sample_books[0].id
        assert snapshot.position == 1
    
    def test_batch_create_ranking_snapshots(self, test_db: Session, sample_ranking: Ranking, sample_books: list):
        """测试批量创建榜单快照"""
        service = RankingService()
        
        snapshots_data = [
            {
                "ranking_id": sample_ranking.id,
                "book_id": sample_books[i].id,
                "position": i + 1,
                "score": 100.0 - i * 5,
                "snapshot_time": datetime.now()
            }
            for i in range(min(3, len(sample_books)))
        ]
        
        snapshots = service.batch_create_ranking_snapshots(test_db, snapshots_data)
        assert len(snapshots) == len(snapshots_data)
        assert all(snapshot.ranking_id == sample_ranking.id for snapshot in snapshots)
    
    def test_compare_rankings(self, test_db: Session, sample_rankings: list[Ranking], sample_complete_data: dict):
        """测试对比多个榜单"""
        service = RankingService()
        ranking_ids = [ranking.id for ranking in sample_rankings[:2]]
        
        result = service.compare_rankings(test_db, ranking_ids)
        
        assert isinstance(result, dict)
        assert "rankings" in result
        assert "comparison_date" in result
        assert "ranking_data" in result
        assert "common_books" in result
        assert "stats" in result
        assert len(result["rankings"]) == 2
    
    def test_compare_rankings_with_date(self, test_db: Session, sample_rankings: list[Ranking]):
        """测试对比指定日期的多个榜单"""
        service = RankingService()
        ranking_ids = [ranking.id for ranking in sample_rankings[:2]]
        target_date = date.today()
        
        result = service.compare_rankings(test_db, ranking_ids, target_date)
        
        assert isinstance(result, dict)
        assert result["comparison_date"] == target_date
    
    def test_cleanup_old_ranking_snapshots(self, test_db: Session, sample_ranking: Ranking, sample_ranking_snapshots: list[RankingSnapshot]):
        """测试清理旧的榜单快照"""
        service = RankingService()
        
        deleted_count = service.cleanup_old_ranking_snapshots(test_db, sample_ranking.id, keep_days=1)
        assert deleted_count >= 0
    
    def test_get_ranking_statistics(self, test_db: Session, sample_ranking: Ranking, sample_ranking_snapshots: list[RankingSnapshot]):
        """测试获取榜单统计信息"""
        service = RankingService()
        
        stats = service.get_ranking_statistics(test_db, sample_ranking.id)
        assert isinstance(stats, dict)
    
    def test_get_ranking_by_id_not_found(self, test_db: Session):
        """测试获取不存在的榜单"""
        service = RankingService()
        result = service.get_ranking_by_id(test_db, 99999)
        assert result is None
    
    def test_get_ranking_detail_not_found(self, test_db: Session):
        """测试获取不存在榜单的详情"""
        service = RankingService()
        result = service.get_ranking_detail(test_db, 99999)
        assert result is None
    
    def test_compare_rankings_insufficient_rankings(self, test_db: Session, sample_ranking: Ranking):
        """测试对比榜单时榜单数量不足"""
        service = RankingService()
        
        with pytest.raises(ValueError, match="至少需要2个榜单进行对比"):
            service.compare_rankings(test_db, [sample_ranking.id])
    
    def test_compare_rankings_nonexistent_ranking(self, test_db: Session, sample_ranking: Ranking):
        """测试对比不存在的榜单"""
        service = RankingService()
        
        with pytest.raises(ValueError, match="部分榜单不存在"):
            service.compare_rankings(test_db, [sample_ranking.id, 99999])