"""
爬虫API测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from datetime import datetime

from app.main import app
from app.models.crawl import TaskStatus

client = TestClient(app)


class TestCrawlAPI:
    """爬虫API测试"""
    
    def test_crawl_all_pages_success(self):
        """测试触发全页面爬取成功"""
        # 发送请求
        response = client.post("/api/v1/crawl/all?force=false")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "已触发全页面爬取任务" in data["message"]
        assert len(data["data"]) == 1
        assert data["count"] == 1
        
        # 验证爬取结果
        result = data["data"][0]
        assert result["page_id"] == "all_pages"
        assert result["success"] is False  # 初始状态
        assert result["books_count"] == 0
        assert result["rankings_count"] == 0
        assert result["duration"] == 0.0
        assert result["error_message"] is None
        
    def test_crawl_all_pages_with_force(self):
        """测试强制触发全页面爬取"""
        # 发送请求
        response = client.post("/api/v1/crawl/all?force=true")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "已触发全页面爬取任务" in data["message"]
        
    def test_crawl_multiple_pages_success(self):
        """测试触发多页面爬取成功"""
        # 发送请求
        response = client.post(
            "/api/v1/crawl/page",
            json=["page1", "page2", "page3"]
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "已触发 3 个页面的爬取任务" in data["message"]
        assert len(data["data"]) == 3
        assert data["count"] == 3
        
        # 验证每个页面的结果
        for i, result in enumerate(data["data"]):
            assert result["page_id"] == f"page{i+1}"
            assert result["success"] is False  # 初始状态
            assert result["books_count"] == 0
            assert result["rankings_count"] == 0
            assert result["duration"] == 0.0
            assert result["error_message"] is None
            
    def test_crawl_multiple_pages_empty_list(self):
        """测试触发空页面列表爬取"""
        # 发送请求
        response = client.post(
            "/api/v1/crawl/page",
            json=[]
        )
        
        # 验证响应
        assert response.status_code == 400
        data = response.json()
        assert "页面ID列表不能为空" in data["detail"]
        
    def test_crawl_multiple_pages_with_force(self):
        """测试强制触发多页面爬取"""
        # 发送请求
        response = client.post(
            "/api/v1/crawl/page?force=true",
            json=["page1", "page2"]
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "已触发 2 个页面的爬取任务" in data["message"]
        
    def test_get_crawl_tasks_success(self):
        """测试获取爬虫任务列表成功"""
        # 先创建一些任务
        client.post("/api/v1/crawl/all")
        client.post("/api/v1/crawl/page", json=["page1"])
        
        # 发送请求
        response = client.get("/api/v1/crawl/tasks")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "获取任务列表成功" in data["message"]
        assert len(data["data"]) >= 2
        assert data["count"] >= 2
        
        # 验证任务数据结构
        for task in data["data"]:
            assert "task_id" in task
            assert "status" in task
            assert "message" in task
            assert "page_ids" in task
            assert "started_at" in task
            
    def test_get_crawl_tasks_with_status_filter(self):
        """测试按状态过滤爬虫任务"""
        # 发送请求
        response = client.get("/api/v1/crawl/tasks?status=pending")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证过滤结果
        for task in data["data"]:
            assert task["status"] == TaskStatus.PENDING
            
    def test_get_crawl_tasks_with_limit(self):
        """测试限制爬虫任务数量"""
        # 发送请求
        response = client.get("/api/v1/crawl/tasks?limit=5")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 5
        
    def test_get_crawl_task_detail_success(self):
        """测试获取爬虫任务详情成功"""
        # 先创建一个任务
        create_response = client.post("/api/v1/crawl/all")
        
        # 等待任务创建完成并获取任务ID
        tasks_response = client.get("/api/v1/crawl/tasks?limit=1")
        assert tasks_response.status_code == 200
        tasks_data = tasks_response.json()
        
        if tasks_data["data"]:
            task_id = tasks_data["data"][0]["task_id"]
            
            # 发送请求
            response = client.get(f"/api/v1/crawl/tasks/{task_id}")
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "获取任务详情成功" in data["message"]
            assert data["data"]["task_id"] == task_id
            
    def test_get_crawl_task_detail_not_found(self):
        """测试获取不存在的任务详情"""
        # 发送请求
        response = client.get("/api/v1/crawl/tasks/nonexistent_task")
        
        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert "任务不存在" in data["detail"]
        
    @patch('app.schedule.get_scheduler')
    def test_trigger_jiazi_crawl_success(self, mock_get_scheduler):
        """测试手动触发夹子榜爬取成功"""
        # 模拟调度器和任务
        mock_job = Mock()
        mock_job.id = "jiazi_crawl"
        
        mock_scheduler = Mock()
        mock_scheduler.is_running.return_value = True
        mock_scheduler.get_job.return_value = mock_job
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post("/api/v1/crawl/jiazi")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "已触发夹子榜爬取任务" in data["message"]
        
        # 验证任务数据
        task = data["data"]
        assert task["status"] == TaskStatus.PENDING
        assert "手动触发夹子榜爬取任务" in task["message"]
        assert task["page_ids"] == ["jiazi"]
        
    @patch('app.schedule.get_scheduler')
    def test_trigger_jiazi_crawl_scheduler_not_running(self, mock_get_scheduler):
        """测试调度器未运行时触发夹子榜爬取"""
        # 模拟调度器未运行
        mock_scheduler = Mock()
        mock_scheduler.is_running.return_value = False
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post("/api/v1/crawl/jiazi")
        
        # 验证响应
        assert response.status_code == 503
        data = response.json()
        assert "调度器未运行" in data["detail"]
        
    @patch('app.schedule.get_scheduler')
    def test_trigger_jiazi_crawl_job_not_found(self, mock_get_scheduler):
        """测试夹子榜任务不存在时触发爬取"""
        # 模拟调度器运行但任务不存在
        mock_scheduler = Mock()
        mock_scheduler.is_running.return_value = True
        mock_scheduler.get_job.return_value = None
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post("/api/v1/crawl/jiazi")
        
        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert "夹子榜爬取任务不存在" in data["detail"]
        
    @patch('app.schedule.get_scheduler')
    def test_trigger_jiazi_crawl_with_force(self, mock_get_scheduler):
        """测试强制触发夹子榜爬取"""
        # 模拟调度器和任务
        mock_job = Mock()
        mock_job.id = "jiazi_crawl"
        
        mock_scheduler = Mock()
        mock_scheduler.is_running.return_value = True
        mock_scheduler.get_job.return_value = mock_job
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post("/api/v1/crawl/jiazi?force=true")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "已触发夹子榜爬取任务" in data["message"]


class TestCrawlAPIIntegration:
    """爬虫API集成测试"""
    
    def test_crawl_api_routes_exist(self):
        """测试爬虫API路由存在"""
        # 测试全页面爬取接口
        response = client.post("/api/v1/crawl/all")
        assert response.status_code == 200
        
        # 测试指定页面爬取接口
        response = client.post("/api/v1/crawl/page", json=["page1"])
        assert response.status_code == 200
        
        # 测试任务列表接口
        response = client.get("/api/v1/crawl/tasks")
        assert response.status_code == 200
        
    def test_crawl_api_cors_headers(self):
        """测试爬虫API的CORS头"""
        response = client.options("/api/v1/crawl/all")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        
    def test_crawl_api_error_handling(self):
        """测试爬虫API错误处理"""
        # 测试空页面列表
        response = client.post("/api/v1/crawl/page", json=[])
        assert response.status_code == 400
        
        # 测试不存在的任务
        response = client.get("/api/v1/crawl/tasks/nonexistent")
        assert response.status_code == 404
        
    def test_crawl_task_lifecycle(self):
        """测试爬虫任务生命周期"""
        # 1. 创建任务
        create_response = client.post("/api/v1/crawl/all")
        assert create_response.status_code == 200
        
        # 2. 获取任务列表
        list_response = client.get("/api/v1/crawl/tasks")
        assert list_response.status_code == 200
        tasks_data = list_response.json()
        assert len(tasks_data["data"]) >= 1
        
        # 3. 获取任务详情
        if tasks_data["data"]:
            task_id = tasks_data["data"][0]["task_id"]
            detail_response = client.get(f"/api/v1/crawl/tasks/{task_id}")
            assert detail_response.status_code == 200
            
            detail_data = detail_response.json()
            assert detail_data["data"]["task_id"] == task_id
            
    def test_crawl_concurrent_requests(self):
        """测试并发爬取请求"""
        # 同时发送多个请求
        responses = []
        for i in range(3):
            response = client.post("/api/v1/crawl/page", json=[f"page{i}"])
            responses.append(response)
        
        # 验证所有请求都成功
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
    def test_crawl_task_storage(self):
        """测试爬虫任务存储"""
        # 创建任务
        create_response = client.post("/api/v1/crawl/all")
        assert create_response.status_code == 200
        
        # 验证任务被存储
        tasks_response = client.get("/api/v1/crawl/tasks")
        assert tasks_response.status_code == 200
        
        tasks_data = tasks_response.json()
        assert len(tasks_data["data"]) >= 1
        
        # 验证任务数据完整性
        task = tasks_data["data"][0]
        required_fields = [
            "task_id", "status", "message", "page_ids", 
            "started_at", "completed_at", "duration"
        ]
        for field in required_fields:
            assert field in task
            
    def test_crawl_task_status_transitions(self):
        """测试爬虫任务状态转换"""
        # 创建任务
        create_response = client.post("/api/v1/crawl/all")
        assert create_response.status_code == 200
        
        # 初始状态应该是PENDING
        tasks_response = client.get("/api/v1/crawl/tasks?limit=1")
        assert tasks_response.status_code == 200
        
        tasks_data = tasks_response.json()
        if tasks_data["data"]:
            task = tasks_data["data"][0]
            assert task["status"] == TaskStatus.PENDING
            
        # 等待一段时间后检查状态变化
        import time
        time.sleep(2)
        
        # 再次检查状态（模拟异步任务可能已完成）
        tasks_response = client.get("/api/v1/crawl/tasks?limit=1")
        assert tasks_response.status_code == 200