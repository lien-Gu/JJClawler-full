"""
JobScheduler模块测试

测试app/schedule/scheduler.py的核心功能，使用mock的APScheduler避免实际调度
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apscheduler.triggers.date import DateTrigger

from app.models.schedule import Job, JobInfo, JobStatus, JobType, SchedulerInfo
from app.schedule.scheduler import JobScheduler, get_scheduler


class TestJobScheduler:
    """JobScheduler测试类"""

    @pytest.fixture
    def scheduler(self):
        """创建调度器实例"""
        return JobScheduler()

    @pytest.fixture
    def mock_apscheduler(self):
        """Mock APScheduler"""
        mock_scheduler = MagicMock()
        mock_scheduler.start = MagicMock()
        mock_scheduler.shutdown = MagicMock()
        mock_scheduler.add_job = MagicMock()
        mock_scheduler.get_job = MagicMock()
        mock_scheduler.get_jobs = MagicMock(return_value=[])
        mock_scheduler.remove_job = MagicMock()
        mock_scheduler.add_listener = MagicMock()
        return mock_scheduler

    @pytest.fixture
    def sample_job(self):
        """示例任务"""
        return Job(
            job_id="CRAWL_20250803_123456",
            job_type=JobType.CRAWL,
            trigger=DateTrigger(run_date=datetime.now()),
            desc="测试任务",
            page_ids=["jiazi"]
        )

    def test_scheduler_initialization(self, scheduler):
        """测试调度器初始化"""
        assert scheduler.scheduler is None
        assert scheduler.start_time is None
        assert scheduler.listener is None
        assert scheduler.job_func_mapping is not None
        assert JobType.CRAWL in scheduler.job_func_mapping

    def test_get_job_func_crawl_type(self, scheduler):
        """测试获取爬取任务执行函数"""
        func = scheduler._get_job_func(JobType.CRAWL)
        assert func is not None
        assert callable(func)

    def test_get_job_func_invalid_type(self, scheduler):
        """测试获取无效任务类型函数"""
        with pytest.raises(ValueError, match="job type .* is not supported"):
            scheduler._get_job_func("invalid_type")

    @pytest.mark.asyncio
    @patch('app.schedule.scheduler.AsyncIOScheduler')
    @patch('app.schedule.scheduler.JobListener')
    async def test_start_scheduler_success(self, mock_listener_class, mock_scheduler_class, scheduler):
        """测试启动调度器 - 成功场景"""
        mock_apscheduler = MagicMock()
        mock_scheduler_class.return_value = mock_apscheduler
        
        mock_listener = MagicMock()
        mock_listener_class.return_value = mock_listener

        # Mock预定义任务和清理任务
        with patch('app.models.schedule.get_predefined_jobs', return_value=[]), \
             patch('app.models.schedule.get_clean_up_job') as mock_cleanup:
            
            mock_cleanup_job = Job(
                job_id="__system_job_cleanup__",
                job_type=JobType.SYSTEM,
                trigger=DateTrigger(run_date=datetime.now()),
                desc="清理任务"
            )
            mock_cleanup.return_value = mock_cleanup_job
            
            await scheduler.start()

        assert scheduler.scheduler is not None
        assert scheduler.start_time is not None
        assert scheduler.listener is not None
        
        # 验证APScheduler配置
        mock_scheduler_class.assert_called_once()
        mock_apscheduler.start.assert_called_once()
        
        # 验证事件监听器注册
        mock_listener.set_scheduler.assert_called_once_with(mock_apscheduler)
        mock_apscheduler.add_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_scheduler_already_started(self, scheduler, mock_apscheduler):
        """测试启动调度器 - 已经启动"""
        scheduler.scheduler = mock_apscheduler
        
        await scheduler.start()
        
        # 应该不会重复启动
        mock_apscheduler.start.assert_not_called()

    @pytest.mark.asyncio
    async def test_shutdown_scheduler(self, scheduler, mock_apscheduler):
        """测试关闭调度器"""
        scheduler.scheduler = mock_apscheduler
        scheduler.start_time = datetime.now()
        
        await scheduler.shutdown()
        
        assert scheduler.scheduler is None
        assert scheduler.start_time is None
        assert scheduler.listener is None
        mock_apscheduler.shutdown.assert_called_once_with(wait=True)

    @pytest.mark.asyncio
    async def test_shutdown_scheduler_not_started(self, scheduler):
        """测试关闭调度器 - 未启动状态"""
        await scheduler.shutdown()
        # 应该正常执行，不抛异常

    @pytest.mark.asyncio
    async def test_add_schedule_job_success(self, scheduler, sample_job, mock_apscheduler):
        """测试添加调度任务 - 成功场景"""
        scheduler.scheduler = mock_apscheduler
        
        result = await scheduler.add_schedule_job(sample_job)
        
        assert result == sample_job
        
        # 验证APScheduler被正确调用
        mock_apscheduler.add_job.assert_called_once()
        call_args = mock_apscheduler.add_job.call_args
        assert call_args[1]['id'] == sample_job.job_id
        assert call_args[1]['trigger'] == sample_job.trigger
        assert call_args[1]['args'] == [sample_job.page_ids]

    @pytest.mark.asyncio
    async def test_add_schedule_job_with_custom_func(self, scheduler, sample_job, mock_apscheduler):
        """测试添加调度任务 - 自定义执行函数"""
        scheduler.scheduler = mock_apscheduler
        
        custom_func = MagicMock()
        result = await scheduler.add_schedule_job(sample_job, exe_func=custom_func)
        
        assert result == sample_job
        
        # 验证使用了自定义函数
        call_args = mock_apscheduler.add_job.call_args
        assert call_args[1]['func'] == custom_func

    @pytest.mark.asyncio
    async def test_add_schedule_job_system_type(self, scheduler, mock_apscheduler):
        """测试添加系统任务"""
        scheduler.scheduler = mock_apscheduler
        
        system_job = Job(
            job_id="__system_job_cleanup__",
            job_type=JobType.SYSTEM,
            trigger=DateTrigger(run_date=datetime.now()),
            desc="系统清理任务"
        )
        
        custom_func = MagicMock()
        result = await scheduler.add_schedule_job(system_job, exe_func=custom_func)
        
        assert result == system_job
        
        # 验证系统任务使用自定义函数
        call_args = mock_apscheduler.add_job.call_args
        assert call_args[1]['func'] == custom_func
        assert call_args[1]['args'] == [None]  # 系统任务args为None

    def test_get_job_info_success(self, scheduler, mock_apscheduler):
        """测试获取任务信息 - 成功场景"""
        scheduler.scheduler = mock_apscheduler
        
        # Mock APScheduler job
        mock_job = MagicMock()
        mock_job.metadata = '{"job_id": "test_job", "job_type": "crawl", "desc": "测试任务"}'
        mock_apscheduler.get_job.return_value = mock_job
        
        result = scheduler.get_job_info("test_job")
        
        assert result is not None
        assert isinstance(result, JobInfo)
        mock_apscheduler.get_job.assert_called_once_with("test_job")

    def test_get_job_info_not_found(self, scheduler, mock_apscheduler):
        """测试获取任务信息 - 任务不存在"""
        scheduler.scheduler = mock_apscheduler
        mock_apscheduler.get_job.return_value = None
        
        result = scheduler.get_job_info("nonexistent_job")
        
        assert result is not None
        assert result.err == "该任务nonexistent_job不存在"

    def test_get_job_info_no_metadata(self, scheduler, mock_apscheduler):
        """测试获取任务信息 - 无元数据"""
        scheduler.scheduler = mock_apscheduler
        
        mock_job = MagicMock()
        mock_job.metadata = None
        mock_apscheduler.get_job.return_value = mock_job
        
        result = scheduler.get_job_info("test_job")
        
        assert result is not None
        assert result.err == "该任务test_job不存在"

    def test_get_job_info_scheduler_not_running(self, scheduler):
        """测试获取任务信息 - 调度器未运行"""
        result = scheduler.get_job_info("test_job")
        
        assert result is not None
        assert result.err == "调度器没有成功运行"

    def test_get_scheduler_info_running(self, scheduler, mock_apscheduler):
        """测试获取调度器状态 - 运行中"""
        scheduler.scheduler = mock_apscheduler
        scheduler.start_time = datetime.now()
        
        # Mock jobs
        mock_job = MagicMock()
        mock_job.id = "test_job"
        mock_job.next_run_time = datetime.now()
        mock_job.trigger = "date"
        mock_job.metadata = {"status": "pending"}
        mock_apscheduler.get_jobs.return_value = [mock_job]
        
        with patch('humanize.naturaldelta', return_value="1小时30分钟"):
            result = scheduler.get_scheduler_info()
        
        assert isinstance(result, SchedulerInfo)
        assert result.status == "running"
        assert len(result.jobs) == 1
        assert result.jobs[0]["id"] == "test_job"
        assert result.jobs[0]["status"] == "pending"

    def test_get_scheduler_info_stopped(self, scheduler):
        """测试获取调度器状态 - 未启动"""
        result = scheduler.get_scheduler_info()
        
        assert isinstance(result, SchedulerInfo)
        assert result.status == "stopped"
        assert result.jobs == []
        assert result.run_time == "0天0小时0分钟0秒"

    def test_get_scheduler_info_error(self, scheduler, mock_apscheduler):
        """测试获取调度器状态 - 异常场景"""
        scheduler.scheduler = mock_apscheduler
        scheduler.start_time = datetime.now()
        
        # 模拟异常
        mock_apscheduler.get_jobs.side_effect = Exception("数据库连接失败")
        
        result = scheduler.get_scheduler_info()
        
        assert isinstance(result, SchedulerInfo)
        assert result.status == "error"
        assert result.jobs == []
        assert result.run_time == "未知"

    def test_calculate_run_time_with_humanize(self, scheduler):
        """测试运行时间计算 - humanize库正常"""
        scheduler.start_time = datetime.now() - timedelta(hours=2, minutes=30)
        
        with patch('humanize.naturaldelta', return_value="2小时30分钟"):
            result = scheduler._calculate_run_time()
        
        assert result == "2小时30分钟"

    def test_calculate_run_time_humanize_fallback(self, scheduler):
        """测试运行时间计算 - humanize库异常回退"""
        scheduler.start_time = datetime.now() - timedelta(days=1, hours=2, minutes=30, seconds=15)
        
        # 需要同时模拟precisedelta和naturaldelta异常
        with patch('humanize.precisedelta', side_effect=Exception("humanize错误")), \
             patch('humanize.naturaldelta', side_effect=Exception("humanize错误")):
            result = scheduler._calculate_run_time()
        
        assert "天" in result and "小时" in result and "分钟" in result and "秒" in result

    def test_calculate_run_time_no_start_time(self, scheduler):
        """测试运行时间计算 - 无启动时间"""
        scheduler.start_time = None
        
        result = scheduler._calculate_run_time()
        
        assert result == "未知"

    def test_cleanup_old_jobs_success(self, scheduler, mock_apscheduler):
        """测试清理过期任务 - 成功场景"""
        from datetime import timezone
        
        scheduler.scheduler = mock_apscheduler
        
        # Mock过期任务
        mock_job = MagicMock()
        mock_job.id = "old_job"
        old_time = datetime.now(timezone.utc) - timedelta(days=10)
        mock_job.metadata = {
            "created_at": old_time.isoformat().replace('+00:00', 'Z'),
            "status": JobStatus.SUCCESS,
            "is_system_job": False
        }
        mock_job.trigger = DateTrigger(run_date=datetime.now())
        mock_apscheduler.get_jobs.return_value = [mock_job]
        
        result = scheduler._cleanup_old_jobs()
        
        assert result["cleaned"] == 1
        assert result["errors"] == []
        mock_apscheduler.remove_job.assert_called_once_with("old_job")

    def test_cleanup_old_jobs_scheduler_not_running(self, scheduler):
        """测试清理过期任务 - 调度器未运行"""
        result = scheduler._cleanup_old_jobs()
        
        assert result["cleaned"] == 0
        assert result["error"] == "调度器未运行"

    def test_should_cleanup_job_completed_onetime(self, scheduler):
        """测试任务清理判断 - 已完成的一次性任务"""
        from datetime import timezone
        
        mock_job = MagicMock()
        # 创建带时区的datetime对象
        old_time = datetime.now(timezone.utc) - timedelta(days=10)
        mock_job.metadata = {
            "created_at": old_time.isoformat().replace('+00:00', 'Z'),
            "status": JobStatus.SUCCESS,
            "is_system_job": False
        }
        mock_job.trigger = DateTrigger(run_date=datetime.now())
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        should_cleanup, reason = scheduler._should_cleanup_job(mock_job, cutoff_date)
        
        assert should_cleanup is True
        assert reason == "completed_onetime_job"

    def test_should_cleanup_job_system_job(self, scheduler):
        """测试任务清理判断 - 系统任务不清理"""
        from datetime import timezone
        
        mock_job = MagicMock()
        old_time = datetime.now(timezone.utc) - timedelta(days=10)
        mock_job.metadata = {
            "created_at": old_time.isoformat().replace('+00:00', 'Z'),
            "is_system_job": True
        }
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        should_cleanup, reason = scheduler._should_cleanup_job(mock_job, cutoff_date)
        
        assert should_cleanup is False
        assert reason == "system job"

    def test_should_cleanup_job_recent_job(self, scheduler):
        """测试任务清理判断 - 最近的任务不清理"""
        from datetime import timezone
        
        mock_job = MagicMock()
        recent_time = datetime.now(timezone.utc)
        mock_job.metadata = {
            "created_at": recent_time.isoformat().replace('+00:00', 'Z'),
            "status": JobStatus.SUCCESS,
            "is_system_job": False
        }
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        should_cleanup, reason = scheduler._should_cleanup_job(mock_job, cutoff_date)
        
        assert should_cleanup is False
        assert reason == "active job"


class TestSchedulerSingleton:
    """测试调度器单例模式"""

    def test_get_scheduler_singleton(self):
        """测试获取调度器单例"""
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()
        
        assert scheduler1 is scheduler2
        assert isinstance(scheduler1, JobScheduler)

    @patch('app.schedule.scheduler._scheduler', None)
    def test_get_scheduler_new_instance(self):
        """测试创建新的调度器实例"""
        scheduler = get_scheduler()
        
        assert isinstance(scheduler, JobScheduler)

    @pytest.mark.asyncio
    async def test_start_stop_scheduler_functions(self):
        """测试启动和停止调度器的便捷函数"""
        from app.schedule.scheduler import start_scheduler, stop_scheduler
        
        # Mock调度器实例
        with patch('app.schedule.scheduler.get_scheduler') as mock_get_scheduler:
            mock_scheduler = MagicMock()
            mock_scheduler.start = AsyncMock()
            mock_scheduler.shutdown = AsyncMock()
            mock_get_scheduler.return_value = mock_scheduler
            
            # 测试启动函数
            await start_scheduler()
            mock_scheduler.start.assert_called_once()
            
            # 测试停止函数
            await stop_scheduler()
            mock_scheduler.shutdown.assert_called_once()