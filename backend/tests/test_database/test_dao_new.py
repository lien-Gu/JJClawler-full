"""
DAO层测试
"""
import pytest
from datetime import datetime, timedelta

from app.database.dao.book_dao import BookDAO, BookSnapshotDAO
from app.database.dao.ranking_dao import RankingDAO, RankingSnapshotDAO


class TestBookDAO:
    """书籍DAO测试"""
    
    def test_get_by_novel_id(self, test_db, sample_book):
        """测试根据novel_id获取书籍"""
        book_dao = BookDAO()
        
        # 获取存在的书籍
        result = book_dao.get_by_novel_id(test_db, sample_book.novel_id)
        assert result is not None
        assert result.id == sample_book.id
        
        # 获取不存在的书籍
        result = book_dao.get_by_novel_id(test_db, 99999)
        assert result is None
    
    def test_search_by_title(self, test_db, sample_books):
        """测试按标题搜索"""
        book_dao = BookDAO()
        
        # 搜索存在的标题
        results = book_dao.search_by_title(test_db, "测试小说", limit=10)
        assert len(results) == 5  # sample_books有5本书
        
        # 搜索特定标题
        results = book_dao.search_by_title(test_db, "测试小说1", limit=10)
        assert len(results) == 1
        assert results[0].title == "测试小说1"
        
        # 搜索不存在的标题
        results = book_dao.search_by_title(test_db, "不存在的书", limit=10)
        assert len(results) == 0
    
    def test_search_by_author(self, test_db, sample_books):
        """测试按作者搜索"""
        book_dao = BookDAO()
        
        # 搜索存在的作者
        results = book_dao.search_by_author(test_db, "作者", limit=10)
        assert len(results) == 5
        
        # 搜索特定作者
        results = book_dao.search_by_author(test_db, "作者1", limit=10)
        assert len(results) == 1
        assert results[0].author == "作者1"
    
    def test_create_or_update_by_novel_id(self, test_db):
        """测试创建或更新书籍"""
        book_dao = BookDAO()
        
        # 创建新书籍
        book_data = {
            "novel_id": 12345,
            "title": "新书籍",
            "author": "新作者"
        }
        book = book_dao.create_or_update_by_novel_id(test_db, book_data)
        assert book.novel_id == 12345
        assert book.title == "新书籍"
        
        # 更新现有书籍
        update_data = {
            "novel_id": 12345,
            "title": "更新后的书籍",
            "author": "新作者"
        }
        updated_book = book_dao.create_or_update_by_novel_id(test_db, update_data)
        assert updated_book.id == book.id  # 同一本书
        assert updated_book.title == "更新后的书籍"


class TestBookSnapshotDAO:
    """书籍快照DAO测试"""
    
    def test_get_latest_by_book_id(self, test_db, sample_book_snapshots):
        """测试获取最新快照"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        latest = snapshot_dao.get_latest_by_book_id(test_db, book_id)
        assert latest is not None
        assert latest.book_id == book_id
        
        # 验证是最新的（最后一个快照）
        all_snapshots = sorted(sample_book_snapshots, key=lambda x: x.snapshot_time)
        assert latest.id == all_snapshots[-1].id
    
    def test_get_trend_by_book_id(self, test_db, sample_book_snapshots):
        """测试获取趋势数据"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        # 获取所有趋势数据
        trend = snapshot_dao.get_trend_by_book_id(test_db, book_id, limit=10)
        assert len(trend) == 7  # sample_book_snapshots有7个快照
        
        # 验证按时间降序排列
        assert trend[0].snapshot_time >= trend[1].snapshot_time
    
    def test_get_statistics_by_book_id(self, test_db, sample_book_snapshots):
        """测试获取统计信息"""
        snapshot_dao = BookSnapshotDAO()
        book_id = sample_book_snapshots[0].book_id
        
        stats = snapshot_dao.get_statistics_by_book_id(test_db, book_id)
        
        assert stats["total_snapshots"] == 7
        assert stats["max_favorites"] == 1060  # 1000 + 6*10
        assert stats["max_clicks"] == 5300    # 5000 + 6*50
        assert stats["first_snapshot_time"] is not None
        assert stats["last_snapshot_time"] is not None
    
    def test_bulk_create(self, test_db, sample_book):
        """测试批量创建快照"""
        snapshot_dao = BookSnapshotDAO()
        
        snapshots_data = []
        for i in range(3):
            snapshots_data.append({
                "book_id": sample_book.id,
                "favorites": 100 + i,
                "clicks": 500 + i,
                "snapshot_time": datetime.now() + timedelta(hours=i)
            })
        
        created_snapshots = snapshot_dao.bulk_create(test_db, snapshots_data)
        assert len(created_snapshots) == 3
        
        # 验证数据正确
        for i, snapshot in enumerate(created_snapshots):
            assert snapshot.book_id == sample_book.id
            assert snapshot.favorites == 100 + i


class TestRankingDAO:
    """榜单DAO测试"""
    
    def test_get_by_rank_id(self, test_db, sample_ranking):
        """测试根据rank_id获取榜单"""
        ranking_dao = RankingDAO()
        
        result = ranking_dao.get_by_rank_id(test_db, sample_ranking.rank_id)
        assert result is not None
        assert result.id == sample_ranking.id
        
        # 获取不存在的榜单
        result = ranking_dao.get_by_rank_id(test_db, 99999)
        assert result is None
    
    def test_get_by_page_id(self, test_db, sample_rankings):
        """测试根据page_id获取榜单"""
        ranking_dao = RankingDAO()
        
        results = ranking_dao.get_by_page_id(test_db, "test_page_1")
        assert len(results) == 1
        assert results[0].page_id == "test_page_1"
    
    def test_get_by_group_type(self, test_db, sample_rankings):
        """测试根据分组类型获取榜单"""
        ranking_dao = RankingDAO()
        
        # 获取romance类型的榜单
        results = ranking_dao.get_by_group_type(test_db, "romance")
        romance_count = len([r for r in sample_rankings if r.rank_group_type == "romance"])
        assert len(results) == romance_count
    
    def test_create_or_update_by_rank_id(self, test_db):
        """测试创建或更新榜单"""
        ranking_dao = RankingDAO()
        
        # 创建新榜单
        ranking_data = {
            "rank_id": 999,
            "name": "新榜单",
            "page_id": "new_page"
        }
        ranking = ranking_dao.create_or_update_by_rank_id(test_db, ranking_data)
        assert ranking.rank_id == 999
        assert ranking.name == "新榜单"
        
        # 更新现有榜单
        update_data = {
            "rank_id": 999,
            "name": "更新后的榜单",
            "page_id": "new_page"
        }
        updated_ranking = ranking_dao.create_or_update_by_rank_id(test_db, update_data)
        assert updated_ranking.id == ranking.id
        assert updated_ranking.name == "更新后的榜单"


class TestRankingSnapshotDAO:
    """榜单快照DAO测试"""
    
    def test_get_latest_by_ranking_id(self, test_db, sample_ranking_snapshots):
        """测试获取最新榜单快照"""
        snapshot_dao = RankingSnapshotDAO()
        ranking_id = sample_ranking_snapshots[0].ranking_id
        
        latest_snapshots = snapshot_dao.get_latest_by_ranking_id(test_db, ranking_id)
        assert len(latest_snapshots) == 3  # sample_ranking_snapshots有3个快照
        
        # 验证按position排序
        positions = [s.position for s in latest_snapshots]
        assert positions == sorted(positions)
    
    def test_get_book_ranking_history(self, test_db, sample_complete_data):
        """测试获取书籍排名历史"""
        snapshot_dao = RankingSnapshotDAO()
        book_id = sample_complete_data["books"][0].id
        
        history = snapshot_dao.get_book_ranking_history(test_db, book_id, limit=10)
        assert len(history) > 0
        
        # 验证都是同一本书的历史
        for snapshot in history:
            assert snapshot.book_id == book_id
    
    def test_get_ranking_statistics(self, test_db, sample_complete_data):
        """测试获取榜单统计"""
        snapshot_dao = RankingSnapshotDAO()
        ranking_id = sample_complete_data["rankings"][0].id
        
        stats = snapshot_dao.get_ranking_statistics(test_db, ranking_id)
        
        assert stats["total_snapshots"] > 0
        assert stats["unique_books"] > 0
        assert stats["first_snapshot_time"] is not None
        assert stats["last_snapshot_time"] is not None
    
    def test_get_ranking_trend(self, test_db, sample_complete_data):
        """测试获取榜单趋势"""
        snapshot_dao = RankingSnapshotDAO()
        ranking_id = sample_complete_data["rankings"][0].id
        
        trend = snapshot_dao.get_ranking_trend(test_db, ranking_id)
        assert len(trend) > 0
        
        # 验证趋势数据格式
        for snapshot_time, book_count in trend:
            assert isinstance(snapshot_time, datetime)
            assert isinstance(book_count, int)
            assert book_count > 0
    
    def test_bulk_create(self, test_db, sample_ranking, sample_books):
        """测试批量创建榜单快照"""
        snapshot_dao = RankingSnapshotDAO()
        
        snapshots_data = []
        snapshot_time = datetime.now()
        
        for i, book in enumerate(sample_books[:3]):
            snapshots_data.append({
                "ranking_id": sample_ranking.id,
                "book_id": book.id,
                "position": i + 1,
                "score": 100.0 - i * 10,
                "snapshot_time": snapshot_time
            })
        
        created_snapshots = snapshot_dao.bulk_create(test_db, snapshots_data)
        assert len(created_snapshots) == 3
        
        # 验证数据正确
        for i, snapshot in enumerate(created_snapshots):
            assert snapshot.ranking_id == sample_ranking.id
            assert snapshot.position == i + 1
    
    def test_get_books_comparison(self, test_db, sample_complete_data):
        """测试获取书籍对比数据"""
        snapshot_dao = RankingSnapshotDAO()
        
        ranking_ids = [r.id for r in sample_complete_data["rankings"][:2]]
        comparison = snapshot_dao.get_books_comparison(test_db, ranking_ids)
        
        assert len(comparison) == 2
        for ranking_id in ranking_ids:
            assert ranking_id in comparison
            assert len(comparison[ranking_id]) > 0