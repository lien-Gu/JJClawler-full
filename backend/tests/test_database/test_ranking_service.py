"""
榜单服务层测试
"""
import pytest
from datetime import datetime, date, timedelta

from app.database.service.ranking_service import RankingService


class TestRankingService:
    """榜单服务层测试"""
    
    def test_get_ranking_by_id(self, test_db, sample_ranking):
        """测试根据ID获取榜单"""
        ranking_service = RankingService()
        
        result = ranking_service.get_ranking_by_id(test_db, sample_ranking.id)
        assert result is not None
        assert result.id == sample_ranking.id
        assert result.name == sample_ranking.name
        
        # 测试不存在的榜单
        result = ranking_service.get_ranking_by_id(test_db, 99999)
        assert result is None
    
    def test_get_ranking_by_rank_id(self, test_db, sample_ranking):
        """测试根据rank_id获取榜单"""
        ranking_service = RankingService()
        
        result = ranking_service.get_ranking_by_rank_id(test_db, sample_ranking.rank_id)
        assert result is not None
        assert result.rank_id == sample_ranking.rank_id
        
        # 测试不存在的rank_id
        result = ranking_service.get_ranking_by_rank_id(test_db, 99999)
        assert result is None
    
    def test_get_rankings_by_page_id(self, test_db, sample_rankings):
        """测试根据页面ID获取榜单列表"""
        ranking_service = RankingService()
        
        results = ranking_service.get_rankings_by_page_id(test_db, "test_page_1")
        assert len(results) == 1
        assert results[0].page_id == "test_page_1"
        
        # 测试不存在的页面ID
        results = ranking_service.get_rankings_by_page_id(test_db, "nonexistent")
        assert len(results) == 0
    
    def test_get_rankings_by_group_type(self, test_db, sample_rankings):
        """测试根据分组类型获取榜单"""
        ranking_service = RankingService()
        
        # 获取romance类型的榜单
        results = ranking_service.get_rankings_by_group_type(test_db, "romance")
        romance_count = len([r for r in sample_rankings if r.rank_group_type == "romance"])
        assert len(results) == romance_count
        
        # 验证结果类型正确
        for ranking in results:
            assert ranking.rank_group_type == "romance"
    
    def test_get_all_rankings(self, test_db, sample_rankings):
        """测试分页获取所有榜单"""
        ranking_service = RankingService()
        
        # 获取第一页
        result = ranking_service.get_all_rankings(test_db, page=1, size=2)
        assert len(result["rankings"]) == 2
        assert result["total"] == 3  # sample_rankings有3个榜单
        assert result["page"] == 1
        assert result["size"] == 2
        assert result["total_pages"] == 2
        
        # 获取第二页
        result = ranking_service.get_all_rankings(test_db, page=2, size=2)
        assert len(result["rankings"]) == 1  # 剩余1个
    
    def test_get_ranking_detail(self, test_db, sample_complete_data):
        """测试获取榜单详情"""
        ranking_service = RankingService()
        ranking = sample_complete_data["rankings"][0]
        
        detail = ranking_service.get_ranking_detail(test_db, ranking.id, limit=50)
        assert detail is not None
        assert detail["ranking"].id == ranking.id
        assert "books" in detail
        assert "snapshot_time" in detail
        assert "total_books" in detail
        assert "statistics" in detail
        
        # 测试不存在的榜单
        detail = ranking_service.get_ranking_detail(test_db, 99999)
        assert detail is None
    
    def test_get_ranking_history(self, test_db, sample_complete_data):
        """测试获取榜单历史趋势"""
        ranking_service = RankingService()
        ranking = sample_complete_data["rankings"][0]
        
        history = ranking_service.get_ranking_history(test_db, ranking.id)
        assert "ranking_id" in history
        assert "trend_data" in history
        assert history["ranking_id"] == ranking.id
        
        # 测试指定日期范围
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        history = ranking_service.get_ranking_history(
            test_db, ranking.id, start_date=start_date, end_date=end_date
        )
        assert history["start_date"] == start_date
        assert history["end_date"] == end_date
    
    def test_get_book_ranking_history(self, test_db, sample_complete_data):
        """测试获取书籍排名历史"""
        ranking_service = RankingService()
        book = sample_complete_data["books"][0]
        
        history = ranking_service.get_book_ranking_history(test_db, book.id, days=30)
        assert isinstance(history, list)
        
        # 如果有历史数据，验证格式
        if history:
            for item in history:
                assert "ranking_id" in item
                assert "ranking_name" in item
                assert "position" in item
                assert "snapshot_time" in item
    
    def test_create_or_update_ranking(self, test_db):
        """测试创建或更新榜单"""
        ranking_service = RankingService()
        
        # 创建新榜单
        ranking_data = {
            "rank_id": 999,
            "name": "新榜单",
            "page_id": "new_page"
        }
        ranking = ranking_service.create_or_update_ranking(test_db, ranking_data)
        assert ranking.rank_id == 999
        assert ranking.name == "新榜单"
        
        # 更新现有榜单
        update_data = {
            "rank_id": 999,
            "name": "更新后的榜单",
            "page_id": "new_page"
        }
        updated_ranking = ranking_service.create_or_update_ranking(test_db, update_data)
        assert updated_ranking.id == ranking.id
        assert updated_ranking.name == "更新后的榜单"
    
    def test_compare_rankings(self, test_db, sample_complete_data):
        """测试对比多个榜单"""
        ranking_service = RankingService()
        
        ranking_ids = [r.id for r in sample_complete_data["rankings"][:2]]
        
        # 正常对比
        comparison = ranking_service.compare_rankings(test_db, ranking_ids)
        
        assert "rankings" in comparison
        assert "comparison_date" in comparison
        assert "ranking_data" in comparison
        assert "common_books" in comparison
        assert "stats" in comparison
        
        assert len(comparison["rankings"]) == 2
        
        # 测试错误情况：榜单数量不足
        with pytest.raises(ValueError, match="至少需要2个榜单进行对比"):
            ranking_service.compare_rankings(test_db, [ranking_ids[0]])
    
    def test_get_ranking_statistics(self, test_db, sample_complete_data):
        """测试获取榜单统计信息"""
        ranking_service = RankingService()
        ranking = sample_complete_data["rankings"][0]
        
        stats = ranking_service.get_ranking_statistics(test_db, ranking.id)
        
        assert "total_snapshots" in stats
        assert "unique_books" in stats
        assert "first_snapshot_time" in stats
        assert "last_snapshot_time" in stats
        
        # 验证统计数据合理性
        assert stats["total_snapshots"] >= 0
        assert stats["unique_books"] >= 0