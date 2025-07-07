"""
爬虫模块测试配置和数据
"""
import pytest
import json
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock


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
def mock_http_client():
    """模拟HTTP客户端"""
    client = AsyncMock()
    client.get = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_crawl_config(mock_urls_config):
    """模拟爬取配置"""
    config = MagicMock()
    config.params = mock_urls_config["global"]["params"]
    config.templates = mock_urls_config["global"]["templates"]
    config._config = mock_urls_config
    
    def get_task_config(task_id: str):
        for task in mock_urls_config["crawl_tasks"]:
            if task["id"] == task_id:
                return task
        return None
    
    def get_all_tasks():
        return mock_urls_config["crawl_tasks"]
    
    def build_url(task_config: Dict):
        template_name = task_config["template"]
        template = mock_urls_config["global"]["templates"][template_name]
        params = {**mock_urls_config["global"]["params"], **task_config.get("params", {})}
        return template.format(**params)
    
    config.get_task_config = get_task_config
    config.get_all_tasks = get_all_tasks
    config.build_url = build_url
    
    return config


@pytest.fixture
def mock_parser():
    """模拟解析器"""
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