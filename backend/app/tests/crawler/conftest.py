"""
爬虫模块测试配置和测试数据

提供测试用的配置数据、fixture和真实URL测试支持
"""
import pytest
import json
import os
from typing import Dict, Any


@pytest.fixture(scope="session")
def real_urls_config() -> Dict[str, Any]:
    """真实的URL配置数据（用于集成测试）"""
    return {
        "version": 20,
        "base_url": "https://app-cdn.jjwxc.com/bookstore/getFullPageV1?channel={}&version={}",
        "novel_url": "https://app-cdn.jjwxc.com/androidapi/novelbasicinfo?novelId={}",
        "content": {
            "api": "bookstore",
            "jiazi": {
                "api": "favObservationByDate",
                "params": {
                    "day": "today",
                    "use_cdn": "1"
                },
                "short_name": "jiazi",
                "zh_name": "夹子",
                "url": "https://app-cdn.jjwxc.com/bookstore/favObservationByDate?day=today&use_cdn=1&version=19",
                "frequency": "hourly",
                "update_interval": 1,
                "type": "hourly"
            },
            "pages": {
                "api": "getFullPageV1",
                "yq": {
                    "short_name": "yq",
                    "channel": "yq", 
                    "zh_name": "言情",
                    "frequency": "daily",
                    "update_interval": 24,
                    "type": "daily",
                    "sub_pages": {
                        "gy": {
                            "short_name": "gy",
                            "channel": "gywx",
                            "zh_name": "古言",
                            "frequency": "hourly",
                            "update_interval": 2
                        },
                        "xy": {
                            "short_name": "xy",
                            "channel": "dsyq",
                            "zh_name": "现言",
                            "frequency": "daily",
                            "update_interval": 24
                        }
                    }
                },
                "ca": {
                    "short_name": "ca",
                    "channel": "noyq",
                    "zh_name": "纯爱",
                    "frequency": "daily",
                    "update_interval": 24,
                    "type": "daily",
                    "sub_pages": {
                        "ds": {
                            "short_name": "ds",
                            "channel": "xddm",
                            "zh_name": "都市",
                            "frequency": "hourly",
                            "update_interval": 2
                        }
                    }
                }
            }
        }
    }


@pytest.fixture(scope="session")
def mock_urls_config() -> Dict[str, Any]:
    """模拟的URL配置数据（用于单元测试）"""
    return {
        "version": 1,
        "base_url": "https://test-api.example.com/ranking/{}/{}",
        "novel_url": "https://test-api.example.com/novel/{}",
        "content": {
            "jiazi": {
                "short_name": "jiazi",
                "zh_name": "测试夹子榜",
                "url": "https://test-api.example.com/jiazi",
                "frequency": "hourly",
                "update_interval": 1,
                "type": "hourly"
            },
            "pages": {
                "test_yq": {
                    "short_name": "test_yq",
                    "channel": "test_yq",
                    "zh_name": "测试言情",
                    "frequency": "daily",
                    "update_interval": 24,
                    "type": "daily"
                },
                "test_ca": {
                    "short_name": "test_ca",
                    "channel": "test_ca",
                    "zh_name": "测试纯爱",
                    "frequency": "daily",
                    "update_interval": 24,
                    "type": "daily"
                }
            }
        }
    }


@pytest.fixture
def sample_jiazi_response_data() -> Dict[str, Any]:
    """夹子榜API响应示例数据"""
    return {
        "code": "200",
        "msg": "success",
        "data": {
            "list": [
                {
                    "novelId": "5485513",
                    "novelName": "重生九零：福运娇妻美又飒",
                    "authorId": "8895234",
                    "authorName": "青丝如墨",
                    "novelClass": "言情",
                    "tags": "现代,重生,系统,甜文",
                    "totalClicks": "125.6万",
                    "totalFavorites": "45.2万",
                    "commentCount": "1.2万",
                    "chapterCount": "134",
                    "ranking": 1
                },
                {
                    "novelId": "5423891",
                    "novelName": "穿书后我成了反派的心尖宠",
                    "authorId": "7728945",
                    "authorName": "柠檬不酸",
                    "novelClass": "言情",
                    "tags": "穿书,古代,宫廷,甜文",
                    "totalClicks": "98.7万",
                    "totalFavorites": "38.9万",
                    "commentCount": "8956",
                    "chapterCount": "89",
                    "ranking": 2
                },
                {
                    "novelId": "5567234",
                    "novelName": "修仙大佬的团宠日常",
                    "authorId": "9123456",
                    "authorName": "星河渡",
                    "novelClass": "纯爱",
                    "tags": "修仙,团宠,系统,爽文",
                    "totalClicks": "87.3万",
                    "totalFavorites": "32.1万",
                    "commentCount": "7234",
                    "chapterCount": "156",
                    "ranking": 3
                }
            ],
            "total": 50,
            "page": 1,
            "pageSize": 50
        }
    }


@pytest.fixture
def sample_page_response_data() -> Dict[str, Any]:
    """分类页面API响应示例数据"""
    return {
        "code": "200",
        "msg": "success", 
        "data": {
            "blocks": [
                {
                    "name": "今日推荐",
                    "type": "recommend",
                    "list": [
                        {
                            "novelId": "5678901",
                            "novelName": "古代种田记",
                            "authorId": "1234567",
                            "authorName": "田园作者",
                            "novelClass": "言情",
                            "tags": "古代,种田,家长里短",
                            "totalClicks": "56.7万",
                            "totalFavorites": "23.4万",
                            "commentCount": "3456",
                            "chapterCount": "78"
                        }
                    ]
                },
                {
                    "name": "热门榜单",
                    "type": "hot",
                    "list": [
                        {
                            "novelId": "5789012",
                            "novelName": "现代霸总文",
                            "authorId": "2345678",
                            "authorName": "都市作者",
                            "novelClass": "言情",
                            "tags": "现代,霸总,商战",
                            "totalClicks": "78.9万",
                            "totalFavorites": "34.5万",
                            "commentCount": "5678",
                            "chapterCount": "123"
                        },
                        {
                            "novelId": "5890123",
                            "novelName": "古言宫斗文",
                            "authorId": "3456789",
                            "authorName": "宫廷作者",
                            "novelClass": "言情",
                            "tags": "古代,宫斗,权谋",
                            "totalClicks": "67.8万",
                            "totalFavorites": "28.9万",
                            "commentCount": "4567",
                            "chapterCount": "167"
                        }
                    ]
                }
            ]
        }
    }


@pytest.fixture
def sample_single_list_response_data() -> Dict[str, Any]:
    """单一列表结构的API响应数据"""
    return {
        "code": "200",
        "msg": "success",
        "data": {
            "list": [
                {
                    "novelId": "6001234",
                    "novelName": "纯爱校园文",
                    "authorId": "4567890",
                    "authorName": "校园作者",
                    "novelClass": "纯爱",
                    "tags": "校园,青春,暗恋",
                    "totalClicks": "43.2万",
                    "totalFavorites": "18.7万",
                    "commentCount": "2345",
                    "chapterCount": "67"
                },
                {
                    "novelId": "6001235",
                    "novelName": "都市情缘",
                    "authorId": "5678901",
                    "authorName": "都市情感",
                    "novelClass": "纯爱",
                    "tags": "都市,职场,治愈",
                    "totalClicks": "38.9万",
                    "totalFavorites": "16.2万",
                    "commentCount": "1987",
                    "chapterCount": "89"
                }
            ]
        }
    }


@pytest.fixture
def invalid_api_response_data() -> Dict[str, Any]:
    """无效的API响应数据"""
    return {
        "code": "500",
        "msg": "服务器内部错误",
        "error": "数据库连接失败"
    }


@pytest.fixture
def empty_api_response_data() -> Dict[str, Any]:
    """空的API响应数据"""
    return {
        "code": "200",
        "msg": "success",
        "data": {
            "list": [],
            "total": 0,
            "page": 1,
            "pageSize": 50
        }
    }


@pytest.fixture
def book_url_test_cases() -> list:
    """书籍URL解析测试用例"""
    return [
        ("https://app-cdn.jjwxc.com/androidapi/novelbasicinfo?novelId=123456", "123456"),
        ("https://my.jjwxc.net/onebook.php?novelid=789012", "789012"),
        ("https://www.jjwxc.net/book/345678/", "345678"),
        ("https://m.jjwxc.net/book/567890", "567890"),
        ("https://www.jjwxc.net/onebook.php?novelid=234567&page=1", "234567"),
        ("https://invalid-url.com/book/abc", None),  # 无效URL
        ("https://example.com/other/path", None)     # 无法匹配的URL
    ]


@pytest.fixture
def numeric_field_test_cases() -> list:
    """数值字段解析测试用例"""
    return [
        ("123", 123),
        ("1,234", 1234),
        ("1万", 10000),
        ("1.5万", 15000),
        ("2.34万", 23400),
        ("5千", 5000),
        ("10.5千", 10500),
        ("1,234.5万", 12345000),
        ("abc", 0),      # 无效值
        ("", 0),         # 空字符串
        (None, 0)        # None值
    ]


@pytest.fixture
def mock_http_client(mocker):
    """模拟的HTTP客户端"""
    client = mocker.AsyncMock()
    client.get = mocker.AsyncMock()
    client.post = mocker.AsyncMock()
    client.close = mocker.AsyncMock()
    return client


@pytest.fixture
def mock_data_parser(mocker):
    """模拟的数据解析器"""
    parser = mocker.Mock()
    parser.parse_jiazi_data = mocker.Mock()
    parser.parse_page_data = mocker.Mock()
    return parser


@pytest.fixture(scope="session")
def test_urls_for_integration():
    """用于集成测试的真实URL（需要网络连接）"""
    return {
        "jiazi_url": "https://app-cdn.jjwxc.com/bookstore/favObservationByDate?day=today&use_cdn=1&version=19",
        "yq_url": "https://app-cdn.jjwxc.com/bookstore/getFullPageV1?channel=yq&version=20",
        "ca_url": "https://app-cdn.jjwxc.com/bookstore/getFullPageV1?channel=noyq&version=20",
        "novel_info_url": "https://app-cdn.jjwxc.com/androidapi/novelbasicinfo?novelId={}"
    }


@pytest.fixture
def enable_real_network_tests():
    """控制是否启用真实网络测试的标记"""
    # 检查环境变量或配置来决定是否启用真实网络测试
    import os
    return os.getenv("ENABLE_REAL_NETWORK_TESTS", "false").lower() == "true"


# 标记用于区分不同类型的测试
pytest.mark.unit = pytest.mark.unit if hasattr(pytest.mark, 'unit') else pytest.mark.skip
pytest.mark.integration = pytest.mark.integration if hasattr(pytest.mark, 'integration') else pytest.mark.skip
pytest.mark.network = pytest.mark.network if hasattr(pytest.mark, 'network') else pytest.mark.skip


def create_temp_urls_config(config_data: Dict[str, Any], temp_dir: str) -> str:
    """创建临时的URL配置文件"""
    config_file = os.path.join(temp_dir, "urls.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)
    return config_file


# 测试数据常量
TEST_BOOK_IDS = [
    "5485513",  # 真实存在的书籍ID（用于集成测试）
    "5423891",
    "5567234"
]

TEST_AUTHOR_IDS = [
    "8895234",
    "7728945", 
    "9123456"
]

# 测试用的默认请求头
TEST_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
                 "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# 爬虫统计测试数据
CRAWLER_STATS_TEST_DATA = {
    "success_scenario": {
        "successful_requests": 10,
        "failed_requests": 2,
        "books_crawled": 150,
        "errors": ["连接超时", "解析失败"]
    },
    "failure_scenario": {
        "successful_requests": 3,
        "failed_requests": 7,
        "books_crawled": 45,
        "errors": ["网络错误"] * 10
    }
}