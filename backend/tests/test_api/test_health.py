"""
健康检查API测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json


class TestHealthAPI:
    """健康检查API测试类"""
    
    def test_health_check(self, client: TestClient):
        """测试健康检查API"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_health_check_detailed(self, client: TestClient):
        """测试详细健康检查API"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert isinstance(data["services"], dict)
    
    def test_database_health(self, client: TestClient):
        """测试数据库健康检查API"""
        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "db" in data
        assert "connection" in data["db"]
    
    def test_scheduler_health(self, client: TestClient):
        """测试调度器健康检查API"""
        response = client.get("/health/scheduler")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "scheduler" in data
        assert "running" in data["scheduler"]
    
    def test_crawler_health(self, client: TestClient):
        """测试爬虫健康检查API"""
        response = client.get("/health/crawler")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "crawler" in data
        assert "active_tasks" in data["crawler"]
    
    def test_system_info(self, client: TestClient):
        """测试系统信息API"""
        response = client.get("/health/system")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "system" in data
        assert "cpu" in data["system"]
        assert "memory" in data["system"]
        assert "disk" in data["system"]
    
    def test_version_info(self, client: TestClient):
        """测试版本信息API"""
        response = client.get("/health/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "build_time" in data
        assert "git_hash" in data
    
    def test_metrics(self, client: TestClient):
        """测试指标API"""
        response = client.get("/health/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert isinstance(data["metrics"], dict)
    
    def test_ready_check(self, client: TestClient):
        """测试就绪检查API"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert isinstance(data["ready"], bool)
    
    def test_live_check(self, client: TestClient):
        """测试存活检查API"""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert "alive" in data
        assert isinstance(data["alive"], bool)
        assert data["alive"] == True
    
    def test_health_response_format(self, client: TestClient):
        """测试健康检查响应格式"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        # 检查响应格式
        assert isinstance(data, dict)
        assert "status" in data
        assert "timestamp" in data
        
        # 检查时间戳格式
        import datetime
        timestamp = data["timestamp"]
        datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    
    @patch('app.db.connection.engine.connect')
    def test_database_health_failure(self, mock_connect, client: TestClient):
        """测试数据库健康检查失败"""
        mock_connect.side_effect = Exception("Database connection failed")
        
        response = client.get("/health/db")
        assert response.status_code == 503  # 服务不可用
        data = response.json()
        assert "status" in data
        assert data["status"] == "unhealthy"
    
    @patch('app.scheduler.task_scheduler.TaskScheduler.is_running')
    def test_scheduler_health_failure(self, mock_running, client: TestClient):
        """测试调度器健康检查失败"""
        mock_running.return_value = False
        
        response = client.get("/health/scheduler")
        assert response.status_code == 503  # 服务不可用
        data = response.json()
        assert "status" in data
        assert data["status"] == "unhealthy" 