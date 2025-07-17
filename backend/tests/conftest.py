"""
pytest配置文件 - 统一的测试fixtures和测试数据
"""
import pytest
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock

from app.api.crawl import router as crawl_router
from app.api.books import router as books_router
from app.api.rankings import router as rankings_router


# ==================== 基础Fixtures ====================

@pytest.fixture
def app():
    """创建FastAPI应用实例"""
    app = FastAPI()
    app.include_router(crawl_router, prefix="/api/v1/crawl")
    app.include_router(books_router, prefix="/api/v1/books")
    app.include_router(rankings_router, prefix="/api/v1/rankings")
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """模拟数据库会话"""
    return Mock()


# ==================== Mock数据 ====================

@pytest.fixture
def mock_scheduler_response():
    """模拟调度器响应数据"""
    return {
        "success": {
            "success": True,
            "message": "批量任务创建成功",
            "batch_id": "batch_20240101_120000",
            "task_ids": ["crawl_jiazi_batch_20240101_120000"],
            "total_pages": 1,
            "successful_tasks": 1
        },
        "failure": {
            "success": False,
            "message": "没有找到有效的页面ID",
            "batch_id": "batch_20240101_120000",
            "task_ids": []
        }
    }


@pytest.fixture
def mock_scheduler_status():
    """模拟调度器状态数据"""
    return {
        "status": "running",
        "job_count": 5,
        "running_jobs": 2,
        "paused_jobs": 3,
        "uptime": 3600.0
    }


@pytest.fixture
def mock_batch_status():
    """模拟批量任务状态数据"""
    return {
        "found": {
            "batch_id": "batch_20240101_120000",
            "status": "running",
            "total_jobs": 2,
            "running_jobs": 1,
            "completed_jobs": 1
        },
        "not_found": {
            "batch_id": "nonexistent_batch",
            "status": "not_found",
            "total_jobs": 0,
            "running_jobs": 0,
            "completed_jobs": 0
        }
    }


@pytest.fixture
def mock_jobs():
    """模拟任务列表数据"""
    return [
        type('MockJob', (), {
            'id': 'test_job_1',
            'name': 'test_job_1',
            'next_run_time': None,
            'trigger': 'interval',
            'args': [],
            'kwargs': {}
        })()
    ]


@pytest.fixture
def mock_batch_jobs():
    """模拟批量任务列表数据"""
    return [
        type('MockJob', (), {
            'id': 'crawl_jiazi_batch_20240101_120000',
            'next_run_time': None
        })(),
        type('MockJob', (), {
            'id': 'crawl_index_batch_20240101_120000',
            'next_run_time': datetime(2024, 1, 1, 12, 0, 0)
        })()
    ]


# ==================== 爬虫测试数据 ====================

@pytest.fixture
def sample_config_data():
    """样本配置数据"""
    return {
        "global": {
            "params": {
                "page": 1,
                "pageSize": 20
            },
            "templates": {
                "jiazi": "https://api.example.com/jiazi?page={page}",
                "category": "https://api.example.com/category/{category}?page={page}"
            }
        },
        "crawl_tasks": [
            {
                "id": "jiazi",
                "template": "jiazi",
                "params": {"page": 1},
                "category": "jiazi"
            },
            {
                "id": "index",
                "template": "category",
                "params": {"category": "index", "page": 1}
            },
            {
                "id": "yq", 
                "template": "category",
                "params": {"category": "yq", "page": 1}
            }
        ]
    }


@pytest.fixture
def mock_http_response():
    """模拟HTTP响应"""
    return {
        "success": {
            "status": "success",
            "data": []
        },
        "failure": {
            "status": "error",
            "message": "Request failed"
        }
    }


@pytest.fixture
def mock_crawl_result():
    """模拟爬取结果"""
    return {
        "success": {
            "success": True,
            "books_crawled": 25,
            "page_id": "test_page"
        },
        "failure": {
            "success": False,
            "error_message": "网络连接失败"
        }
    }


# ==================== 调度器测试数据 ====================

@pytest.fixture
def sample_job_config():
    """样本任务配置"""
    return {
        "job_id": "test_job",
        "trigger_type": "date",
        "handler_class": "CrawlJobHandler",
        "page_ids": ["test_page"],
        "enabled": True,
        "force": False
    }


@pytest.fixture
def sample_job_context():
    """样本任务上下文"""
    return {
        "job_id": "test_job",
        "job_name": "test_job",
        "trigger_time": datetime(2024, 1, 1, 12, 0, 0),
        "scheduled_time": datetime(2024, 1, 1, 12, 0, 0)
    }


@pytest.fixture
def sample_job_result():
    """样本任务结果"""
    return {
        "success": {
            "success": True,
            "message": "任务执行成功",
            "data": {"count": 5},
            "execution_time": 1.5
        },
        "failure": {
            "success": False,
            "message": "任务执行失败",
            "exception": "测试异常",
            "execution_time": 0.5
        }
    }


# ==================== 书籍API测试数据 ====================

@pytest.fixture
def mock_pagination_data():
    """模拟分页数据"""
    return {
        "books": [
            {
                "id": 1,
                "novel_id": 12345,
                "title": "测试小说1",
                "author_name": "作者1",
                "status": "连载中"
            },
            {
                "id": 2,
                "novel_id": 12346,
                "title": "测试小说2",
                "author_name": "作者2",
                "status": "完结"
            }
        ],
        "total": 2,
        "page": 1,
        "size": 20,
        "total_pages": 1
    }


@pytest.fixture
def mock_search_results():
    """模拟搜索结果"""
    return [
        {
            "id": 1,
            "novel_id": 12345,
            "title": "搜索结果1",
            "author_name": "作者1",
            "status": "连载中"
        },
        {
            "id": 2,
            "novel_id": 12346,
            "title": "搜索结果2",
            "author_name": "作者2",
            "status": "完结"
        }
    ]


@pytest.fixture
def mock_book_data():
    """模拟书籍数据"""
    return {
        "book": {
            "id": 1,
            "novel_id": 12345,
            "title": "测试小说",
            "author_name": "测试作者",
            "status": "连载中",
            "tags": "现代言情",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime(2024, 1, 15, 12, 0, 0)
        }
    }


@pytest.fixture
def mock_book_snapshot_data():
    """模拟书籍快照数据"""
    return {
        "latest_snapshot": {
            "id": 1,
            "novel_id": 12345,
            "clicks": 50000,
            "favorites": 1200,
            "comments": 800,
            "recommendations": 300,
            "word_count": 120000,
            "status": "连载中",
            "snapshot_time": datetime(2024, 1, 15, 12, 0, 0)
        },
        "trend_snapshots": [
            {
                "id": 1,
                "novel_id": 12345,
                "clicks": 48000,
                "favorites": 1150,
                "snapshot_time": datetime(2024, 1, 14, 12, 0, 0)
            },
            {
                "id": 2,
                "novel_id": 12345,
                "clicks": 50000,
                "favorites": 1200,
                "snapshot_time": datetime(2024, 1, 15, 12, 0, 0)
            }
        ],
        "aggregated_data": [
            {
                "period": "2024-01-15T12:00:00",
                "clicks": 50000,
                "favorites": 1200,
                "avg_clicks": 49000,
                "avg_favorites": 1175
            }
        ]
    }


@pytest.fixture
def mock_ranking_history_data():
    """模拟排名历史数据"""
    return [
        {
            "ranking_id": 1,
            "ranking_name": "测试榜单",
            "position": 5,
            "score": 95.5,
            "snapshot_time": datetime(2024, 1, 14, 12, 0, 0)
        },
        {
            "ranking_id": 1,
            "ranking_name": "测试榜单",
            "position": 3,
            "score": 97.2,
            "snapshot_time": datetime(2024, 1, 15, 12, 0, 0)
        }
    ]


# ==================== 通用测试常量 ====================

@pytest.fixture
def test_page_ids():
    """测试页面ID"""
    return {
        "valid": ["jiazi", "index", "yq"],
        "invalid": ["invalid", "nonexistent"],
        "special": ["all", "jiazi", "category"],
        "single": ["jiazi"],
        "multiple": ["jiazi", "index"]
    }


@pytest.fixture
def test_batch_ids():
    """测试批量任务ID"""
    return {
        "valid": "batch_20240101_120000",
        "invalid": "nonexistent_batch"
    }


@pytest.fixture
def api_endpoints():
    """API端点"""
    return {
        "crawl_all": "/api/v1/crawl/all",
        "crawl_pages": "/api/v1/crawl/pages",
        "crawl_single": "/api/v1/crawl/page/{page_id}",
        "scheduler_status": "/api/v1/crawl/status",
        "batch_status": "/api/v1/crawl/batch/{batch_id}/status"
    }