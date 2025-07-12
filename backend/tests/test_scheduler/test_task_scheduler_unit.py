"""
调度模块单元测试 - 测试重构后的调度模块核心功能
"""
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.schedule import TaskScheduler, get_scheduler, BaseJobHandler
from app.models.schedule import JobContextModel, JobResultModel
from app.models.schedule import JobStatus, TriggerType, JobHandlerType, PREDEFINED_JOB_CONFIGS


class TestTaskScheduler:
    """TaskScheduler核心功能测试"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 清除全局单例
        import app.schedule
        app.schedule._scheduler = None
        
        # 创建新的调度器实例
        self.scheduler = TaskScheduler()
        
    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        scheduler = TaskScheduler()
        
        # 验证初始状态
        assert scheduler.scheduler is None
        assert scheduler.start_time is None
        assert len(scheduler.job_handlers) == 3
        assert JobHandlerType.CRAWL in scheduler.job_handlers
        assert JobHandlerType.MAINTENANCE in scheduler.job_handlers
        assert JobHandlerType.REPORT in scheduler.job_handlers
        
    def test_scheduler_singleton(self):
        """测试调度器单例模式"""
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()
        
        assert scheduler1 is scheduler2
        
    @patch('app.schedule.TaskScheduler._create_scheduler')
    async def test_start_scheduler(self, mock_create_scheduler):
        """测试调度器启动"""
        mock_apscheduler = Mock()
        mock_create_scheduler.return_value = mock_apscheduler
        
        # 启动调度器
        await self.scheduler.start()
        
        # 验证状态
        assert self.scheduler.scheduler is not None
        assert self.scheduler.start_time is not None
        mock_apscheduler.start.assert_called_once()
        
    async def test_start_scheduler_already_running(self):
        """测试重复启动调度器"""
        self.scheduler.scheduler = Mock()
        
        # 尝试重复启动
        await self.scheduler.start()
        
        # 验证不会创建新的调度器
        assert self.scheduler.scheduler is not None
        
    @patch('app.schedule.TaskScheduler._create_scheduler')
    async def test_shutdown_scheduler(self, mock_create_scheduler):
        """测试调度器关闭"""
        mock_apscheduler = Mock()
        mock_create_scheduler.return_value = mock_apscheduler
        
        # 先启动再关闭
        await self.scheduler.start()
        await self.scheduler.shutdown()
        
        # 验证状态
        assert self.scheduler.scheduler is None
        assert self.scheduler.start_time is None
        mock_apscheduler.shutdown.assert_called_once_with(wait=True)
        
    async def test_shutdown_not_started(self):
        """测试关闭未启动的调度器"""
        # 关闭未启动的调度器不应该报错
        await self.scheduler.shutdown()
        
        assert self.scheduler.scheduler is None
        
    def test_is_running_true(self):
        """测试调度器运行状态检查 - 运行中"""
        mock_scheduler = Mock()
        mock_scheduler.running = True
        self.scheduler.scheduler = mock_scheduler
        
        assert self.scheduler.is_running() is True
        
    def test_is_running_false(self):
        """测试调度器运行状态检查 - 未运行"""
        assert self.scheduler.is_running() is False
        
        mock_scheduler = Mock()
        mock_scheduler.running = False
        self.scheduler.scheduler = mock_scheduler
        
        assert self.scheduler.is_running() is False
        
    def test_get_status_stopped(self):
        """测试获取停止状态的调度器状态"""
        status = self.scheduler.get_status()
        
        assert status["status"] == "stopped"
        assert status["job_count"] == 0
        assert status["running_jobs"] == 0
        assert status["paused_jobs"] == 0
        assert status["uptime"] == 0.0
        
    def test_get_status_running(self):
        """测试获取运行状态的调度器状态"""
        # 模拟运行中的调度器
        mock_scheduler = Mock()
        mock_scheduler.running = True
        mock_scheduler.timezone = "Asia/Shanghai"
        mock_scheduler.state = "running"
        
        # 模拟任务
        mock_jobs = [Mock(), Mock(), Mock()]
        mock_jobs[0].next_run_time = datetime.now()
        mock_jobs[1].next_run_time = datetime.now()
        mock_jobs[2].next_run_time = None  # 暂停的任务
        
        self.scheduler.scheduler = mock_scheduler
        self.scheduler.start_time = datetime.now()
        
        with patch.object(self.scheduler, 'get_jobs', return_value=mock_jobs):
            status = self.scheduler.get_status()
            
            assert status["status"] == "running"
            assert status["job_count"] == 3
            assert status["running_jobs"] == 2
            assert status["paused_jobs"] == 1
            assert status["uptime"] > 0
            
    def test_get_metrics(self):
        """测试获取调度器指标"""
        with patch.object(self.scheduler, 'get_status') as mock_get_status:
            mock_get_status.return_value = {
                "job_count": 5,
                "running_jobs": 3,
                "paused_jobs": 2,
                "status": "running",
                "uptime": 100.0
            }
            
            metrics = self.scheduler.get_metrics()
            
            assert metrics["total_jobs"] == 5
            assert metrics["running_jobs"] == 3
            assert metrics["paused_jobs"] == 2
            assert metrics["scheduler_status"] == "running"
            assert metrics["uptime"] == 100.0
            assert "success_rate" in metrics
            assert "average_execution_time" in metrics
            
    def test_get_job_data_by_type(self):
        """测试根据任务类型获取任务数据"""
        from app.models.schedule import IntervalJobConfigModel
        
        # 测试各种任务类型
        jiazi_config = IntervalJobConfigModel(
            job_id="jiazi_crawl",
            handler_class=JobHandlerType.CRAWL,
            interval_seconds=3600
        )
        
        data = self.scheduler._get_job_data_by_type(jiazi_config)
        assert data["type"] == "jiazi"
        
        category_config = IntervalJobConfigModel(
            job_id="category_crawl",
            handler_class=JobHandlerType.CRAWL,
            interval_seconds=3600
        )
        
        data = self.scheduler._get_job_data_by_type(category_config)
        assert data["type"] == "category"
        
        # 测试未知任务类型
        unknown_config = IntervalJobConfigModel(
            job_id="unknown_task",
            handler_class=JobHandlerType.CRAWL,
            interval_seconds=3600
        )
        
        data = self.scheduler._get_job_data_by_type(unknown_config)
        assert data == {}


class TestJobHandlers:
    """任务处理器测试"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 创建一个具体的处理器实例用于测试
        class TestHandler(BaseJobHandler):
            async def execute(self, context):
                return JobResultModel.success_result("测试成功")
        
        self.handler = TestHandler()
        
    def test_job_context_creation(self):
        """测试任务上下文创建"""
        context = JobContextModel(
            job_id="test_job",
            job_name="测试任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"key": "value"}
        )
        
        assert context.job_id == "test_job"
        assert context.job_name == "测试任务"
        assert context.job_data == {"key": "value"}
        assert context.retry_count == 0
        assert context.max_retries == 3
        
    def test_job_context_to_model(self):
        """测试任务上下文转换为模型"""
        context = JobContextModel(
            job_id="test_job",
            job_name="测试任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now()
        )
        
        model = context.to_model()
        assert model.job_id == "test_job"
        assert model.job_name == "测试任务"
        
    def test_job_result_success(self):
        """测试成功结果创建"""
        result = JobResultModel.success_result("任务完成", {"count": 10})
        
        assert result.success is True
        assert result.message == "任务完成"
        assert result.data == {"count": 10}
        assert result.exception is None
        
    def test_job_result_error(self):
        """测试错误结果创建"""
        exception = Exception("测试错误")
        result = JobResultModel.error_result("任务失败", exception)
        
        assert result.success is False
        assert result.message == "任务失败"
        assert result.exception == exception
        assert result.data is None
        
    def test_job_result_to_model(self):
        """测试任务结果转换为模型"""
        result = JobResultModel.success_result("任务完成", {"count": 10})
        
        model = result.to_model()
        assert model.success is True
        assert model.message == "任务完成"
        assert model.data == {"count": 10}
        
    def test_should_retry_retryable_exception(self):
        """测试可重试异常"""
        connection_error = ConnectionError("连接失败")
        assert self.handler.should_retry(connection_error, 0) is True
        
        timeout_error = TimeoutError("超时")
        assert self.handler.should_retry(timeout_error, 0) is True
        
    def test_should_retry_non_retryable_exception(self):
        """测试不可重试异常"""
        value_error = ValueError("值错误")
        assert self.handler.should_retry(value_error, 0) is False
        
        assert self.handler.should_retry(None, 0) is False
        
    def test_get_retry_delay(self):
        """测试重试延迟计算"""
        # 测试指数退避
        assert self.handler.get_retry_delay(1) == 1
        assert self.handler.get_retry_delay(2) == 2
        assert self.handler.get_retry_delay(3) == 4
        assert self.handler.get_retry_delay(4) == 8
        
        # 测试最大延迟限制
        assert self.handler.get_retry_delay(10) == 60
        
    async def test_execute_with_retry_success(self):
        """测试带重试的执行 - 成功情况"""
        # 创建模拟的处理器
        handler = Mock(spec=BaseJobHandler)
        handler.logger = Mock()
        handler.should_retry = Mock(return_value=False)
        handler.get_retry_delay = Mock(return_value=1)
        handler.on_success = AsyncMock()
        handler.on_failure = AsyncMock()
        handler.on_retry = AsyncMock()
        
        # 模拟成功执行
        success_result = JobResultModel.success_result("执行成功")
        handler.execute = AsyncMock(return_value=success_result)
        
        # 执行测试
        context = JobContextModel(
            job_id="test_job",
            job_name="测试任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now()
        )
        
        result = await BaseJobHandler.execute_with_retry(handler, context)
        
        # 验证结果
        assert result.success is True
        assert result.message == "执行成功"
        handler.on_success.assert_called_once()
        handler.on_failure.assert_not_called()
        handler.on_retry.assert_not_called()


class TestPredefinedJobs:
    """预定义任务测试"""
    
    def test_predefined_jobs_exist(self):
        """测试预定义任务存在"""
        assert len(PREDEFINED_JOB_CONFIGS) == 5
        
        # 验证所有预定义任务都存在
        expected_jobs = [
            "jiazi_crawl",
            "category_crawl", 
            "database_cleanup",
            "log_rotation",
            "system_health_check"
        ]
        
        for job_id in expected_jobs:
            assert job_id in PREDEFINED_JOB_CONFIGS
            
    def test_predefined_job_configs(self):
        """测试预定义任务配置"""
        jiazi_config = PREDEFINED_JOB_CONFIGS["jiazi_crawl"]
        
        assert jiazi_config.job_id == "jiazi_crawl"
        assert jiazi_config.handler_class == JobHandlerType.CRAWL
        assert jiazi_config.trigger_type == TriggerType.INTERVAL
        assert jiazi_config.interval_seconds == 3600
        assert jiazi_config.enabled is True
        
    def test_job_handler_types(self):
        """测试任务处理器类型"""
        assert JobHandlerType.CRAWL == "CrawlJobHandler"
        assert JobHandlerType.MAINTENANCE == "MaintenanceJobHandler"
        assert JobHandlerType.REPORT == "ReportJobHandler"
        
    def test_job_status_enum(self):
        """测试任务状态枚举"""
        assert JobStatus.PENDING == "pending"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.SUCCESS == "success"
        assert JobStatus.FAILED == "failed"
        assert JobStatus.CANCELLED == "cancelled"
        assert JobStatus.PAUSED == "paused"
        assert JobStatus.RETRYING == "retrying"
        
    def test_trigger_type_enum(self):
        """测试触发器类型枚举"""
        assert TriggerType.INTERVAL == "interval"
        assert TriggerType.CRON == "cron"
        assert TriggerType.DATE == "date"