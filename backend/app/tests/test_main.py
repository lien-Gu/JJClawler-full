"""
主应用测试
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["project"] == "JJCrawler3"
    assert data["version"] == "0.1.0"
    assert "message" in data
    assert data["docs"] == "/docs"
    assert data["api"] == "/api/v1"


def test_health_check(client: TestClient):
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "jjcrawler3"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_docs_available_in_debug(client: TestClient):
    """测试调试模式下文档可用"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema(client: TestClient):
    """测试OpenAPI schema生成"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert schema["info"]["title"] == "JJCrawler3"
    assert schema["info"]["version"] == "0.1.0"