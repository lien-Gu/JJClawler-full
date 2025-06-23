"""
Pytest配置文件

提供测试所需的fixtures和配置
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """测试客户端fixture"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_data():
    """示例测试数据"""
    return {
        "book": {
            "book_id": "12345",
            "title": "测试小说",
            "author_name": "测试作者",
            "novel_class": "原创-言情-架空历史",
        },
        "ranking": {
            "ranking_id": "jiazi",
            "name": "夹子",
            "channel": "favObservation",
        },
    }