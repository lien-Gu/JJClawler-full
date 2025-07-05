"""
数据库测试配置和数据生成
"""
import pytest
from datetime import datetime, timedelta
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database.db.base import Base
from app.database.db.book import Book, BookSnapshot
from app.database.db.ranking import Ranking, RankingSnapshot


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """创建测试数据库会话"""
    # 使用内存SQLite数据库
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_book(test_db: Session) -> Book:
    """创建示例书籍"""
    book = Book(
        novel_id=12345,
        title="测试小说",
        author="测试作者"
    )
    test_db.add(book)
    test_db.commit()
    test_db.refresh(book)
    return book


@pytest.fixture
def sample_books(test_db: Session) -> list[Book]:
    """创建多个示例书籍"""
    books = []
    for i in range(5):
        book = Book(
            novel_id=10000 + i,
            title=f"测试小说{i+1}",
            author=f"作者{i+1}"
        )
        books.append(book)
    
    test_db.add_all(books)
    test_db.commit()
    
    for book in books:
        test_db.refresh(book)
    
    return books


@pytest.fixture
def sample_book_snapshots(test_db: Session, sample_book: Book) -> list[BookSnapshot]:
    """创建书籍快照数据"""
    snapshots = []
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(7):
        snapshot = BookSnapshot(
            book_id=sample_book.id,
            favorites=1000 + i * 10,
            clicks=5000 + i * 50,
            comments=100 + i * 5,
            recommendations=50 + i * 2,
            word_count=100000 + i * 1000,
            status="连载中",
            snapshot_time=base_time + timedelta(days=i)
        )
        snapshots.append(snapshot)
    
    test_db.add_all(snapshots)
    test_db.commit()
    
    for snapshot in snapshots:
        test_db.refresh(snapshot)
    
    return snapshots


@pytest.fixture
def sample_ranking(test_db: Session) -> Ranking:
    """创建示例榜单"""
    ranking = Ranking(
        rank_id=1,
        name="测试榜单",
        page_id="test_page",
        rank_group_type="romance"
    )
    test_db.add(ranking)
    test_db.commit()
    test_db.refresh(ranking)
    return ranking


@pytest.fixture
def sample_rankings(test_db: Session) -> list[Ranking]:
    """创建多个示例榜单"""
    rankings = []
    for i in range(3):
        ranking = Ranking(
            rank_id=100 + i,
            name=f"测试榜单{i+1}",
            page_id=f"test_page_{i+1}",
            rank_group_type="romance" if i % 2 == 0 else "fantasy"
        )
        rankings.append(ranking)
    
    test_db.add_all(rankings)
    test_db.commit()
    
    for ranking in rankings:
        test_db.refresh(ranking)
    
    return rankings


@pytest.fixture
def sample_ranking_snapshots(
    test_db: Session, 
    sample_ranking: Ranking, 
    sample_books: list[Book]
) -> list[RankingSnapshot]:
    """创建榜单快照数据"""
    snapshots = []
    snapshot_time = datetime.now()
    
    # 为前3本书创建排名快照
    for i, book in enumerate(sample_books[:3]):
        snapshot = RankingSnapshot(
            ranking_id=sample_ranking.id,
            book_id=book.id,
            position=i + 1,
            score=100.0 - i * 10,
            snapshot_time=snapshot_time
        )
        snapshots.append(snapshot)
    
    test_db.add_all(snapshots)
    test_db.commit()
    
    for snapshot in snapshots:
        test_db.refresh(snapshot)
    
    return snapshots


@pytest.fixture
def sample_complete_data(
    test_db: Session,
    sample_books: list[Book],
    sample_rankings: list[Ranking]
) -> dict:
    """创建完整的测试数据集"""
    # 为每本书创建快照
    book_snapshots = []
    base_time = datetime.now() - timedelta(days=30)
    
    for book in sample_books:
        for day in range(30):
            snapshot = BookSnapshot(
                book_id=book.id,
                favorites=1000 + day * 10,
                clicks=5000 + day * 50,
                comments=100 + day * 5,
                recommendations=50 + day * 2,
                snapshot_time=base_time + timedelta(days=day)
            )
            book_snapshots.append(snapshot)
    
    test_db.add_all(book_snapshots)
    
    # 为每个榜单创建排名快照
    ranking_snapshots = []
    for ranking in sample_rankings:
        for day in range(7):  # 最近7天的排名
            snapshot_time = datetime.now() - timedelta(days=6-day)
            
            # 每个榜单包含前3本书
            for i, book in enumerate(sample_books[:3]):
                ranking_snapshot = RankingSnapshot(
                    ranking_id=ranking.id,
                    book_id=book.id,
                    position=i + 1 + (day % 2),  # 位置有轻微变化
                    score=100.0 - i * 10 - day,
                    snapshot_time=snapshot_time
                )
                ranking_snapshots.append(ranking_snapshot)
    
    test_db.add_all(ranking_snapshots)
    test_db.commit()
    
    return {
        "books": sample_books,
        "rankings": sample_rankings,
        "book_snapshots": book_snapshots,
        "ranking_snapshots": ranking_snapshots
    }