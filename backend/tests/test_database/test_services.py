"""
简化的数据库服务测试
测试核心的CRUD操作和数据验证
"""

from datetime import datetime

import pytest

from app.database.service.book_service import BookService
from app.database.service.ranking_service import RankingService


class TestBookService:
    """测试BookService核心功能"""

    @pytest.fixture
    def book_service(self):
        return BookService()

    def test_create_or_update_book(self, book_service, test_db_session):
        """测试创建或更新书籍 - 核心业务逻辑"""
        book_data = {
            "novel_id": "123456",
            "title": "测试小说",
            "author_id": "1001",
            "author_name": "测试作者"
        }
        
        # 第一次创建
        book1 = book_service.create_or_update_book(test_db_session, book_data)
        assert book1.title == "测试小说"
        
        # 第二次更新
        book_data["title"] = "更新后的小说"
        book2 = book_service.create_or_update_book(test_db_session, book_data)
        assert book2.title == "更新后的小说"
        assert book1.id == book2.id  # 应该是更新而不是创建新记录

    def test_batch_create_book_snapshots(self, book_service, test_db_session):
        """测试批量创建书籍快照"""
        # 先创建书籍
        book_data = {
            "novel_id": "123456",
            "title": "测试小说",
            "author_id": "1001",
            "author_name": "测试作者"
        }
        book = book_service.create_book(test_db_session, book_data)
        
        # 创建快照数据
        snapshots_data = [
            {
                "book_id": book.id,
                "total_clicks": 1000,
                "total_favorites": 100,
                "comment_count": 50,
                "chapter_count": 10,
                "snapshot_time": datetime.now()
            }
        ]
        
        batch_id = "test_batch_001"
        result = book_service.batch_create_book_snapshots(
            test_db_session, snapshots_data, batch_id
        )
        
        assert len(result) == 1  # 成功创建1个快照


class TestRankingService:
    """测试RankingService核心功能"""

    @pytest.fixture
    def ranking_service(self):
        return RankingService()

    def test_create_or_update_ranking(self, ranking_service, test_db_session):
        """测试创建或更新榜单 - 核心业务逻辑"""
        ranking_data = {
            "rank_id": "jiazi",
            "rank_name": "夹子榜单",
            "channel_name": "夹子频道",
            "page_id": "jiazi"
        }
        
        # 第一次创建
        ranking1 = ranking_service.create_or_update_ranking(test_db_session, ranking_data)
        assert ranking1.rank_name == "夹子榜单"
        
        # 第二次更新
        ranking_data["rank_name"] = "更新的夹子榜单"
        ranking2 = ranking_service.create_or_update_ranking(test_db_session, ranking_data)
        assert ranking2.rank_name == "更新的夹子榜单"
        assert ranking1.id == ranking2.id  # 应该是更新而不是创建

    def test_batch_create_ranking_snapshots(self, ranking_service, test_db_session):
        """测试批量创建榜单快照"""
        # 先创建榜单和书籍
        ranking_data = {
            "rank_id": "jiazi",
            "rank_name": "夹子榜单",
            "channel_name": "夹子频道",
            "page_id": "jiazi"
        }
        ranking = ranking_service.create_ranking(test_db_session, ranking_data)
        
        book_service = BookService()
        book_data = {
            "novel_id": "123456",
            "title": "测试小说",
            "author_id": "1001",
            "author_name": "测试作者"
        }
        book = book_service.create_book(test_db_session, book_data)
        
        # 创建榜单快照数据
        snapshots_data = [
            {
                "ranking_id": ranking.id,
                "book_id": book.id,
                "position": 1,
                "snapshot_time": datetime.now()
            }
        ]
        
        batch_id = "test_batch_001"
        result = ranking_service.batch_create_ranking_snapshots(
            test_db_session, snapshots_data, batch_id
        )
        
        assert len(result) == 1  # 成功创建1个快照


class TestServicesIntegration:
    """测试服务之间的集成"""

    def test_complete_crawl_data_flow(self, test_db_session):
        """测试完整的爬虫数据流程"""
        book_service = BookService()
        ranking_service = RankingService()
        
        # 1. 创建榜单
        ranking_data = {
            "rank_id": "jiazi",
            "rank_name": "夹子榜单",
            "channel_name": "夹子频道",
            "page_id": "jiazi"
        }
        ranking = ranking_service.create_or_update_ranking(test_db_session, ranking_data)
        
        # 2. 创建书籍
        book_data = {
            "novel_id": "123456",
            "title": "测试小说",
            "author_id": "1001",
            "author_name": "测试作者"
        }
        book = book_service.create_or_update_book(test_db_session, book_data)
        
        # 3. 创建书籍快照
        book_snapshots = [
            {
                "book_id": book.id,
                "total_clicks": 1000,
                "total_favorites": 100,
                "comment_count": 50,
                "chapter_count": 10,
                "snapshot_time": datetime.now()
            }
        ]
        batch_id = "test_batch_001"
        book_result = book_service.batch_create_book_snapshots(
            test_db_session, book_snapshots, batch_id
        )
        
        # 4. 创建榜单快照
        ranking_snapshots = [
            {
                "ranking_id": ranking.id,
                "book_id": book.id,
                "position": 1,
                "snapshot_time": datetime.now()
            }
        ]
        ranking_result = ranking_service.batch_create_ranking_snapshots(
            test_db_session, ranking_snapshots, batch_id
        )
        
        # 验证所有操作成功
        assert ranking.id is not None
        assert book.id is not None
        assert len(book_result) == 1
        assert len(ranking_result) == 1
        
        print(f"✅ 完整数据流程测试成功:")
        print(f"   - 榜单: {ranking.rank_name}")
        print(f"   - 书籍: {book.title}")
        print(f"   - 书籍快照: {len(book_result)} 条")
        print(f"   - 榜单快照: {len(ranking_result)} 条")