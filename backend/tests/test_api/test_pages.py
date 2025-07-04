"""
页面配置API测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json


class TestPagesAPI:
    """页面配置API测试类"""
    
    def test_get_pages_config(self, client: TestClient):
        """测试获取页面配置API"""
        response = client.get("/api/v1/pages")
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        assert isinstance(data["pages"], list)
    
    def test_get_page_config_detail(self, client: TestClient):
        """测试获取单个页面配置详情API"""
        page_id = "jiazi"
        response = client.get(f"/api/v1/pages/{page_id}")
        
        if response.status_code == 404:
            assert response.json()["detail"] == "Page not found"
        else:
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "name" in data
            assert "url" in data
            assert "type" in data
    
    def test_get_active_pages(self, client: TestClient):
        """测试获取活跃页面配置API"""
        response = client.get("/api/v1/pages/active")
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        assert isinstance(data["pages"], list)
    
    def test_get_pages_by_type(self, client: TestClient):
        """测试按类型获取页面配置API"""
        page_type = "ranking"
        response = client.get(f"/api/v1/pages/type/{page_type}")
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        assert isinstance(data["pages"], list)
    
    def test_get_crawl_config(self, client: TestClient):
        """测试获取爬虫配置API"""
        response = client.get("/api/v1/pages/crawl-config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert isinstance(data["config"], dict)
    
    def test_get_scheduler_config(self, client: TestClient):
        """测试获取调度器配置API"""
        response = client.get("/api/v1/pages/scheduler-config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert isinstance(data["config"], dict)
    
    def test_get_jiazi_config(self, client: TestClient):
        """测试获取夹子榜配置API"""
        response = client.get("/api/v1/pages/jiazi-config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert isinstance(data["config"], dict)
        
        # 检查夹子榜配置的必要字段
        config = data["config"]
        expected_fields = ["name", "url", "crawl_interval", "parser_type"]
        for field in expected_fields:
            assert field in config
    
    def test_get_category_configs(self, client: TestClient):
        """测试获取分类配置API"""
        response = client.get("/api/v1/pages/category-configs")
        assert response.status_code == 200
        data = response.json()
        assert "configs" in data
        assert isinstance(data["configs"], list)
    
    def test_get_system_config(self, client: TestClient):
        """测试获取系统配置API"""
        response = client.get("/api/v1/pages/system-config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert isinstance(data["config"], dict)
    
    def test_get_database_config(self, client: TestClient):
        """测试获取数据库配置API"""
        response = client.get("/api/v1/pages/db-config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert isinstance(data["config"], dict)
    
    def test_get_api_config(self, client: TestClient):
        """测试获取API配置API"""
        response = client.get("/api/v1/pages/api-config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert isinstance(data["config"], dict)
    
    def test_get_logging_config(self, client: TestClient):
        """测试获取日志配置API"""
        response = client.get("/api/v1/pages/logging-config")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert isinstance(data["config"], dict)
    
    def test_validate_page_config(self, client: TestClient):
        """测试验证页面配置API"""
        config_data = {
            "name": "测试页面",
            "url": "https://example.com",
            "type": "ranking",
            "crawl_interval": 3600
        }
        
        response = client.post("/api/v1/pages/validate", json=config_data)
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert isinstance(data["valid"], bool)
    
    def test_validate_invalid_page_config(self, client: TestClient):
        """测试验证无效页面配置API"""
        config_data = {
            "name": "",  # 空名称
            "url": "invalid-url",  # 无效URL
            "type": "unknown",  # 未知类型
            "crawl_interval": -1  # 无效间隔
        }
        
        response = client.post("/api/v1/pages/validate", json=config_data)
        assert response.status_code == 422  # 验证错误
    
    def test_get_page_not_found(self, client: TestClient):
        """测试获取不存在的页面配置"""
        response = client.get("/api/v1/pages/nonexistent_page")
        assert response.status_code == 404
        assert response.json()["detail"] == "Page not found"
    
    def test_get_default_configs(self, client: TestClient):
        """测试获取默认配置API"""
        response = client.get("/api/v1/pages/defaults")
        assert response.status_code == 200
        data = response.json()
        assert "defaults" in data
        assert isinstance(data["defaults"], dict)
    
    def test_get_config_schema(self, client: TestClient):
        """测试获取配置模式API"""
        response = client.get("/api/v1/pages/schema")
        assert response.status_code == 200
        data = response.json()
        assert "schema" in data
        assert isinstance(data["schema"], dict)
    
    def test_pages_response_format(self, client: TestClient):
        """测试页面配置响应格式"""
        response = client.get("/api/v1/pages")
        assert response.status_code == 200
        data = response.json()
        
        # 检查响应格式
        assert isinstance(data, dict)
        assert "pages" in data
        assert isinstance(data["pages"], list)
        
        # 检查页面配置数据格式
        if data["pages"]:
            page = data["pages"][0]
            required_fields = ["id", "name", "url", "type"]
            for field in required_fields:
                assert field in page
    
    def test_config_api_error_handling(self, client: TestClient):
        """测试配置API错误处理"""
        # 测试无效的页面类型
        response = client.get("/api/v1/pages/type/invalid_type")
        assert response.status_code == 200  # 应该返回空列表
        data = response.json()
        assert "pages" in data
        assert len(data["pages"]) == 0
        
        # 测试无效的配置验证
        response = client.post("/api/v1/pages/validate", json={})
        assert response.status_code == 422  # 验证错误 