"""
Database模块测试配置文件
提供数据库测试专用的fixtures和mock数据
"""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.db.base import Base

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
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


# ==================== 测试数据 ====================

@pytest.fixture
def sample_book_data():
    """样本书籍数据"""
    return {
        "novel_id": "123456",
        "title": "测试小说",
        "author_id": "1001", 
        "author_name": "测试作者",
        "status": "连载中",
        "word_counts": 50000,
        "chapter_counts": 25,
        "tags": "言情,现代",
        "first_seen": datetime.now(),
        "last_updated": datetime.now()
    }


@pytest.fixture  
def sample_ranking_data():
    """样本榜单数据"""
    return {
        "rank_id": "jiazi",
        "rank_name": "夹子榜单",
        "rank_group_type": "推荐",
        "channel_id": "jiazi_channel",
        "channel_name": "夹子频道",
        "page_id": "jiazi",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }