"""
爬虫模块测试配置和数据
"""
import pytest
import json
from typing import Dict, List, Any


@pytest.fixture
def mock_urls_config() -> Dict[str, Any]:
    """模拟URL配置数据"""
    return {
        "global": {
            "params": {
                "channelId": "test_channel",
                "size": "20"
            },
            "templates": {
                "page_rank": "https://api.example.com/page?channelId={channelId}&size={size}",
                "novel_detail": "https://api.example.com/novel/{novel_id}?channelId={channelId}"
            }
        },
        "crawl_tasks": [
            {
                "id": "test_task_1",
                "template": "page_rank",
                "params": {
                    "channelId": "romance"
                }
            },
            {
                "id": "jiazi",
                "template": "page_rank",
                "params": {
                    "channelId": "jiazi"
                }
            }
        ]
    }


@pytest.fixture
def mock_page_response() -> Dict[str, Any]:
    """模拟页面响应数据"""
    return {
        "content": {
            "data": [
                {
                    "rankid": 1001,
                    "channelName": "言情榜单",
                    "rank_group_type": "romance",
                    "data": [
                        {
                            "novelId": 12345,
                            "novelName": "测试小说1",
                            "novelClickCount": 1000,
                            "novelFavoriteCount": 500
                        },
                        {
                            "novelId": 12346,
                            "novelName": "测试小说2",
                            "novelClickCount": 2000,
                            "novelFavoriteCount": 800
                        }
                    ]
                }
            ]
        }
    }


@pytest.fixture
def mock_jiazi_response() -> Dict[str, Any]:
    """模拟夹子榜响应数据"""
    return {
        "list": [
            {
                "novelId": 11111,
                "novelName": "夹子榜小说1",
                "novelClickCount": 5000,
                "novelFavoriteCount": 2000
            },
            {
                "novelId": 11112,
                "novelName": "夹子榜小说2",
                "novelClickCount": 4000,
                "novelFavoriteCount": 1500
            }
        ]
    }


@pytest.fixture
def mock_book_detail_response() -> Dict[str, Any]:
    """模拟书籍详情响应数据"""
    return {
        "novelId": 12345,
        "novelName": "测试小说详情",
        "novip_clicks": 10000,
        "novelFavoriteCount": 5000,
        "CommentCount": 200,
        "nutritionNovel": 95
    }



@pytest.fixture
def real_parser():
    """真实解析器（用于某些测试）"""
    from app.crawl.parser import Parser
    return Parser()


@pytest.fixture
def expected_parsed_page_data() -> List[Dict]:
    """期望的页面解析结果"""
    return [
        {
            "rank_id": 1001,
            "rank_name": "言情榜单",
            "rank_group_type": "romance",
            "books": [
                {
                    "book_id": 12345,
                    "title": "测试小说1",
                    "position": 1,
                    "clicks": 1000,
                    "favorites": 500
                },
                {
                    "book_id": 12346,
                    "title": "测试小说2",
                    "position": 2,
                    "clicks": 2000,
                    "favorites": 800
                }
            ]
        }
    ]


@pytest.fixture
def expected_parsed_jiazi_data() -> List[Dict]:
    """期望的夹子榜解析结果"""
    return [
        {
            "rank_id": "jiazi",
            "rank_name": "夹子榜",
            "books": [
                {
                    "book_id": 11111,
                    "title": "夹子榜小说1",
                    "position": 1,
                    "clicks": 5000,
                    "favorites": 2000
                },
                {
                    "book_id": 11112,
                    "title": "夹子榜小说2",
                    "position": 2,
                    "clicks": 4000,
                    "favorites": 1500
                }
            ]
        }
    ]


@pytest.fixture
def expected_parsed_book_data() -> Dict[str, Any]:
    """期望的书籍详情解析结果"""
    return {
        "novel_id": 12345,
        "title": "测试小说详情",
        "clicks": 10000,
        "favorites": 5000,
        "comments": 200,
        "nutrition": 95
    }


@pytest.fixture
def mock_successful_crawl_result() -> Dict[str, Any]:
    """模拟成功的爬取结果"""
    return {
        "task_id": "test_task_1",
        "success": True,
        "url": "https://api.example.com/page?channelId=romance&size=20",
        "rankings": [
            {
                "rank_id": 1001,
                "rank_name": "言情榜单",
                "rank_group_type": "romance",
                "books": [
                    {
                        "book_id": 12345,
                        "title": "测试小说1",
                        "position": 1,
                        "clicks": 1000,
                        "favorites": 500
                    }
                ]
            }
        ],
        "books": [
            {
                "novel_id": 12345,
                "title": "测试小说详情",
                "clicks": 10000,
                "favorites": 5000,
                "comments": 200,
                "nutrition": 95
            }
        ],
        "books_crawled": 1,
        "stats": {
            "books_crawled": 1,
            "total_requests": 2,
            "start_time": 1234567890.0,
            "end_time": 1234567895.0
        },
        "timestamp": 1234567895.0
    }


@pytest.fixture
def mock_failed_crawl_result() -> Dict[str, Any]:
    """模拟失败的爬取结果"""
    return {
        "task_id": "invalid_task",
        "success": False,
        "error": "无法生成页面地址",
        "stats": {
            "books_crawled": 0,
            "total_requests": 0,
            "start_time": None,
            "end_time": None
        },
        "timestamp": 1234567890.0
    }


@pytest.fixture
def mock_crawl_config(mocker):
    """模拟爬取配置"""
    mock_config = mocker.MagicMock()
    mock_config.get_task_config.return_value = {"template": "page_rank", "params": {}}
    mock_config.build_url.return_value = "https://api.example.com/page"
    mock_config.templates = {"novel_detail": "https://api.example.com/novel/{novel_id}"}
    mock_config.params = {}
    return mock_config


@pytest.fixture 
def mock_http_client(mocker):
    """模拟HTTP客户端"""
    mock_client = mocker.MagicMock()
    mock_client.get = mocker.AsyncMock()
    mock_client.close = mocker.AsyncMock()
    return mock_client


@pytest.fixture
def mock_parser(mocker):
    """模拟解析器"""
    from app.crawl.parser import ParsedItem, DataType
    
    mock_parser = mocker.MagicMock()
    mock_parser.parse.return_value = [
        ParsedItem(DataType.RANKING, {
            "rank_id": 1001,
            "rank_name": "测试榜单",
            "books": [{"book_id": 12345, "title": "测试小说"}]
        })
    ]
    return mock_parser


@pytest.fixture
def mock_crawl_flow_dependencies(mocker, mock_crawl_config, mock_http_client, mock_parser):
    """模拟CrawlFlow的所有依赖项"""
    # Mock settings
    mock_settings = mocker.patch('app.crawl.crawl_flow.settings')
    mock_settings.crawler.request_delay = 0.1
    
    # Mock classes
    mocker.patch('app.crawl.crawl_flow.CrawlConfig', return_value=mock_crawl_config)
    mocker.patch('app.crawl.crawl_flow.HttpClient', return_value=mock_http_client)
    mocker.patch('app.crawl.crawl_flow.Parser', return_value=mock_parser)
    
    return {
        'config': mock_crawl_config,
        'client': mock_http_client, 
        'parser': mock_parser,
        'settings': mock_settings
    }


@pytest.fixture
def mock_file_operations(mocker):
    """模拟文件操作"""
    return {
        'open': mocker.patch("builtins.open"),
        'mock_open': mocker.mock_open
    }


@pytest.fixture
def mock_httpx_client(mocker):
    """模拟httpx.AsyncClient"""
    mock_client = mocker.MagicMock()
    mock_client.get = mocker.AsyncMock()
    mock_client.aclose = mocker.AsyncMock()
    
    # Mock类本身
    mocker.patch('httpx.AsyncClient', return_value=mock_client)
    
    return mock_client


@pytest.fixture
def mock_crawler_manager_dependencies(mocker):
    """模拟CrawlerManager的所有依赖项"""
    # Mock settings
    mock_settings = mocker.patch('app.crawl.manager.settings')
    mock_settings.crawler.request_delay = 1.5
    
    # Mock CrawlFlow
    mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
    mock_flow = mocker.AsyncMock()
    mock_flow_class.return_value = mock_flow
    
    # Mock CrawlConfig for manager tests
    mock_config_class = mocker.patch('app.crawl.base.CrawlConfig')
    mock_config = mocker.MagicMock()
    mock_config_class.return_value = mock_config
    
    return {
        'settings': mock_settings,
        'flow_class': mock_flow_class,
        'flow': mock_flow,
        'config_class': mock_config_class,
        'config': mock_config
    }