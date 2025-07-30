"""
任务处理器测试

测试各种任务处理器的功能，使用mock避免实际的爬虫执行
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.schedule import JobResultModel, JobStatus
from app.schedule.handlers import BaseJobHandler, CrawlJobHandler, ReportJobHandler


class TestBaseJobHandler:
    """测试BaseJobHandler基类"""

    class TestJobHandler(BaseJobHandler):
        """测试用的具体处理器类"""

        async def execute(self, page_ids=None):
            # 模拟一些执行时间
            import asyncio
            await asyncio.sleep(0.001)  # 1ms
            return JobResultModel.success_result("测试任务执行成功")

    @pytest.fixture
    def handler(self):
        """创建测试处理器实例"""
        return self.TestJobHandler()

    @pytest.mark.asyncio
    async def test_execute_success(self, handler):
        """测试执行成功"""
        result = await handler.execute(page_ids=["test_page"])

        assert result.success is True
        assert result.message == "测试任务执行成功"

    def test_abstract_execute_method(self):
        """测试抽象方法"""
        # 不能直接实例化抽象类
        with pytest.raises(TypeError):
            BaseJobHandler()


class TestCrawlJobHandler:
    """测试CrawlJobHandler类"""

    @pytest.fixture
    def handler(self, mocker):
        """创建CrawlJobHandler实例"""
        # Mock CrawlConfig 避免文件依赖
        mock_config = mocker.MagicMock()
        mock_config.validate_page_id.return_value = True
        
        with mocker.patch('app.schedule.handlers.CrawlConfig', return_value=mock_config):
            handler = CrawlJobHandler()
            return handler

    @pytest.fixture
    def mock_crawl_result(self):
        """模拟爬取结果"""
        return {
            "success": {"success": True, "books_crawled": 25, "page_id": "test_page"},
            "failure": {"success": False, "error_message": "爬取失败"}
        }

    @pytest.mark.asyncio
    async def test_execute_success_single_page(
        self, handler, mocker, mock_crawl_result
    ):
        """测试单页面执行成功"""
        # 设置模拟
        mock_config = mocker.patch.object(handler, "config")
        mock_config.validate_page_id.return_value = True

        mock_crawler = mocker.patch("app.schedule.handlers.CrawlFlow")
        # execute_crawl_task 是async方法，需要使用AsyncMock
        mock_crawler.return_value.execute_crawl_task = mocker.AsyncMock(
            return_value=mock_crawl_result["success"]
        )
        mock_crawler.return_value.close = mocker.AsyncMock()

        result = await handler.execute(page_ids=["test_page"])

        assert result.success is True
        assert "共爬取 25 本书籍" in result.message
        assert result.data["page_id"] == "test_page"
        assert result.data["books_crawled"] == 25

        mock_config.validate_page_id.assert_called_once_with("test_page")
        mock_crawler.return_value.execute_crawl_task.assert_called_once_with(
            "test_page"
        )
        mock_crawler.return_value.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_empty_page_ids(self, handler):
        """测试空页面ID列表"""
        result = await handler.execute(page_ids=[])

        assert result.success is False
        assert "任务数据为空" in result.message

    @pytest.mark.asyncio
    async def test_execute_multiple_page_ids(self, handler, mocker):
        """测试多页面ID处理"""
        # Mock 配置和爬虫
        mock_config = mocker.patch.object(handler, "config")
        mock_config.validate_page_id.return_value = True

        mock_crawler = mocker.patch("app.schedule.handlers.CrawlFlow")
        mock_crawler.return_value.execute_crawl_task = mocker.AsyncMock(
            return_value={"success": False, "error_message": "页面不存在"}
        )
        mock_crawler.return_value.close = mocker.AsyncMock()

        result = await handler.execute(page_ids=["page1", "page2"])

        assert result.success is False
        assert "多页面爬取全部失败" in result.message

    @pytest.mark.asyncio
    async def test_execute_invalid_page_id(self, handler, mocker):
        """测试无效页面ID"""
        mock_config = mocker.patch.object(handler, "config")
        mock_config.validate_page_id.return_value = False

        result = await handler.execute(page_ids=["invalid_page"])

        assert result.success is False
        assert "无效的页面ID" in result.message
        mock_config.validate_page_id.assert_called_once_with("invalid_page")

    @pytest.mark.asyncio
    async def test_execute_crawl_failure(self, handler, mocker, mock_crawl_result):
        """测试爬取失败"""
        # 设置模拟
        mock_config = mocker.patch.object(handler, "config")
        mock_config.validate_page_id.return_value = True

        mock_crawler = mocker.patch("app.schedule.handlers.CrawlFlow")
        # execute_crawl_task 是async方法，需要使用AsyncMock
        mock_crawler.return_value.execute_crawl_task = mocker.AsyncMock(
            return_value=mock_crawl_result["failure"]
        )
        mock_crawler.return_value.close = mocker.AsyncMock()

        result = await handler.execute(page_ids=["test_page"])

        assert result.success is False
        assert "爬取失败" in result.message
        mock_crawler.return_value.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_crawl_exception(self, handler, mocker):
        """测试爬取异常"""
        # 设置模拟
        mock_config = mocker.patch.object(handler, "config")
        mock_config.validate_page_id.return_value = True

        mock_crawler = mocker.patch("app.schedule.handlers.CrawlFlow")
        # execute_crawl_task 是async方法，需要使用AsyncMock
        mock_crawler.return_value.execute_crawl_task = mocker.AsyncMock(
            side_effect=Exception("爬取异常")
        )
        mock_crawler.return_value.close = mocker.AsyncMock()

        result = await handler.execute(page_ids=["test_page"])

        assert result.success is False
        assert "爬取异常: 爬取异常" in result.message
        mock_crawler.return_value.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_crawler_close_exception(self, handler, mocker):
        """测试爬虫关闭异常"""
        # 设置模拟
        mock_config = mocker.patch.object(handler, "config")
        mock_config.validate_page_id.return_value = True

        mock_crawler = mocker.patch("app.schedule.handlers.CrawlFlow")
        # execute_crawl_task 是async方法，需要使用AsyncMock
        mock_crawler.return_value.execute_crawl_task = mocker.AsyncMock(
            return_value={"success": True, "books_crawled": 10}
        )
        mock_crawler.return_value.close = mocker.AsyncMock(
            side_effect=Exception("关闭异常")
        )

        result = await handler.execute(page_ids=["test_page"])

        # 关闭异常会导致整个任务失败（被外层catch块捕获）
        assert result.success is False
        assert "爬取异常: 关闭异常" in result.message

    def test_initialization(self, handler):
        """测试初始化"""
        assert handler.config is not None
        assert hasattr(handler, "logger")
        assert hasattr(handler, "settings")


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
        assert hasattr(handler, "logger")
        assert hasattr(handler, "settings")


class TestJobResultModel:
    """测试JobResultModel类"""

    def test_success_result_creation(self):
        """测试创建成功结果"""
        result = JobResultModel.success_result("操作成功", {"count": 5})

        assert result.success is True
        assert result.message == "操作成功"
        assert result.data == {"count": 5}
        assert result.exception is None
        assert result.execution_time is None  # 默认时间为None

    def test_error_result_creation(self):
        """测试创建错误结果"""
        test_exception = Exception("测试异常")
        result = JobResultModel.error_result("操作失败", test_exception)

        assert result.success is False
        assert result.message == "操作失败"
        assert result.data is None
        assert result.exception == "测试异常"
        assert result.execution_time is None  # 默认时间为None

    def test_error_result_without_exception(self):
        """测试创建无异常的错误结果"""
        result = JobResultModel.error_result("操作失败")

        assert result.success is False
        assert result.message == "操作失败"
        assert result.exception is None


class TestIntegration:
    """集成测试"""

    @pytest.fixture
    def mock_scheduler_integration(self):
        """集成测试用的Mock调度器"""
        from unittest.mock import MagicMock
        scheduler = MagicMock()
        scheduler._update_job_status = AsyncMock()
        return scheduler

    @pytest.mark.asyncio
    async def test_crawl_handler_full_workflow(self, mock_scheduler_integration, mocker):
        """测试爬虫处理器完整工作流程"""
        # Mock CrawlConfig 避免文件依赖
        mock_config = mocker.MagicMock()
        mock_config.validate_page_id.return_value = True
        
        mocker.patch('app.schedule.handlers.CrawlConfig', return_value=mock_config)
        handler = CrawlJobHandler()

        # 模拟爬虫
        mock_crawler = mocker.patch("app.schedule.handlers.CrawlFlow")
        
        # 添加执行延迟的Mock
        async def mock_crawl_task(page_id):
            import asyncio
            await asyncio.sleep(0.001)  # 1ms延迟
            return {"success": True, "books_crawled": 15, "rankings_crawled": 5, "page_id": "jiazi"}
        
        mock_crawler.return_value.execute_crawl_task = mocker.AsyncMock(
            side_effect=mock_crawl_task
        )
        mock_crawler.return_value.close = mocker.AsyncMock()

        # 执行任务
        result = await handler.execute(page_ids=["jiazi"])

        # 验证结果
        assert result.success is True
        assert "共爬取 15 本书籍" in result.message
        assert result.data["page_id"] == "jiazi"
        assert result.data["books_crawled"] == 15
        assert result.data["rankings_crawled"] == 5

        # 验证调用
        mock_config.validate_page_id.assert_called_once_with("jiazi")
        mock_crawler.return_value.execute_crawl_task.assert_called_once_with("jiazi")
        mock_crawler.return_value.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_multiple_pages_workflow(self, mocker):
        """测试多页面爬虫处理器工作流程"""
        # Mock CrawlConfig 避免文件依赖
        mock_config = mocker.MagicMock()
        mock_config.validate_page_id.return_value = True
        
        mocker.patch('app.schedule.handlers.CrawlConfig', return_value=mock_config)
        handler = CrawlJobHandler()

        # 模拟爬虫
        mock_crawler = mocker.patch("app.schedule.handlers.CrawlFlow")
        mock_crawler.return_value.close = mocker.AsyncMock()

        call_count = 0
        async def mock_execute_task(page_id):
            nonlocal call_count
            call_count += 1
            # 第一个页面成功，第二个页面失败
            if call_count == 1:
                return {"success": True, "books_crawled": 10, "rankings_crawled": 3, "page_id": page_id}
            else:
                return {"success": False, "error_message": "网络超时"}

        mock_crawler.return_value.execute_crawl_task = mocker.AsyncMock(
            side_effect=mock_execute_task
        )

        result = await handler.execute(page_ids=["page1", "page2"])

        # 验证结果 - 部分成功
        assert result.success is True
        assert "多页面爬取部分成功" in result.message
        assert result.data["total_pages"] == 2
        assert len(result.data["success_pages"]) == 1
        assert len(result.data["failed_pages"]) == 1
        assert result.data["total_books"] == 10
        assert result.data["total_rankings"] == 3

        # 验证调用次数
        assert mock_crawler.return_value.execute_crawl_task.call_count == 2
        assert mock_crawler.return_value.close.call_count == 2
