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

    books_data = [
        [3682327, "扫描你的心", 348407],
        [6571279, "春雪欲燃", 763229],
        [4315135, "全家提前两年准备大逃荒", 2373250],
    ]

    book_snapshot_data = [
        [3682327, 1000, 5000, 50, 200, 50000, 0, 25, "连载中", base_time - timedelta(days=2)],
        [3682327, 1023, 5100, 53, 206, 70000, 19, 28, "连载中", base_time - timedelta(days=1)],
        [3682327, 1456, 7000, 66, 258, 73008, 19, 29, "连载中", base_time],
        [6571279, 800, 3000, 30, 200, 30000, 0, 12, "连载中", base_time - timedelta(days=1)],
    ]

    rankings_data = [
        ["jiazi", "夹子", None, None, "jiazi", None],
        ["826", "VIP金榜", "vipgold", "vipgoldgroup", "index", None],
        ["822", "VIP金榜", "vipgold", "natural_822", "index", None],
        [None, "版权强推", "ysqt", "channel=index&ranktype=ysqt", "index", None],
        ["657", "霸王票日榜读者栽培榜", "kingcultivate", "king_ticket_daily_0", "index", "霸王票日榜"],
        ["657", "霸王票日榜读者栽培榜", "kingcultivate", "natural_657", "index", "读者栽培榜"],
        ["653", "霸王票日榜读者栽培榜", "kingcultivate", "king_ticket_daily_1", "yq", "霸王票日榜"],
        ["70000005", None, "yshotdongman", "70000005", "index", "版权改编"],
        ["70000005", None, "yshotdongman", "70000005", "yq", "版权改编"],
        ["70000003", None, "yshotdongman", "70000003", "yq", "最新海外及繁体出版"]

    ]

    # 创建测试书籍数据
    books = [Book(novel_id=i[0], title=i[1], author_id=i[2]) for i in books_data]
    session.add_all(books)

    # 创建测试榜单数据
    rankings = [Ranking(rank_id=i[0], channel_name=i[1], rank_group_type=i[2], channel_id=i[3], page_id=i[4],
                        sub_channel_name=i[5]) for i in rankings_data]
    session.add_all(rankings)
    session.commit()

    # 创建书籍快照数据
    book_snapshots = [BookSnapshot(
            novel_id=i[0],
            favorites=i[1],
            clicks=i[2],
            comments=i[3],
            nutrition=i[4],
            word_counts=i[5],
            vip_chapter_id=i[6],
            chapter_counts=i[7],
            status=i[8],
            snapshot_time=i[9]
        ) for i in book_snapshot_data
    ]
    session.add_all(book_snapshots)

    # 创建榜单快照数据
    batch_id_1 = generate_batch_id()
    batch_id_2 = generate_batch_id()

    ranking_snapshots = [
        # 夹子榜单快照 - 批次1
        RankingSnapshot(
            ranking_id=1,
            novel_id=123456,
            batch_id=batch_id_1,
            position=1,
            snapshot_time=base_time - timedelta(hours=1)
        ),
        RankingSnapshot(
            ranking_id=1,
            novel_id=123457,
            batch_id=batch_id_1,
            position=2,
            snapshot_time=base_time - timedelta(hours=1)
        ),
        # 夹子榜单快照 - 批次2（最新）
        RankingSnapshot(
            ranking_id=1,
            novel_id=123457,
            batch_id=batch_id_2,
            position=1,
            snapshot_time=base_time
        ),
        RankingSnapshot(
            ranking_id=1,
            novel_id=123456,
            batch_id=batch_id_2,
            position=2,
            snapshot_time=base_time
        ),
        # 收藏榜快照
        RankingSnapshot(
            ranking_id=2,
            novel_id=123456,
            batch_id=batch_id_2,
            position=1,
            snapshot_time=base_time
        ),
    ]
    session.add_all(ranking_snapshots)
    session.commit()

    return session


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
    """样本书籍快照数据"""
    base_time = datetime.now()
    return [
        {
            "novel_id": 123456,
            "favorites": 1200,
            "clicks": 6000,
            "comments": 60,
            "nutrition": 240,
            "word_counts": 54000,
            "chapter_counts": 27,
            "status": "连载中",
            "snapshot_time": base_time
        },
        {
            "novel_id": 123457,
            "favorites": 900,
            "clicks": 3500,
            "comments": 35,
            "nutrition": 170,
            "word_counts": 32000,
            "chapter_counts": 16,
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
    """样本榜单快照数据"""
    batch_id = generate_batch_id()
    base_time = datetime.now()

    return [
        {
            "ranking_id": 1,
            "novel_id": 123456,
            "batch_id": batch_id,
            "position": 1,
            "snapshot_time": base_time
        },
        {
            "ranking_id": 1,
            "novel_id": 123457,
            "batch_id": batch_id,
            "position": 2,
            "snapshot_time": base_time
        },
        {
            "ranking_id": 1,
            "novel_id": 123458,
            "batch_id": batch_id,
            "position": 3,
            "snapshot_time": base_time
        },
    ]
