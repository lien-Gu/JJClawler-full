"""
调度API测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app
from app.schedule import TaskScheduler
from app.models.schedule import JobStatus, TriggerType, JobHandlerType

client = TestClient(app)


class TestScheduleAPI:
    """调度API测试"""
    
    @patch('app.schedule.get_scheduler')
    def test_get_scheduler_status_success(self, mock_get_scheduler):
        """测试获取调度器状态成功"""
        # 模拟调度器
        mock_scheduler = Mock()
        mock_scheduler.get_status.return_value = {
            "status": "running",
            "timezone": "Asia/Shanghai",
            "job_count": 5,
            "running_jobs": 3,
            "paused_jobs": 2,
            "state": "running",
            "uptime": 3600.0
        }
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.get("/api/v1/schedule/status")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取调度器状态成功"
        assert data["data"]["status"] == "running"
        assert data["data"]["job_count"] == 5
        assert data["data"]["running_jobs"] == 3
        assert data["data"]["paused_jobs"] == 2
        assert data["data"]["uptime"] == 3600.0
        
    @patch('app.schedule.get_scheduler')
    def test_get_scheduler_status_exception(self, mock_get_scheduler):
        """测试获取调度器状态异常"""
        # 模拟调度器异常
        mock_scheduler = Mock()
        mock_scheduler.get_status.side_effect = Exception("调度器错误")
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.get("/api/v1/schedule/status")
        
        # 验证响应
        assert response.status_code == 500
        data = response.json()
        assert "获取调度器状态失败" in data["detail"]
        
    @patch('app.schedule.get_scheduler')
    def test_get_scheduler_metrics_success(self, mock_get_scheduler):
        """测试获取调度器指标成功"""
        # 模拟调度器
        mock_scheduler = Mock()
        mock_scheduler.get_metrics.return_value = {
            "total_jobs": 5,
            "running_jobs": 3,
            "paused_jobs": 2,
            "scheduler_status": "running",
            "uptime": 3600.0,
            "success_rate": 0.95,
            "average_execution_time": 2.5
        }
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.get("/api/v1/schedule/metrics")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取调度器指标成功"
        assert data["data"]["total_jobs"] == 5
        assert data["data"]["success_rate"] == 0.95
        assert data["data"]["average_execution_time"] == 2.5
        
    @patch('app.schedule.get_scheduler')
    def test_start_scheduler_success(self, mock_get_scheduler):
        """测试启动调度器成功"""
        # 模拟调度器
        mock_scheduler = Mock()
        mock_scheduler.is_running.return_value = False
        mock_scheduler.start = AsyncMock()
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post("/api/v1/schedule/start")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "调度器启动成功"
        
    @patch('app.schedule.get_scheduler')
    def test_start_scheduler_already_running(self, mock_get_scheduler):
        """测试启动已运行的调度器"""
        # 模拟调度器已运行
        mock_scheduler = Mock()
        mock_scheduler.is_running.return_value = True
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post("/api/v1/schedule/start")
        
        # 验证响应
        assert response.status_code == 400
        data = response.json()
        assert "调度器已经在运行中" in data["detail"]
        
    @patch('app.schedule.get_scheduler')
    def test_stop_scheduler_success(self, mock_get_scheduler):
        """测试停止调度器成功"""
        # 模拟调度器
        mock_scheduler = Mock()
        mock_scheduler.is_running.return_value = True
        mock_scheduler.shutdown = AsyncMock()
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post("/api/v1/schedule/stop")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "调度器停止成功"
        
    @patch('app.schedule.get_scheduler')
    def test_stop_scheduler_not_running(self, mock_get_scheduler):
        """测试停止未运行的调度器"""
        # 模拟调度器未运行
        mock_scheduler = Mock()
        mock_scheduler.is_running.return_value = False
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post("/api/v1/schedule/stop")
        
        # 验证响应
        assert response.status_code == 400
        data = response.json()
        assert "调度器未运行" in data["detail"]
        
    @patch('app.schedule.get_scheduler')
    def test_get_jobs_success(self, mock_get_scheduler):
        """测试获取任务列表成功"""
        # 模拟任务
        mock_job1 = Mock()
        mock_job1.id = "jiazi_crawl"
        mock_job1.name = "夹子榜爬取任务"
        mock_job1.next_run_time = "2024-01-01T10:00:00"
        mock_job1.max_instances = 1
        mock_job1.trigger = Mock()
        mock_job1.trigger.interval = 3600
        mock_job1.func = "CrawlJobHandler"
        
        mock_job2 = Mock()
        mock_job2.id = "category_crawl"
        mock_job2.name = "分类榜单爬取任务"
        mock_job2.next_run_time = None  # 暂停的任务
        mock_job2.max_instances = 2
        mock_job2.trigger = Mock()
        mock_job2.func = "CrawlJobHandler"
        
        mock_scheduler = Mock()
        mock_scheduler.get_jobs.return_value = [mock_job1, mock_job2]
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.get("/api/v1/schedule/jobs")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取任务列表成功"
        assert len(data["data"]) == 2
        assert data["total"] == 2
        
        # 验证任务数据
        job1_data = data["data"][0]
        assert job1_data["id"] == "jiazi_crawl"
        assert job1_data["name"] == "夹子榜爬取任务"
        assert job1_data["status"] == "running"
        assert job1_data["max_instances"] == 1
        
        job2_data = data["data"][1]
        assert job2_data["id"] == "category_crawl"
        assert job2_data["name"] == "分类榜单爬取任务"
        assert job2_data["status"] == "paused"
        assert job2_data["max_instances"] == 2
        
    @patch('app.schedule.get_scheduler')
    def test_get_job_detail_success(self, mock_get_scheduler):
        """测试获取任务详情成功"""
        # 模拟任务
        mock_job = Mock()
        mock_job.id = "jiazi_crawl"
        mock_job.name = "夹子榜爬取任务"
        mock_job.next_run_time = "2024-01-01T10:00:00"
        mock_job.max_instances = 1
        mock_job.trigger = Mock()
        mock_job.trigger.interval = 3600
        mock_job.func = "CrawlJobHandler"
        
        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = mock_job
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.get("/api/v1/schedule/jobs/jiazi_crawl")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取任务详情成功"
        assert data["data"]["id"] == "jiazi_crawl"
        assert data["data"]["name"] == "夹子榜爬取任务"
        assert data["data"]["status"] == "running"
        assert data["data"]["max_instances"] == 1
        
    @patch('app.schedule.get_scheduler')
    def test_get_job_detail_not_found(self, mock_get_scheduler):
        """测试获取不存在的任务详情"""
        # 模拟任务不存在
        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = None
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.get("/api/v1/schedule/jobs/nonexistent")
        
        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert "任务不存在" in data["detail"]
        
    @patch('app.schedule.get_scheduler')
    def test_delete_job_success(self, mock_get_scheduler):
        """测试删除任务成功"""
        # 模拟任务存在
        mock_job = Mock()
        mock_job.id = "test_job"
        
        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = mock_job
        mock_scheduler.remove_job.return_value = True
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.delete("/api/v1/schedule/jobs/test_job")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "任务 test_job 删除成功" in data["message"]
        
    @patch('app.schedule.get_scheduler')
    def test_delete_job_not_found(self, mock_get_scheduler):
        """测试删除不存在的任务"""
        # 模拟任务不存在
        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = None
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.delete("/api/v1/schedule/jobs/nonexistent")
        
        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert "任务不存在" in data["detail"]
        
    @patch('app.schedule.get_scheduler')
    def test_job_action_pause_success(self, mock_get_scheduler):
        """测试暂停任务成功"""
        # 模拟任务存在
        mock_job = Mock()
        mock_job.id = "test_job"
        
        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = mock_job
        mock_scheduler.pause_job.return_value = True
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post(
            "/api/v1/schedule/jobs/test_job/action",
            json={"action": "pause"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "任务 test_job 暂停成功" in data["message"]
        
    @patch('app.schedule.get_scheduler')
    def test_job_action_resume_success(self, mock_get_scheduler):
        """测试恢复任务成功"""
        # 模拟任务存在
        mock_job = Mock()
        mock_job.id = "test_job"
        
        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = mock_job
        mock_scheduler.resume_job.return_value = True
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post(
            "/api/v1/schedule/jobs/test_job/action",
            json={"action": "resume"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "任务 test_job 恢复成功" in data["message"]
        
    @patch('app.schedule.get_scheduler')
    def test_job_action_run_success(self, mock_get_scheduler):
        """测试立即执行任务成功"""
        # 模拟任务存在
        mock_job = Mock()
        mock_job.id = "test_job"
        
        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = mock_job
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post(
            "/api/v1/schedule/jobs/test_job/action",
            json={"action": "run"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "任务 test_job 触发执行成功" in data["message"]
        
    @patch('app.schedule.get_scheduler')
    def test_job_action_invalid_action(self, mock_get_scheduler):
        """测试无效的任务操作"""
        # 模拟任务存在
        mock_job = Mock()
        mock_job.id = "test_job"
        
        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = mock_job
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post(
            "/api/v1/schedule/jobs/test_job/action",
            json={"action": "invalid"}
        )
        
        # 验证响应
        assert response.status_code == 400
        data = response.json()
        assert "不支持的操作" in data["detail"]
        
    @patch('app.schedule.get_scheduler')
    def test_job_action_job_not_found(self, mock_get_scheduler):
        """测试对不存在的任务执行操作"""
        # 模拟任务不存在
        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = None
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.post(
            "/api/v1/schedule/jobs/nonexistent/action",
            json={"action": "pause"}
        )
        
        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert "任务不存在" in data["detail"]
        
    @patch('app.schedule.get_scheduler')
    def test_get_job_history_success(self, mock_get_scheduler):
        """测试获取任务执行历史成功"""
        # 模拟调度器
        mock_scheduler = Mock()
        mock_get_scheduler.return_value = mock_scheduler
        
        # 发送请求
        response = client.get("/api/v1/schedule/jobs/test_job/history")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取任务执行历史成功"
        assert data["data"] == []
        assert data["total"] == 0


class TestScheduleAPIIntegration:
    """调度API集成测试"""
    
    def test_schedule_api_routes_exist(self):
        """测试调度API路由存在"""
        # 测试状态接口
        response = client.get("/api/v1/schedule/status")
        assert response.status_code in [200, 500]  # 可能因为调度器未启动而返回500
        
        # 测试指标接口
        response = client.get("/api/v1/schedule/metrics")
        assert response.status_code in [200, 500]
        
        # 测试任务列表接口
        response = client.get("/api/v1/schedule/jobs")
        assert response.status_code in [200, 500]
        
    def test_schedule_api_cors_headers(self):
        """测试调度API的CORS头"""
        response = client.options("/api/v1/schedule/status")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        
    def test_schedule_api_error_handling(self):
        """测试调度API错误处理"""
        # 测试不存在的任务
        response = client.get("/api/v1/schedule/jobs/nonexistent")
        assert response.status_code in [404, 500]
        
        # 测试无效的操作
        response = client.post(
            "/api/v1/schedule/jobs/test/action",
            json={"action": "invalid"}
        )
        assert response.status_code in [400, 404, 500]