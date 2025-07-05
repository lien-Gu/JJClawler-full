"""
API测试配置文件
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.main import app
from app.database.connection import get_db
from app.database.db.base import Base
from app.database.db.book import Book, BookSnapshot
from app.database.db.ranking import Ranking, RankingSnapshot


# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """创建测试数据库会话"""
    # 创建表
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 清理表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """创建测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    
    # 添加测试数据
    _create_test_data(db)
    
    with TestClient(app) as c:
        yield c
    
    # 清理依赖覆盖
    app.dependency_overrides.clear()


def _create_test_data(db):
    """创建测试数据"""
    # 创建测试书籍
    test_books = [
        Book(
            id=1,
            novel_id=12345,
            title="测试书籍1",
            created_at=datetime.now()
        ),
        Book(
            id=2,
            novel_id=12346,
            title="现代言情小说",
            created_at=datetime.now()
        ),
        Book(
            id=3,
            novel_id=12347,
            title="古代言情",
            created_at=datetime.now()
        ),
        Book(
            id=4,
            novel_id=12348,
            title="玄幻小说",
            created_at=datetime.now()
        ),
        Book(
            id=5,
            novel_id=12349,
            title="科幻小说",
            created_at=datetime.now()
        )
    ]
    
    for book in test_books:
        db.add(book)
    
    # 创建测试榜单
    test_rankings = [
        Ranking(
            rank_id=1,
            name="晋江VIP完结榜",
            rank_group_type="VIP",
            page_id="vip_complete",
            created_at=datetime.now()
        ),
        Ranking(
            rank_id=2,
            name="原创小说风云榜",
            rank_group_type="原创",
            page_id="original_popular",
            created_at=datetime.now()
        ),
        Ranking(
            rank_id=3,
            name="现代言情榜",
            rank_group_type="现代",
            page_id="modern_romance",
            created_at=datetime.now()
        )
    ]
    
    for ranking in test_rankings:
        db.add(ranking)
    
    db.commit()
    
    # 创建书籍快照数据
    base_time = datetime.now() - timedelta(days=30)
    
    for i, book in enumerate(test_books, 1):
        for day in range(30):
            snapshot_time = base_time + timedelta(days=day)
            snapshot = BookSnapshot(
                book_id=book.id,
                clicks=1000 + i * 100 + day * 10,
                favorites=500 + i * 50 + day * 5,
                comments=100 + i * 10 + day * 2,
                recommendations=50 + i * 5 + day,
                snapshot_time=snapshot_time
            )
            db.add(snapshot)
    
    # 创建榜单快照数据
    for day in range(30):
        snapshot_time = base_time + timedelta(days=day)
        
        # 为每个榜单创建快照
        for ranking in test_rankings:
            # 每个榜单包含3-5本书
            book_count = 3 + (day % 3)
            for pos in range(1, book_count + 1):
                book_id = ((day + pos + ranking.rank_id) % 5) + 1
                
                ranking_snapshot = RankingSnapshot(
                    ranking_id=ranking.rank_id,
                    book_id=book_id,
                    position=pos,
                    snapshot_time=snapshot_time
                )
                db.add(ranking_snapshot)
    
    db.commit()


@pytest.fixture
def sample_book_data():
    """示例书籍数据"""
    return {
        "id": 1,
        "novel_id": 12345,
        "title": "测试书籍1"
    }


@pytest.fixture
def sample_ranking_data():
    """示例榜单数据"""
    return {
        "rank_id": 1,
        "name": "晋江VIP完结榜",
        "rank_group_type": "VIP",
        "page_id": "vip_complete"
    }


@pytest.fixture
def sample_books_list():
    """示例书籍列表"""
    return [
        {
            "id": 1,
            "novel_id": 12345,
            "title": "测试书籍1"
        },
        {
            "id": 2,
            "novel_id": 12346,
            "title": "现代言情小说"
        },
        {
            "id": 3,
            "novel_id": 12347,
            "title": "古代言情"
        }
    ]


@pytest.fixture
def sample_rankings_list():
    """示例榜单列表"""
    return [
        {
            "rank_id": 1,
            "name": "晋江VIP完结榜",
            "rank_group_type": "VIP",
            "page_id": "vip_complete"
        },
        {
            "rank_id": 2,
            "name": "原创小说风云榜",
            "rank_group_type": "原创",
            "page_id": "original_popular"
        },
        {
            "rank_id": 3,
            "name": "现代言情榜",
            "rank_group_type": "现代",
            "page_id": "modern_romance"
        }
    ]