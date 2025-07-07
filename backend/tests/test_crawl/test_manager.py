"""
爬虫管理器测试 - 使用 pytest-mock，专注逻辑验证
"""
import pytest

from app.crawl.manager import CrawlerManager


class TestCrawlerManager:
    """爬虫管理器测试类"""

    def test_init_with_default_delay(self, mock_crawler_manager_dependencies):
        """测试使用默认延迟初始化"""
        deps = mock_crawler_manager_dependencies

        manager = CrawlerManager()
        
        assert manager.request_delay == 1.5

    def test_init_with_custom_delay(self, mock_crawler_manager_dependencies):
        """测试使用自定义延迟初始化"""
        deps = mock_crawler_manager_dependencies
        
        manager = CrawlerManager(request_delay=2.0)
        
        assert manager.request_delay == 2.0

    @pytest.mark.asyncio
    async def test_crawl_single_task_string(self, mock_crawler_manager_dependencies, mock_successful_crawl_result):
        """测试爬取单个任务（字符串输入）"""
        deps = mock_crawler_manager_dependencies
        deps['flow'].execute_crawl_task.return_value = mock_successful_crawl_result
        
        manager = CrawlerManager()
        results = await manager.crawl("test_task_1")
        
        assert len(results) == 1
        assert results[0] == mock_successful_crawl_result
        deps['flow'].execute_crawl_task.assert_called_once_with("test_task_1")

    @pytest.mark.asyncio
    async def test_crawl_single_task_list(self, mock_crawler_manager_dependencies, mock_successful_crawl_result):
        """测试爬取单个任务（列表输入）"""
        deps = mock_crawler_manager_dependencies
        deps['flow'].execute_multiple_tasks.return_value = [mock_successful_crawl_result]
        
        manager = CrawlerManager()
        results = await manager.crawl(["test_task_1"])
        
        assert len(results) == 1
        assert results[0] == mock_successful_crawl_result
        deps['flow'].execute_multiple_tasks.assert_called_once_with(["test_task_1"])

    @pytest.mark.asyncio
    async def test_crawl_multiple_tasks(self, mock_crawler_manager_dependencies):
        """测试爬取多个任务"""
        deps = mock_crawler_manager_dependencies
        mock_results = [
            {"task_id": "task1", "success": True},
            {"task_id": "task2", "success": True}
        ]
        deps['flow'].execute_multiple_tasks.return_value = mock_results
        
        manager = CrawlerManager()
        results = await manager.crawl(["task1", "task2"])
        
        assert len(results) == 2
        assert results == mock_results
        deps['flow'].execute_multiple_tasks.assert_called_once_with(["task1", "task2"])

    @pytest.mark.asyncio
    async def test_crawl_failed_task(self, mock_crawler_manager_dependencies, mock_failed_crawl_result):
        """测试爬取失败的任务"""
        deps = mock_crawler_manager_dependencies
        deps['flow'].execute_crawl_task.return_value = mock_failed_crawl_result
        
        manager = CrawlerManager()
        results = await manager.crawl("invalid_task")
        
        assert len(results) == 1
        assert results[0]["success"] is False
        assert results[0]["error"] == "无法生成页面地址"

    @pytest.mark.asyncio
    async def test_crawl_all_tasks(self, mock_crawler_manager_dependencies):
        """测试爬取所有任务"""
        deps = mock_crawler_manager_dependencies
        deps['config'].get_all_tasks.return_value = [
            {"id": "task1"},
            {"id": "task2"},
            {"id": "task3"}
        ]
        deps['flow'].execute_multiple_tasks.return_value = [
            {"task_id": "task1", "success": True},
            {"task_id": "task2", "success": True},
            {"task_id": "task3", "success": True}
        ]
        
        manager = CrawlerManager()
        results = await manager.crawl_all_tasks()
        
        assert len(results) == 3
        deps['flow'].execute_multiple_tasks.assert_called_once_with(["task1", "task2", "task3"])

    @pytest.mark.asyncio
    async def test_crawl_tasks_by_category_exact_match(self, mock_crawler_manager_dependencies):
        """测试根据分类爬取任务（精确匹配）"""
        deps = mock_crawler_manager_dependencies
        deps['config'].get_all_tasks.return_value = [
            {"id": "romance"},
            {"id": "romance.modern"},
            {"id": "fantasy"},
            {"id": "fantasy.magic"}
        ]
        deps['flow'].execute_multiple_tasks.return_value = [
            {"task_id": "romance", "success": True},
            {"task_id": "romance.modern", "success": True}
        ]
        
        manager = CrawlerManager()
        results = await manager.crawl_tasks_by_category("romance")
        
        assert len(results) == 2
        deps['flow'].execute_multiple_tasks.assert_called_once_with(["romance", "romance.modern"])

    @pytest.mark.asyncio
    async def test_crawl_tasks_by_category_no_match(self, mock_crawler_manager_dependencies):
        """测试根据分类爬取任务（无匹配）"""
        deps = mock_crawler_manager_dependencies
        deps['config'].get_all_tasks.return_value = [
            {"id": "romance"},
            {"id": "fantasy"}
        ]
        
        manager = CrawlerManager()
        results = await manager.crawl_tasks_by_category("nonexistent")
        
        assert results == []

    @pytest.mark.asyncio
    async def test_crawl_tasks_by_category_prefix_match(self, mock_crawler_manager_dependencies):
        """测试根据分类爬取任务（前缀匹配）"""
        deps = mock_crawler_manager_dependencies
        deps['config'].get_all_tasks.return_value = [
            {"id": "romance"},
            {"id": "romance.modern"},
            {"id": "romance.ancient"},
            {"id": "fantasy"}
        ]
        deps['flow'].execute_multiple_tasks.return_value = [
            {"task_id": "romance", "success": True},
            {"task_id": "romance.modern", "success": True},
            {"task_id": "romance.ancient", "success": True}
        ]
        
        manager = CrawlerManager()
        results = await manager.crawl_tasks_by_category("romance")
        
        assert len(results) == 3
        expected_task_ids = ["romance", "romance.modern", "romance.ancient"]
        deps['flow'].execute_multiple_tasks.assert_called_once_with(expected_task_ids)

    def test_get_stats(self, mock_crawler_manager_dependencies):
        """测试获取统计信息"""
        deps = mock_crawler_manager_dependencies
        mock_stats = {
            "books_crawled": 10,
            "total_requests": 50,
            "execution_time": 30.5
        }
        deps['flow'].get_stats.return_value = mock_stats
        
        manager = CrawlerManager()
        manager.flow = deps['flow']  # 直接设置flow
        stats = manager.get_stats()
        
        assert stats == mock_stats
        deps['flow'].get_stats.assert_called_once()

    def test_get_data(self, mock_crawler_manager_dependencies):
        """测试获取爬取数据"""
        deps = mock_crawler_manager_dependencies
        mock_data = {
            "books": [
                {"novel_id": 12345, "title": "测试小说1"},
                {"novel_id": 12346, "title": "测试小说2"}
            ]
        }
        deps['flow'].get_all_data.return_value = mock_data
        
        manager = CrawlerManager()
        manager.flow = deps['flow']  # 直接设置flow
        data = manager.get_data()
        
        assert data == mock_data
        deps['flow'].get_all_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, mock_crawler_manager_dependencies):
        """测试关闭连接"""
        deps = mock_crawler_manager_dependencies
        
        manager = CrawlerManager()
        await manager.close()
        
        deps['flow'].close.assert_called_once()

    @pytest.mark.asyncio
    async def test_crawl_empty_task_list(self, mock_crawler_manager_dependencies):
        """测试爬取空任务列表"""
        deps = mock_crawler_manager_dependencies
        deps['flow'].execute_multiple_tasks.return_value = []
        
        manager = CrawlerManager()
        results = await manager.crawl([])
        
        assert results == []
        deps['flow'].execute_multiple_tasks.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_crawl_with_exception(self, mock_crawler_manager_dependencies):
        """测试爬取过程中出现异常"""
        deps = mock_crawler_manager_dependencies
        deps['flow'].execute_crawl_task.side_effect = Exception("Unexpected error")
        
        manager = CrawlerManager()
        
        # 验证异常会向上传播
        with pytest.raises(Exception, match="Unexpected error"):
            await manager.crawl("test_task")

    @pytest.mark.asyncio
    async def test_crawl_mixed_success_and_failure(self, mock_crawler_manager_dependencies):
        """测试混合成功和失败的爬取结果"""
        deps = mock_crawler_manager_dependencies
        mixed_results = [
            {"task_id": "task1", "success": True, "books_crawled": 5},
            {"task_id": "task2", "success": False, "error": "Network error"},
            {"task_id": "task3", "success": True, "books_crawled": 3}
        ]
        deps['flow'].execute_multiple_tasks.return_value = mixed_results
        
        manager = CrawlerManager()
        results = await manager.crawl(["task1", "task2", "task3"])
        
        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert results[2]["success"] is True

    @pytest.mark.asyncio
    async def test_crawl_all_tasks_empty_config(self, mock_crawler_manager_dependencies):
        """测试爬取所有任务（空配置）"""
        deps = mock_crawler_manager_dependencies
        deps['config'].get_all_tasks.return_value = []
        deps['flow'].execute_multiple_tasks.return_value = []
        
        manager = CrawlerManager()
        results = await manager.crawl_all_tasks()
        
        assert results == []
        deps['flow'].execute_multiple_tasks.assert_called_once_with([])

    def test_get_stats_empty_stats(self, mock_crawler_manager_dependencies):
        """测试获取空统计信息"""
        deps = mock_crawler_manager_dependencies
        deps['flow'].get_stats.return_value = {}
        
        manager = CrawlerManager()
        manager.flow = deps['flow']
        stats = manager.get_stats()
        
        assert stats == {}

    def test_get_data_empty_data(self, mock_crawler_manager_dependencies):
        """测试获取空数据"""
        deps = mock_crawler_manager_dependencies
        deps['flow'].get_all_data.return_value = {"books": []}
        
        manager = CrawlerManager()
        manager.flow = deps['flow']
        data = manager.get_data()
        
        assert data == {"books": []}
    
    @pytest.mark.asyncio
    async def test_crawl_with_data_storage(self, mock_crawler_manager_dependencies, mock_successful_crawl_result):
        """测试爬取任务并保存数据到数据库"""
        deps = mock_crawler_manager_dependencies
        deps['flow'].execute_crawl_task.return_value = mock_successful_crawl_result
        
        # Mock数据库服务方法的返回值
        mock_book = deps['book_service'].create_or_update_book.return_value
        mock_book.id = 1
        
        mock_ranking = deps['ranking_service'].create_or_update_ranking.return_value  
        mock_ranking.id = 100
        
        manager = CrawlerManager()
        results = await manager.crawl("test_task_1")
        
        # 验证爬取结果
        assert len(results) == 1
        assert results[0] == mock_successful_crawl_result
        
        # 验证数据库操作被调用
        deps['book_service'].create_or_update_book.assert_called()
        deps['ranking_service'].create_or_update_ranking.assert_called()
        deps['book_service'].batch_create_book_snapshots.assert_called_once()
        deps['ranking_service'].batch_create_ranking_snapshots.assert_called_once()
        deps['db'].commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_crawl_with_failed_result_no_storage(self, mock_crawler_manager_dependencies, mock_failed_crawl_result):
        """测试爬取失败时不保存数据"""
        deps = mock_crawler_manager_dependencies
        deps['flow'].execute_crawl_task.return_value = mock_failed_crawl_result
        
        manager = CrawlerManager()
        results = await manager.crawl("invalid_task")
        
        # 验证爬取结果
        assert len(results) == 1
        assert results[0]["success"] is False
        
        # 验证数据库操作没有被调用
        deps['book_service'].create_or_update_book.assert_not_called()
        deps['ranking_service'].create_or_update_ranking.assert_not_called()
        deps['db'].commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_crawl_data_storage_exception_handling(self, mock_crawler_manager_dependencies, mock_successful_crawl_result):
        """测试数据存储异常处理"""
        deps = mock_crawler_manager_dependencies
        deps['flow'].execute_crawl_task.return_value = mock_successful_crawl_result
        
        # Mock数据库操作抛出异常
        deps['book_service'].create_or_update_book.side_effect = Exception("Database error")
        
        manager = CrawlerManager()
        results = await manager.crawl("test_task_1")
        
        # 验证爬取结果依然返回
        assert len(results) == 1
        assert results[0] == mock_successful_crawl_result
        
        # 验证异常被捕获，事务被回滚
        deps['db'].rollback.assert_called_once()
        deps['logger'].error.assert_called()