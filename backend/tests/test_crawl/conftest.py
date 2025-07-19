"""
爬虫模块测试配置文件
集中管理爬虫相关的测试数据和fixtures
"""

import os

import pytest
from pytest_mock import MockerFixture

from app.crawl.parser import DataType, ParsedItem
from app.database.connection import create_tables, drop_tables

# ==================== 数据库初始化 ====================


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """测试数据库初始化

    这个fixture会在所有测试开始前创建数据库表，
    并在测试结束后清理数据库
    """
    # 设置测试环境使用独立的数据库
    original_db_url = os.environ.get("DATABASE_URL")
    test_db_url = "sqlite:///./test.db"
    os.environ["DATABASE_URL"] = test_db_url

    # 导入需要在设置环境变量后重新导入
    from app.database.connection import create_tables as create_test_tables

    try:
        # 创建数据库表
        create_test_tables()

        yield

    finally:
        # 恢复原始数据库配置
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)

        # 清理测试数据库文件
        if os.path.exists("test.db"):
            os.remove("test.db")


@pytest.fixture
def clean_database():
    """清理数据库数据的fixture

    在需要干净数据库环境的测试中使用
    """
    # 导入当前的数据库连接

    # 清理现有数据
    drop_tables()
    create_tables()

    yield

    # 测试后可以选择保留数据用于调试
    # drop_tables()


# ==================== 爬虫配置数据 ====================


@pytest.fixture
def sample_config_data():
    """样本配置数据"""
    return {
        "global": {
            "base_params": {"version": 20, "use_cdn": "1"},
            "templates": {
                "jiazi_ranking": "https://app-cdn.jjwxc.com/bookstore/favObservationByDate?day={day}&use_cdn={use_cdn}&version={version}",
                "page_ranking": "https://app-cdn.jjwxc.com/bookstore/getFullPageV1?channel={channel}&version={version}",
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


@pytest.fixture
def test_page_ids():
    """测试页面ID"""
    return {
        "valid": ["jiazi", "index", "yq"],
        "invalid": ["invalid", "nonexistent"],
        "special": ["all", "jiazi", "category"],
        "single": ["jiazi"],
        "multiple": ["jiazi", "index"],
    }


# ==================== HTTP 响应数据 ====================


@pytest.fixture
def mock_http_response():
    """模拟HTTP响应"""
    return {
        "success": {"status": "success", "data": []},
        "failure": {"status": "error", "message": "Request failed"},
    }


@pytest.fixture
def mock_page_content():
    """模拟页面内容"""
    return {
        "content": {
            "code": "200",
            "data": [
                {
                    "rankid": "1",
                    "channelName": "测试榜单",
                    "rank_group_type": "热门",
                    "data": [
                        {
                            "novelId": "12345",
                            "novelName": "测试小说1",
                            "novelClickCount": 1000,
                            "novelFavoriteCount": 500,
                        },
                        {
                            "novelId": "12346",
                            "novelName": "测试小说2",
                            "novelClickCount": 2000,
                            "novelFavoriteCount": 800,
                        },
                    ],
                }
            ],
        }
    }


@pytest.fixture
def mock_jiazi_content():
    """模拟夹子榜内容"""
    return {
        "code": "200",
        "data": {
            "list": [
                {
                    "novelId": "55555",
                    "novelName": "夹子测试小说1",
                    "novelClickCount": 8000,
                    "novelFavoriteCount": 2000,
                },
                {
                    "novelId": "55556",
                    "novelName": "夹子测试小说2",
                    "novelClickCount": 9000,
                    "novelFavoriteCount": 2500,
                },
            ]
        },
    }


@pytest.fixture
def mock_book_detail():
    """模拟书籍详情"""
    return {
        "novelId": "12345",
        "novelName": "测试小说详情",
        "novelClickCount": 5000,
        "novelFavoriteCount": 1200,
        "CommentCount": 100,
        "nutritionNovel": 95,
    }


# ==================== 解析器数据 ====================


@pytest.fixture
def mock_parsed_items():
    """模拟解析结果"""
    return {
        "ranking": ParsedItem(
            DataType.RANKING,
            {
                "rank_id": "1",
                "rank_name": "测试榜单",
                "books": [
                    {"book_id": "12345", "title": "测试小说1", "position": 1},
                    {"book_id": "12346", "title": "测试小说2", "position": 2},
                ],
            },
        ),
        "book": ParsedItem(
            DataType.BOOK,
            {"book_id": "12345", "title": "测试小说", "clicks": 1000, "favorites": 500},
        ),
        "page": ParsedItem(DataType.PAGE, {"page_info": "test"}),
    }


# ==================== 爬取结果数据 ====================


@pytest.fixture
def mock_crawl_result():
    """模拟爬取结果"""
    return {
        "success": {
            "success": True,
            "page_id": "test_page",
            "books_crawled": 25,
            "execution_time": 5.0,
            "data": {"url": "https://test.com", "rankings_count": 1},
        },
        "failure": {
            "success": False,
            "page_id": "test_page",
            "books_crawled": 0,
            "execution_time": 1.0,
            "error_message": "网络连接失败",
        },
    }


@pytest.fixture
def mock_rankings_data():
    """模拟榜单数据"""
    return [
        {
            "rank_id": "1",
            "rank_name": "测试榜单",
            "page_id": "test_page",
            "rank_group_type": "热门",
            "books": [
                {"book_id": "12345", "title": "测试小说1", "position": 1, "score": 95.0}
            ],
        }
    ]


@pytest.fixture
def mock_books_data():
    """模拟书籍数据"""
    return [
        {
            "book_id": "12345",
            "title": "测试小说1",
            "clicks": 1000,
            "favorites": 500,
            "comments": 100,
            "word_count": 50000,
        }
    ]


# ==================== 数据库Mock ====================


@pytest.fixture
def mock_db_objects():
    """模拟数据库对象"""

    class MockRanking:
        def __init__(self):
            self.id = 1

    class MockBook:
        def __init__(self):
            self.id = 1

    return {"ranking": MockRanking(), "book": MockBook()}


# ==================== Service Mock ====================


@pytest.fixture
def mock_services(mocker: MockerFixture):
    """模拟服务对象"""
    book_service = mocker.Mock()
    ranking_service = mocker.Mock()

    # 设置默认返回值
    book_service.create_or_update_book.return_value = type("MockBook", (), {"id": 1})()
    book_service.batch_create_book_snapshots.return_value = None

    ranking_service.create_or_update_ranking.return_value = type(
        "MockRanking", (), {"id": 1}
    )()
    ranking_service.batch_create_ranking_snapshots.return_value = None

    return {"book_service": book_service, "ranking_service": ranking_service}


# ==================== 测试工厂函数 ====================


def create_mock_config(mocker: MockerFixture, config_data: dict):
    """创建模拟配置对象"""
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("json.load", return_value=config_data)


def create_mock_http_client(mocker: MockerFixture, response_data: dict):
    """创建模拟HTTP客户端"""
    mock_client = mocker.Mock()
    mock_client.get = mocker.AsyncMock(return_value=response_data)
    mock_client.close = mocker.AsyncMock()
    return mock_client


def create_mock_parser(mocker: MockerFixture, parsed_items: list):
    """创建模拟解析器"""
    mock_parser = mocker.Mock()
    mock_parser.parse.return_value = parsed_items
    return mock_parser
