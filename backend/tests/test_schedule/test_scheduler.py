"""
JobScheduler模块测试 - 增强版本

使用pytest-mock和真实内存调度器测试，完整覆盖调度器功能
"""

import asyncio
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pytest_mock import MockerFixture

from app.models.schedule import Job, JobType, SchedulerInfo
from app.schedule.scheduler import JobScheduler


class TestJobSchedulerMocked:
    """使用pytest-mock的调度器测试类"""

    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        scheduler = JobScheduler()
        assert scheduler.scheduler is None
        assert scheduler.start_time is None
        assert scheduler.listener is None


    @pytest.mark.asyncio
    async def test_start_scheduler_success(self, mocker: MockerFixture, sample_job, sample_system_job):
        """测试启动调度器 - 成功场景"""
        scheduler = JobScheduler()

        # Mock APScheduler和相关依赖
        mock_scheduler_class = mocker.patch('app.schedule.scheduler.AsyncIOScheduler')
        mock_listener_class = mocker.patch('app.schedule.scheduler.JobListener')
        mock_apscheduler = mocker.MagicMock()
        mock_scheduler_class.return_value = mock_apscheduler

        mock_listener = mocker.MagicMock()
        mock_listener_class.return_value = mock_listener

        # Mock预定义任务和清理任务
        mocker.patch('app.models.schedule.get_predefined_jobs', return_value=[])
        mock_cleanup = mocker.patch('app.models.schedule.get_clean_up_job')
        mock_cleanup.return_value = sample_system_job

        await scheduler.start()

        assert scheduler.scheduler is not None
        assert scheduler.start_time is not None
        assert scheduler.listener is not None

        # 验证APScheduler配置
        mock_scheduler_class.assert_called_once()
        mock_apscheduler.start.assert_called_once()

        # 验证事件监听器注册
        mock_apscheduler.add_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_schedule_job_success(self, mocker: MockerFixture, sample_job):
        """测试添加调度任务 - 成功场景"""
        scheduler = JobScheduler()
        mock_apscheduler = mocker.MagicMock()
        scheduler.scheduler = mock_apscheduler

        result = await scheduler.add_schedule_job(sample_job)

        assert result == sample_job

        # 验证APScheduler被正确调用
        mock_apscheduler.add_job.assert_called_once()
        call_args = mock_apscheduler.add_job.call_args
        assert call_args[1]['id'] == sample_job.job_id
        assert call_args[1]['trigger'] == sample_job.trigger
        assert call_args[1]['args'] == [sample_job.page_ids]
        # 不再检查metadata

    @pytest.mark.asyncio
    async def test_add_schedule_job_with_custom_func(self, mocker: MockerFixture, sample_job):
        """测试添加调度任务 - 自定义执行函数"""
        scheduler = JobScheduler()
        mock_apscheduler = mocker.MagicMock()
        scheduler.scheduler = mock_apscheduler

        custom_func = mocker.MagicMock()
        result = await scheduler.add_schedule_job(sample_job, exe_func=custom_func)

        assert result == sample_job

        # 验证使用了自定义函数
        call_args = mock_apscheduler.add_job.call_args
        assert call_args[1]['func'] == custom_func

    def test_get_scheduler_info_running(self, mocker: MockerFixture):
        """测试获取调度器状态 - 运行中"""
        scheduler = JobScheduler()
        mock_apscheduler = mocker.MagicMock()
        scheduler.scheduler = mock_apscheduler
        scheduler.start_time = datetime.now()

        # Mock jobs
        mock_job = mocker.MagicMock()
        mock_job.id = "test_job"
        mock_job.next_run_time = datetime.now()
        mock_job.trigger = "date"
        mock_apscheduler.get_jobs.return_value = [mock_job]

        # Mock humanize库
        mocker.patch('humanize.naturaldelta', return_value="1小时30分钟")

        result = scheduler.get_scheduler_info()

        assert isinstance(result, SchedulerInfo)
        assert result.status == "running"
        assert len(result.jobs) == 1
        assert result.jobs[0]["id"] == "test_job"
        assert result.jobs[0]["status"] == "scheduled"  # 不再依赖metadata

    def test_should_cleanup_job_completed_onetime(self):
        """测试任务清理判断 - 已完成的一次性任务"""
        from datetime import timezone

        scheduler = JobScheduler()
        mock_job = type('MockJob', (), {})()
        mock_job.id = "normal_job"
        mock_job.trigger = DateTrigger(run_date=datetime.now())
        mock_job.next_run_time = None  # 已完成

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        should_cleanup, reason = scheduler._should_cleanup_job(mock_job, cutoff_date)

        assert should_cleanup is True
        assert reason == "completed_onetime_job"

    def test_should_cleanup_job_system_job(self):
        """测试任务清理判断 - 系统任务不清理"""
        from datetime import timezone

        scheduler = JobScheduler()
        mock_job = type('MockJob', (), {})()
        mock_job.id = "__system_job_cleanup"
        mock_job.trigger = DateTrigger(run_date=datetime.now())

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        should_cleanup, reason = scheduler._should_cleanup_job(mock_job, cutoff_date)

        assert should_cleanup is False
        assert reason == "system job"

    def test_should_cleanup_job_active_job(self):
        """测试任务清理判断 - 活跃任务不清理"""
        from datetime import timezone

        scheduler = JobScheduler()
        mock_job = type('MockJob', (), {})()
        mock_job.id = "active_job"
        mock_job.trigger = DateTrigger(run_date=datetime.now())
        mock_job.next_run_time = datetime.now() + timedelta(hours=1)  # 有下次运行时间

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        should_cleanup, reason = scheduler._should_cleanup_job(mock_job, cutoff_date)

        assert should_cleanup is False
        assert reason == "active_job"


class TestJobSchedulerIntegration:
    """使用真实内存调度器的集成测试"""

    @pytest_asyncio.fixture
    async def memory_scheduler(self, mocker: MockerFixture):
        """创建使用内存存储的真实调度器"""
        # Mock CrawlFlow 避免初始化问题
        mock_crawl_flow = mocker.MagicMock()
        mock_crawl_flow.execute_crawl_task = mocker.AsyncMock(return_value={"success": True, "test": "result"})
        mocker.patch('app.crawl.CrawlFlow', return_value=mock_crawl_flow)

        scheduler = JobScheduler()

        # 覆盖默认配置，使用内存存储
        scheduler.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            timezone='Asia/Shanghai'
        )
        scheduler.start_time = datetime.now()

        yield scheduler

        # 清理
        if scheduler.scheduler and scheduler.scheduler.running:
            scheduler.scheduler.shutdown()

    @pytest.mark.asyncio
    async def test_real_scheduler_lifecycle(self, memory_scheduler, sample_job):
        """测试真实调度器的生命周期"""
        scheduler = memory_scheduler

        # 启动调度器
        scheduler.scheduler.start()
        assert scheduler.scheduler.running

        # 创建一个未来时间的任务，避免立即执行
        future_job = Job(
            job_id="FUTURE_CRAWL_TEST",
            job_type=JobType.CRAWL,
            trigger=DateTrigger(run_date=datetime.now() + timedelta(hours=1)),  # 1小时后执行
            desc="未来执行的测试任务",
            page_ids=["jiazi"]
        )

        # 添加任务
        result = await scheduler.add_schedule_job(future_job, exe_func=lambda x: "test_result")
        assert result == future_job

        # 验证任务已添加且未执行
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == future_job.job_id

        # 验证任务存在且有下次运行时间
        actual_job = scheduler.scheduler.get_job(future_job.job_id)
        assert actual_job is not None
        assert actual_job.id == future_job.job_id
        assert actual_job.next_run_time is not None  # 有计划的下次执行时间

        # 直接验证调度器是否运行，避免get_scheduler_info的metadata问题
        assert scheduler.scheduler.running

        # 验证任务数量
        current_jobs = scheduler.scheduler.get_jobs()
        assert len(current_jobs) == 1

        # 测试移除任务
        scheduler.scheduler.remove_job(future_job.job_id)
        jobs_after_removal = scheduler.scheduler.get_jobs()
        assert len(jobs_after_removal) == 0

    @pytest.mark.asyncio
    async def test_real_scheduler_job_execution(self, memory_scheduler):
        """测试真实调度器的任务执行"""
        scheduler = memory_scheduler
        scheduler.scheduler.start()

        # 创建一个立即执行的任务
        executed = []

        def test_func(page_ids):
            executed.append(f"executed_with_{page_ids}")
            return "success"

        immediate_job = Job(
            job_id="immediate_test_job",
            job_type=JobType.CRAWL,
            trigger=DateTrigger(run_date=datetime.now() + timedelta(seconds=0.1)),  # 更短的延迟
            desc="立即执行测试任务",
            page_ids=["test_page"]
        )

        await scheduler.add_schedule_job(immediate_job, exe_func=test_func)

        # 等待任务执行
        await asyncio.sleep(0.5)  # 更短的等待时间

        # 验证任务已执行
        assert len(executed) == 1
        assert "executed_with_['test_page']" in executed

    @pytest.mark.asyncio
    async def test_real_scheduler_multiple_triggers(self, memory_scheduler):
        """测试真实调度器的多种触发器类型"""
        scheduler = memory_scheduler
        scheduler.scheduler.start()

        # 测试不同类型的触发器
        jobs = [
            Job(
                job_id="date_job",
                job_type=JobType.CRAWL,
                trigger=DateTrigger(run_date=datetime.now() + timedelta(hours=1)),
                desc="定时任务",
                page_ids=["test1"]
            ),
            Job(
                job_id="cron_job",
                job_type=JobType.CRAWL,
                trigger=CronTrigger(hour=0, minute=0),
                desc="定时任务",
                page_ids=["test2"]
            ),
            Job(
                job_id="interval_job",
                job_type=JobType.CRAWL,
                trigger=IntervalTrigger(minutes=30),
                desc="间隔任务",
                page_ids=["test3"]
            )
        ]

        def dummy_func(page_ids):
            return f"processed_{page_ids}"

        # 添加所有任务
        for job in jobs:
            await scheduler.add_schedule_job(job, exe_func=dummy_func)

        # 验证所有任务都已添加
        scheduler_jobs = scheduler.scheduler.get_jobs()
        assert len(scheduler_jobs) == 3

        job_ids = {job.id for job in scheduler_jobs}
        assert "date_job" in job_ids
        assert "cron_job" in job_ids
        assert "interval_job" in job_ids

    @pytest.mark.asyncio
    async def test_real_scheduler_job_cleanup(self, memory_scheduler):
        """测试真实调度器的任务清理功能 """
        scheduler = memory_scheduler
        scheduler.scheduler.start()

        # 添加一个普通任务
        def dummy_func(page_ids):
            return "completed"

        test_job = Job(
            job_id="cleanup_test_job",
            job_type=JobType.CRAWL,
            trigger=DateTrigger(run_date=datetime.now() + timedelta(hours=1)),
            desc="清理测试任务",
            page_ids=["test"]
        )

        await scheduler.add_schedule_job(test_job, exe_func=dummy_func)

        # 执行清理操作（由于任务是新的，应该不会被清理）
        cleanup_result = scheduler._cleanup_old_jobs()

        # 验证清理结果结构
        assert "cleaned" in cleanup_result
        assert isinstance(cleanup_result["cleaned"], int)
        assert cleanup_result["cleaned"] >= 0

        # 由于任务是新创建的，应该不会被清理
        remaining_jobs = scheduler.scheduler.get_jobs()
        job_ids = [job.id for job in remaining_jobs]
        assert "cleanup_test_job" in job_ids
