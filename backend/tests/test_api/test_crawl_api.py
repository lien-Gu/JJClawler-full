"""
爬虫API模块测试文件
测试api.crawl模块的关键功能
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.api.crawl import router
from app.schedule.scheduler import TaskScheduler
from app.models.schedule import JobConfigModel, TriggerType, JobHandlerType


@pytest.fixture
def client():
    """创建测试客户端"""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_scheduler():
    """创建模拟的调度器"""
    scheduler = Mock(spec=TaskScheduler)
    scheduler.add_batch_jobs = AsyncMock()
    scheduler.get_status = Mock()
    scheduler.get_batch_status = Mock()
    scheduler.get_batch_jobs = Mock()
    scheduler.get_jobs = Mock()
    return scheduler


class TestCrawlAllPages:
    """测试爬取所有页面接口"""
    
    @patch('app.api.crawl.get_scheduler')
    @pytest.mark.asyncio
    async def test_crawl_all_pages_success(self, mock_get_scheduler, mock_scheduler):
        """测试成功爬取所有页面"""
        # 设置模拟返回值
        mock_get_scheduler.return_value = mock_scheduler
        mock_scheduler.add_batch_jobs.return_value = {
            "success": True,
            "message": "批量任务创建成功",
            "batch_id": "batch_20240101_120000",
            "task_ids": ["crawl_jiazi_batch_20240101_120000"],
            "total_pages": 1,
            "successful_tasks": 1
        }
        
        # 创建测试客户端
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # 发送请求
        response = client.post("/all?force=false")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "batch_id" in data["data"]
        assert "task_ids" in data["data"]
        
        # 验证调度器调用
        mock_scheduler.add_batch_jobs.assert_called_once_with(
            page_ids=["all"],
            force=False
        )
    
    @patch('app.api.crawl.get_scheduler')
    @pytest.mark.asyncio
    async def test_crawl_all_pages_failure(self, mock_get_scheduler, mock_scheduler):
        """测试爬取所有页面失败"""
        # 设置模拟返回值
        mock_get_scheduler.return_value = mock_scheduler
        mock_scheduler.add_batch_jobs.return_value = {
            "success": False,
            "message": "没有找到有效的页面ID",
            "batch_id": "batch_20240101_120000",
            "task_ids": []
        }
        
        # 创建测试客户端
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # 发送请求
        response = client.post("/all")
        
        # 验证响应
        assert response.status_code == 500


class TestCrawlSpecificPages:
    """测试爬取指定页面接口"""
    
    @patch('app.api.crawl.get_scheduler')
    @pytest.mark.asyncio
    async def test_crawl_specific_pages_success(self, mock_get_scheduler, mock_scheduler):
        """测试成功爬取指定页面"""
        # 设置模拟返回值
        mock_get_scheduler.return_value = mock_scheduler
        mock_scheduler.add_batch_jobs.return_value = {
            "success": True,
            "message": "批量任务创建成功",
            "batch_id": "batch_20240101_120000",
            "task_ids": ["crawl_jiazi_batch_20240101_120000", "crawl_index_batch_20240101_120000"],
            "total_pages": 2,
            "successful_tasks": 2
        }
        
        # 创建测试客户端
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # 发送请求
        response = client.post("/pages", json=["jiazi", "index"])
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_pages"] == 2
        assert data["data"]["successful_tasks"] == 2
        
        # 验证调度器调用
        mock_scheduler.add_batch_jobs.assert_called_once_with(
            page_ids=["jiazi", "index"],
            force=False
        )
    
    @patch('app.api.crawl.get_scheduler')
    @pytest.mark.asyncio
    async def test_crawl_specific_pages_empty_list(self, mock_get_scheduler, mock_scheduler):
        """测试空页面列表"""
        # 创建测试客户端
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # 发送请求
        response = client.post("/pages", json=[])
        
        # 验证响应
        assert response.status_code == 400


class TestCrawlSinglePage:
    """测试爬取单个页面接口"""
    
    @patch('app.api.crawl.get_scheduler')
    @pytest.mark.asyncio
    async def test_crawl_single_page_success(self, mock_get_scheduler, mock_scheduler):
        """测试成功爬取单个页面"""
        # 设置模拟返回值
        mock_get_scheduler.return_value = mock_scheduler
        mock_scheduler.add_batch_jobs.return_value = {
            "success": True,
            "message": "批量任务创建成功",
            "batch_id": "batch_20240101_120000",
            "task_ids": ["crawl_jiazi_batch_20240101_120000"],
            "total_pages": 1,
            "successful_tasks": 1
        }
        
        # 创建测试客户端
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # 发送请求
        response = client.post("/page/jiazi?force=true")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["page_id"] == "jiazi"
        
        # 验证调度器调用
        mock_scheduler.add_batch_jobs.assert_called_once_with(
            page_ids=["jiazi"],
            force=True
        )


class TestSchedulerStatus:
    """测试调度器状态接口"""
    
    @patch('app.api.crawl.get_scheduler')
    def test_get_scheduler_status_success(self, mock_get_scheduler, mock_scheduler):
        """测试成功获取调度器状态"""
        # 设置模拟返回值
        mock_get_scheduler.return_value = mock_scheduler
        mock_scheduler.get_status.return_value = {
            "status": "running",
            "job_count": 5,
            "running_jobs": 2,
            "paused_jobs": 3,
            "uptime": 3600.0
        }
        mock_scheduler.get_jobs.return_value = [
            Mock(id="test_job_1", name="test_job_1", next_run_time=None, 
                 trigger="interval", args=[], kwargs={})
        ]
        
        # 创建测试客户端
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # 发送请求
        response = client.get("/status")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["scheduler_status"]["status"] == "running"
        assert data["data"]["job_count"] == 1
        assert len(data["data"]["jobs"]) == 1
        
        # 验证调度器调用
        mock_scheduler.get_status.assert_called_once()
        mock_scheduler.get_jobs.assert_called_once()


class TestBatchStatus:
    """测试批量任务状态接口"""
    
    @patch('app.api.crawl.get_scheduler')
    def test_get_batch_status_success(self, mock_get_scheduler, mock_scheduler):
        """测试成功获取批量任务状态"""
        # 设置模拟返回值
        mock_get_scheduler.return_value = mock_scheduler
        mock_scheduler.get_batch_status.return_value = {
            "batch_id": "batch_20240101_120000",
            "status": "running",
            "total_jobs": 2,
            "running_jobs": 1,
            "completed_jobs": 1
        }
        mock_scheduler.get_batch_jobs.return_value = [
            Mock(id="crawl_jiazi_batch_20240101_120000", next_run_time=None),
            Mock(id="crawl_index_batch_20240101_120000", next_run_time="2024-01-01T12:00:00")
        ]
        
        # 创建测试客户端
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # 发送请求
        response = client.get("/batch/batch_20240101_120000/status")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["batch_id"] == "batch_20240101_120000"
        assert data["data"]["status"] == "running"
        assert data["data"]["total_jobs"] == 2
        assert len(data["data"]["jobs"]) == 2
        
        # 验证调度器调用
        mock_scheduler.get_batch_status.assert_called_once_with("batch_20240101_120000")
        mock_scheduler.get_batch_jobs.assert_called_once_with("batch_20240101_120000")
    
    @patch('app.api.crawl.get_scheduler')
    def test_get_batch_status_not_found(self, mock_get_scheduler, mock_scheduler):
        """测试批量任务不存在"""
        # 设置模拟返回值
        mock_get_scheduler.return_value = mock_scheduler
        mock_scheduler.get_batch_status.return_value = {
            "batch_id": "nonexistent_batch",
            "status": "not_found",
            "total_jobs": 0,
            "running_jobs": 0,
            "completed_jobs": 0
        }
        mock_scheduler.get_batch_jobs.return_value = []
        
        # 创建测试客户端
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # 发送请求
        response = client.get("/batch/nonexistent_batch/status")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "not_found"
        assert data["data"]["total_jobs"] == 0
        assert len(data["data"]["jobs"]) == 0


class TestErrorHandling:
    """测试错误处理"""
    
    @patch('app.api.crawl.get_scheduler')
    @pytest.mark.asyncio
    async def test_scheduler_exception_handling(self, mock_get_scheduler, mock_scheduler):
        """测试调度器异常处理"""
        # 设置模拟异常
        mock_get_scheduler.return_value = mock_scheduler
        mock_scheduler.add_batch_jobs.side_effect = Exception("调度器异常")
        
        # 创建测试客户端
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # 发送请求
        response = client.post("/all")
        
        # 验证响应
        assert response.status_code == 500
        data = response.json()
        assert "触发爬取失败" in data["detail"]
    
    @patch('app.api.crawl.get_scheduler')
    def test_status_exception_handling(self, mock_get_scheduler, mock_scheduler):
        """测试状态查询异常处理"""
        # 设置模拟异常
        mock_get_scheduler.return_value = mock_scheduler
        mock_scheduler.get_status.side_effect = Exception("状态查询异常")
        
        # 创建测试客户端
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # 发送请求
        response = client.get("/status")
        
        # 验证响应
        assert response.status_code == 500
        data = response.json()
        assert "获取调度器状态失败" in data["detail"]


# 运行测试的示例
if __name__ == "__main__":
    pytest.main([__file__, "-v"])