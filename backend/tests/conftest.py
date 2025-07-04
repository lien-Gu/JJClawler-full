"""
pytest配置文件 - 测试fixtures和数据库设置
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os

# 导入应用和数据库相关模块
from app.main import app
from app.database.connection import get_db, Base
from app.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    # 创建临时数据库文件
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    # 创建测试数据库引擎
    engine = create_engine(
        f"sqlite:///{temp_db.name}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # 创建表
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal
    
    # 清理
    os.unlink(temp_db.name)


@pytest.fixture
def client(test_db):
    """创建测试客户端"""
    def override_get_db():
        try:
            db = test_db()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_book_data():
    """示例书籍数据"""
    return {
        "novel_id": 12345,
        "title": "测试小说",
        "author": "测试作者",
        "status": "连载中",
        "tag": "现代言情",
        "length": 100000,
        "favorites": 1000,
        "total_clicks": 5000,
        "monthly_clicks": 500,
        "weekly_clicks": 100,
        "daily_clicks": 20,
        "total_comments": 200,
        "monthly_comments": 50,
        "weekly_comments": 10,
        "daily_comments": 2,
        "total_recs": 100,
        "monthly_recs": 25,
        "weekly_recs": 5,
        "daily_recs": 1,
        "total_words": 100000,
        "intro": "这是一本测试小说",
        "last_update": "2024-01-01 12:00:00"
    }


@pytest.fixture
def sample_ranking_data():
    """示例榜单数据"""
    return {
        "name": "夹子榜",
        "type": "jiazi",
        "url": "https://www.jjwxc.net/topten.php?orderstr=4",
        "description": "夹子榜单",
        "is_active": True,
        "crawl_interval": 3600,
        "last_crawl": None
    }


@pytest.fixture
def mock_http_response():
    """模拟HTTP响应"""
    return {
        "status_code": 200,
        "text": """
        <html>
        <body>
        <table>
        <tr>
            <td>测试小说</td>
            <td>测试作者</td>
            <td>1000</td>
        </tr>
        </table>
        </body>
        </html>
        """
    }


@pytest.fixture
def mock_task_data():
    """模拟任务数据"""
    return {
        "task_id": "test_task_001",
        "task_type": "crawl_jiazi",
        "status": "pending",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "result": None,
        "error": None
    }


# ==================== 调度模块测试数据 ====================

@pytest.fixture
def scheduler_config():
    """调度器配置数据"""
    return {
        "timezone": "Asia/Shanghai",
        "job_defaults": {
            "coalesce": False,
            "max_instances": 3,
            "misfire_grace_time": 30
        },
        "executors": {
            "default": {
                "type": "threadpool",
                "max_workers": 10
            }
        }
    }


@pytest.fixture
def sample_job_data():
    """示例定时任务数据"""
    return {
        "jiazi_crawl_job": {
            "id": "jiazi_crawl_job",
            "func": "crawl_jiazi_ranking",
            "trigger": "interval",
            "hours": 1,
            "name": "夹子榜爬取任务",
            "description": "每小时爬取夹子榜数据",
            "max_instances": 1,
            "coalesce": True,
            "misfire_grace_time": 300
        },
        "category_crawl_job": {
            "id": "category_crawl_job",
            "func": "crawl_category_rankings",
            "trigger": "interval",
            "hours": 6,
            "name": "分类榜爬取任务",
            "description": "每6小时爬取分类榜数据",
            "max_instances": 1,
            "coalesce": True,
            "misfire_grace_time": 600
        },
        "data_cleanup_job": {
            "id": "data_cleanup_job",
            "func": "cleanup_old_data",
            "trigger": "cron",
            "hour": 2,
            "minute": 0,
            "name": "数据清理任务",
            "description": "每天凌晨2点清理过期数据",
            "max_instances": 1,
            "coalesce": True,
            "misfire_grace_time": 3600
        }
    }


@pytest.fixture
def mock_scheduler_jobs():
    """模拟调度器任务列表"""
    return [
        {
            "id": "jiazi_crawl_job",
            "name": "夹子榜爬取任务",
            "func": "crawl_jiazi_ranking",
            "trigger": "interval",
            "next_run_time": "2024-01-01T13:00:00+08:00",
            "state": "running"
        },
        {
            "id": "category_crawl_job", 
            "name": "分类榜爬取任务",
            "func": "crawl_category_rankings",
            "trigger": "interval",
            "next_run_time": "2024-01-01T18:00:00+08:00",
            "state": "paused"
        },
        {
            "id": "data_cleanup_job",
            "name": "数据清理任务",
            "func": "cleanup_old_data",
            "trigger": "cron",
            "next_run_time": "2024-01-02T02:00:00+08:00",
            "state": "running"
        }
    ]


@pytest.fixture
def mock_task_execution_data():
    """模拟任务执行数据"""
    return {
        "successful_execution": {
            "task_id": "jiazi_crawl_job_20240101_120000",
            "job_id": "jiazi_crawl_job",
            "start_time": "2024-01-01T12:00:00+08:00",
            "end_time": "2024-01-01T12:02:30+08:00",
            "status": "success",
            "result": {
                "books_processed": 50,
                "new_books": 5,
                "updated_books": 45,
                "execution_time": 150.5
            },
            "error": None
        },
        "failed_execution": {
            "task_id": "category_crawl_job_20240101_120000",
            "job_id": "category_crawl_job",
            "start_time": "2024-01-01T12:00:00+08:00",
            "end_time": "2024-01-01T12:01:15+08:00",
            "status": "failed",
            "result": None,
            "error": "Network timeout: Failed to connect to target server"
        },
        "running_execution": {
            "task_id": "data_cleanup_job_20240101_020000",
            "job_id": "data_cleanup_job",
            "start_time": "2024-01-01T02:00:00+08:00",
            "end_time": None,
            "status": "running",
            "result": None,
            "error": None
        }
    }


@pytest.fixture
def mock_scheduler_statistics():
    """模拟调度器统计数据"""
    return {
        "total_jobs": 3,
        "running_jobs": 2,
        "paused_jobs": 1,
        "failed_jobs": 0,
        "total_executions": 150,
        "successful_executions": 145,
        "failed_executions": 5,
        "average_execution_time": 125.8,
        "last_execution_time": "2024-01-01T12:30:00+08:00",
        "scheduler_uptime": 86400,  # 24小时，单位：秒
        "scheduler_status": "running"
    } 