"""
Schedule API模块测试

测试app/api/schedule.py的API接口功能，使用mock的调度器避免实际任务执行
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schedule import JobBasic, JobStatus, JobType


class TestScheduleAPI:
    """Schedule API测试类"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def mock_scheduler(self):
        """Mock调度器"""
        from unittest.mock import AsyncMock
        mock_scheduler = MagicMock()
        mock_scheduler.add_schedule_job = AsyncMock()
        mock_scheduler.get_job_info = MagicMock()
        mock_scheduler.get_scheduler_info = MagicMock()
        return mock_scheduler

    def test_create_crawl_job_success(self, client, mock_scheduler):
        """测试创建爬取任务 - 成功场景"""
        # 准备mock返回值 - 创建真实的Job对象
        from app.models.schedule import Job
        from apscheduler.triggers.date import DateTrigger
        from datetime import datetime
        
        expected_job = Job(
            job_id="CRAWL_20250803_123456",
            job_type=JobType.CRAWL,
            trigger=DateTrigger(run_date=datetime.now()),
            desc="手动创建的爬取任务",
            page_ids=["jiazi"]
        )
        
        mock_scheduler.add_schedule_job.return_value = expected_job

        # Mock调度器
        with patch('app.api.schedule.scheduler', mock_scheduler):
            # 发送请求
            response = client.post(
                "/api/v1/schedule/task/create",
                params={
                    "page_ids": ["jiazi"],
                    "run_time": "2025-08-03T10:00:00"
                }
            )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "成功创建爬取任务"
        assert data["data"]["job_id"] == "CRAWL_20250803_123456"
        
        # 验证调度器被正确调用
        mock_scheduler.add_schedule_job.assert_called_once()

    def test_create_crawl_job_multiple_pages(self, client, mock_scheduler):
        """测试创建多页面爬取任务"""
        # 准备mock返回值 - 创建真实的Job对象
        from app.models.schedule import Job
        from apscheduler.triggers.date import DateTrigger
        from datetime import datetime
        
        expected_job = Job(
            job_id="CRAWL_20250803_123456",
            job_type=JobType.CRAWL,
            trigger=DateTrigger(run_date=datetime.now()),
            desc="手动创建的爬取任务",
            page_ids=["jiazi", "category"]
        )
        
        mock_scheduler.add_schedule_job.return_value = expected_job

        # Mock调度器
        with patch('app.api.schedule.scheduler', mock_scheduler):
            # 发送请求
            response = client.post(
                "/api/v1/schedule/task/create",
                params={
                    "page_ids": ["jiazi", "category"],
                }
            )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # JobBasic模型中没有page_ids字段，这是正确的行为
        assert data["data"]["job_id"] == "CRAWL_20250803_123456"
        assert data["data"]["job_type"] == "crawl"
        assert data["data"]["desc"] == "手动创建的爬取任务"

    def test_create_crawl_job_failure(self, client, mock_scheduler):
        """测试创建爬取任务 - 失败场景"""
        # 模拟调度器抛出异常
        mock_scheduler.add_schedule_job.side_effect = Exception("调度器错误")

        # Mock调度器
        with patch('app.api.schedule.scheduler', mock_scheduler):
            # 发送请求
            response = client.post(
                "/api/v1/schedule/task/create",
                params={
                    "page_ids": ["invalid_page"],
                    "run_time": "2025-08-03T10:00:00"
                }
            )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "任务创建失败" in data["message"]
        assert data["data"] is None

    def test_create_crawl_job_default_time(self, client, mock_scheduler):
        """测试创建爬取任务 - 使用默认时间"""
        from app.models.schedule import Job
        from apscheduler.triggers.date import DateTrigger
        from datetime import datetime
        
        expected_job = Job(
            job_id="CRAWL_20250803_123456",
            job_type=JobType.CRAWL,
            trigger=DateTrigger(run_date=datetime.now()),
            desc="手动创建的爬取任务",
            page_ids=["jiazi"]
        )
        
        mock_scheduler.add_schedule_job.return_value = expected_job

        with patch('app.api.schedule.scheduler', mock_scheduler):
            # 不提供run_time参数
            response = client.post(
                "/api/v1/schedule/task/create",
                params={"page_ids": ["jiazi"]}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_scheduler.add_schedule_job.assert_called_once()

    def test_get_task_status_success(self, client, mock_scheduler):
        """测试获取任务状态 - 成功场景"""
        # 准备mock返回值
        expected_job = JobBasic(
            job_id="CRAWL_20250803_123456",
            job_type=JobType.CRAWL,
            desc="测试任务"
        )
        mock_scheduler.get_job_info.return_value = expected_job

        # Mock调度器
        with patch('app.api.schedule.scheduler', mock_scheduler):
            # 发送请求
            response = client.get("/api/v1/schedule/status/CRAWL_20250803_123456")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取任务状态成功"
        assert data["data"]["job_id"] == "CRAWL_20250803_123456"
        
        # 验证调度器被正确调用
        mock_scheduler.get_job_info.assert_called_once_with("CRAWL_20250803_123456")

    def test_get_task_status_not_found(self, client, mock_scheduler):
        """测试获取任务状态 - 任务不存在"""
        # 模拟任务不存在
        mock_scheduler.get_job_info.return_value = None

        # Mock调度器
        with patch('app.api.schedule.scheduler', mock_scheduler):
            # 发送请求
            response = client.get("/api/v1/schedule/status/nonexistent_job")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "未找到任务" in data["message"]
        assert data["data"] is None

    def test_get_task_status_failure(self, client, mock_scheduler):
        """测试获取任务状态 - 系统异常"""
        # 模拟系统异常
        mock_scheduler.get_job_info.side_effect = Exception("数据库连接失败")

        with patch('app.api.schedule.scheduler', mock_scheduler):
            response = client.get("/api/v1/schedule/status/test_job")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "获取任务状态失败" in data["message"]

    def test_get_scheduler_status_success(self, client, mock_scheduler):
        """测试获取调度器状态 - 成功场景"""
        from app.models.schedule import SchedulerInfo
        
        # 准备mock返回值
        expected_status = SchedulerInfo(
            status="running",
            jobs=[
                {"id": "job1", "next_run_time": "2025-08-03T11:00:00", "trigger": "date[2025-08-03T11:00:00]", "status": "pending"}
            ],
            run_time="1天2小时30分钟15秒"
        )
        mock_scheduler.get_scheduler_info.return_value = expected_status

        # Mock调度器
        with patch('app.api.schedule.scheduler', mock_scheduler):
            # 发送请求
            response = client.get("/api/v1/schedule/status")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取调度器状态成功"
        assert data["data"]["status"] == "running"
        assert data["data"]["run_time"] == "1天2小时30分钟15秒"
        assert len(data["data"]["jobs"]) == 1

    def test_get_scheduler_status_failure(self, client, mock_scheduler):
        """测试获取调度器状态 - 失败场景"""
        # 模拟调度器抛出异常
        mock_scheduler.get_scheduler_info.side_effect = Exception("调度器连接失败")

        # Mock调度器
        with patch('app.api.schedule.scheduler', mock_scheduler):
            # 发送请求
            response = client.get("/api/v1/schedule/status")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "获取调度器状态失败" in data["message"]
        assert data["data"] is None

    def test_job_basic_model_conversion(self, client, mock_scheduler):
        """测试JobBasic模型转换"""
        from app.models.schedule import Job
        from apscheduler.triggers.date import DateTrigger
        
        # 创建完整的Job对象
        complete_job = Job(
            job_id="CRAWL_20250803_123456",
            job_type=JobType.CRAWL,
            trigger=DateTrigger(run_date=datetime.now()),
            desc="测试任务",
            page_ids=["jiazi"]
        )
        
        mock_scheduler.add_schedule_job.return_value = complete_job

        with patch('app.api.schedule.scheduler', mock_scheduler):
            response = client.post(
                "/api/v1/schedule/task/create",
                params={"page_ids": ["jiazi"]}
            )

        # 验证JobBasic转换正确
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 验证只包含JobBasic字段，不包含trigger等复杂字段
        assert "job_id" in data["data"]
        assert "job_type" in data["data"]
        assert "desc" in data["data"]
        assert "trigger" not in data["data"]  # trigger不应该在JobBasic中

    def test_api_path_consistency(self, client):
        """测试API路径一致性"""
        # 测试所有API路径都以/api/v1/schedule开头
        
        # 创建任务API
        response = client.post("/api/v1/schedule/task/create", params={"page_ids": ["jiazi"]})
        # 不验证具体逻辑，只验证路径存在
        assert response.status_code in [200, 422]  # 200成功或422参数错误都表明路径存在
        
        # 获取任务状态API  
        response = client.get("/api/v1/schedule/status/test_job")
        assert response.status_code in [200, 422]
        
        # 获取调度器状态API
        response = client.get("/api/v1/schedule/status")
        assert response.status_code in [200, 422]