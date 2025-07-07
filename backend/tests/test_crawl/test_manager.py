"""
爬虫管理器测试 - 使用 pytest-mock
"""
import pytest
from typing import Dict, Any, List

from app.crawl.manager import CrawlerManager


class TestCrawlerManager:
    """爬虫管理器测试类"""

    def test_init_with_default_delay(self, mocker):
        """测试使用默认延迟初始化"""
        mock_settings = mocker.patch('app.crawl.manager.settings')
        mock_settings.crawler.request_delay = 1.5
        mocker.patch('app.crawl.manager.CrawlFlow')
        
        manager = CrawlerManager()
        
        assert manager.request_delay == 1.5

    def test_init_with_custom_delay(self, mocker):
        """测试使用自定义延迟初始化"""
        mock_settings = mocker.patch('app.crawl.manager.settings')
        mock_settings.crawler.request_delay = 1.5
        mocker.patch('app.crawl.manager.CrawlFlow')
        
        manager = CrawlerManager(request_delay=2.0)
        
        assert manager.request_delay == 2.0

    @pytest.mark.asyncio
    async def test_crawl_single_task_string(self, mocker, mock_successful_crawl_result):
        """测试爬取单个任务（字符串输入）"""
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.execute_crawl_task = mocker.AsyncMock(return_value=mock_successful_crawl_result)
        
        manager = CrawlerManager()
        results = await manager.crawl("test_task_1")
        
        assert len(results) == 1
        assert results[0] == mock_successful_crawl_result
        mock_flow.execute_crawl_task.assert_called_once_with("test_task_1")

    @pytest.mark.asyncio
    async def test_crawl_single_task_list(self, mocker, mock_successful_crawl_result):
        """测试爬取单个任务（列表输入）"""
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.execute_multiple_tasks = mocker.AsyncMock(return_value=[mock_successful_crawl_result])
        
        manager = CrawlerManager()
        results = await manager.crawl(["test_task_1"])
        
        assert len(results) == 1
        assert results[0] == mock_successful_crawl_result
        mock_flow.execute_multiple_tasks.assert_called_once_with(["test_task_1"])

    @pytest.mark.asyncio
    async def test_crawl_multiple_tasks(self, mocker):
        """测试爬取多个任务"""
        mock_results = [
            {"task_id": "task1", "success": True},
            {"task_id": "task2", "success": True}
        ]
        
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.execute_multiple_tasks = mocker.AsyncMock(return_value=mock_results)
        
        manager = CrawlerManager()
        results = await manager.crawl(["task1", "task2"])
        
        assert len(results) == 2
        assert results == mock_results
        mock_flow.execute_multiple_tasks.assert_called_once_with(["task1", "task2"])

    @pytest.mark.asyncio
    async def test_crawl_failed_task(self, mocker, mock_failed_crawl_result):
        """测试爬取失败的任务"""
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.execute_crawl_task = mocker.AsyncMock(return_value=mock_failed_crawl_result)
        
        manager = CrawlerManager()
        results = await manager.crawl("invalid_task")
        
        assert len(results) == 1
        assert results[0]["success"] is False
        assert results[0]["error"] == "无法生成页面地址"

    @pytest.mark.asyncio
    async def test_crawl_all_tasks(self, mocker):
        """测试爬取所有任务"""
        mock_config_class = mocker.patch('app.crawl.base.CrawlConfig')
        mock_config = mock_config_class.return_value
        mock_config.get_all_tasks.return_value = [
            {"id": "task1"},
            {"id": "task2"},
            {"id": "task3"}
        ]
        
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.execute_multiple_tasks = mocker.AsyncMock(return_value=[
            {"task_id": "task1", "success": True},
            {"task_id": "task2", "success": True},
            {"task_id": "task3", "success": True}
        ])
        
        manager = CrawlerManager()
        results = await manager.crawl_all_tasks()
        
        assert len(results) == 3
        mock_flow.execute_multiple_tasks.assert_called_once_with(["task1", "task2", "task3"])

    @pytest.mark.asyncio
    async def test_crawl_tasks_by_category_exact_match(self, mocker):
        """测试根据分类爬取任务（精确匹配）"""
        mock_config_class = mocker.patch('app.crawl.base.CrawlConfig')
        mock_config = mock_config_class.return_value
        mock_config.get_all_tasks.return_value = [
            {"id": "romance"},
            {"id": "romance.modern"},
            {"id": "fantasy"},
            {"id": "fantasy.magic"}
        ]
        
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.execute_multiple_tasks = mocker.AsyncMock(return_value=[
            {"task_id": "romance", "success": True},
            {"task_id": "romance.modern", "success": True}
        ])
        
        manager = CrawlerManager()
        results = await manager.crawl_tasks_by_category("romance")
        
        assert len(results) == 2
        mock_flow.execute_multiple_tasks.assert_called_once_with(["romance", "romance.modern"])

    @pytest.mark.asyncio
    async def test_crawl_tasks_by_category_no_match(self, mocker):
        """测试根据分类爬取任务（无匹配）"""
        mock_config_class = mocker.patch('app.crawl.base.CrawlConfig')
        mock_config = mock_config_class.return_value
        mock_config.get_all_tasks.return_value = [
            {"id": "romance"},
            {"id": "fantasy"}
        ]
        
        manager = CrawlerManager()
        results = await manager.crawl_tasks_by_category("nonexistent")
        
        assert results == []

    @pytest.mark.asyncio
    async def test_crawl_tasks_by_category_prefix_match(self, mocker):
        """测试根据分类爬取任务（前缀匹配）"""
        mock_config_class = mocker.patch('app.crawl.base.CrawlConfig')
        mock_config = mock_config_class.return_value
        mock_config.get_all_tasks.return_value = [
            {"id": "romance"},
            {"id": "romance.modern"},
            {"id": "romance.ancient"},
            {"id": "fantasy"}
        ]
        
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.execute_multiple_tasks = mocker.AsyncMock(return_value=[
            {"task_id": "romance", "success": True},
            {"task_id": "romance.modern", "success": True},
            {"task_id": "romance.ancient", "success": True}
        ])
        
        manager = CrawlerManager()
        results = await manager.crawl_tasks_by_category("romance")
        
        assert len(results) == 3
        expected_task_ids = ["romance", "romance.modern", "romance.ancient"]
        mock_flow.execute_multiple_tasks.assert_called_once_with(expected_task_ids)

    def test_get_stats(self, mocker):
        """测试获取统计信息"""
        mock_stats = {
            "books_crawled": 10,
            "total_requests": 50,
            "execution_time": 30.5
        }
        
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.get_stats.return_value = mock_stats
        
        manager = CrawlerManager()
        stats = manager.get_stats()
        
        assert stats == mock_stats
        mock_flow.get_stats.assert_called_once()

    def test_get_data(self, mocker):
        """测试获取爬取数据"""
        mock_data = {
            "books": [
                {"novel_id": 12345, "title": "测试小说1"},
                {"novel_id": 12346, "title": "测试小说2"}
            ]
        }
        
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.get_all_data.return_value = mock_data
        
        manager = CrawlerManager()
        data = manager.get_data()
        
        assert data == mock_data
        mock_flow.get_all_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, mocker):
        """测试关闭连接"""
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.close = mocker.AsyncMock()
        
        manager = CrawlerManager()
        await manager.close()
        
        mock_flow.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_crawl_empty_task_list(self, mocker):
        """测试爬取空任务列表"""
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.execute_multiple_tasks = mocker.AsyncMock(return_value=[])
        
        manager = CrawlerManager()
        results = await manager.crawl([])
        
        assert results == []
        mock_flow.execute_multiple_tasks.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_crawl_with_exception(self, mocker):
        """测试爬取过程中出现异常"""
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.execute_crawl_task = mocker.AsyncMock(side_effect=Exception("Unexpected error"))
        
        manager = CrawlerManager()
        
        # 验证异常会向上传播
        with pytest.raises(Exception, match="Unexpected error"):
            await manager.crawl("test_task")

    @pytest.mark.asyncio
    async def test_crawl_mixed_success_and_failure(self, mocker):
        """测试混合成功和失败的爬取结果"""
        mixed_results = [
            {"task_id": "task1", "success": True, "books_crawled": 5},
            {"task_id": "task2", "success": False, "error": "Network error"},
            {"task_id": "task3", "success": True, "books_crawled": 3}
        ]
        
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.execute_multiple_tasks = mocker.AsyncMock(return_value=mixed_results)
        
        manager = CrawlerManager()
        results = await manager.crawl(["task1", "task2", "task3"])
        
        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert results[2]["success"] is True

    @pytest.mark.asyncio
    async def test_crawl_all_tasks_empty_config(self, mocker):
        """测试爬取所有任务（空配置）"""
        mock_config_class = mocker.patch('app.crawl.base.CrawlConfig')
        mock_config = mock_config_class.return_value
        mock_config.get_all_tasks.return_value = []
        
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.execute_multiple_tasks = mocker.AsyncMock(return_value=[])
        
        manager = CrawlerManager()
        results = await manager.crawl_all_tasks()
        
        assert results == []
        mock_flow.execute_multiple_tasks.assert_called_once_with([])

    def test_get_stats_empty_stats(self, mocker):
        """测试获取空统计信息"""
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.get_stats.return_value = {}
        
        manager = CrawlerManager()
        stats = manager.get_stats()
        
        assert stats == {}

    def test_get_data_empty_data(self, mocker):
        """测试获取空数据"""
        mock_flow_class = mocker.patch('app.crawl.manager.CrawlFlow')
        mock_flow = mock_flow_class.return_value
        mock_flow.get_all_data.return_value = {"books": []}
        
        manager = CrawlerManager()
        data = manager.get_data()
        
        assert data == {"books": []}