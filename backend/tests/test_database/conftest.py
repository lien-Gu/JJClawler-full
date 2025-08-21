"""
Database模块测试配置文件
提供数据库测试专用的fixtures和测试数据
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.db.base import Base
from app.database.db.book import Book, BookSnapshot
from app.database.db.ranking import Ranking, RankingSnapshot
from app.utils import generate_batch_id


# ==================== 测试数据库配置 ====================


@pytest.fixture(scope="function")
def test_db_session():
    """创建测试数据库会话"""
    # 使用内存SQLite数据库
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建session
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def populated_db_session(test_db_session):
    """包含测试数据的数据库会话"""
    session = test_db_session
    base_time = datetime.now()
    
    # 定义测试数据 - 使用列表结构便于维护
    books_data = [
        # [novel_id, title, author_id]
        [3682327, "扫描你的心", 348407],
        [6571279, "春雪欲燃", 763229],
        [4315135, "全家提前两年准备大逃荒", 2373250],
    ]

    rankings_data = [
        # [rank_id, channel_name, rank_group_type, channel_id, page_id, sub_channel_name]
        ["jiazi", "夹子", None, None, "jiazi", None],
        ["826", "VIP金榜", "vipgold", "vipgoldgroup", "index", None],
        ["822", "VIP金榜", "vipgold", "natural_822", "index", None],
        ["ysqt_001", "版权强推", "ysqt", "channel=index&ranktype=ysqt", "index", None],
        ["657", "霸王票日榜读者栽培榜", "kingcultivate", "king_ticket_daily_0", "index", "霸王票日榜"],
        ["657_b", "霸王票日榜读者栽培榜", "kingcultivate", "natural_657", "index", "读者栽培榜"],
        ["653", "霸王票日榜读者栽培榜", "kingcultivate", "king_ticket_daily_1", "yq", "霸王票日榜"],
        ["70000005", "版权改编榜", "yshotdongman", "70000005", "index", "版权改编"],
        ["70000005_yq", "版权改编榜", "yshotdongman", "70000005", "yq", "版权改编"],
        ["70000003", "海外出版榜", "yshotdongman", "70000003", "yq", "最新海外及繁体出版"]
    ]
    
    book_snapshots_data = [
        # [novel_id, favorites, clicks, comments, nutrition, word_counts, vip_chapter_id, chapter_counts, status, snapshot_time]
        [3682327, 1000, 5000, 50, 200, 50000, 0, 25, "连载中", base_time - timedelta(days=2)],
        [3682327, 1023, 5100, 53, 206, 70000, 19, 28, "连载中", base_time - timedelta(days=1)],
        [3682327, 1456, 7000, 66, 258, 73008, 19, 29, "连载中", base_time],
        [6571279, 800, 3000, 30, 200, 30000, 0, 12, "连载中", base_time - timedelta(days=1)],
        [4315135, 2000, 8000, 80, 400, 120000, 0, 50, "连载中", base_time - timedelta(hours=2)],
    ]
    
    # 生成批次ID
    batch_id_1 = generate_batch_id()
    batch_id_2 = generate_batch_id()
    batch_id_3 = generate_batch_id()
    
    ranking_snapshots_data = [
        # [ranking_id, novel_id, batch_id, position, snapshot_time]
        # 夹子榜单(榜单ID=1) - 早期批次
        [1, 3682327, batch_id_1, 1, base_time - timedelta(hours=2)],
        [1, 6571279, batch_id_1, 2, base_time - timedelta(hours=2)],
        [1, 4315135, batch_id_1, 3, base_time - timedelta(hours=2)],
        
        # 夹子榜单(榜单ID=1) - 中期批次  
        [1, 6571279, batch_id_2, 1, base_time - timedelta(hours=1)],
        [1, 3682327, batch_id_2, 2, base_time - timedelta(hours=1)],
        [1, 4315135, batch_id_2, 3, base_time - timedelta(hours=1)],
        
        # 夹子榜单(榜单ID=1) - 最新批次
        [1, 4315135, batch_id_3, 1, base_time],
        [1, 3682327, batch_id_3, 2, base_time],
        [1, 6571279, batch_id_3, 3, base_time],
        
        # VIP金榜(榜单ID=2) - 最新批次
        [2, 3682327, batch_id_3, 1, base_time],
        [2, 6571279, batch_id_3, 2, base_time],
        
        # VIP金榜(榜单ID=3) - 最新批次
        [3, 6571279, batch_id_3, 1, base_time],
        [3, 4315135, batch_id_3, 2, base_time],
    ]

    # 创建并插入数据 - 按顺序执行以维护外键约束
    _create_books(session, books_data)
    _create_rankings(session, rankings_data) 
    _create_book_snapshots(session, book_snapshots_data)
    _create_ranking_snapshots(session, ranking_snapshots_data)
    
    return session


def _create_books(session, books_data):
    """创建书籍数据"""
    books = [Book(novel_id=data[0], title=data[1], author_id=data[2]) for data in books_data]
    session.add_all(books)
    session.commit()


def _create_rankings(session, rankings_data):
    """创建榜单数据"""
    rankings = [
        Ranking(
            rank_id=data[0],
            channel_name=data[1], 
            rank_group_type=data[2],
            channel_id=data[3],
            page_id=data[4],
            sub_channel_name=data[5]
        ) for data in rankings_data
    ]
    session.add_all(rankings)
    session.commit()


def _create_book_snapshots(session, book_snapshots_data):
    """创建书籍快照数据"""
    book_snapshots = [
        BookSnapshot(
            novel_id=data[0],
            favorites=data[1],
            clicks=data[2],
            comments=data[3],
            nutrition=data[4],
            word_counts=data[5],
            vip_chapter_id=data[6],
            chapter_counts=data[7],
            status=data[8],
            snapshot_time=data[9]
        ) for data in book_snapshots_data
    ]
    session.add_all(book_snapshots)
    session.commit()


def _create_ranking_snapshots(session, ranking_snapshots_data):
    """创建榜单快照数据"""
    ranking_snapshots = [
        RankingSnapshot(
            ranking_id=data[0],
            novel_id=data[1],
            batch_id=data[2],
            position=data[3],
            snapshot_time=data[4]
        ) for data in ranking_snapshots_data
    ]
    session.add_all(ranking_snapshots)
    session.commit()


# ==================== 测试数据fixtures ====================

@pytest.fixture
def sample_book_data():
    """样本书籍数据"""
    return {
        "novel_id": 999999,
        "title": "新测试小说",
        "author_id": 9999
    }


@pytest.fixture
def sample_book_snapshots_data():
    """样本书籍快照数据 - 与现有数据保持一致的新增数据"""
    base_time = datetime.now()
    return [
        {
            "novel_id": 3682327,  # 使用已存在的书籍ID
            "favorites": 1500,
            "clicks": 7500,
            "comments": 70,
            "nutrition": 280,
            "word_counts": 75000,
            "vip_chapter_id": 19,
            "chapter_counts": 30,
            "status": "连载中",
            "snapshot_time": base_time
        },
        {
            "novel_id": 6571279,  # 使用已存在的书籍ID
            "favorites": 950,
            "clicks": 3800,
            "comments": 38,
            "nutrition": 210,
            "word_counts": 35000,
            "vip_chapter_id": 0,
            "chapter_counts": 18,
            "status": "连载中",
            "snapshot_time": base_time
        },
    ]


@pytest.fixture
def sample_ranking_data():
    """样本榜单数据"""
    return {
        "rank_id": "new_ranking",
        "channel_name": "新榜单",
        "rank_group_type": "测试",
        "channel_id": "test_channel",
        "page_id": "test_page",
        "sub_channel_name": "测试子榜"
    }


@pytest.fixture
def sample_ranking_snapshots_data():
    """样本榜单快照数据 - 与现有数据保持一致的新增数据"""
    batch_id = generate_batch_id()
    base_time = datetime.now()

    return [
        {
            "ranking_id": 1,  # 夹子榜单
            "novel_id": 3682327,  # 使用已存在的书籍ID
            "batch_id": batch_id,
            "position": 1,
            "snapshot_time": base_time
        },
        {
            "ranking_id": 1,  # 夹子榜单
            "novel_id": 6571279,  # 使用已存在的书籍ID
            "batch_id": batch_id,
            "position": 2,
            "snapshot_time": base_time
        },
        {
            "ranking_id": 2,  # VIP金榜
            "novel_id": 4315135,  # 使用已存在的书籍ID
            "batch_id": batch_id,
            "position": 1,
            "snapshot_time": base_time
        },
    ]
