"""
爬虫管理API测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime


class TestCrawlAPI:
    """爬虫管理API测试类"""
    
    def test_get_crawl_status(self, client: TestClient):
        """测试获取爬虫状态API"""
        response = client.get("/api/v1/crawl/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "active_tasks" in data
        assert "completed_tasks" in data
        assert "failed_tasks" in data
    
    def test_get_crawl_tasks(self, client: TestClient):
        """测试获取爬虫任务列表API"""
        response = client.get("/api/v1/crawl/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
    
    def test_get_crawl_task_detail(self, client: TestClient):
        """测试获取爬虫任务详情API"""
        task_id = "test_task_001"
        response = client.get(f"/api/v1/crawl/tasks/{task_id}")
        
        if response.status_code == 404:
            assert response.json()["detail"] == "Task not found"
        else:
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert "task_type" in data
            assert "status" in data
            assert "created_at" in data
    
    @patch('app.scheduler.task_scheduler.TaskScheduler.trigger_crawl')
    def test_trigger_jiazi_crawl(self, mock_trigger, client: TestClient):
        """测试触发夹子榜爬取API"""
        mock_trigger.return_value = {"task_id": "test_task_001", "status": "pending"}
        
        response = client.post("/api/v1/crawl/jiazi")
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "pending"
    
    @patch('app.scheduler.task_scheduler.TaskScheduler.trigger_crawl')
    def test_trigger_category_crawl(self, mock_trigger, client: TestClient):
        """测试触发分类榜爬取API"""
        mock_trigger.return_value = {"task_id": "test_task_002", "status": "pending"}
        
        response = client.post("/api/v1/crawl/category/现代言情")
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "pending"
    
    @patch('app.scheduler.task_scheduler.TaskScheduler.trigger_crawl')
    def test_trigger_full_crawl(self, mock_trigger, client: TestClient):
        """测试触发全量爬取API"""
        mock_trigger.return_value = {"task_id": "test_task_003", "status": "pending"}
        
        response = client.post("/api/v1/crawl/full")
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "pending"
    
    @patch('app.scheduler.task_scheduler.TaskScheduler.cancel_task')
    def test_cancel_crawl_task(self, mock_cancel, client: TestClient):
        """测试取消爬虫任务API"""
        task_id = "test_task_001"
        mock_cancel.return_value = True
        
        response = client.delete(f"/api/v1/crawl/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cancelled" in data["message"].lower()
    
    def test_get_crawl_history(self, client: TestClient):
        """测试获取爬虫历史API"""
        response = client.get("/api/v1/crawl/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert isinstance(data["history"], list)
    
    def test_get_crawl_history_with_filters(self, client: TestClient):
        """测试带过滤条件的爬虫历史API"""
        response = client.get(
            "/api/v1/crawl/history"
            "?task_type=jiazi&status=completed&start_date=2024-01-01&end_date=2024-01-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert isinstance(data["history"], list)
    
    def test_get_crawl_statistics(self, client: TestClient):
        """测试获取爬虫统计API"""
        response = client.get("/api/v1/crawl/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data
        assert isinstance(data["statistics"], dict)
    
    def test_get_crawl_logs(self, client: TestClient):
        """测试获取爬虫日志API"""
        task_id = "test_task_001"
        response = client.get(f"/api/v1/crawl/tasks/{task_id}/logs")
        
        if response.status_code == 404:
            assert response.json()["detail"] == "Task not found"
        else:
            assert response.status_code == 200
            data = response.json()
            assert "logs" in data
            assert isinstance(data["logs"], list)
    
    @patch('app.scheduler.task_scheduler.TaskScheduler.pause_scheduler')
    def test_pause_scheduler(self, mock_pause, client: TestClient):
        """测试暂停调度器API"""
        mock_pause.return_value = True
        
        response = client.post("/api/v1/crawl/scheduler/pause")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "paused" in data["message"].lower()
    
    @patch('app.scheduler.task_scheduler.TaskScheduler.resume_scheduler')
    def test_resume_scheduler(self, mock_resume, client: TestClient):
        """测试恢复调度器API"""
        mock_resume.return_value = True
        
        response = client.post("/api/v1/crawl/scheduler/resume")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "resumed" in data["message"].lower()
    
    def test_get_scheduler_status(self, client: TestClient):
        """测试获取调度器状态API"""
        response = client.get("/api/v1/crawl/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "running" in data
        assert "jobs" in data
    
    def test_get_active_jobs(self, client: TestClient):
        """测试获取活跃任务API"""
        response = client.get("/api/v1/crawl/jobs/active")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)
    
    def test_get_job_detail(self, client: TestClient):
        """测试获取任务详情API"""
        job_id = "jiazi_crawl_job"
        response = client.get(f"/api/v1/crawl/jobs/{job_id}")
        
        if response.status_code == 404:
            assert response.json()["detail"] == "Job not found"
        else:
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert "next_run_time" in data
            assert "trigger" in data
    
    def test_crawl_task_not_found(self, client: TestClient):
        """测试获取不存在的爬虫任务"""
        response = client.get("/api/v1/crawl/tasks/nonexistent_task")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
    
    def test_crawl_api_error_handling(self, client: TestClient):
        """测试爬虫API错误处理"""
        # 测试无效的任务ID
        response = client.delete("/api/v1/crawl/tasks/")
        assert response.status_code == 404
        
        # 测试无效的日期格式
        response = client.get("/api/v1/crawl/history?start_date=invalid")
        assert response.status_code == 422  # 验证错误
    
    def test_crawl_response_format(self, client: TestClient):
        """测试爬虫API响应格式"""
        response = client.get("/api/v1/crawl/status")
        assert response.status_code == 200
        data = response.json()
        
        # 检查响应格式
        assert isinstance(data, dict)
        assert "status" in data
        assert "active_tasks" in data
        assert "completed_tasks" in data
        assert "failed_tasks" in data
        
        # 检查数据类型
        assert isinstance(data["active_tasks"], int)
        assert isinstance(data["completed_tasks"], int)
        assert isinstance(data["failed_tasks"], int) 