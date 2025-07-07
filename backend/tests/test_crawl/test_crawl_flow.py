"""
爬取流程测试 - 使用 pytest-mock
"""
import pytest
from typing import Dict, Any

from app.crawl.crawl_flow import CrawlFlow
from app.crawl.parser import DataType, ParsedItem


class TestCrawlFlow:
    """爬取流程测试类"""

    def test_init(self, mocker):
        """测试爬取流程初始化"""
        mock_settings = mocker.patch('app.crawl.crawl_flow.settings')
        mock_settings.crawler.request_delay = 1.0
        mocker.patch('app.crawl.crawl_flow.CrawlConfig')
        mocker.patch('app.crawl.crawl_flow.HttpClient')
        mocker.patch('app.crawl.crawl_flow.Parser')
        
        flow = CrawlFlow()
        
        assert flow is not None
        assert flow.crawled_book_ids == set()
        assert flow.books_data == []
        assert flow.pages_data == []
        assert flow.rankings_data == []
        assert isinstance(flow.stats, dict)

    @pytest.mark.asyncio
    async def test_execute_crawl_task_invalid_task_id(self, mocker):
        """测试执行无效任务ID的爬取任务"""
        mock_settings = mocker.patch('app.crawl.crawl_flow.settings')
        mock_settings.crawler.request_delay = 0.1
        
        mock_config_class = mocker.patch('app.crawl.crawl_flow.CrawlConfig')
        mock_config = mock_config_class.return_value
        mock_config.get_task_config.return_value = None
        
        mocker.patch('app.crawl.crawl_flow.HttpClient')
        mocker.patch('app.crawl.crawl_flow.Parser')
        
        flow = CrawlFlow()
        result = await flow.execute_crawl_task("invalid_task")
        
        assert result["success"] is False
        assert result["error"] == "无法生成页面地址"

    def test_extract_book_ids_from_rankings(self, mocker):
        """测试从榜单中提取书籍ID"""
        mock_settings = mocker.patch('app.crawl.crawl_flow.settings')
        mock_settings.crawler.request_delay = 1.0
        mocker.patch('app.crawl.crawl_flow.CrawlConfig')
        mocker.patch('app.crawl.crawl_flow.HttpClient')
        mocker.patch('app.crawl.crawl_flow.Parser')
        
        flow = CrawlFlow()
        rankings = [
            {
                "books": [
                    {"book_id": 12345},
                    {"book_id": 12346}
                ]
            },
            {
                "books": [
                    {"book_id": 12347}
                ]
            }
        ]
        
        book_ids = flow._extract_book_ids_from_rankings(rankings)
        
        assert book_ids == ["12345", "12346", "12347"]

    def test_deduplicate_book_ids(self, mocker):
        """测试书籍ID去重"""
        mock_settings = mocker.patch('app.crawl.crawl_flow.settings')
        mock_settings.crawler.request_delay = 1.0
        mocker.patch('app.crawl.crawl_flow.CrawlConfig')
        mocker.patch('app.crawl.crawl_flow.HttpClient')
        mocker.patch('app.crawl.crawl_flow.Parser')
        
        flow = CrawlFlow()
        book_ids = ["12345", "12346", "12345", "12347", "12346"]
        
        unique_ids = flow._deduplicate_book_ids(book_ids)
        
        assert unique_ids == ["12345", "12346", "12347"]
        assert flow.crawled_book_ids == {"12345", "12346", "12347"}

    def test_create_success_result(self, mocker):
        """测试创建成功结果"""
        mock_settings = mocker.patch('app.crawl.crawl_flow.settings')
        mock_settings.crawler.request_delay = 1.0
        mocker.patch('app.crawl.crawl_flow.CrawlConfig')
        mocker.patch('app.crawl.crawl_flow.HttpClient')
        mocker.patch('app.crawl.crawl_flow.Parser')
        
        flow = CrawlFlow()
        rankings = [{"rank_id": 1001}]
        books = [{"novel_id": 12345}]
        
        result = flow._create_success_result("test_task", "https://api.example.com", rankings, books)
        
        assert result["success"] is True
        assert result["task_id"] == "test_task"
        assert result["url"] == "https://api.example.com"
        assert result["rankings"] == rankings
        assert result["books"] == books

    def test_create_error_result(self, mocker):
        """测试创建错误结果"""
        mock_settings = mocker.patch('app.crawl.crawl_flow.settings')
        mock_settings.crawler.request_delay = 1.0
        mocker.patch('app.crawl.crawl_flow.CrawlConfig')
        mocker.patch('app.crawl.crawl_flow.HttpClient')
        mocker.patch('app.crawl.crawl_flow.Parser')
        
        flow = CrawlFlow()
        result = flow._create_error_result("test_task", "Test error")
        
        assert result["success"] is False
        assert result["task_id"] == "test_task"
        assert result["error"] == "Test error"

    @pytest.mark.asyncio
    async def test_close(self, mocker):
        """测试关闭资源"""
        mock_settings = mocker.patch('app.crawl.crawl_flow.settings')
        mock_settings.crawler.request_delay = 1.0
        
        mock_client_class = mocker.patch('app.crawl.crawl_flow.HttpClient')
        mock_client = mock_client_class.return_value
        mock_client.close = mocker.AsyncMock()
        
        mocker.patch('app.crawl.crawl_flow.CrawlConfig')
        mocker.patch('app.crawl.crawl_flow.Parser')
        
        flow = CrawlFlow()
        await flow.close()
        
        mock_client.close.assert_called_once()