"""
Schedule API模块测试

测试schedule API的各项功能，使用mock的调度器避免实际任务执行
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schedule import JobHandlerType, JobInfo, JobStatus, TriggerType


class TestScheduleAPI:
    """Schedule API测试类"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def mock_scheduler(self, monkeypatch):
        """Mock调度器"""
        mock_scheduler = MagicMock()
        mock_scheduler.add_job = AsyncMock()
        mock_scheduler.get_job_info = AsyncMock()
        mock_scheduler.get_scheduler_info = AsyncMock()
        
        # 导入并替换调度器
        from app.api import schedule
        monkeypatch.setattr(schedule, "scheduler", mock_scheduler)
        
        return mock_scheduler

    def test_create_crawl_job_success(self, client, mock_scheduler):
        """测试创建爬取任务 - 成功场景"""
        # 准备mock返回值
        expected_job = JobInfo(
            job_id="test_job_123",
            trigger_type=TriggerType.DATE,
            trigger_time={"run_time": datetime.now()},
            handler=JobHandlerType.CRAWL,
            page_ids=["jiazi"],
            status=(JobStatus.PENDING, "任务创建成功"),
            desc="手动创建的爬取任务 - 页面: jiazi"
        )
        mock_scheduler.add_job.return_value = expected_job

        # 发送请求
        response = client.post(
            "/schedule/task/create",
            params={
                "page_ids": ["jiazi"],
                "run_time": "2025-07-29T10:00:00"
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "任务创建成功"
        assert data["data"]["job_id"] == "test_job_123"
        assert data["data"]["handler"] == "CrawlJobHandler"
        
        # 验证调度器被正确调用
        mock_scheduler.add_job.assert_called_once()

    def test_create_crawl_job_failure(self, client, mock_scheduler):
        """测试创建爬取任务 - 失败场景"""
        # 模拟调度器抛出异常
        mock_scheduler.add_job.side_effect = Exception("调度器错误")

        # 发送请求
        response = client.post(
            "/schedule/task/create",
            params={
                "page_ids": ["invalid_page"],
                "run_time": "2025-07-29T10:00:00"
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "任务创建失败" in data["message"]
        assert data["data"] is None

    def test_get_task_status_success(self, client, mock_scheduler):
        """测试获取任务状态 - 成功场景"""
        # 准备mock返回值
        expected_job = JobInfo(
            job_id="test_job_456",
            trigger_type=TriggerType.DATE,
            trigger_time={"run_time": datetime.now()},
            handler=JobHandlerType.CRAWL,
            status=(JobStatus.RUNNING, "任务执行中"),
            desc="测试任务"
        )
        mock_scheduler.get_job_info.return_value = expected_job

        # 发送请求
        response = client.get("/schedule/task/test_job_456")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取任务状态成功"
        assert data["data"]["job_id"] == "test_job_456"
        assert data["data"]["status"][0] == "running"
        
        # 验证调度器被正确调用
        mock_scheduler.get_job_info.assert_called_once_with("test_job_456")

    def test_get_task_status_not_found(self, client, mock_scheduler):
        """测试获取任务状态 - 任务不存在"""
        # 模拟任务不存在
        mock_scheduler.get_job_info.return_value = None

        # 发送请求
        response = client.get("/schedule/task/nonexistent_job")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "未找到任务" in data["message"]
        assert data["data"] is None

    def test_get_scheduler_status_success(self, client, mock_scheduler):
        """测试获取调度器状态 - 成功场景"""
        # 准备mock返回值
        expected_status = {
            "status": "running",
            "job_wait": [
                {"id": "job1", "next_run_time": "2025-07-29T11:00:00", "trigger": "date"}
            ],
            "job_running": [],
            "run_time": "1天2小时30分钟15秒"
        }
        mock_scheduler.get_scheduler_info.return_value = expected_status

        # 发送请求
        response = client.get("/schedule/status")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取调度器状态成功"
        assert data["data"]["status"] == "running"
        assert data["data"]["run_time"] == "1天2小时30分钟15秒"
        assert len(data["data"]["job_wait"]) == 1

    def test_get_scheduler_status_failure(self, client, mock_scheduler):
        """测试获取调度器状态 - 失败场景"""
        # 模拟调度器抛出异常
        mock_scheduler.get_scheduler_info.side_effect = Exception("调度器连接失败")

        # 发送请求
        response = client.get("/schedule/status")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "获取调度器状态失败" in data["message"]
        assert data["data"] is None

    def test_create_crawl_job_with_multiple_pages(self, client, mock_scheduler):
        """测试创建多页面爬取任务"""
        # 准备mock返回值
        expected_job = JobInfo(
            job_id="batch_job_789",
            trigger_type=TriggerType.DATE,
            trigger_time={"run_time": datetime.now()},
            handler=JobHandlerType.CRAWL,
            page_ids=["jiazi", "category"],
            status=(JobStatus.PENDING, "批次任务创建成功"),
            desc="手动创建的爬取任务 - 页面: jiazi, category"
        )
        mock_scheduler.add_job.return_value = expected_job

        # 发送请求
        response = client.post(
            "/schedule/task/create",
            params={
                "page_ids": ["jiazi", "category"],
                "run_time": "2025-07-29T10:00:00"
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["page_ids"]) == 2
        assert "jiazi" in data["data"]["page_ids"]
        assert "category" in data["data"]["page_ids"]