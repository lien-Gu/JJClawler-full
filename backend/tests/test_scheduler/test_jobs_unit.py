"""
调度任务处理器单元测试 - 测试具体的任务处理器实现
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.schedule import CrawlJobHandler
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
            scheduled_time=datetime.now()
        )
        job_data = {"type": "jiazi"}
        
        result = await self.handler.execute(context, job_data)
        
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
            scheduled_time=datetime.now()
        )
        job_data = {"type": "category"}
        
        result = await self.handler.execute(context, job_data)
        
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
            scheduled_time=datetime.now()
        )
        job_data = {"type": "unknown"}
        
        result = await self.handler.execute(context, job_data)
        
        assert result.success is False
        assert "未知的爬虫任务类型" in result.message
        
    async def test_execute_with_exception(self):
        """测试爬虫任务执行异常"""
        context = JobContextModel(
            job_id="jiazi_crawl",
            job_name="夹子榜爬取任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now()
        )
        job_data = {"type": "jiazi"}
        
        # 模拟异步睡眠抛出异常
        with patch('asyncio.sleep', side_effect=Exception("网络错误")):
            result = await self.handler.execute(context, job_data)
            
            assert result.success is False
            assert "爬虫任务执行失败" in result.message
            assert result.exception is not None






class TestJobHandlerIntegration:
    """任务处理器集成测试"""
    
    def test_all_handlers_inherit_from_base(self):
        """测试所有处理器都继承自基类"""
        from app.schedule import BaseJobHandler
        
        crawl_handler = CrawlJobHandler()
        
        assert isinstance(crawl_handler, BaseJobHandler)
        
    def test_all_handlers_have_logger(self):
        """测试所有处理器都有日志记录器"""
        crawl_handler = CrawlJobHandler()
        
        assert hasattr(crawl_handler, 'logger')
        
        assert crawl_handler.logger.name == 'CrawlJobHandler'
        
    def test_job_context_basic_validation(self):
        """测试任务上下文基本验证"""
        # 测试上下文创建
        context = JobContextModel(
            job_id="test_job",
            job_name="测试任务",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now()
        )
        
        # 验证基本属性
        assert context.job_id == "test_job"
        assert context.job_name == "测试任务"
        
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