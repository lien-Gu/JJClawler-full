"""
TaskScheduler模块测试

测试调度器的核心功能，使用mock的APScheduler避免实际调度
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schedule import JobHandlerType, JobInfo, JobStatus, TriggerType
from app.schedule.scheduler import TaskScheduler


class TestTaskScheduler:
    """TaskScheduler测试类"""

    @pytest.fixture
    def scheduler(self):
        """创建调度器实例"""
        return TaskScheduler()

    @pytest.fixture
    def mock_apscheduler(self):
        """Mock APScheduler"""
        mock_scheduler = MagicMock()
        mock_scheduler.start_in_background = AsyncMock()
        mock_scheduler.stop = AsyncMock()
        mock_scheduler.add_schedule = AsyncMock()
        mock_scheduler.get_schedules = AsyncMock(return_value=[])
        return mock_scheduler

    @pytest.fixture
    def sample_job_info(self):
        """示例任务信息"""
        return JobInfo(
            job_id="test_job_123",
            trigger_type=TriggerType.DATE,
            trigger_time={"run_time": datetime.now()},
            handler=JobHandlerType.CRAWL,
            page_ids=["jiazi"],
            desc="测试任务"
        )

    def test_scheduler_initialization(self, scheduler):
        """测试调度器初始化"""
        assert scheduler.scheduler is None
        assert scheduler.start_time is None
        assert len(scheduler.job_handlers) == 2  # CRAWL 和 REPORT
        assert JobHandlerType.CRAWL in scheduler.job_handlers
        assert JobHandlerType.REPORT in scheduler.job_handlers

    def test_generate_job_id_with_page_id(self, scheduler):
        """测试任务ID生成 - 带页面ID"""
        job_id = scheduler._generate_job_id("CrawlJobHandler", "jiazi")
        
        assert "CrawlJobHandler" in job_id
        assert "jiazi" in job_id
        assert len(job_id.split("_")) >= 3  # handler_pageid_timestamp

    def test_generate_job_id_without_page_id(self, scheduler):
        """测试任务ID生成 - 不带页面ID"""
        job_id = scheduler._generate_job_id("CrawlJobHandler")
        
        assert "CrawlJobHandler" in job_id
        assert len(job_id.split("_")) >= 3  # handler_timestamp_uuid

    def test_create_date_trigger(self, scheduler):
        """测试DATE触发器创建"""
        run_time = datetime.now()
        trigger_time = {"run_time": run_time}
        
        trigger = scheduler._create_trigger(TriggerType.DATE, trigger_time)
        
        assert trigger is not None
        assert trigger.run_date == run_time

    def test_create_cron_trigger(self, scheduler):
        """测试CRON触发器创建"""
        trigger_time = {"hour": "10", "minute": "30"}
        
        trigger = scheduler._create_trigger(TriggerType.CRON, trigger_time)
        
        assert trigger is not None

    def test_create_interval_trigger(self, scheduler):
        """测试INTERVAL触发器创建"""
        trigger_time = {"seconds": 60}
        
        trigger = scheduler._create_trigger(TriggerType.INTERVAL, trigger_time)
        
        assert trigger is not None

    def test_create_invalid_trigger(self, scheduler):
        """测试无效触发器类型"""
        with pytest.raises(ValueError, match="不支持的触发器类型"):
            scheduler._create_trigger("invalid_type", {})

    @patch('app.schedule.scheduler.AsyncScheduler')
    async def test_start_scheduler_success(self, mock_scheduler_class, scheduler, mock_apscheduler):
        """测试启动调度器 - 成功场景"""
        mock_scheduler_class.return_value = mock_apscheduler
        
        # Mock get_full_page_ids
        with patch.object(scheduler, 'get_full_page_ids', return_value=["jiazi"]):
            await scheduler.start()
        
        assert scheduler.scheduler is not None
        assert scheduler.start_time is not None
        mock_apscheduler.start_in_background.assert_called_once()

    async def test_start_scheduler_already_started(self, scheduler, mock_apscheduler):
        """测试启动调度器 - 已经启动"""
        scheduler.scheduler = mock_apscheduler
        
        await scheduler.start()
        
        # 应该不会重复启动
        mock_apscheduler.start_in_background.assert_not_called()

    async def test_shutdown_scheduler(self, scheduler, mock_apscheduler):
        """测试关闭调度器"""
        scheduler.scheduler = mock_apscheduler
        scheduler.start_time = datetime.now()
        
        await scheduler.shutdown()
        
        assert scheduler.scheduler is None
        assert scheduler.start_time is None
        mock_apscheduler.stop.assert_called_once()

    async def test_shutdown_scheduler_not_started(self, scheduler):
        """测试关闭调度器 - 未启动状态"""
        await scheduler.shutdown()
        # 应该正常执行，不抛异常

    @patch('app.schedule.scheduler.AsyncScheduler')
    async def test_add_single_job_success(self, mock_scheduler_class, scheduler, mock_apscheduler, sample_job_info):
        """测试添加单个任务 - 成功场景"""
        mock_scheduler_class.return_value = mock_apscheduler
        scheduler.scheduler = mock_apscheduler
        
        # Mock get_full_page_ids
        with patch.object(scheduler, 'get_full_page_ids', return_value=["jiazi"]):
            result = await scheduler.add_job(sample_job_info)
        
        assert result.job_id == sample_job_info.job_id
        assert result.status[0] == JobStatus.PENDING
        assert sample_job_info.job_id in scheduler._job_store
        mock_apscheduler.add_schedule.assert_called_once()

    @patch('app.schedule.scheduler.AsyncScheduler')
    async def test_add_batch_jobs_success(self, mock_scheduler_class, scheduler, mock_apscheduler):
        """测试添加批次任务 - 成功场景"""
        mock_scheduler_class.return_value = mock_apscheduler
        scheduler.scheduler = mock_apscheduler
        
        # 创建多页面任务
        batch_job_info = JobInfo(
            job_id="batch_job_456",
            trigger_type=TriggerType.DATE,
            trigger_time={"run_time": datetime.now()},
            handler=JobHandlerType.CRAWL,
            page_ids=["jiazi", "category"],
            desc="批次测试任务"
        )
        
        # Mock get_full_page_ids
        with patch.object(scheduler, 'get_full_page_ids', return_value=["jiazi", "category"]):
            result = await scheduler.add_job(batch_job_info)
        
        assert result.job_id == "batch_job_456"
        assert result.status[0] == JobStatus.PENDING
        assert "批次任务全部添加成功" in result.status[1]
        # 应该调用add_schedule两次（每个页面一次）
        assert mock_apscheduler.add_schedule.call_count == 2

    async def test_get_job_info_success(self, scheduler, sample_job_info, mock_apscheduler):
        """测试获取任务信息 - 成功场景"""
        scheduler.scheduler = mock_apscheduler
        scheduler._job_store[sample_job_info.job_id] = sample_job_info
        
        result = await scheduler.get_job_info(sample_job_info.job_id)
        
        assert result is not None
        assert result.job_id == sample_job_info.job_id

    async def test_get_job_info_not_found(self, scheduler):
        """测试获取任务信息 - 任务不存在"""
        result = await scheduler.get_job_info("nonexistent_job")
        
        assert result is None

    async def test_get_scheduler_info_running(self, scheduler, mock_apscheduler):
        """测试获取调度器状态 - 运行中"""
        scheduler.scheduler = mock_apscheduler
        scheduler.start_time = datetime.now()
        
        # Mock schedules
        mock_schedule = MagicMock()
        mock_schedule.id = "test_schedule"
        mock_schedule.next_fire_time = datetime.now()
        mock_schedule.trigger = "date"
        mock_apscheduler.get_schedules.return_value = [mock_schedule]
        
        result = await scheduler.get_scheduler_info()
        
        assert result["status"] == "running"
        assert len(result["job_wait"]) == 1
        assert "天" in result["run_time"]

    async def test_get_scheduler_info_stopped(self, scheduler):
        """测试获取调度器状态 - 未启动"""
        result = await scheduler.get_scheduler_info()
        
        assert result["status"] == "stopped"
        assert result["job_wait"] == []
        assert result["job_running"] == []
        assert result["run_time"] == "0天0小时0分钟0秒"

    def test_get_full_page_ids_success(self, scheduler):
        """测试获取完整页面ID列表 - 成功场景"""
        with patch('app.crawl_config.CrawlConfig') as mock_config:
            mock_instance = mock_config.return_value
            mock_instance.determine_page_ids.return_value = ["jiazi", "category"]
            
            result = scheduler.get_full_page_ids(["jiazi"])
            
            assert result == ["jiazi", "category"]
            mock_instance.determine_page_ids.assert_called_once_with(["jiazi"])

    def test_get_full_page_ids_fallback(self, scheduler):
        """测试获取完整页面ID列表 - 异常回退"""
        with patch('app.crawl_config.CrawlConfig', side_effect=Exception("Config error")):
            result = scheduler.get_full_page_ids(["jiazi"])
            
            assert result == ["jiazi"]

    def test_get_full_page_ids_empty(self, scheduler):
        """测试获取完整页面ID列表 - 空输入"""
        result = scheduler.get_full_page_ids(None)
        assert result == []
        
        result = scheduler.get_full_page_ids([])
        assert result == []