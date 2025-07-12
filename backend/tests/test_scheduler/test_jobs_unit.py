"""
调度任务处理器单元测试 - 测试具体的任务处理器实现
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.schedule import (
    CrawlJobHandler, MaintenanceJobHandler, ReportJobHandler
)
from app.models.schedule import JobContextModel, JobResultModel


class TestCrawlJobHandler:
    """爬虫任务处理器测试"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.handler = CrawlJobHandler()
        
    async def test_execute_jiazi_crawl_success(self):
        """测试夹子榜爬取任务成功执行"""
        context = JobContextModel(
            job_id="jiazi_crawl",
            job_name="夹子榜爬取任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "jiazi"}
        )
        
        result = await self.handler.execute(context)
        
        assert result.success is True
        assert "夹子榜爬取完成" in result.message
        assert "crawled_count" in result.data
        assert result.data["crawled_count"] == 50
        
    async def test_execute_category_crawl_success(self):
        """测试分类榜单爬取任务成功执行"""
        context = JobContextModel(
            job_id="category_crawl",
            job_name="分类榜单爬取任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "category"}
        )
        
        result = await self.handler.execute(context)
        
        assert result.success is True
        assert "分类榜单爬取完成" in result.message
        assert "crawled_count" in result.data
        assert result.data["crawled_count"] == 100
        
    async def test_execute_unknown_crawl_type(self):
        """测试未知爬虫任务类型"""
        context = JobContextModel(
            job_id="unknown_crawl",
            job_name="未知爬虫任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "unknown"}
        )
        
        result = await self.handler.execute(context)
        
        assert result.success is False
        assert "未知的爬虫任务类型" in result.message
        
    async def test_execute_with_exception(self):
        """测试爬虫任务执行异常"""
        context = JobContextModel(
            job_id="jiazi_crawl",
            job_name="夹子榜爬取任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "jiazi"}
        )
        
        # 模拟异步睡眠抛出异常
        with patch('asyncio.sleep', side_effect=Exception("网络错误")):
            result = await self.handler.execute(context)
            
            assert result.success is False
            assert "爬虫任务执行失败" in result.message
            assert result.exception is not None


class TestMaintenanceJobHandler:
    """维护任务处理器测试"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.handler = MaintenanceJobHandler()
        
    async def test_execute_database_cleanup_success(self):
        """测试数据库清理任务成功执行"""
        context = JobContextModel(
            job_id="database_cleanup",
            job_name="数据库清理任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "database_cleanup"}
        )
        
        result = await self.handler.execute(context)
        
        assert result.success is True
        assert "数据库清理完成" in result.message
        assert "cleaned_records" in result.data
        assert result.data["cleaned_records"] == 1000
        
    async def test_execute_log_rotation_success(self):
        """测试日志轮转任务成功执行"""
        context = JobContextModel(
            job_id="log_rotation",
            job_name="日志轮转任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "log_rotation"}
        )
        
        result = await self.handler.execute(context)
        
        assert result.success is True
        assert "日志轮转完成" in result.message
        assert "rotated_files" in result.data
        assert result.data["rotated_files"] == 5
        
    async def test_execute_health_check_success(self):
        """测试健康检查任务成功执行"""
        context = JobContextModel(
            job_id="system_health_check",
            job_name="系统健康检查任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "health_check"}
        )
        
        result = await self.handler.execute(context)
        
        assert result.success is True
        assert "系统健康检查完成" in result.message
        assert "status" in result.data
        assert result.data["status"] == "healthy"
        
    async def test_execute_unknown_maintenance_type(self):
        """测试未知维护任务类型"""
        context = JobContextModel(
            job_id="unknown_maintenance",
            job_name="未知维护任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "unknown"}
        )
        
        result = await self.handler.execute(context)
        
        assert result.success is False
        assert "未知的维护任务类型" in result.message
        
    async def test_execute_with_exception(self):
        """测试维护任务执行异常"""
        context = JobContextModel(
            job_id="database_cleanup",
            job_name="数据库清理任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "database_cleanup"}
        )
        
        # 模拟异步睡眠抛出异常
        with patch('asyncio.sleep', side_effect=Exception("磁盘错误")):
            result = await self.handler.execute(context)
            
            assert result.success is False
            assert "维护任务执行失败" in result.message
            assert result.exception is not None


class TestReportJobHandler:
    """报告任务处理器测试"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.handler = ReportJobHandler()
        
    async def test_execute_data_analysis_success(self):
        """测试数据分析报告任务成功执行"""
        context = JobContextModel(
            job_id="data_analysis_report",
            job_name="数据分析报告任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "data_analysis"}
        )
        
        result = await self.handler.execute(context)
        
        assert result.success is True
        assert "数据分析报告生成完成" in result.message
        assert "report_size" in result.data
        assert result.data["report_size"] == "2.5MB"
        
    async def test_execute_unknown_report_type(self):
        """测试未知报告任务类型"""
        context = JobContextModel(
            job_id="unknown_report",
            job_name="未知报告任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "unknown"}
        )
        
        result = await self.handler.execute(context)
        
        assert result.success is False
        assert "未知的报告任务类型" in result.message
        
    async def test_execute_with_exception(self):
        """测试报告任务执行异常"""
        context = JobContextModel(
            job_id="data_analysis_report",
            job_name="数据分析报告任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            job_data={"type": "data_analysis"}
        )
        
        # 模拟异步睡眠抛出异常
        with patch('asyncio.sleep', side_effect=Exception("内存不足")):
            result = await self.handler.execute(context)
            
            assert result.success is False
            assert "报告任务执行失败" in result.message
            assert result.exception is not None


class TestJobHandlerIntegration:
    """任务处理器集成测试"""
    
    def test_all_handlers_inherit_from_base(self):
        """测试所有处理器都继承自基类"""
        from app.schedule import BaseJobHandler
        
        crawl_handler = CrawlJobHandler()
        maintenance_handler = MaintenanceJobHandler()
        report_handler = ReportJobHandler()
        
        assert isinstance(crawl_handler, BaseJobHandler)
        assert isinstance(maintenance_handler, BaseJobHandler)
        assert isinstance(report_handler, BaseJobHandler)
        
    def test_all_handlers_have_logger(self):
        """测试所有处理器都有日志记录器"""
        crawl_handler = CrawlJobHandler()
        maintenance_handler = MaintenanceJobHandler()
        report_handler = ReportJobHandler()
        
        assert hasattr(crawl_handler, 'logger')
        assert hasattr(maintenance_handler, 'logger')
        assert hasattr(report_handler, 'logger')
        
        assert crawl_handler.logger.name == 'CrawlJobHandler'
        assert maintenance_handler.logger.name == 'MaintenanceJobHandler'
        assert report_handler.logger.name == 'ReportJobHandler'
        
    def test_job_context_basic_validation(self):
        """测试任务上下文基本验证"""
        # 测试上下文创建
        context = JobContextModel(
            job_id="test_job",
            job_name="测试任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now(),
            max_retries=3,
            retry_count=0
        )
        
        # 验证基本属性
        assert context.job_id == "test_job"
        assert context.job_name == "测试任务"
        assert context.max_retries == 3
        assert context.retry_count == 0
        
    def test_job_result_basic_validation(self):
        """测试任务结果基本验证"""
        # 测试成功结果
        success_result = JobResultModel.success_result("任务完成", {"count": 10})
        assert success_result.success is True
        assert success_result.message == "任务完成"
        assert success_result.data == {"count": 10}
        
        # 测试错误结果
        error_result = JobResultModel.error_result("任务失败", Exception("测试错误"))
        assert error_result.success is False
        assert error_result.message == "任务失败"
        assert error_result.exception is not None