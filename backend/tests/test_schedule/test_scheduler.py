"""
调度器模块测试文件
测试schedule.scheduler模块的关键功能
"""
import pytest
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
    
    def test_create_scheduler(self, scheduler, mocker):
        """测试创建APScheduler实例"""
        mock_asyncio_scheduler = mocker.patch('app.schedule.scheduler.AsyncIOScheduler')
        mock_jobstore = mocker.patch('app.schedule.scheduler.SQLAlchemyJobStore')
        mock_executor = mocker.patch('app.schedule.scheduler.AsyncIOExecutor')
        
        mock_scheduler_instance = mocker.Mock()
        mock_asyncio_scheduler.return_value = mock_scheduler_instance
        
        result = scheduler._create_scheduler()
        
        assert result == mock_scheduler_instance
        mock_jobstore.assert_called_once()
        mock_executor.assert_called_once()
        mock_asyncio_scheduler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_success(self, scheduler, mocker):
        """测试启动调度器成功"""
        mock_apscheduler = mocker.Mock()
        mock_apscheduler.start = mocker.Mock()
        
        mock_create_scheduler = mocker.patch.object(scheduler, '_create_scheduler', return_value=mock_apscheduler)
        mock_load_jobs = mocker.patch.object(scheduler, '_load_predefined_jobs', return_value=None)
        
        await scheduler.start()
        
        assert scheduler.scheduler == mock_apscheduler
        assert scheduler.start_time is not None
        mock_create_scheduler.assert_called_once()
        mock_load_jobs.assert_called_once()
        mock_apscheduler.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_already_running(self, scheduler, mocker):
        """测试调度器已经启动"""
        mock_apscheduler = mocker.Mock()
        scheduler.scheduler = mock_apscheduler
        
        mock_create_scheduler = mocker.patch.object(scheduler, '_create_scheduler')
        mock_load_jobs = mocker.patch.object(scheduler, '_load_predefined_jobs')
        
        await scheduler.start()
        
        mock_create_scheduler.assert_not_called()
        mock_load_jobs.assert_not_called()
        mock_apscheduler.start.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_shutdown_success(self, scheduler, mocker):
        """测试关闭调度器成功"""
        mock_apscheduler = mocker.Mock()
        mock_apscheduler.shutdown = mocker.Mock()
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
    
    @pytest.mark.asyncio
    async def test_load_predefined_jobs_single_page(self, scheduler, mocker):
        """测试加载预定义任务（单页面）"""
        # 模拟单页面任务
        mock_job_config = mocker.Mock()
        mock_job_config.is_single_page_task = True
        
        mock_add_job = mocker.patch.object(scheduler, 'add_job', return_value=True)
        mock_add_batch_jobs = mocker.patch.object(scheduler, 'add_batch_jobs')
        
        # 正确的方式mock PREDEFINED_JOB_CONFIGS
        mocker.patch('app.schedule.scheduler.PREDEFINED_JOB_CONFIGS', {"test_job": mock_job_config})
        
        await scheduler._load_predefined_jobs()
        
        mock_add_job.assert_called_once_with(mock_job_config)
        mock_add_batch_jobs.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_load_predefined_jobs_multi_page(self, scheduler, mocker):
        """测试加载预定义任务（多页面）"""
        # 模拟多页面任务
        mock_job_config = mocker.Mock()
        mock_job_config.is_single_page_task = False
        mock_job_config.page_ids = ["page1", "page2"]
        mock_job_config.force = False
        
        mock_add_job = mocker.patch.object(scheduler, 'add_job')
        mock_add_batch_jobs = mocker.patch.object(scheduler, 'add_batch_jobs', 
                                                return_value={"success": True, "successful_tasks": 2})
        
        # 正确的方式mock PREDEFINED_JOB_CONFIGS
        mocker.patch('app.schedule.scheduler.PREDEFINED_JOB_CONFIGS', {"test_batch_job": mock_job_config})
        
        await scheduler._load_predefined_jobs()
        
        mock_add_job.assert_not_called()
        mock_add_batch_jobs.assert_called_once_with(
            page_ids=["page1", "page2"],
            force=False,
            batch_id="predefined_test_batch_job"
        )
    
    @pytest.mark.asyncio
    async def test_add_job_success(self, scheduler, mocker, sample_job_config):
        """测试添加任务成功"""
        mock_apscheduler = mocker.Mock()
        scheduler.scheduler = mock_apscheduler
        
        job_config = JobConfigModel(**sample_job_config)
        
        # 不要mock build_trigger方法，让它自然执行
        # 这样测试更接近真实行为
        result = await scheduler.add_job(job_config)
        
        assert result is True
        mock_apscheduler.add_job.assert_called_once()
        # 验证add_job被调用时包含了正确的参数
        args, kwargs = mock_apscheduler.add_job.call_args
        assert kwargs['id'] == job_config.job_id
        assert kwargs['name'] == job_config.job_id
    
    @pytest.mark.asyncio
    async def test_add_job_scheduler_not_started(self, scheduler, sample_job_config):
        """测试在调度器未启动时添加任务"""
        job_config = JobConfigModel(**sample_job_config)
        
        with pytest.raises(RuntimeError) as exc_info:
            await scheduler.add_job(job_config)
        
        assert "调度器未启动" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_add_batch_jobs_success(self, scheduler, mocker, test_page_ids):
        """测试添加批量任务成功"""
        # 设置模拟
        mock_config = mocker.patch('app.crawl.base.CrawlConfig')
        mock_config.return_value.determine_page_ids.return_value = test_page_ids["multiple"]
        mock_add_job = mocker.patch.object(scheduler, 'add_job', return_value=True)
        
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
    
    def test_get_jobs_with_scheduler(self, scheduler, mocker, mock_jobs):
        """测试获取任务列表（调度器已启动）"""
        mock_apscheduler = mocker.Mock()
        scheduler.scheduler = mock_apscheduler
        mock_apscheduler.get_jobs.return_value = mock_jobs
        
        result = scheduler.get_jobs()
        
        assert result == mock_jobs
        mock_apscheduler.get_jobs.assert_called_once()
    
    def test_get_jobs_without_scheduler(self, scheduler):
        """测试获取任务列表（调度器未启动）"""
        result = scheduler.get_jobs()
        
        assert result == []
    
    def test_is_running_true(self, scheduler, mocker):
        """测试调度器运行状态（运行中）"""
        mock_apscheduler = mocker.Mock()
        scheduler.scheduler = mock_apscheduler
        mock_apscheduler.running = True
        
        result = scheduler.is_running()
        
        assert result is True
    
    def test_is_running_false(self, scheduler, mocker):
        """测试调度器运行状态（未运行）"""
        mock_apscheduler = mocker.Mock()
        scheduler.scheduler = mock_apscheduler
        mock_apscheduler.running = False
        
        result = scheduler.is_running()
        
        assert result is False
    
    def test_is_running_no_scheduler(self, scheduler):
        """测试调度器运行状态（调度器未启动）"""
        result = scheduler.is_running()
        
        assert result is False
    
    def test_get_status_with_scheduler(self, scheduler, mocker):
        """测试获取调度器状态（调度器已启动）"""
        mock_apscheduler = mocker.Mock()
        scheduler.scheduler = mock_apscheduler
        scheduler.start_time = datetime.now()
        
        mock_job1 = mocker.Mock()
        mock_job1.next_run_time = datetime.now()
        mock_job2 = mocker.Mock()
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
    
    def test_get_batch_status_found(self, scheduler, mocker, test_batch_ids):
        """测试获取批量任务状态（找到）"""
        mock_apscheduler = mocker.Mock()
        scheduler.scheduler = mock_apscheduler
        
        mock_job1 = mocker.Mock()
        mock_job1.id = f"crawl_page1_{test_batch_ids['valid']}"
        mock_job1.next_run_time = datetime.now()
        mock_job2 = mocker.Mock()
        mock_job2.id = f"crawl_page2_{test_batch_ids['valid']}"
        mock_job2.next_run_time = None
        
        mock_apscheduler.get_jobs.return_value = [mock_job1, mock_job2]
        
        result = scheduler.get_batch_status(test_batch_ids["valid"])
        
        assert result["batch_id"] == test_batch_ids["valid"]
        assert result["status"] == "running"
        assert result["total_jobs"] == 2
        assert result["running_jobs"] == 1
        assert result["completed_jobs"] == 1


class TestSchedulerSingleton:
    """测试调度器单例模式"""
    
    def test_get_scheduler_singleton(self):
        """测试获取调度器单例"""
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()
        
        assert scheduler1 is scheduler2
        assert isinstance(scheduler1, TaskScheduler)
    
    def test_get_scheduler_create_new(self, mocker):
        """测试创建新的调度器实例"""
        mocker.patch('app.schedule.scheduler._scheduler', None)
        scheduler = get_scheduler()
        
        assert isinstance(scheduler, TaskScheduler)


class TestSchedulerModuleFunctions:
    """测试调度器模块函数"""
    
    @pytest.mark.asyncio
    async def test_start_scheduler(self, mocker):
        """测试启动调度器函数"""
        from app.schedule.scheduler import start_scheduler
        
        mock_scheduler = mocker.Mock()
        mock_scheduler.start = mocker.AsyncMock()
        mock_get_scheduler = mocker.patch('app.schedule.scheduler.get_scheduler', return_value=mock_scheduler)
        
        await start_scheduler()
        
        mock_get_scheduler.assert_called_once()
        mock_scheduler.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_scheduler(self, mocker):
        """测试停止调度器函数"""
        from app.schedule.scheduler import stop_scheduler
        
        mock_scheduler = mocker.Mock()
        mock_scheduler.shutdown = mocker.AsyncMock()
        mock_get_scheduler = mocker.patch('app.schedule.scheduler.get_scheduler', return_value=mock_scheduler)
        
        await stop_scheduler()
        
        mock_get_scheduler.assert_called_once()
        mock_scheduler.shutdown.assert_called_once()