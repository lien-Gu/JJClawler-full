"""
任务处理器测试文件
测试schedule.handlers模块的关键功能
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.schedule.handlers import BaseJobHandler, CrawlJobHandler, ReportJobHandler
from app.models.schedule import JobContextModel, JobResultModel


class TestBaseJobHandler:
    """测试BaseJobHandler基类"""
    
    class TestJobHandler(BaseJobHandler):
        """测试用的具体处理器类"""
        
        async def execute(self, page_ids=None):
            return JobResultModel.success_result("测试任务执行成功")
    
    @pytest.fixture
    def handler(self):
        """创建测试处理器实例"""
        return self.TestJobHandler()
    
    @pytest.fixture
    def job_context(self):
        """创建任务上下文"""
        return JobContextModel(
            job_id="test_job",
            job_name="test_job",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_try(self, handler, job_context):
        """测试第一次执行成功"""
        result = await handler.execute_with_retry(context=job_context, page_ids=["test_page"])
        
        assert result.success is True
        assert result.message == "测试任务执行成功"
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_retry(self, handler, job_context):
        """测试重试后成功"""
        # 模拟第一次失败，第二次成功
        call_count = 0
        
        async def mock_execute(page_ids=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return JobResultModel.error_result("第一次执行失败")
            else:
                return JobResultModel.success_result("重试后执行成功")
        
        handler.execute = mock_execute
        
        result = await handler.execute_with_retry(context=job_context, page_ids=["test_page"])
        
        assert result.success is True
        assert result.message == "重试后执行成功"
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries_exceeded(self, handler, job_context):
        """测试超过最大重试次数"""
        # 模拟总是失败
        async def mock_execute(page_ids=None):
            return JobResultModel.error_result("执行失败")
        
        handler.execute = mock_execute
        handler.max_retries = 2  # 设置最大重试次数为2
        
        result = await handler.execute_with_retry(context=job_context, page_ids=["test_page"])
        
        assert result.success is False
        assert "已重试 2 次" in result.message
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_exception_handling(self, handler, job_context):
        """测试异常处理"""
        # 模拟抛出异常
        async def mock_execute(page_ids=None):
            raise Exception("执行异常")
        
        handler.execute = mock_execute
        handler.max_retries = 1
        
        result = await handler.execute_with_retry(context=job_context, page_ids=["test_page"])
        
        assert result.success is False
        assert "已重试 1 次" in result.message
        assert result.execution_time > 0
    
    @patch('asyncio.sleep')
    @pytest.mark.asyncio
    async def test_execute_with_retry_delay(self, mock_sleep, handler, job_context):
        """测试重试延迟"""
        # 模拟第一次异常，第二次成功
        call_count = 0
        
        async def mock_execute(page_ids=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("第一次执行异常")
            else:
                return JobResultModel.success_result("重试后执行成功")
        
        handler.execute = mock_execute
        handler.max_retries = 1
        
        result = await handler.execute_with_retry(context=job_context, page_ids=["test_page"])
        
        assert result.success is True
        mock_sleep.assert_called_once()  # 验证调用了sleep
    
    def test_abstract_execute_method(self):
        """测试抽象方法"""
        # 不能直接实例化抽象类
        with pytest.raises(TypeError):
            BaseJobHandler()


class TestCrawlJobHandler:
    """测试CrawlJobHandler类"""
    
    @pytest.fixture
    def handler(self):
        """创建CrawlJobHandler实例"""
        return CrawlJobHandler()
    
    @pytest.fixture
    def mock_config(self):
        """模拟CrawlConfig"""
        config = Mock()
        config.validate_page_id.return_value = True
        return config
    
    @pytest.fixture
    def mock_crawler(self):
        """模拟CrawlFlow"""
        crawler = Mock()
        crawler.execute_crawl_task = AsyncMock()
        crawler.close = AsyncMock()
        return crawler
    
    @pytest.mark.asyncio
    async def test_execute_success_single_page(self, handler, mock_config, mock_crawler):
        """测试单页面执行成功"""
        # 设置模拟
        handler.config = mock_config
        mock_crawler.execute_crawl_task.return_value = {
            "success": True,
            "books_crawled": 25,
            "page_id": "test_page"
        }
        
        with patch('app.schedule.handlers.CrawlFlow', return_value=mock_crawler):
            result = await handler.execute(page_ids=["test_page"])
        
        assert result.success is True
        assert "共爬取 25 本书籍" in result.message
        assert result.data["page_id"] == "test_page"
        assert result.data["books_crawled"] == 25
        
        mock_config.validate_page_id.assert_called_once_with("test_page")
        mock_crawler.execute_crawl_task.assert_called_once_with("test_page")
        mock_crawler.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_empty_page_ids(self, handler):
        """测试空页面ID列表"""
        result = await handler.execute(page_ids=[])
        
        assert result.success is False
        assert "任务数据为空" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_multiple_page_ids(self, handler):
        """测试多页面ID（应该失败）"""
        result = await handler.execute(page_ids=["page1", "page2"])
        
        assert result.success is False
        assert "应该只包含一个页面ID" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_invalid_page_id(self, handler, mock_config):
        """测试无效页面ID"""
        handler.config = mock_config
        mock_config.validate_page_id.return_value = False
        
        result = await handler.execute(page_ids=["invalid_page"])
        
        assert result.success is False
        assert "无效的页面ID" in result.message
        mock_config.validate_page_id.assert_called_once_with("invalid_page")
    
    @pytest.mark.asyncio
    async def test_execute_crawl_failure(self, handler, mock_config, mock_crawler):
        """测试爬取失败"""
        # 设置模拟
        handler.config = mock_config
        mock_crawler.execute_crawl_task.return_value = {
            "success": False,
            "error_message": "网络连接失败"
        }
        
        with patch('app.schedule.handlers.CrawlFlow', return_value=mock_crawler):
            result = await handler.execute(page_ids=["test_page"])
        
        assert result.success is False
        assert "爬取失败: 网络连接失败" in result.message
        mock_crawler.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_crawl_exception(self, handler, mock_config, mock_crawler):
        """测试爬取异常"""
        # 设置模拟
        handler.config = mock_config
        mock_crawler.execute_crawl_task.side_effect = Exception("爬取异常")
        
        with patch('app.schedule.handlers.CrawlFlow', return_value=mock_crawler):
            result = await handler.execute(page_ids=["test_page"])
        
        assert result.success is False
        assert "爬取异常: 爬取异常" in result.message
        mock_crawler.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_crawler_close_exception(self, handler, mock_config, mock_crawler):
        """测试爬虫关闭异常"""
        # 设置模拟
        handler.config = mock_config
        mock_crawler.execute_crawl_task.return_value = {
            "success": True,
            "books_crawled": 10
        }
        mock_crawler.close.side_effect = Exception("关闭异常")
        
        with patch('app.schedule.handlers.CrawlFlow', return_value=mock_crawler):
            result = await handler.execute(page_ids=["test_page"])
        
        # 即使关闭异常，任务仍应该成功（因为爬取成功了）
        assert result.success is True
        assert "共爬取 10 本书籍" in result.message
    
    def test_initialization(self, handler):
        """测试初始化"""
        assert handler.config is not None
        assert hasattr(handler, 'logger')
        assert hasattr(handler, 'settings')
        assert hasattr(handler, 'max_retries')


class TestReportJobHandler:
    """测试ReportJobHandler类"""
    
    @pytest.fixture
    def handler(self):
        """创建ReportJobHandler实例"""
        return ReportJobHandler()
    
    @pytest.mark.asyncio
    async def test_execute_not_implemented(self, handler):
        """测试未实现的execute方法"""
        result = await handler.execute(page_ids=["test_page"])
        
        assert result.success is False
        assert "暂时未实现" in result.message
    
    def test_initialization(self, handler):
        """测试初始化"""
        assert hasattr(handler, 'logger')
        assert hasattr(handler, 'settings')
        assert hasattr(handler, 'max_retries')


class TestJobResultModel:
    """测试JobResultModel类"""
    
    def test_success_result_creation(self):
        """测试创建成功结果"""
        result = JobResultModel.success_result("操作成功", {"count": 5})
        
        assert result.success is True
        assert result.message == "操作成功"
        assert result.data == {"count": 5}
        assert result.exception is None
        assert isinstance(result.timestamp, datetime)
    
    def test_error_result_creation(self):
        """测试创建错误结果"""
        test_exception = Exception("测试异常")
        result = JobResultModel.error_result("操作失败", test_exception)
        
        assert result.success is False
        assert result.message == "操作失败"
        assert result.data is None
        assert result.exception == "测试异常"
        assert isinstance(result.timestamp, datetime)
    
    def test_error_result_without_exception(self):
        """测试创建无异常的错误结果"""
        result = JobResultModel.error_result("操作失败")
        
        assert result.success is False
        assert result.message == "操作失败"
        assert result.exception is None


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def job_context(self):
        """创建任务上下文"""
        return JobContextModel(
            job_id="integration_test_job",
            job_name="integration_test_job",
            trigger_time=datetime.now(),
            scheduled_time=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_crawl_handler_full_workflow(self, job_context):
        """测试爬虫处理器完整工作流程"""
        handler = CrawlJobHandler()
        
        # 模拟配置
        mock_config = Mock()
        mock_config.validate_page_id.return_value = True
        handler.config = mock_config
        
        # 模拟爬虫
        mock_crawler = Mock()
        mock_crawler.execute_crawl_task = AsyncMock()
        mock_crawler.execute_crawl_task.return_value = {
            "success": True,
            "books_crawled": 15,
            "page_id": "jiazi"
        }
        mock_crawler.close = AsyncMock()
        
        with patch('app.schedule.handlers.CrawlFlow', return_value=mock_crawler):
            # 执行带重试的任务
            result = await handler.execute_with_retry(
                context=job_context,
                page_ids=["jiazi"]
            )
        
        # 验证结果
        assert result.success is True
        assert "共爬取 15 本书籍" in result.message
        assert result.data["page_id"] == "jiazi"
        assert result.data["books_crawled"] == 15
        assert result.execution_time > 0
        
        # 验证调用
        mock_config.validate_page_id.assert_called_once_with("jiazi")
        mock_crawler.execute_crawl_task.assert_called_once_with("jiazi")
        mock_crawler.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handler_retry_workflow(self, job_context):
        """测试处理器重试工作流程"""
        handler = CrawlJobHandler()
        handler.max_retries = 2
        
        # 模拟配置
        mock_config = Mock()
        mock_config.validate_page_id.return_value = True
        handler.config = mock_config
        
        # 模拟爬虫（第一次失败，第二次成功）
        mock_crawler = Mock()
        mock_crawler.execute_crawl_task = AsyncMock()
        mock_crawler.close = AsyncMock()
        
        call_count = 0
        async def mock_execute_task(page_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"success": False, "error_message": "网络超时"}
            else:
                return {"success": True, "books_crawled": 20, "page_id": page_id}
        
        mock_crawler.execute_crawl_task.side_effect = mock_execute_task
        
        with patch('app.schedule.handlers.CrawlFlow', return_value=mock_crawler):
            result = await handler.execute_with_retry(
                context=job_context,
                page_ids=["test_page"]
            )
        
        # 验证结果
        assert result.success is True
        assert "共爬取 20 本书籍" in result.message
        assert result.execution_time > 0
        
        # 验证重试机制
        assert mock_crawler.execute_crawl_task.call_count == 2
        assert mock_crawler.close.call_count == 2


# 运行测试的示例
if __name__ == "__main__":
    pytest.main([__file__, "-v"])