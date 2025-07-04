"""
调度模块单元测试 - 测试TaskScheduler类的各个方法和功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent
from apscheduler.job import Job
import asyncio

# 假设的导入（根据项目实际结构调整）
from app.scheduler.task_scheduler import TaskScheduler
from app.scheduler.jobs import JobManager


class TestTaskScheduler:
    """TaskScheduler单元测试类"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.scheduler = TaskScheduler()
        self.mock_apscheduler = Mock(spec=AsyncIOScheduler)
        self.scheduler.scheduler = self.mock_apscheduler
    
    def test_init_scheduler(self, scheduler_config):
        """测试调度器初始化"""
        # 测试默认初始化
        scheduler = TaskScheduler()
        assert scheduler.timezone == "Asia/Shanghai"
        assert scheduler.job_defaults is not None
        assert scheduler.executors is not None
        
        # 测试自定义配置初始化
        custom_config = scheduler_config.copy()
        custom_config["timezone"] = "UTC"
        scheduler_custom = TaskScheduler(config=custom_config)
        assert scheduler_custom.timezone == "UTC"
    
    def test_start_scheduler_success(self):
        """测试成功启动调度器"""
        self.mock_apscheduler.start = Mock()
        self.mock_apscheduler.running = False
        
        # 执行启动
        self.scheduler.start()
        
        # 验证调用
        self.mock_apscheduler.start.assert_called_once()
        assert self.scheduler.is_running is True
    
    def test_start_scheduler_already_running(self):
        """测试调度器已经在运行的情况"""
        self.mock_apscheduler.running = True
        self.mock_apscheduler.start = Mock()
        
        # 执行启动
        self.scheduler.start()
        
        # 验证不会重复启动
        self.mock_apscheduler.start.assert_not_called()
    
    def test_start_scheduler_with_exception(self):
        """测试启动调度器时发生异常"""
        self.mock_apscheduler.start = Mock(side_effect=Exception("启动失败"))
        self.mock_apscheduler.running = False
        
        # 执行启动并验证异常
        with pytest.raises(Exception) as exc_info:
            self.scheduler.start()
        
        assert "启动失败" in str(exc_info.value)
        assert self.scheduler.is_running is False
    
    def test_stop_scheduler_success(self):
        """测试成功停止调度器"""
        self.mock_apscheduler.shutdown = Mock()
        self.mock_apscheduler.running = True
        self.scheduler.is_running = True
        
        # 执行停止
        self.scheduler.stop()
        
        # 验证调用
        self.mock_apscheduler.shutdown.assert_called_once_with(wait=True)
        assert self.scheduler.is_running is False
    
    def test_stop_scheduler_not_running(self):
        """测试停止未运行的调度器"""
        self.mock_apscheduler.running = False
        self.mock_apscheduler.shutdown = Mock()
        self.scheduler.is_running = False
        
        # 执行停止
        self.scheduler.stop()
        
        # 验证不会调用shutdown
        self.mock_apscheduler.shutdown.assert_not_called()
    
    def test_add_job_success(self, sample_job_data):
        """测试成功添加任务"""
        job_config = sample_job_data["jiazi_crawl_job"]
        mock_job = Mock(spec=Job)
        mock_job.id = job_config["id"]
        
        self.mock_apscheduler.add_job = Mock(return_value=mock_job)
        
        # 执行添加任务
        result = self.scheduler.add_job(
            func=job_config["func"],
            trigger=job_config["trigger"],
            id=job_config["id"],
            name=job_config["name"],
            hours=job_config["hours"]
        )
        
        # 验证结果
        assert result == mock_job
        self.mock_apscheduler.add_job.assert_called_once()
    
    def test_add_job_with_exception(self, sample_job_data):
        """测试添加任务时发生异常"""
        job_config = sample_job_data["jiazi_crawl_job"]
        self.mock_apscheduler.add_job = Mock(side_effect=Exception("添加失败"))
        
        # 执行添加任务并验证异常
        with pytest.raises(Exception) as exc_info:
            self.scheduler.add_job(
                func=job_config["func"],
                trigger=job_config["trigger"],
                id=job_config["id"],
                name=job_config["name"],
                hours=job_config["hours"]
            )
        
        assert "添加失败" in str(exc_info.value)
    
    def test_remove_job_success(self):
        """测试成功删除任务"""
        job_id = "test_job_id"
        self.mock_apscheduler.remove_job = Mock()
        
        # 执行删除任务
        self.scheduler.remove_job(job_id)
        
        # 验证调用
        self.mock_apscheduler.remove_job.assert_called_once_with(job_id)
    
    def test_remove_job_not_found(self):
        """测试删除不存在的任务"""
        job_id = "non_existent_job"
        self.mock_apscheduler.remove_job = Mock(side_effect=Exception("任务不存在"))
        
        # 执行删除任务并验证异常
        with pytest.raises(Exception) as exc_info:
            self.scheduler.remove_job(job_id)
        
        assert "任务不存在" in str(exc_info.value)
    
    def test_pause_job_success(self):
        """测试成功暂停任务"""
        job_id = "test_job_id"
        self.mock_apscheduler.pause_job = Mock()
        
        # 执行暂停任务
        self.scheduler.pause_job(job_id)
        
        # 验证调用
        self.mock_apscheduler.pause_job.assert_called_once_with(job_id)
    
    def test_resume_job_success(self):
        """测试成功恢复任务"""
        job_id = "test_job_id"
        self.mock_apscheduler.resume_job = Mock()
        
        # 执行恢复任务
        self.scheduler.resume_job(job_id)
        
        # 验证调用
        self.mock_apscheduler.resume_job.assert_called_once_with(job_id)
    
    def test_get_job_success(self):
        """测试成功获取任务"""
        job_id = "test_job_id"
        mock_job = Mock(spec=Job)
        mock_job.id = job_id
        mock_job.name = "测试任务"
        
        self.mock_apscheduler.get_job = Mock(return_value=mock_job)
        
        # 执行获取任务
        result = self.scheduler.get_job(job_id)
        
        # 验证结果
        assert result == mock_job
        self.mock_apscheduler.get_job.assert_called_once_with(job_id)
    
    def test_get_job_not_found(self):
        """测试获取不存在的任务"""
        job_id = "non_existent_job"
        self.mock_apscheduler.get_job = Mock(return_value=None)
        
        # 执行获取任务
        result = self.scheduler.get_job(job_id)
        
        # 验证结果
        assert result is None
    
    def test_get_jobs_success(self, mock_scheduler_jobs):
        """测试成功获取任务列表"""
        mock_jobs = []
        for job_data in mock_scheduler_jobs:
            mock_job = Mock(spec=Job)
            mock_job.id = job_data["id"]
            mock_job.name = job_data["name"]
            mock_job.func = job_data["func"]
            mock_job.trigger = job_data["trigger"]
            mock_job.next_run_time = datetime.fromisoformat(job_data["next_run_time"])
            mock_jobs.append(mock_job)
        
        self.mock_apscheduler.get_jobs = Mock(return_value=mock_jobs)
        
        # 执行获取任务列表
        result = self.scheduler.get_jobs()
        
        # 验证结果
        assert len(result) == len(mock_scheduler_jobs)
        assert all(isinstance(job, Mock) for job in result)
        self.mock_apscheduler.get_jobs.assert_called_once()
    
    def test_get_jobs_empty(self):
        """测试获取空任务列表"""
        self.mock_apscheduler.get_jobs = Mock(return_value=[])
        
        # 执行获取任务列表
        result = self.scheduler.get_jobs()
        
        # 验证结果
        assert result == []
    
    def test_modify_job_success(self):
        """测试成功修改任务"""
        job_id = "test_job_id"
        changes = {"hours": 2, "name": "修改后的任务"}
        
        self.mock_apscheduler.modify_job = Mock()
        
        # 执行修改任务
        self.scheduler.modify_job(job_id, **changes)
        
        # 验证调用
        self.mock_apscheduler.modify_job.assert_called_once_with(job_id, **changes)
    
    def test_modify_job_not_found(self):
        """测试修改不存在的任务"""
        job_id = "non_existent_job"
        changes = {"hours": 2}
        
        self.mock_apscheduler.modify_job = Mock(side_effect=Exception("任务不存在"))
        
        # 执行修改任务并验证异常
        with pytest.raises(Exception) as exc_info:
            self.scheduler.modify_job(job_id, **changes)
        
        assert "任务不存在" in str(exc_info.value)
    
    def test_reschedule_job_success(self):
        """测试成功重新调度任务"""
        job_id = "test_job_id"
        trigger = "interval"
        trigger_args = {"hours": 3}
        
        self.mock_apscheduler.reschedule_job = Mock()
        
        # 执行重新调度任务
        self.scheduler.reschedule_job(job_id, trigger, **trigger_args)
        
        # 验证调用
        self.mock_apscheduler.reschedule_job.assert_called_once_with(
            job_id, trigger=trigger, **trigger_args
        )
    
    def test_get_scheduler_info_success(self, mock_scheduler_statistics):
        """测试成功获取调度器信息"""
        # 模拟调度器状态
        self.mock_apscheduler.running = True
        self.mock_apscheduler.get_jobs = Mock(return_value=[Mock(), Mock(), Mock()])
        
        with patch.object(self.scheduler, 'get_scheduler_statistics') as mock_stats:
            mock_stats.return_value = mock_scheduler_statistics
            
            # 执行获取调度器信息
            result = self.scheduler.get_scheduler_info()
            
            # 验证结果
            assert result["running"] is True
            assert result["total_jobs"] == 3
            assert "statistics" in result
            assert result["statistics"] == mock_scheduler_statistics
    
    def test_get_scheduler_info_not_running(self):
        """测试获取未运行调度器的信息"""
        self.mock_apscheduler.running = False
        
        # 执行获取调度器信息
        result = self.scheduler.get_scheduler_info()
        
        # 验证结果
        assert result["running"] is False
        assert result["total_jobs"] == 0
    
    def test_job_execution_event_success(self, mock_task_execution_data):
        """测试任务执行成功事件处理"""
        execution_data = mock_task_execution_data["successful_execution"]
        
        # 创建模拟事件
        mock_event = Mock(spec=JobExecutionEvent)
        mock_event.job_id = execution_data["job_id"]
        mock_event.scheduled_run_time = datetime.fromisoformat(execution_data["start_time"])
        mock_event.retval = execution_data["result"]
        mock_event.exception = None
        
        # 执行事件处理
        with patch.object(self.scheduler, '_handle_job_execution') as mock_handler:
            self.scheduler._on_job_executed(mock_event)
            
            # 验证调用
            mock_handler.assert_called_once_with(mock_event, success=True)
    
    def test_job_execution_event_failure(self, mock_task_execution_data):
        """测试任务执行失败事件处理"""
        execution_data = mock_task_execution_data["failed_execution"]
        
        # 创建模拟事件
        mock_event = Mock(spec=JobExecutionEvent)
        mock_event.job_id = execution_data["job_id"]
        mock_event.scheduled_run_time = datetime.fromisoformat(execution_data["start_time"])
        mock_event.retval = None
        mock_event.exception = Exception(execution_data["error"])
        
        # 执行事件处理
        with patch.object(self.scheduler, '_handle_job_execution') as mock_handler:
            self.scheduler._on_job_error(mock_event)
            
            # 验证调用
            mock_handler.assert_called_once_with(mock_event, success=False)
    
    def test_add_event_listener_success(self):
        """测试成功添加事件监听器"""
        self.mock_apscheduler.add_listener = Mock()
        
        # 执行添加事件监听器
        self.scheduler.add_event_listener(EVENT_JOB_EXECUTED, self.scheduler._on_job_executed)
        
        # 验证调用
        self.mock_apscheduler.add_listener.assert_called_once_with(
            self.scheduler._on_job_executed, EVENT_JOB_EXECUTED
        )
    
    def test_remove_event_listener_success(self):
        """测试成功移除事件监听器"""
        self.mock_apscheduler.remove_listener = Mock()
        
        # 执行移除事件监听器
        self.scheduler.remove_event_listener(self.scheduler._on_job_executed)
        
        # 验证调用
        self.mock_apscheduler.remove_listener.assert_called_once_with(
            self.scheduler._on_job_executed
        )
    
    def test_get_scheduler_statistics_success(self, mock_scheduler_statistics):
        """测试成功获取调度器统计信息"""
        # 模拟统计数据
        with patch.object(self.scheduler, '_calculate_statistics') as mock_calc:
            mock_calc.return_value = mock_scheduler_statistics
            
            # 执行获取统计信息
            result = self.scheduler.get_scheduler_statistics()
            
            # 验证结果
            assert result == mock_scheduler_statistics
            assert result["total_jobs"] == 3
            assert result["successful_executions"] == 145
            assert result["failed_executions"] == 5
            assert result["scheduler_status"] == "running"
    
    def test_validate_job_config_success(self, sample_job_data):
        """测试成功验证任务配置"""
        job_config = sample_job_data["jiazi_crawl_job"]
        
        # 执行验证任务配置
        result = self.scheduler.validate_job_config(job_config)
        
        # 验证结果
        assert result is True
    
    def test_validate_job_config_missing_required_field(self):
        """测试验证缺少必需字段的任务配置"""
        invalid_config = {
            "id": "test_job",
            # 缺少 func 字段
            "trigger": "interval",
            "hours": 1
        }
        
        # 执行验证任务配置
        result = self.scheduler.validate_job_config(invalid_config)
        
        # 验证结果
        assert result is False
    
    def test_validate_job_config_invalid_trigger(self):
        """测试验证无效触发器的任务配置"""
        invalid_config = {
            "id": "test_job",
            "func": "test_function",
            "trigger": "invalid_trigger",  # 无效的触发器类型
            "hours": 1
        }
        
        # 执行验证任务配置
        result = self.scheduler.validate_job_config(invalid_config)
        
        # 验证结果
        assert result is False
    
    def test_health_check_healthy(self):
        """测试健康检查 - 健康状态"""
        self.mock_apscheduler.running = True
        self.mock_apscheduler.get_jobs = Mock(return_value=[Mock(), Mock()])
        
        # 执行健康检查
        result = self.scheduler.health_check()
        
        # 验证结果
        assert result["status"] == "healthy"
        assert result["scheduler_running"] is True
        assert result["total_jobs"] == 2
        assert "last_check_time" in result
    
    def test_health_check_unhealthy(self):
        """测试健康检查 - 不健康状态"""
        self.mock_apscheduler.running = False
        
        # 执行健康检查
        result = self.scheduler.health_check()
        
        # 验证结果
        assert result["status"] == "unhealthy"
        assert result["scheduler_running"] is False
        assert result["total_jobs"] == 0
        assert "last_check_time" in result
    
    def teardown_method(self):
        """每个测试方法执行后的清理"""
        if hasattr(self.scheduler, 'scheduler') and self.scheduler.scheduler:
            self.scheduler.scheduler = None 