"""
数据访问层(DAO)测试
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os
from typing import List, Optional


class TestBookDAO:
    """书籍数据访问层测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """设置测试数据库"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # 创建数据库引擎
        self.engine = create_engine(
            f"sqlite:///{self.temp_db.name}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        
        # 创建表
        from app.database.models import Base
        Base.metadata.create_all(bind=self.engine)
        
        # 创建会话
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.SessionLocal()
        
        # 创建DAO实例
        from app.database.dao.book_dao import BookDAO
        self.book_dao = BookDAO(self.session)
        
        yield
        
        # 清理
        self.session.close()
        os.unlink(self.temp_db.name)
    
    def test_create_book(self):
        """测试创建书籍"""
        book_data = {
            "novel_id": 12345,
            "title": "测试小说",
            "author": "测试作者",
            "status": "连载中",
            "tag": "现代言情",
            "length": 100000,
            "favorites": 1000,
            "intro": "这是一本测试小说"
        }
        
        # 创建书籍
        book = self.book_dao.create(book_data)
        
        # 验证创建成功
        assert book is not None
        assert book.novel_id == 12345
        assert book.title == "测试小说"
        assert book.author == "测试作者"
        assert book.id is not None
    
    def test_get_book_by_id(self):
        """测试通过ID获取书籍"""
        # 先创建书籍
        book_data = {
            "novel_id": 12345,
            "title": "测试小说",
            "author": "测试作者"
        }
        created_book = self.book_dao.create(book_data)
        
        # 通过ID获取书籍
        book = self.book_dao.get_by_id(created_book.id)
        
        # 验证获取成功
        assert book is not None
        assert book.id == created_book.id
        assert book.title == "测试小说"
    
    def test_get_book_by_novel_id(self):
        """测试通过小说ID获取书籍"""
        # 先创建书籍
        book_data = {
            "novel_id": 12345,
            "title": "测试小说",
            "author": "测试作者"
        }
        self.book_dao.create(book_data)
        
        # 通过小说ID获取书籍
        book = self.book_dao.get_by_novel_id(12345)
        
        # 验证获取成功
        assert book is not None
        assert book.novel_id == 12345
        assert book.title == "测试小说"
    
    def test_get_books_by_author(self):
        """测试通过作者获取书籍"""
        # 创建多本书籍
        books_data = [
            {"novel_id": 1, "title": "小说1", "author": "作者1"},
            {"novel_id": 2, "title": "小说2", "author": "作者1"},
            {"novel_id": 3, "title": "小说3", "author": "作者2"},
        ]
        
        for book_data in books_data:
            self.book_dao.create(book_data)
        
        # 通过作者获取书籍
        books = self.book_dao.get_by_author("作者1")
        
        # 验证获取成功
        assert len(books) == 2
        assert all(book.author == "作者1" for book in books)
    
    def test_get_books_by_tag(self):
        """测试通过标签获取书籍"""
        # 创建多本书籍
        books_data = [
            {"novel_id": 1, "title": "小说1", "author": "作者1", "tag": "现代言情"},
            {"novel_id": 2, "title": "小说2", "author": "作者2", "tag": "现代言情"},
            {"novel_id": 3, "title": "小说3", "author": "作者3", "tag": "古代言情"},
        ]
        
        for book_data in books_data:
            self.book_dao.create(book_data)
        
        # 通过标签获取书籍
        books = self.book_dao.get_by_tag("现代言情")
        
        # 验证获取成功
        assert len(books) == 2
        assert all(book.tag == "现代言情" for book in books)
    
    def test_search_books(self):
        """测试搜索书籍"""
        # 创建多本书籍
        books_data = [
            {"novel_id": 1, "title": "爱情小说", "author": "作者1"},
            {"novel_id": 2, "title": "武侠小说", "author": "作者2"},
            {"novel_id": 3, "title": "科幻小说", "author": "作者3"},
        ]
        
        for book_data in books_data:
            self.book_dao.create(book_data)
        
        # 搜索书籍
        books = self.book_dao.search("小说")
        
        # 验证搜索结果
        assert len(books) == 3
        assert all("小说" in book.title for book in books)
    
    def test_update_book(self):
        """测试更新书籍"""
        # 先创建书籍
        book_data = {
            "novel_id": 12345,
            "title": "原始标题",
            "author": "测试作者"
        }
        book = self.book_dao.create(book_data)
        
        # 更新书籍
        update_data = {
            "title": "更新后的标题",
            "favorites": 2000
        }
        updated_book = self.book_dao.update(book.id, update_data)
        
        # 验证更新成功
        assert updated_book.title == "更新后的标题"
        assert updated_book.favorites == 2000
        assert updated_book.author == "测试作者"  # 未更新的字段保持不变
    
    def test_delete_book(self):
        """测试删除书籍"""
        # 先创建书籍
        book_data = {
            "novel_id": 12345,
            "title": "测试小说",
            "author": "测试作者"
        }
        book = self.book_dao.create(book_data)
        
        # 删除书籍
        success = self.book_dao.delete(book.id)
        
        # 验证删除成功
        assert success is True
        
        # 验证书籍已不存在
        deleted_book = self.book_dao.get_by_id(book.id)
        assert deleted_book is None
    
    def test_get_books_with_pagination(self):
        """测试分页获取书籍"""
        # 创建多本书籍
        books_data = [
            {"novel_id": i, "title": f"小说{i}", "author": f"作者{i}"}
            for i in range(1, 11)
        ]
        
        for book_data in books_data:
            self.book_dao.create(book_data)
        
        # 分页获取书籍
        books, total = self.book_dao.get_with_pagination(page=1, size=5)
        
        # 验证分页结果
        assert len(books) == 5
        assert total == 10
        
        # 获取第二页
        books_page2, total = self.book_dao.get_with_pagination(page=2, size=5)
        assert len(books_page2) == 5
        assert total == 10
    
    def test_get_popular_books(self):
        """测试获取热门书籍"""
        # 创建多本书籍
        books_data = [
            {"novel_id": 1, "title": "小说1", "author": "作者1", "favorites": 1000},
            {"novel_id": 2, "title": "小说2", "author": "作者2", "favorites": 2000},
            {"novel_id": 3, "title": "小说3", "author": "作者3", "favorites": 500},
        ]
        
        for book_data in books_data:
            self.book_dao.create(book_data)
        
        # 获取热门书籍
        popular_books = self.book_dao.get_popular(limit=2)
        
        # 验证热门书籍按收藏数排序
        assert len(popular_books) == 2
        assert popular_books[0].favorites == 2000
        assert popular_books[1].favorites == 1000
    
    def test_get_recent_books(self):
        """测试获取最新书籍"""
        # 创建多本书籍
        books_data = [
            {"novel_id": 1, "title": "小说1", "author": "作者1"},
            {"novel_id": 2, "title": "小说2", "author": "作者2"},
            {"novel_id": 3, "title": "小说3", "author": "作者3"},
        ]
        
        for book_data in books_data:
            self.book_dao.create(book_data)
        
        # 获取最新书籍
        recent_books = self.book_dao.get_recent(limit=2)
        
        # 验证最新书籍按创建时间排序
        assert len(recent_books) == 2
        assert recent_books[0].created_at >= recent_books[1].created_at
    
    def test_book_exists(self):
        """测试书籍是否存在"""
        # 创建书籍
        book_data = {
            "novel_id": 12345,
            "title": "测试小说",
            "author": "测试作者"
        }
        self.book_dao.create(book_data)
        
        # 测试书籍存在
        assert self.book_dao.exists(novel_id=12345) is True
        assert self.book_dao.exists(title="测试小说") is True
        
        # 测试书籍不存在
        assert self.book_dao.exists(novel_id=99999) is False
        assert self.book_dao.exists(title="不存在的小说") is False
    
    def test_count_books(self):
        """测试统计书籍数量"""
        # 创建多本书籍
        books_data = [
            {"novel_id": 1, "title": "小说1", "author": "作者1", "tag": "现代言情"},
            {"novel_id": 2, "title": "小说2", "author": "作者2", "tag": "现代言情"},
            {"novel_id": 3, "title": "小说3", "author": "作者3", "tag": "古代言情"},
        ]
        
        for book_data in books_data:
            self.book_dao.create(book_data)
        
        # 统计总数
        total_count = self.book_dao.count()
        assert total_count == 3
        
        # 按标签统计
        modern_count = self.book_dao.count(tag="现代言情")
        assert modern_count == 2
        
        ancient_count = self.book_dao.count(tag="古代言情")
        assert ancient_count == 1
    
    def test_bulk_create_books(self):
        """测试批量创建书籍"""
        # 准备批量数据
        books_data = [
            {"novel_id": i, "title": f"小说{i}", "author": f"作者{i}"}
            for i in range(1, 6)
        ]
        
        # 批量创建书籍
        created_books = self.book_dao.bulk_create(books_data)
        
        # 验证批量创建成功
        assert len(created_books) == 5
        assert all(book.id is not None for book in created_books)
        
        # 验证书籍已保存到数据库
        total_count = self.book_dao.count()
        assert total_count == 5
    
    def test_bulk_update_books(self):
        """测试批量更新书籍"""
        # 先创建书籍
        books_data = [
            {"novel_id": i, "title": f"小说{i}", "author": f"作者{i}"}
            for i in range(1, 4)
        ]
        created_books = self.book_dao.bulk_create(books_data)
        
        # 准备更新数据
        updates = [
            {"id": created_books[0].id, "favorites": 1000},
            {"id": created_books[1].id, "favorites": 2000},
            {"id": created_books[2].id, "favorites": 3000},
        ]
        
        # 批量更新书籍
        updated_count = self.book_dao.bulk_update(updates)
        
        # 验证批量更新成功
        assert updated_count == 3
        
        # 验证更新结果
        for i, book in enumerate(created_books):
            refreshed_book = self.book_dao.get_by_id(book.id)
            assert refreshed_book.favorites == (i + 1) * 1000 