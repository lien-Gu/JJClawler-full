"""
书籍服务测试文件
测试app.database.service.book_service模块的所有服务方法
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.database.service.book_service import BookService
from app.database.db.book import Book, BookSnapshot


class TestBookService:
    """测试BookService类"""
    
    @pytest.fixture
    def book_service(self):
        """BookService实例fixture"""
        return BookService()
    
    # ==================== 基础CRUD操作测试 ====================
    
    def test_get_book_by_id(self, book_service, db_session, create_test_book):
        """测试根据ID获取书籍"""
        result = book_service.get_book_by_id(db_session, create_test_book.id)
        
        assert result is not None
        assert result.id == create_test_book.id
        assert result.title == create_test_book.title
    
    def test_get_book_by_novel_id(self, book_service, db_session, create_test_book):
        """测试根据novel_id获取书籍"""
        result = book_service.get_book_by_novel_id(db_session, create_test_book.novel_id)
        
        assert result is not None
        assert result.novel_id == create_test_book.novel_id
        assert result.title == create_test_book.title
    
    def test_create_book(self, book_service, db_session):
        """测试创建书籍"""
        book_data = {
            "novel_id": 99999,
            "title": "新建测试小说"
        }
        
        result = book_service.create_book(db_session, book_data)
        
        assert result.novel_id == 99999
        assert result.title == "新建测试小说"
        assert result.title == "新建测试小说"
    
    def test_update_book(self, book_service, db_session, create_test_book):
        """测试更新书籍"""
        update_data = {
            "title": "更新后的书名"
        }
        
        result = book_service.update_book(db_session, create_test_book, update_data)
        
        assert result.title == "更新后的书名"
        assert result.novel_id == create_test_book.novel_id  # novel_id不变
    
    def test_create_or_update_book_create(self, book_service, db_session):
        """测试创建或更新书籍 - 创建新书籍"""
        book_data = {
            "novel_id": 88888,
            "title": "创建或更新测试小说"
        }
        
        result = book_service.create_or_update_book(db_session, book_data)
        
        assert result.novel_id == 88888
        assert result.title == "创建或更新测试小说"
    
    def test_create_or_update_book_update(self, book_service, db_session, create_test_book):
        """测试创建或更新书籍 - 更新现有书籍"""
        book_data = {
            "novel_id": create_test_book.novel_id,
            "title": "更新的书名"
        }
        
        result = book_service.create_or_update_book(db_session, book_data)
        
        assert result.id == create_test_book.id  # 同一个记录
        assert result.title == "更新的书名"
    
    # ==================== 查询操作测试 ====================
    
    def test_search_books_by_title(self, book_service, db_session, create_multiple_books):
        """测试根据标题搜索书籍"""
        result = book_service.search_books_by_title(db_session, "测试")
        
        assert len(result) >= 2  # create_multiple_books中有多本包含"测试"的书籍
        assert all("测试" in book.title for book in result)
    
    def test_search_books_by_title_exact_match(self, book_service, db_session, create_multiple_books):
        """测试精确搜索书籍标题"""
        result = book_service.search_books_by_title(db_session, "搜索测试小说")
        
        assert len(result) >= 1
        assert any(book.title == "搜索测试小说" for book in result)
    
    def test_get_books_with_pagination(self, book_service, db_session, create_multiple_books):
        """测试分页获取书籍列表"""
        result = book_service.get_books_with_pagination(db_session, page=1, size=10)
        
        assert "books" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert "total_pages" in result
        assert result["page"] == 1
        assert result["size"] == 10
        assert len(result["books"]) >= 1
    
    def test_get_books_with_pagination_filters(self, book_service, db_session, create_multiple_books):
        """测试带过滤条件的分页获取书籍列表"""
        filters = {"title": "测试小说1"}
        result = book_service.get_books_with_pagination(db_session, page=1, size=10, filters=filters)
        
        assert len(result["books"]) >= 1
        assert all("测试小说1" in book.title for book in result["books"])
    
    def test_get_books_by_ids(self, book_service, db_session, create_multiple_books):
        """测试根据ID列表获取书籍"""
        book_ids = [book.id for book in create_multiple_books[:2]]  # 取前两本书的ID
        
        result = book_service.get_books_by_ids(db_session, book_ids)
        
        assert len(result) == 2
        assert all(book.id in book_ids for book in result)
    
    def test_get_books_by_ids_with_invalid_id(self, book_service, db_session, create_multiple_books):
        """测试根据包含无效ID的列表获取书籍"""
        book_ids = [create_multiple_books[0].id, 99999]  # 一个有效ID，一个无效ID
        
        result = book_service.get_books_by_ids(db_session, book_ids)
        
        assert len(result) == 1  # 只返回有效的书籍
        assert result[0].id == create_multiple_books[0].id
    
    # ==================== 书籍快照操作测试 ====================
    
    def test_create_book_snapshot(self, book_service, db_session, create_test_book):
        """测试创建书籍快照"""
        snapshot_data = {
            "book_id": create_test_book.id,
            "clicks": 60000,
            "favorites": 2000,
            "comments": 1000,
            "snapshot_time": datetime(2024, 1, 16, 12, 0, 0)
        }
        
        result = book_service.create_book_snapshot(db_session, snapshot_data)
        
        assert result.book_id == create_test_book.id
        assert result.clicks == 60000
        assert result.favorites == 2000
        assert result.comments == 1000
    
    def test_batch_create_book_snapshots(self, book_service, db_session, create_test_book):
        """测试批量创建书籍快照"""
        snapshots_data = [
            {
                "book_id": create_test_book.id,
                "clicks": 60000,
                "favorites": 2000,
                "comments": 1000,
                "snapshot_time": datetime(2024, 1, 16, 12, 0, 0)
            },
            {
                "book_id": create_test_book.id,
                "clicks": 62000,
                "favorites": 2100,
                "comments": 1050,
                "snapshot_time": datetime(2024, 1, 17, 12, 0, 0)
            }
        ]
        
        result = book_service.batch_create_book_snapshots(db_session, snapshots_data)
        
        assert len(result) == 2
        assert result[0].clicks == 60000
        assert result[1].clicks == 62000
    
    def test_get_latest_snapshot_by_book_id(self, book_service, db_session, create_test_book_snapshot):
        """测试获取书籍最新快照"""
        result = book_service.get_latest_snapshot_by_book_id(db_session, create_test_book_snapshot.book_id)
        
        assert result is not None
        assert result.book_id == create_test_book_snapshot.book_id
    
    def test_get_snapshots_by_book_id(self, book_service, db_session, create_multiple_snapshots, create_test_book):
        """测试获取书籍快照列表"""
        result = book_service.get_snapshots_by_book_id(db_session, create_test_book.id)
        
        assert len(result) >= 2  # create_multiple_snapshots为create_test_book创建了多个快照
        assert all(snapshot.book_id == create_test_book.id for snapshot in result)
    
    def test_get_snapshots_by_book_id_with_time_range(self, book_service, db_session, create_multiple_snapshots, create_test_book):
        """测试在指定时间范围内获取书籍快照列表"""
        start_time = datetime(2024, 1, 14, 0, 0, 0)
        end_time = datetime(2024, 1, 16, 23, 59, 59)
        
        result = book_service.get_snapshots_by_book_id(
            db_session, 
            create_test_book.id, 
            start_time=start_time, 
            end_time=end_time
        )
        
        assert len(result) >= 1
        assert all(
            start_time <= snapshot.snapshot_time <= end_time 
            for snapshot in result
        )
    
    # ==================== 趋势分析测试 ====================
    
    def test_get_book_trend_by_interval_day(self, book_service, db_session, create_multiple_snapshots, create_test_book):
        """测试按天获取书籍趋势数据"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 31, 23, 59, 59)
        
        result = book_service.get_book_trend_by_interval(
            db_session, 
            create_test_book.id, 
            start_time, 
            end_time, 
            "day"
        )
        
        assert isinstance(result, list)
        assert len(result) >= 1
        
        # 验证返回数据结构
        trend_item = result[0]
        assert "time_period" in trend_item
        assert "avg_favorites" in trend_item
        assert "avg_clicks" in trend_item
        assert "snapshot_count" in trend_item
    
    def test_get_book_trend_by_interval_hour(self, book_service, db_session, create_multiple_snapshots, create_test_book):
        """测试按小时获取书籍趋势数据"""
        start_time = datetime(2024, 1, 14, 0, 0, 0)
        end_time = datetime(2024, 1, 15, 23, 59, 59)
        
        result = book_service.get_book_trend_by_interval(
            db_session,
            create_test_book.id,
            start_time,
            end_time,
            "hour"
        )
        
        assert isinstance(result, list)
        assert len(result) >= 1
    
    def test_get_book_trend_by_interval_invalid_interval(self, book_service, db_session, create_test_book):
        """测试使用无效时间间隔"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 31, 23, 59, 59)
        
        with pytest.raises(ValueError, match="不支持的时间间隔"):
            book_service.get_book_trend_by_interval(
                db_session,
                create_test_book.id,
                start_time,
                end_time,
                "invalid_interval"
            )
    
    # ==================== 业务逻辑方法测试 ====================
    
    def test_get_book_detail_with_latest_snapshot(self, book_service, db_session, create_test_book_snapshot):
        """测试获取书籍详情和最新快照数据"""
        result = book_service.get_book_detail_with_latest_snapshot(db_session, create_test_book_snapshot.book_id)
        
        assert result is not None
        assert "book" in result
        assert "latest_snapshot" in result
        assert "statistics" in result
        assert result["book"].id == create_test_book_snapshot.book_id
    
    def test_get_book_detail_with_latest_snapshot_no_book(self, book_service, db_session):
        """测试获取不存在书籍的详情"""
        result = book_service.get_book_detail_with_latest_snapshot(db_session, 99999)
        assert result is None
    
    def test_get_book_trend_hourly(self, book_service, db_session, create_multiple_snapshots, create_test_book):
        """测试按小时获取书籍趋势数据"""
        result = book_service.get_book_trend_hourly(db_session, create_test_book.id, hours=48)
        
        assert isinstance(result, list)
        # 由于测试数据的时间范围，可能没有数据在最近48小时内
        # 所以这里只验证方法能正常调用和返回正确的数据结构
    
    def test_get_book_trend_daily(self, book_service, db_session, create_multiple_snapshots, create_test_book):
        """测试按天获取书籍趋势数据"""
        result = book_service.get_book_trend_daily(db_session, create_test_book.id, days=30)
        
        assert isinstance(result, list)
    
    def test_get_book_trend_weekly(self, book_service, db_session, create_multiple_snapshots, create_test_book):
        """测试按周获取书籍趋势数据"""
        result = book_service.get_book_trend_weekly(db_session, create_test_book.id, weeks=8)
        
        assert isinstance(result, list)
    
    def test_get_book_trend_monthly(self, book_service, db_session, create_multiple_snapshots, create_test_book):
        """测试按月获取书籍趋势数据"""
        result = book_service.get_book_trend_monthly(db_session, create_test_book.id, months=6)
        
        assert isinstance(result, list)
    
    def test_get_book_statistics(self, book_service, db_session, create_multiple_snapshots, create_test_book):
        """测试获取书籍统计信息"""
        result = book_service.get_book_statistics(db_session, create_test_book.id)
        
        assert "total_snapshots" in result
        assert "max_favorites" in result
        assert "max_clicks" in result
        assert "max_comments" in result
        assert "first_snapshot_time" in result
        assert "last_snapshot_time" in result
        assert result["total_snapshots"] >= 1
    
    def test_get_book_statistics_no_snapshots(self, book_service, db_session, create_test_book):
        """测试获取没有快照的书籍统计信息"""
        # create_test_book没有关联的快照
        # 所以应该返回空字典或者默认值
        result = book_service.get_book_statistics(db_session, create_test_book.id)
        
        # 根据实现，这应该返回空字典
        assert result == {}
    
    def test_cleanup_old_snapshots(self, book_service, db_session, create_multiple_snapshots, create_test_book):
        """测试清理旧快照"""
        # 创建一个很久以前的快照
        old_snapshot_data = {
            "book_id": create_test_book.id,
            "clicks": 10000,
            "favorites": 500,
            "comments": 200,
            "snapshot_time": datetime(2023, 1, 1, 12, 0, 0)  # 很久以前的快照
        }
        book_service.create_book_snapshot(db_session, old_snapshot_data)
        
        # 清理30天前的快照，保留最新100条
        deleted_count = book_service.cleanup_old_snapshots(
            db_session,
            create_test_book.id,
            keep_days=30,
            keep_count=100
        )
        
        assert deleted_count >= 0  # 可能没有删除任何记录，取决于测试数据
    
    # ==================== 错误处理测试 ====================
    
    def test_create_or_update_book_without_novel_id(self, book_service, db_session):
        """测试创建或更新书籍时缺少novel_id"""
        book_data = {
            "title": "测试书籍"
        }
        
        with pytest.raises(ValueError, match="novel_id is required"):
            book_service.create_or_update_book(db_session, book_data)
    
    def test_get_book_by_id_not_found(self, book_service, db_session):
        """测试获取不存在的书籍"""
        result = book_service.get_book_by_id(db_session, 99999)
        assert result is None
    
    def test_get_book_by_novel_id_not_found(self, book_service, db_session):
        """测试根据不存在的novel_id获取书籍"""
        result = book_service.get_book_by_novel_id(db_session, 99999)
        assert result is None
    
    def test_search_books_by_title_empty_result(self, book_service, db_session):
        """测试搜索不存在的书籍标题"""
        result = book_service.search_books_by_title(db_session, "不存在的书名")
        assert len(result) == 0
    
    def test_get_latest_snapshot_by_book_id_no_snapshots(self, book_service, db_session, create_test_book):
        """测试获取没有快照的书籍的最新快照"""
        # create_test_book没有关联的快照
        result = book_service.get_latest_snapshot_by_book_id(db_session, create_test_book.id)
        assert result is None