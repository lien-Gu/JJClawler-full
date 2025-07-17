"""
Database模块测试配置文件
提供数据库测试专用的fixtures和mock数据
"""
import pytest
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database.db.base import Base
from app.database.db.book import Book, BookSnapshot
from app.database.db.ranking import Ranking, RankingSnapshot


# ==================== 测试数据库配置 ====================

@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    # 使用内存SQLite数据库
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def db_session(test_db):
    """数据库会话fixture"""
    return test_db


# ==================== 测试数据 ====================

@pytest.fixture
def sample_book_data():
    """样本书籍数据"""
    return {
        "novel_id": 12345,
        "title": "测试小说",
        "author_id": 101,
        "novel_class": "现代言情",
        "tags": "现代都市,言情",
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime(2024, 1, 1, 12, 0, 0)
    }


@pytest.fixture
def sample_book_snapshot_data():
    """样本书籍快照数据"""
    return {
        "book_id": 1,  # 指向Book表的主键id
        "clicks": 50000,
        "favorites": 1500,
        "comments": 800,
        "snapshot_time": datetime(2024, 1, 15, 12, 0, 0)
    }


@pytest.fixture
def sample_ranking_data():
    """样本榜单数据"""
    return {
        "rank_id": 1,
        "rank_name": "测试榜单",
        "page_id": "test_ranking",
        "rank_group_type": "热门",
        "created_at": datetime(2024, 1, 1, 12, 0, 0)
    }


@pytest.fixture
def sample_ranking_snapshot_data():
    """样本榜单快照数据"""
    return {
        "ranking_id": 1,
        "book_id": 1,  # 指向Book表的主键id
        "position": 1,
        "score": 95.5,
        "snapshot_time": datetime(2024, 1, 15, 12, 0, 0)
    }


# ==================== 预置数据库记录 ====================

@pytest.fixture
def create_test_book(db_session, sample_book_data):
    """创建测试书籍记录"""
    book = Book(**sample_book_data)
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book


@pytest.fixture
def create_test_book_snapshot(db_session, create_test_book, sample_book_snapshot_data):
    """创建测试书籍快照记录"""
    snapshot_data = sample_book_snapshot_data.copy()
    snapshot_data["book_id"] = create_test_book.id
    
    snapshot = BookSnapshot(**snapshot_data)
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)
    return snapshot


@pytest.fixture
def create_test_ranking(db_session, sample_ranking_data):
    """创建测试榜单记录"""
    ranking = Ranking(**sample_ranking_data)
    db_session.add(ranking)
    db_session.commit()
    db_session.refresh(ranking)
    return ranking


@pytest.fixture
def create_test_ranking_snapshot(db_session, create_test_ranking, create_test_book, sample_ranking_snapshot_data):
    """创建测试榜单快照记录"""
    snapshot_data = sample_ranking_snapshot_data.copy()
    snapshot_data["ranking_id"] = create_test_ranking.id
    snapshot_data["book_id"] = create_test_book.id
    
    snapshot = RankingSnapshot(**snapshot_data)
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)
    return snapshot


# ==================== 批量测试数据 ====================

@pytest.fixture
def create_multiple_books(db_session):
    """创建多个测试书籍"""
    books_data = [
        {
            "novel_id": 12348,
            "title": "测试小说1",
            "author_id": 201,
            "novel_class": "现代言情",
            "tags": "都市,甜文",
            "created_at": datetime(2024, 1, 1, 12, 0, 0)
        },
        {
            "novel_id": 12349,
            "title": "测试小说2", 
            "author_id": 202,
            "novel_class": "古代言情",
            "tags": "宫廷,重生",
            "created_at": datetime(2024, 1, 2, 12, 0, 0)
        },
        {
            "novel_id": 12350,
            "title": "搜索测试小说",
            "author_id": 203,
            "novel_class": "纯爱小说",
            "tags": "仙侠,幻想",
            "created_at": datetime(2024, 1, 3, 12, 0, 0)
        }
    ]
    
    books = []
    for book_data in books_data:
        book = Book(**book_data)
        db_session.add(book)
        books.append(book)
    
    db_session.commit()
    
    for book in books:
        db_session.refresh(book)
    
    return books


@pytest.fixture
def create_multiple_snapshots(db_session, create_multiple_books, create_test_book):
    """创建多个书籍快照"""
    snapshots_data = [
        # 为create_test_book创建快照
        {
            "book_id": create_test_book.id,
            "clicks": 50000,
            "favorites": 1500,
            "comments": 800,
                "snapshot_time": datetime(2024, 1, 14, 12, 0, 0)
        },
        {
            "book_id": create_test_book.id,
            "clicks": 52000,
            "favorites": 1600,
            "comments": 850,
            "snapshot_time": datetime(2024, 1, 15, 12, 0, 0)
        },
        # 为create_multiple_books创建快照
        {
            "book_id": create_multiple_books[0].id,
            "clicks": 30000,
            "favorites": 800,
            "comments": 400,
            "snapshot_time": datetime(2024, 1, 15, 12, 0, 0)
        }
    ]
    
    snapshots = []
    for snapshot_data in snapshots_data:
        snapshot = BookSnapshot(**snapshot_data)
        db_session.add(snapshot)
        snapshots.append(snapshot)
    
    db_session.commit()
    
    for snapshot in snapshots:
        db_session.refresh(snapshot)
    
    return snapshots


# ==================== Mock对象 ====================

@pytest.fixture
def mock_db_session(mocker):
    """模拟数据库Session"""
    session = mocker.Mock(spec=Session)
    session.add = mocker.Mock()
    session.commit = mocker.Mock()
    session.refresh = mocker.Mock()
    session.rollback = mocker.Mock()
    session.close = mocker.Mock()
    session.scalar = mocker.Mock()
    session.execute = mocker.Mock()
    session.query = mocker.Mock()
    return session


@pytest.fixture
def mock_query_result(mocker):
    """模拟查询结果"""
    result = mocker.Mock()
    result.scalars = mocker.Mock()
    result.fetchall = mocker.Mock()
    result.fetchone = mocker.Mock()
    return result


# ==================== 业务逻辑测试数据 ====================

@pytest.fixture
def pagination_params():
    """分页参数"""
    return {
        "valid": {"page": 1, "size": 20, "skip": 0},
        "second_page": {"page": 2, "size": 10, "skip": 10},
        "large_page": {"page": 5, "size": 50, "skip": 200}
    }


@pytest.fixture
def search_params():
    """搜索参数"""
    return {
        "valid_keyword": "测试",
        "empty_keyword": "",
        "nonexistent_keyword": "不存在的内容",
        "partial_match": "小说"
    }


@pytest.fixture
def trend_params():
    """趋势数据参数"""
    return {
        "days": 7,
        "hours": 24,
        "weeks": 4,
        "months": 3,
        "start_time": datetime(2024, 1, 1, 0, 0, 0),
        "end_time": datetime(2024, 1, 15, 23, 59, 59)
    }


# ==================== 统计数据Mock ====================

@pytest.fixture
def mock_statistics_data():
    """模拟统计数据"""
    return {
        "book_stats": {
            "total_snapshots": 100,
            "avg_clicks": 45000.0,
            "max_clicks": 60000,
            "min_clicks": 30000,
            "latest_snapshot_time": datetime(2024, 1, 15, 12, 0, 0),
            "first_snapshot_time": datetime(2024, 1, 1, 12, 0, 0)
        },
        "ranking_stats": {
            "total_snapshots": 50,
            "unique_books": 25,
            "avg_books_per_snapshot": 20.5,
            "most_stable_book": {"book_id": 12345, "title": "稳定书籍"},
            "first_snapshot_time": datetime(2024, 1, 1, 12, 0, 0),
            "last_snapshot_time": datetime(2024, 1, 15, 12, 0, 0)
        }
    }


# ==================== 验证助手函数 ====================

def assert_book_equal(book1: Book, book2: Book):
    """验证两个书籍对象相等"""
    assert book1.novel_id == book2.novel_id
    assert book1.title == book2.title
    assert book1.author_id == book2.author_id
    assert book1.novel_class == book2.novel_class


def assert_snapshot_equal(snapshot1: BookSnapshot, snapshot2: BookSnapshot):
    """验证两个快照对象相等"""
    assert snapshot1.book_id == snapshot2.book_id
    assert snapshot1.clicks == snapshot2.clicks
    assert snapshot1.favorites == snapshot2.favorites
    assert snapshot1.comments == snapshot2.comments
