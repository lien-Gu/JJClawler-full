"""
调度器模块测试文件
测试schedule.scheduler模块的关键功能
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.schedule.scheduler import TaskScheduler, get_scheduler
from app.models.schedule import JobConfigModel, TriggerType, JobHandlerType, PREDEFINED_JOB_CONFIGS
from app.schedule.handlers import CrawlJobHandler, ReportJobHandler


class TestTaskScheduler:
    """测试TaskScheduler类"""
    
    @pytest.fixture
    def scheduler(self):
        """创建TaskScheduler实例"""
        return TaskScheduler()
    
    @pytest.fixture
    def mock_apscheduler(self):
        """模拟APScheduler实例"""
        scheduler = Mock()
        scheduler.start = Mock()
        scheduler.shutdown = Mock()
        scheduler.add_job = Mock()
        scheduler.pause_job = Mock()
        scheduler.get_jobs = Mock(return_value=[])
        scheduler.get_job = Mock(return_value=None)
        scheduler.running = True
        scheduler.state = "running"
        scheduler.timezone = "Asia/Shanghai"
        return scheduler
    
    def test_initialization(self, scheduler):
        """测试调度器初始化"""
        assert scheduler.scheduler is None
        assert scheduler.start_time is None
        assert JobHandlerType.CRAWL in scheduler.job_handlers
        assert JobHandlerType.REPORT in scheduler.job_handlers
        assert scheduler.job_handlers[JobHandlerType.CRAWL] == CrawlJobHandler
        assert scheduler.job_handlers[JobHandlerType.REPORT] == ReportJobHandler
    
    def test_register_default_handlers(self, scheduler):
        """测试默认处理器注册"""
        assert len(scheduler.job_handlers) == 2
        assert scheduler.job_handlers[JobHandlerType.CRAWL] == CrawlJobHandler
        assert scheduler.job_handlers[JobHandlerType.REPORT] == ReportJobHandler
    
    @patch('app.schedule.scheduler.AsyncIOScheduler')
    @patch('app.schedule.scheduler.SQLAlchemyJobStore')
    @patch('app.schedule.scheduler.AsyncIOExecutor')
    def test_create_scheduler(self, mock_executor, mock_jobstore, mock_scheduler, scheduler):
        """测试创建APScheduler实例"""
        mock_scheduler_instance = Mock()
        mock_scheduler.return_value = mock_scheduler_instance
        
        result = scheduler._create_scheduler()
        
        assert result == mock_scheduler_instance
        mock_jobstore.assert_called_once()
        mock_executor.assert_called_once()
        mock_scheduler.assert_called_once()
    
    @patch.object(TaskScheduler, '_create_scheduler')
    @patch.object(TaskScheduler, '_load_predefined_jobs')
    @pytest.mark.asyncio
    async def test_start_success(self, mock_load_jobs, mock_create_scheduler, mock_apscheduler, scheduler):
        """测试启动调度器成功"""
        mock_create_scheduler.return_value = mock_apscheduler
        mock_load_jobs.return_value = None
        
        await scheduler.start()
        
        assert scheduler.scheduler == mock_apscheduler
        assert scheduler.start_time is not None
        mock_create_scheduler.assert_called_once()
        mock_load_jobs.assert_called_once()
        mock_apscheduler.start.assert_called_once()
    
    @patch.object(TaskScheduler, '_create_scheduler')
    @patch.object(TaskScheduler, '_load_predefined_jobs')
    @pytest.mark.asyncio
    async def test_start_already_running(self, mock_load_jobs, mock_create_scheduler, mock_apscheduler, scheduler):
        """测试调度器已经启动"""
        scheduler.scheduler = mock_apscheduler
        
        await scheduler.start()
        
        mock_create_scheduler.assert_not_called()
        mock_load_jobs.assert_not_called()
        mock_apscheduler.start.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_shutdown_success(self, mock_apscheduler, scheduler):
        """测试关闭调度器成功"""
        scheduler.scheduler = mock_apscheduler
        scheduler.start_time = datetime.now()
        
        await scheduler.shutdown()
        
        assert scheduler.scheduler is None
        assert scheduler.start_time is None
        mock_apscheduler.shutdown.assert_called_once_with(wait=True)
    
    @pytest.mark.asyncio
    async def test_shutdown_not_started(self, scheduler):
        """测试关闭未启动的调度器"""
        await scheduler.shutdown()
        
        assert scheduler.scheduler is None
        assert scheduler.start_time is None
    
    @patch.object(TaskScheduler, 'add_job')
    @patch.object(TaskScheduler, 'add_batch_jobs')
    @pytest.mark.asyncio
    async def test_load_predefined_jobs_single_page(self, mock_add_batch_jobs, mock_add_job, scheduler):
        """测试加载预定义任务（单页面）"""
        # 模拟单页面任务
        mock_job_config = Mock()
        mock_job_config.is_single_page_task = True
        mock_add_job.return_value = True
        
        with patch.dict(PREDEFINED_JOB_CONFIGS, {"test_job": mock_job_config}):
            await scheduler._load_predefined_jobs()
        
        mock_add_job.assert_called_once_with(mock_job_config)
        mock_add_batch_jobs.assert_not_called()
    
    @patch.object(TaskScheduler, 'add_job')
    @patch.object(TaskScheduler, 'add_batch_jobs')
    @pytest.mark.asyncio
    async def test_load_predefined_jobs_multi_page(self, mock_add_batch_jobs, mock_add_job, scheduler):
        """测试加载预定义任务（多页面）"""
        # 模拟多页面任务
        mock_job_config = Mock()
        mock_job_config.is_single_page_task = False
        mock_job_config.page_ids = ["page1", "page2"]
        mock_job_config.force = False
        mock_add_batch_jobs.return_value = {"success": True, "successful_tasks": 2}
        
        with patch.dict(PREDEFINED_JOB_CONFIGS, {"test_batch_job": mock_job_config}):
            await scheduler._load_predefined_jobs()
        
        mock_add_job.assert_not_called()
        mock_add_batch_jobs.assert_called_once_with(
            page_ids=["page1", "page2"],
            force=False,
            batch_id="predefined_test_batch_job"
        )
    
    @pytest.mark.asyncio
    async def test_add_job_success(self, mock_apscheduler, scheduler):
        """测试添加任务成功"""
        scheduler.scheduler = mock_apscheduler
        
        job_config = JobConfigModel(
            job_id="test_job",
            trigger_type=TriggerType.DATE,
            handler_class=JobHandlerType.CRAWL,
            page_ids=["test_page"]
        )
        
        with patch.object(job_config, 'build_trigger') as mock_build_trigger:
            mock_trigger = Mock()
            mock_build_trigger.return_value = mock_trigger
            
            result = await scheduler.add_job(job_config)
            
            assert result is True
            mock_apscheduler.add_job.assert_called_once()
            mock_build_trigger.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_job_disabled(self, mock_apscheduler, scheduler):
        """测试添加禁用的任务"""
        scheduler.scheduler = mock_apscheduler
        
        job_config = JobConfigModel(
            job_id="test_job",
            trigger_type=TriggerType.DATE,
            handler_class=JobHandlerType.CRAWL,
            page_ids=["test_page"],
            enabled=False
        )
        
        with patch.object(job_config, 'build_trigger') as mock_build_trigger:
            mock_trigger = Mock()
            mock_build_trigger.return_value = mock_trigger
            
            result = await scheduler.add_job(job_config)
            
            assert result is True
            mock_apscheduler.add_job.assert_called_once()
            mock_apscheduler.pause_job.assert_called_once_with("test_job")
    
    @pytest.mark.asyncio
    async def test_add_job_scheduler_not_started(self, scheduler):
        """测试在调度器未启动时添加任务"""
        job_config = JobConfigModel(
            job_id="test_job",
            trigger_type=TriggerType.DATE,
            handler_class=JobHandlerType.CRAWL,
            page_ids=["test_page"]
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            await scheduler.add_job(job_config)
        
        assert "调度器未启动" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_add_job_exception(self, mock_apscheduler, scheduler):
        """测试添加任务异常"""
        scheduler.scheduler = mock_apscheduler
        mock_apscheduler.add_job.side_effect = Exception("添加任务失败")
        
        job_config = JobConfigModel(
            job_id="test_job",
            trigger_type=TriggerType.DATE,
            handler_class=JobHandlerType.CRAWL,
            page_ids=["test_page"]
        )
        
        with patch.object(job_config, 'build_trigger') as mock_build_trigger:
            mock_trigger = Mock()
            mock_build_trigger.return_value = mock_trigger
            
            result = await scheduler.add_job(job_config)
            
            assert result is False
    
    @patch('app.schedule.scheduler.CrawlConfig')
    @patch.object(TaskScheduler, 'add_job')
    @pytest.mark.asyncio
    async def test_add_batch_jobs_success(self, mock_add_job, mock_config_class, scheduler):
        """测试添加批量任务成功"""
        # 设置模拟
        mock_config = Mock()
        mock_config.determine_page_ids.return_value = ["page1", "page2"]
        mock_config_class.return_value = mock_config
        mock_add_job.return_value = True
        
        result = await scheduler.add_batch_jobs(
            page_ids=["all"],
            force=True,
            batch_id="test_batch"
        )
        
        assert result["success"] is True
        assert result["batch_id"] == "test_batch"
        assert result["total_pages"] == 2
        assert result["successful_tasks"] == 2
        assert result["failed_tasks"] == 0
        assert len(result["task_ids"]) == 2
        
        # 验证add_job被调用了2次
        assert mock_add_job.call_count == 2
    
    @patch('app.schedule.scheduler.CrawlConfig')
    @patch.object(TaskScheduler, 'add_job')
    @pytest.mark.asyncio
    async def test_add_batch_jobs_partial_success(self, mock_add_job, mock_config_class, scheduler):
        """测试添加批量任务部分成功"""
        # 设置模拟
        mock_config = Mock()
        mock_config.determine_page_ids.return_value = ["page1", "page2"]
        mock_config_class.return_value = mock_config
        mock_add_job.side_effect = [True, False]  # 第一个成功，第二个失败
        
        result = await scheduler.add_batch_jobs(
            page_ids=["all"],
            force=False
        )
        
        assert result["success"] is True
        assert result["total_pages"] == 2
        assert result["successful_tasks"] == 1
        assert result["failed_tasks"] == 1
    
    @patch('app.schedule.scheduler.CrawlConfig')
    @pytest.mark.asyncio
    async def test_add_batch_jobs_no_valid_pages(self, mock_config_class, scheduler):
        """测试添加批量任务无有效页面"""
        # 设置模拟
        mock_config = Mock()
        mock_config.determine_page_ids.return_value = []
        mock_config_class.return_value = mock_config
        
        result = await scheduler.add_batch_jobs(
            page_ids=["invalid"],
            force=False
        )
        
        assert result["success"] is False
        assert result["message"] == "没有找到有效的页面ID"
        assert result["task_ids"] == []
    
    @patch('app.schedule.scheduler.CrawlJobHandler')
    @patch('app.schedule.scheduler.JobContextModel')
    @pytest.mark.asyncio
    async def test_execute_job_success(self, mock_context_class, mock_handler_class, scheduler):
        """测试执行任务成功"""
        # 设置模拟
        mock_handler = Mock()
        mock_handler.execute_with_retry = AsyncMock()
        mock_result = Mock()
        mock_result.message = "任务执行成功"
        mock_handler.execute_with_retry.return_value = mock_result
        mock_handler_class.return_value = mock_handler
        
        mock_context = Mock()
        mock_context_class.return_value = mock_context
        
        job_config = JobConfigModel(
            job_id="test_job",
            trigger_type=TriggerType.DATE,
            handler_class=JobHandlerType.CRAWL,
            page_ids=["test_page"]
        )
        
        await scheduler._execute_job(job_config)
        
        mock_handler_class.assert_called_once_with(scheduler=scheduler)
        mock_handler.execute_with_retry.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_job_handler_not_found(self, scheduler):
        """测试执行任务处理器未找到"""
        job_config = JobConfigModel(
            job_id="test_job",
            trigger_type=TriggerType.DATE,
            handler_class="NonExistentHandler",
            page_ids=["test_page"]
        )
        
        with pytest.raises(ValueError) as exc_info:
            await scheduler._execute_job(job_config)
        
        assert "未找到处理器" in str(exc_info.value)
    
    def test_get_jobs_with_scheduler(self, mock_apscheduler, scheduler):
        """测试获取任务列表（调度器已启动）"""
        scheduler.scheduler = mock_apscheduler
        mock_jobs = [Mock(), Mock()]
        mock_apscheduler.get_jobs.return_value = mock_jobs
        
        result = scheduler.get_jobs()
        
        assert result == mock_jobs
        mock_apscheduler.get_jobs.assert_called_once()
    
    def test_get_jobs_without_scheduler(self, scheduler):
        """测试获取任务列表（调度器未启动）"""
        result = scheduler.get_jobs()
        
        assert result == []
    
    def test_get_job_with_scheduler(self, mock_apscheduler, scheduler):
        """测试获取指定任务（调度器已启动）"""
        scheduler.scheduler = mock_apscheduler
        mock_job = Mock()
        mock_apscheduler.get_job.return_value = mock_job
        
        result = scheduler.get_job("test_job")
        
        assert result == mock_job
        mock_apscheduler.get_job.assert_called_once_with("test_job")
    
    def test_get_job_without_scheduler(self, scheduler):
        """测试获取指定任务（调度器未启动）"""
        result = scheduler.get_job("test_job")
        
        assert result is None
    
    def test_is_running_true(self, mock_apscheduler, scheduler):
        """测试调度器运行状态（运行中）"""
        scheduler.scheduler = mock_apscheduler
        mock_apscheduler.running = True
        
        result = scheduler.is_running()
        
        assert result is True
    
    def test_is_running_false(self, mock_apscheduler, scheduler):
        """测试调度器运行状态（未运行）"""
        scheduler.scheduler = mock_apscheduler
        mock_apscheduler.running = False
        
        result = scheduler.is_running()
        
        assert result is False
    
    def test_is_running_no_scheduler(self, scheduler):
        """测试调度器运行状态（调度器未启动）"""
        result = scheduler.is_running()
        
        assert result is False
    
    def test_get_status_with_scheduler(self, mock_apscheduler, scheduler):
        """测试获取调度器状态（调度器已启动）"""
        scheduler.scheduler = mock_apscheduler
        scheduler.start_time = datetime.now()
        
        mock_job1 = Mock()
        mock_job1.next_run_time = datetime.now()
        mock_job2 = Mock()
        mock_job2.next_run_time = None
        mock_apscheduler.get_jobs.return_value = [mock_job1, mock_job2]
        
        result = scheduler.get_status()
        
        assert result["status"] == "running"
        assert result["job_count"] == 2
        assert result["running_jobs"] == 1
        assert result["paused_jobs"] == 1
        assert result["uptime"] > 0
    
    def test_get_status_without_scheduler(self, scheduler):
        """测试获取调度器状态（调度器未启动）"""
        result = scheduler.get_status()
        
        assert result["status"] == "stopped"
        assert result["job_count"] == 0
        assert result["running_jobs"] == 0
        assert result["paused_jobs"] == 0
        assert result["uptime"] == 0.0
    
    def test_get_batch_jobs(self, mock_apscheduler, scheduler):
        """测试获取批量任务"""
        scheduler.scheduler = mock_apscheduler
        
        mock_job1 = Mock()
        mock_job1.id = "crawl_page1_batch_123"
        mock_job2 = Mock()
        mock_job2.id = "crawl_page2_batch_123"
        mock_job3 = Mock()
        mock_job3.id = "crawl_page3_batch_456"
        
        mock_apscheduler.get_jobs.return_value = [mock_job1, mock_job2, mock_job3]
        
        result = scheduler.get_batch_jobs("batch_123")
        
        assert len(result) == 2
        assert mock_job1 in result
        assert mock_job2 in result
        assert mock_job3 not in result
    
    def test_get_batch_status_found(self, mock_apscheduler, scheduler):
        """测试获取批量任务状态（找到）"""
        scheduler.scheduler = mock_apscheduler
        
        mock_job1 = Mock()
        mock_job1.id = "crawl_page1_batch_123"
        mock_job1.next_run_time = datetime.now()
        mock_job2 = Mock()
        mock_job2.id = "crawl_page2_batch_123"
        mock_job2.next_run_time = None
        
        mock_apscheduler.get_jobs.return_value = [mock_job1, mock_job2]
        
        result = scheduler.get_batch_status("batch_123")
        
        assert result["batch_id"] == "batch_123"
        assert result["status"] == "running"
        assert result["total_jobs"] == 2
        assert result["running_jobs"] == 1
        assert result["completed_jobs"] == 1
    
    def test_get_batch_status_not_found(self, mock_apscheduler, scheduler):
        """测试获取批量任务状态（未找到）"""
        scheduler.scheduler = mock_apscheduler
        mock_apscheduler.get_jobs.return_value = []
        
        result = scheduler.get_batch_status("nonexistent_batch")
        
        assert result["batch_id"] == "nonexistent_batch"
        assert result["status"] == "not_found"
        assert result["total_jobs"] == 0
        assert result["running_jobs"] == 0
        assert result["completed_jobs"] == 0


class TestSchedulerSingleton:
    """测试调度器单例模式"""
    
    def test_get_scheduler_singleton(self):
        """测试获取调度器单例"""
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()
        
        assert scheduler1 is scheduler2
        assert isinstance(scheduler1, TaskScheduler)
    
    @patch('app.schedule.scheduler._scheduler', None)
    def test_get_scheduler_create_new(self):
        """测试创建新的调度器实例"""
        scheduler = get_scheduler()
        
        assert isinstance(scheduler, TaskScheduler)


class TestSchedulerModuleFunctions:
    """测试调度器模块函数"""
    
    @patch('app.schedule.scheduler.get_scheduler')
    @pytest.mark.asyncio
    async def test_start_scheduler(self, mock_get_scheduler):
        """测试启动调度器函数"""
        from app.schedule.scheduler import start_scheduler
        
        mock_scheduler = Mock()
        mock_scheduler.start = AsyncMock()
        mock_get_scheduler.return_value = mock_scheduler
        
        await start_scheduler()
        
        mock_get_scheduler.assert_called_once()
        mock_scheduler.start.assert_called_once()
    
    @patch('app.schedule.scheduler.get_scheduler')
    @pytest.mark.asyncio
    async def test_stop_scheduler(self, mock_get_scheduler):
        """测试停止调度器函数"""
        from app.schedule.scheduler import stop_scheduler
        
        mock_scheduler = Mock()
        mock_scheduler.shutdown = AsyncMock()
        mock_get_scheduler.return_value = mock_scheduler
        
        await stop_scheduler()
        
        mock_get_scheduler.assert_called_once()
        mock_scheduler.shutdown.assert_called_once()


# 运行测试的示例
if __name__ == "__main__":
    pytest.main([__file__, "-v"])