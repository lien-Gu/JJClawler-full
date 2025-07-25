"""
爬虫模块测试配置文件
集中管理爬虫相关的测试数据和fixtures
"""

import os
import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.db.base import Base
from app.database.connection import get_db


# ==================== 数据库初始化 ====================

@pytest.fixture(scope="session")
def test_engine():
    """测试数据库引擎"""
    # 使用内存SQLite数据库进行测试
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_db_session(test_engine):
    """测试数据库会话"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ==================== 爬虫配置数据 ====================

@pytest.fixture
def sample_config_data():
    """样本配置数据"""
    return {
        "global": {
            "base_params": {"version": 20, "use_cdn": "1"},
            "templates": {
                "jiazi_ranking": "https://app-cdn.jjwxc.com/bookstore/favObservationByDate?day={day}&use_cdn={use_cdn}&version={version}",
                "page_ranking": "https://app-cdn.jjwxc.com/bookstore/getFullPageV1?channel={channel}&version={version}&use_cdn={use_cdn}",
                "novel_detail": "https://app-cdn.jjwxc.com/androidapi/novelbasicinfo?novelId={novel_id}",
            },
        },
        "crawl_tasks": [
            {
                "id": "jiazi",
                "template": "jiazi_ranking",
                "params": {"day": "today"},
                "category": "jiazi",
            },
            {"id": "index", "template": "page_ranking", "params": {"channel": "index"}},
            {"id": "yq", "template": "page_ranking", "params": {"channel": "yq"}},
        ],
    }


# ==================== HTTP 响应数据 ====================

@pytest.fixture
def mock_jiazi_response():
    """模拟夹子榜API响应"""
    return {
        "code": "200",
        "data": {
            "list": [
                {
                    "novelId": "123456",
                    "novelName": "测试小说1",
                    "authorid": "1001",
                },
                {
                    "novelId": "123457",
                    "novelName": "测试小说2", 
                    "authorid": "1002",
                }
            ]
        }
    }


@pytest.fixture
def mock_page_response():
    """模拟页面API响应"""
    return {
        "code": "200",
        "data": [
            {
                "rankid": "hottest",
                "channelName": "热门榜单",
                "rank_group_type": "热门",
                "channelMoreId": "index_hot",
                "data": [
                    {
                        "novelId": "789101",
                        "novelName": "页面测试小说1",
                        "authorid": "2001",
                    },
                    {
                        "novelId": "789102", 
                        "novelName": "页面测试小说2",
                        "authorid": "2002",
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_book_detail_response():
    """模拟书籍详情API响应"""
    return {
        "novelId": "123456",
        "novelName": "测试小说详情",
        "authorId": "1001",
        "series": "连载中",
        "novelSize": 50000,
        "novelChapterCount": 25,
        "vipChapterid": "chapter_10",
        "novelbefavoritedcount": 1200,
        "novip_clicks": 5000,
        "comment_count": 100,
        "nutrition_novel": 95,
    }


# ==================== Mock工厂函数 ====================

@pytest.fixture
def mock_http_client():
    """模拟HTTP客户端"""
    client = Mock()
    client.run = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_crawl_config(mocker, sample_config_data):
    """模拟爬虫配置"""
    mock_config = Mock()
    mock_config._config = sample_config_data
    mock_config.params = sample_config_data["global"]["base_params"]
    mock_config.templates = sample_config_data["global"]["templates"]
    
    # 模拟配置方法
    def get_task_config(task_id):
        for task in sample_config_data["crawl_tasks"]:
            if task["id"] == task_id:
                return task
        return None
    
    def build_url(task_id):
        task = get_task_config(task_id)
        if not task:
            return None
        template = mock_config.templates[task["template"]]
        params = {**mock_config.params, **task.get("params", {})}
        return template.format(**params)
        
    def build_novel_url(novel_id):
        return mock_config.templates["novel_detail"].format(novel_id=novel_id)
    
    mock_config.get_task_config = get_task_config
    mock_config.build_url = build_url
    mock_config.build_novel_url = build_novel_url
    mock_config.get_all_tasks = lambda: sample_config_data["crawl_tasks"]
    mock_config.validate_page_id = lambda pid: pid in ["jiazi", "index", "yq"]
    
    return mock_config


# ==================== 数据库Mock ====================

@pytest.fixture
def mock_book_service(mocker):
    """模拟书籍服务"""
    service = Mock()
    
    # 模拟返回的书籍对象
    mock_book = Mock()
    mock_book.id = 1
    mock_book.novel_id = 123456
    
    service.create_or_update_book.return_value = mock_book
    service.batch_create_book_snapshots.return_value = []
    
    return service


@pytest.fixture
def mock_ranking_service(mocker):
    """模拟榜单服务"""
    service = Mock()
    
    # 模拟返回的榜单对象
    mock_ranking = Mock()
    mock_ranking.id = 1
    mock_ranking.rank_id = "test_rank"
    
    service.create_or_update_ranking.return_value = mock_ranking
    service.batch_create_ranking_snapshots.return_value = []
    
    return service


# ==================== 真实网络测试标记 ====================

def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(  
        "markers", "real_network: marks tests that require real network access"
    )