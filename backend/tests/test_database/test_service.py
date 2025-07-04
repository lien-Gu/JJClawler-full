"""
数据库服务层测试
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from typing import List, Optional, Dict, Any


class TestBookService:
    """书籍服务层测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_service(self):
        """设置测试服务"""
        # 模拟数据库会话
        self.mock_session = Mock()
        
        # 模拟DAO
        self.mock_book_dao = Mock()
        self.mock_ranking_dao = Mock()
        
        # 创建服务实例
        from app.database.service.book_service import BookService
        self.book_service = BookService(
            session=self.mock_session,
            book_dao=self.mock_book_dao,
            ranking_dao=self.mock_ranking_dao
        )
    
    def test_get_book_by_id(self):
        """测试通过ID获取书籍"""
        # 模拟返回数据
        mock_book = Mock()
        mock_book.id = 1
        mock_book.title = "测试小说"
        mock_book.author = "测试作者"
        self.mock_book_dao.get_by_id.return_value = mock_book
        
        # 调用服务方法
        result = self.book_service.get_book_by_id(1)
        
        # 验证结果
        assert result is not None
        assert result.id == 1
        assert result.title == "测试小说"
        self.mock_book_dao.get_by_id.assert_called_once_with(1)
    
    def test_get_book_by_id_not_found(self):
        """测试获取不存在的书籍"""
        # 模拟返回None
        self.mock_book_dao.get_by_id.return_value = None
        
        # 调用服务方法
        result = self.book_service.get_book_by_id(999)
        
        # 验证结果
        assert result is None
        self.mock_book_dao.get_by_id.assert_called_once_with(999)
    
    def test_create_book(self):
        """测试创建书籍"""
        # 准备测试数据
        book_data = {
            "novel_id": 12345,
            "title": "测试小说",
            "author": "测试作者",
            "status": "连载中",
            "tag": "现代言情"
        }
        
        # 模拟返回数据
        mock_book = Mock()
        mock_book.id = 1
        mock_book.novel_id = 12345
        mock_book.title = "测试小说"
        self.mock_book_dao.create.return_value = mock_book
        
        # 调用服务方法
        result = self.book_service.create_book(book_data)
        
        # 验证结果
        assert result is not None
        assert result.id == 1
        assert result.novel_id == 12345
        self.mock_book_dao.create.assert_called_once_with(book_data)
    
    def test_create_book_validation_error(self):
        """测试创建书籍时的验证错误"""
        # 准备无效数据
        invalid_data = {
            "novel_id": 0,  # 无效ID
            "title": "",  # 空标题
            "author": "测试作者"
        }
        
        # 调用服务方法，应该抛出异常
        with pytest.raises(ValueError):
            self.book_service.create_book(invalid_data)
    
    def test_update_book(self):
        """测试更新书籍"""
        # 准备测试数据
        book_id = 1
        update_data = {
            "title": "更新后的标题",
            "favorites": 2000
        }
        
        # 模拟返回数据
        mock_book = Mock()
        mock_book.id = 1
        mock_book.title = "更新后的标题"
        mock_book.favorites = 2000
        self.mock_book_dao.update.return_value = mock_book
        
        # 调用服务方法
        result = self.book_service.update_book(book_id, update_data)
        
        # 验证结果
        assert result is not None
        assert result.title == "更新后的标题"
        assert result.favorites == 2000
        self.mock_book_dao.update.assert_called_once_with(book_id, update_data)
    
    def test_delete_book(self):
        """测试删除书籍"""
        # 模拟返回成功
        self.mock_book_dao.delete.return_value = True
        
        # 调用服务方法
        result = self.book_service.delete_book(1)
        
        # 验证结果
        assert result is True
        self.mock_book_dao.delete.assert_called_once_with(1)
    
    def test_search_books(self):
        """测试搜索书籍"""
        # 准备测试数据
        query = "测试"
        filters = {"tag": "现代言情", "status": "连载中"}
        
        # 模拟返回数据
        mock_books = [Mock(id=1, title="测试小说1"), Mock(id=2, title="测试小说2")]
        self.mock_book_dao.search.return_value = mock_books
        
        # 调用服务方法
        result = self.book_service.search_books(query, filters)
        
        # 验证结果
        assert len(result) == 2
        assert result[0].title == "测试小说1"
        assert result[1].title == "测试小说2"
        self.mock_book_dao.search.assert_called_once_with(query, filters)
    
    def test_get_books_with_pagination(self):
        """测试分页获取书籍"""
        # 模拟返回数据
        mock_books = [Mock(id=i, title=f"小说{i}") for i in range(1, 6)]
        self.mock_book_dao.get_with_pagination.return_value = (mock_books, 10)
        
        # 调用服务方法
        result, total = self.book_service.get_books_with_pagination(page=1, size=5)
        
        # 验证结果
        assert len(result) == 5
        assert total == 10
        self.mock_book_dao.get_with_pagination.assert_called_once_with(page=1, size=5)
    
    def test_get_popular_books(self):
        """测试获取热门书籍"""
        # 模拟返回数据
        mock_books = [
            Mock(id=1, title="热门小说1", favorites=2000),
            Mock(id=2, title="热门小说2", favorites=1000)
        ]
        self.mock_book_dao.get_popular.return_value = mock_books
        
        # 调用服务方法
        result = self.book_service.get_popular_books(limit=2)
        
        # 验证结果
        assert len(result) == 2
        assert result[0].favorites == 2000
        assert result[1].favorites == 1000
        self.mock_book_dao.get_popular.assert_called_once_with(limit=2)
    
    def test_get_book_trends(self):
        """测试获取书籍趋势"""
        # 准备测试数据
        book_id = 1
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # 模拟返回数据
        mock_snapshots = [
            Mock(favorites=1000, snapshot_time=datetime(2024, 1, 1)),
            Mock(favorites=1500, snapshot_time=datetime(2024, 1, 15)),
            Mock(favorites=2000, snapshot_time=datetime(2024, 1, 31))
        ]
        self.mock_book_dao.get_snapshots.return_value = mock_snapshots
        
        # 调用服务方法
        result = self.book_service.get_book_trends(book_id, start_date, end_date)
        
        # 验证结果
        assert "favorites" in result
        assert "growth_rate" in result
        assert len(result["favorites"]) == 3
        self.mock_book_dao.get_snapshots.assert_called_once_with(book_id, start_date, end_date)
    
    def test_get_book_ranking_history(self):
        """测试获取书籍排名历史"""
        # 准备测试数据
        book_id = 1
        
        # 模拟返回数据
        mock_rankings = [
            Mock(ranking_name="夹子榜", position=1, snapshot_time=datetime(2024, 1, 1)),
            Mock(ranking_name="夹子榜", position=2, snapshot_time=datetime(2024, 1, 2))
        ]
        self.mock_ranking_dao.get_book_ranking_history.return_value = mock_rankings
        
        # 调用服务方法
        result = self.book_service.get_book_ranking_history(book_id)
        
        # 验证结果
        assert len(result) == 2
        assert result[0].position == 1
        assert result[1].position == 2
        self.mock_ranking_dao.get_book_ranking_history.assert_called_once_with(book_id)
    
    def test_bulk_create_books(self):
        """测试批量创建书籍"""
        # 准备测试数据
        books_data = [
            {"novel_id": 1, "title": "小说1", "author": "作者1"},
            {"novel_id": 2, "title": "小说2", "author": "作者2"}
        ]
        
        # 模拟返回数据
        mock_books = [Mock(id=1, novel_id=1), Mock(id=2, novel_id=2)]
        self.mock_book_dao.bulk_create.return_value = mock_books
        
        # 调用服务方法
        result = self.book_service.bulk_create_books(books_data)
        
        # 验证结果
        assert len(result) == 2
        assert result[0].novel_id == 1
        assert result[1].novel_id == 2
        self.mock_book_dao.bulk_create.assert_called_once_with(books_data)
    
    def test_bulk_update_books(self):
        """测试批量更新书籍"""
        # 准备测试数据
        updates = [
            {"id": 1, "favorites": 1000},
            {"id": 2, "favorites": 2000}
        ]
        
        # 模拟返回数据
        self.mock_book_dao.bulk_update.return_value = 2
        
        # 调用服务方法
        result = self.book_service.bulk_update_books(updates)
        
        # 验证结果
        assert result == 2
        self.mock_book_dao.bulk_update.assert_called_once_with(updates)
    
    def test_get_books_statistics(self):
        """测试获取书籍统计"""
        # 模拟返回数据
        self.mock_book_dao.count.return_value = 100
        self.mock_book_dao.count_by_tag.return_value = {
            "现代言情": 50,
            "古代言情": 30,
            "纯爱": 20
        }
        
        # 调用服务方法
        result = self.book_service.get_books_statistics()
        
        # 验证结果
        assert result["total_books"] == 100
        assert result["by_tag"]["现代言情"] == 50
        assert result["by_tag"]["古代言情"] == 30
        assert result["by_tag"]["纯爱"] == 20
    
    def test_update_book_snapshot(self):
        """测试更新书籍快照"""
        # 准备测试数据
        book_id = 1
        snapshot_data = {
            "favorites": 1000,
            "total_clicks": 5000,
            "monthly_clicks": 500,
            "weekly_clicks": 100,
            "daily_clicks": 20
        }
        
        # 模拟返回数据
        mock_snapshot = Mock()
        mock_snapshot.id = 1
        mock_snapshot.book_id = book_id
        mock_snapshot.favorites = 1000
        self.mock_book_dao.create_snapshot.return_value = mock_snapshot
        
        # 调用服务方法
        result = self.book_service.update_book_snapshot(book_id, snapshot_data)
        
        # 验证结果
        assert result is not None
        assert result.book_id == book_id
        assert result.favorites == 1000
        self.mock_book_dao.create_snapshot.assert_called_once_with(book_id, snapshot_data)
    
    def test_get_book_comparison(self):
        """测试获取书籍对比"""
        # 准备测试数据
        book_ids = [1, 2]
        
        # 模拟返回数据
        mock_books = [
            Mock(id=1, title="小说1", favorites=1000),
            Mock(id=2, title="小说2", favorites=2000)
        ]
        self.mock_book_dao.get_by_ids.return_value = mock_books
        
        # 调用服务方法
        result = self.book_service.get_book_comparison(book_ids)
        
        # 验证结果
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        self.mock_book_dao.get_by_ids.assert_called_once_with(book_ids)
    
    @patch('app.db.service.book_service.logger')
    def test_service_error_handling(self, mock_logger):
        """测试服务错误处理"""
        # 模拟DAO抛出异常
        self.mock_book_dao.get_by_id.side_effect = Exception("Database error")
        
        # 调用服务方法
        with pytest.raises(Exception):
            self.book_service.get_book_by_id(1)
        
        # 验证日志记录
        mock_logger.error.assert_called_once()
    
    def test_cache_integration(self):
        """测试缓存集成"""
        # 这里可以测试缓存机制（如果有的话）
        pass
    
    def test_transaction_management(self):
        """测试事务管理"""
        # 准备测试数据
        book_data = {
            "novel_id": 12345,
            "title": "测试小说",
            "author": "测试作者"
        }
        
        # 模拟事务成功
        self.mock_session.commit.return_value = None
        self.mock_book_dao.create.return_value = Mock(id=1)
        
        # 调用服务方法
        result = self.book_service.create_book_with_transaction(book_data)
        
        # 验证事务操作
        self.mock_session.commit.assert_called_once()
        assert result is not None
    
    def test_transaction_rollback(self):
        """测试事务回滚"""
        # 准备测试数据
        book_data = {
            "novel_id": 12345,
            "title": "测试小说",
            "author": "测试作者"
        }
        
        # 模拟操作失败
        self.mock_book_dao.create.side_effect = Exception("Create failed")
        
        # 调用服务方法
        with pytest.raises(Exception):
            self.book_service.create_book_with_transaction(book_data)
        
        # 验证回滚操作
        self.mock_session.rollback.assert_called_once()


class TestRankingService:
    """榜单服务层测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_service(self):
        """设置测试服务"""
        # 模拟数据库会话
        self.mock_session = Mock()
        
        # 模拟DAO
        self.mock_ranking_dao = Mock()
        self.mock_book_dao = Mock()
        
        # 创建服务实例
        from app.database.service.ranking_service import RankingService
        self.ranking_service = RankingService(
            session=self.mock_session,
            ranking_dao=self.mock_ranking_dao,
            book_dao=self.mock_book_dao
        )
    
    def test_get_ranking_by_id(self):
        """测试通过ID获取榜单"""
        # 模拟返回数据
        mock_ranking = Mock()
        mock_ranking.id = 1
        mock_ranking.name = "夹子榜"
        mock_ranking.type = "jiazi"
        self.mock_ranking_dao.get_by_id.return_value = mock_ranking
        
        # 调用服务方法
        result = self.ranking_service.get_ranking_by_id(1)
        
        # 验证结果
        assert result is not None
        assert result.id == 1
        assert result.name == "夹子榜"
        self.mock_ranking_dao.get_by_id.assert_called_once_with(1)
    
    def test_get_ranking_snapshots(self):
        """测试获取榜单快照"""
        # 准备测试数据
        ranking_id = 1
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # 模拟返回数据
        mock_snapshots = [
            Mock(id=1, position=1, book_id=1, snapshot_time=datetime(2024, 1, 1)),
            Mock(id=2, position=2, book_id=2, snapshot_time=datetime(2024, 1, 1))
        ]
        self.mock_ranking_dao.get_snapshots.return_value = mock_snapshots
        
        # 调用服务方法
        result = self.ranking_service.get_ranking_snapshots(ranking_id, start_date, end_date)
        
        # 验证结果
        assert len(result) == 2
        assert result[0].position == 1
        assert result[1].position == 2
        self.mock_ranking_dao.get_snapshots.assert_called_once_with(ranking_id, start_date, end_date)
    
    def test_update_ranking_snapshot(self):
        """测试更新榜单快照"""
        # 准备测试数据
        ranking_id = 1
        books_data = [
            {"book_id": 1, "position": 1, "score": 1000},
            {"book_id": 2, "position": 2, "score": 900}
        ]
        
        # 模拟返回数据
        mock_snapshots = [Mock(id=1, position=1), Mock(id=2, position=2)]
        self.mock_ranking_dao.create_snapshots.return_value = mock_snapshots
        
        # 调用服务方法
        result = self.ranking_service.update_ranking_snapshot(ranking_id, books_data)
        
        # 验证结果
        assert len(result) == 2
        assert result[0].position == 1
        assert result[1].position == 2
        self.mock_ranking_dao.create_snapshots.assert_called_once_with(ranking_id, books_data)
    
    def test_get_ranking_trends(self):
        """测试获取榜单趋势"""
        # 准备测试数据
        ranking_id = 1
        
        # 模拟返回数据
        mock_snapshots = [
            Mock(snapshot_time=datetime(2024, 1, 1), position=1, book_id=1),
            Mock(snapshot_time=datetime(2024, 1, 2), position=2, book_id=1)
        ]
        self.mock_ranking_dao.get_snapshots.return_value = mock_snapshots
        
        # 调用服务方法
        result = self.ranking_service.get_ranking_trends(ranking_id)
        
        # 验证结果
        assert "position_changes" in result
        assert "stability_score" in result
        self.mock_ranking_dao.get_snapshots.assert_called_once_with(ranking_id)
    
    def test_get_ranking_statistics(self):
        """测试获取榜单统计"""
        # 模拟返回数据
        self.mock_ranking_dao.count.return_value = 10
        self.mock_ranking_dao.count_by_type.return_value = {
            "jiazi": 1,
            "category": 9
        }
        
        # 调用服务方法
        result = self.ranking_service.get_ranking_statistics()
        
        # 验证结果
        assert result["total_rankings"] == 10
        assert result["by_type"]["jiazi"] == 1
        assert result["by_type"]["category"] == 9 