"""
爬取流程测试
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.crawl.crawl_flow import CrawlFlow
from app.crawl.parser import DataType, ParsedItem


class TestCrawlFlow:
    """爬取流程测试类"""

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    def test_init(self, mock_parser_class, mock_client_class, mock_config_class):
        """测试爬取流程初始化"""
        flow = CrawlFlow()
        
        assert flow is not None
        assert flow.crawled_book_ids == set()
        assert flow.books_data == []
        assert flow.pages_data == []
        assert flow.rankings_data == []
        assert isinstance(flow.stats, dict)

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    async def test_execute_crawl_task_success(
        self, 
        mock_parser_class, 
        mock_client_class, 
        mock_config_class,
        mock_page_response,
        mock_book_detail_response
    ):
        """测试成功执行爬取任务"""
        # 设置模拟对象
        mock_config = mock_config_class.return_value
        mock_config.get_task_config.return_value = {"template": "page_rank", "params": {}}
        mock_config.build_url.return_value = "https://api.example.com/page"
        mock_config.templates = {"novel_detail": "https://api.example.com/novel/{novel_id}"}
        mock_config.params = {}
        
        mock_client = mock_client_class.return_value
        mock_client.get.side_effect = [mock_page_response, mock_book_detail_response]
        
        mock_parser = mock_parser_class.return_value
        mock_parser.parse.side_effect = [
            [ParsedItem(DataType.RANKING, {
                "rank_id": 1001,
                "rank_name": "测试榜单",
                "books": [{"book_id": 12345, "title": "测试小说"}]
            })],
            [ParsedItem(DataType.BOOK, {
                "novel_id": 12345,
                "title": "测试小说详情",
                "clicks": 10000
            })]
        ]
        
        flow = CrawlFlow()
        result = await flow.execute_crawl_task("test_task")
        
        assert result["success"] is True
        assert result["task_id"] == "test_task"
        assert len(result["rankings"]) == 1
        assert len(result["books"]) == 1

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    async def test_execute_crawl_task_invalid_task_id(
        self, 
        mock_parser_class, 
        mock_client_class, 
        mock_config_class
    ):
        """测试执行无效任务ID的爬取任务"""
        mock_config = mock_config_class.return_value
        mock_config.get_task_config.return_value = None
        
        flow = CrawlFlow()
        result = await flow.execute_crawl_task("invalid_task")
        
        assert result["success"] is False
        assert result["error"] == "无法生成页面地址"

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    async def test_execute_crawl_task_page_content_failed(
        self, 
        mock_parser_class, 
        mock_client_class, 
        mock_config_class
    ):
        """测试页面内容爬取失败"""
        mock_config = mock_config_class.return_value
        mock_config.get_task_config.return_value = {"template": "page_rank"}
        mock_config.build_url.return_value = "https://api.example.com/page"
        
        mock_client = mock_client_class.return_value
        mock_client.get.side_effect = Exception("Network error")
        
        flow = CrawlFlow()
        result = await flow.execute_crawl_task("test_task")
        
        assert result["success"] is False
        assert result["error"] == "页面内容爬取失败"

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    async def test_execute_multiple_tasks(
        self, 
        mock_parser_class, 
        mock_client_class, 
        mock_config_class,
        mock_page_response
    ):
        """测试执行多个爬取任务"""
        # 由于execute_multiple_tasks创建新的CrawlFlow实例，我们需要模拟整个流程
        with patch('app.crawl.crawl_flow.CrawlFlow') as mock_flow_class:
            mock_flow_instance = AsyncMock()
            mock_flow_instance.execute_crawl_task.return_value = {
                "success": True,
                "task_id": "test_task",
                "books_crawled": 1
            }
            mock_flow_class.return_value = mock_flow_instance
            
            flow = CrawlFlow()
            results = await flow.execute_multiple_tasks(["task1", "task2"])
            
            assert len(results) == 2
            assert all(r.get("success") for r in results)

    def test_generate_page_url_success(self, mock_crawl_config):
        """测试成功生成页面地址"""
        with patch('app.crawl.crawl_flow.CrawlConfig', return_value=mock_crawl_config):
            flow = CrawlFlow()
            url = flow._generate_page_url("test_task_1")
            
            assert url == "https://api.example.com/page?channelId=romance&size=20"

    def test_generate_page_url_invalid_task(self, mock_crawl_config):
        """测试无效任务ID生成页面地址"""
        with patch('app.crawl.crawl_flow.CrawlConfig', return_value=mock_crawl_config):
            flow = CrawlFlow()
            url = flow._generate_page_url("invalid_task")
            
            assert url is None

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    async def test_crawl_page_content_success(
        self, 
        mock_parser_class, 
        mock_client_class, 
        mock_config_class,
        mock_page_response
    ):
        """测试成功爬取页面内容"""
        mock_client = mock_client_class.return_value
        mock_client.get.return_value = mock_page_response
        
        flow = CrawlFlow()
        content = await flow._crawl_page_content("https://api.example.com/page")
        
        assert content == mock_page_response
        assert flow.stats["total_requests"] == 1

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    async def test_crawl_page_content_failed(
        self, 
        mock_parser_class, 
        mock_client_class, 
        mock_config_class
    ):
        """测试爬取页面内容失败"""
        mock_client = mock_client_class.return_value
        mock_client.get.side_effect = Exception("Network error")
        
        flow = CrawlFlow()
        content = await flow._crawl_page_content("https://api.example.com/page")
        
        assert content is None

    def test_parse_rankings_from_page_success(self, mock_page_response):
        """测试成功从页面解析榜单"""
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            ParsedItem(DataType.RANKING, {"rank_id": 1001, "books": []})
        ]
        
        with patch('app.crawl.crawl_flow.CrawlConfig'), \
             patch('app.crawl.crawl_flow.HttpClient'), \
             patch('app.crawl.crawl_flow.Parser', return_value=mock_parser):
            
            flow = CrawlFlow()
            rankings = flow._parse_rankings_from_page(mock_page_response)
            
            assert len(rankings) == 1
            assert rankings[0]["rank_id"] == 1001

    def test_parse_rankings_from_page_failed(self):
        """测试从页面解析榜单失败"""
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("Parse error")
        
        with patch('app.crawl.crawl_flow.CrawlConfig'), \
             patch('app.crawl.crawl_flow.HttpClient'), \
             patch('app.crawl.crawl_flow.Parser', return_value=mock_parser):
            
            flow = CrawlFlow()
            rankings = flow._parse_rankings_from_page({"invalid": "data"})
            
            assert rankings == []

    def test_extract_book_ids_from_rankings(self):
        """测试从榜单中提取书籍ID"""
        with patch('app.crawl.crawl_flow.CrawlConfig'), \
             patch('app.crawl.crawl_flow.HttpClient'), \
             patch('app.crawl.crawl_flow.Parser'):
            
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

    def test_extract_book_ids_empty_rankings(self):
        """测试从空榜单中提取书籍ID"""
        with patch('app.crawl.crawl_flow.CrawlConfig'), \
             patch('app.crawl.crawl_flow.HttpClient'), \
             patch('app.crawl.crawl_flow.Parser'):
            
            flow = CrawlFlow()
            book_ids = flow._extract_book_ids_from_rankings([])
            
            assert book_ids == []

    def test_deduplicate_book_ids(self):
        """测试书籍ID去重"""
        with patch('app.crawl.crawl_flow.CrawlConfig'), \
             patch('app.crawl.crawl_flow.HttpClient'), \
             patch('app.crawl.crawl_flow.Parser'):
            
            flow = CrawlFlow()
            book_ids = ["12345", "12346", "12345", "12347", "12346"]
            
            unique_ids = flow._deduplicate_book_ids(book_ids)
            
            assert unique_ids == ["12345", "12346", "12347"]
            assert flow.crawled_book_ids == {"12345", "12346", "12347"}

    def test_deduplicate_book_ids_empty_list(self):
        """测试空书籍ID列表去重"""
        with patch('app.crawl.crawl_flow.CrawlConfig'), \
             patch('app.crawl.crawl_flow.HttpClient'), \
             patch('app.crawl.crawl_flow.Parser'):
            
            flow = CrawlFlow()
            unique_ids = flow._deduplicate_book_ids([])
            
            assert unique_ids == []
            assert flow.crawled_book_ids == set()

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    async def test_crawl_books_details_success(
        self, 
        mock_parser_class, 
        mock_client_class, 
        mock_config_class,
        mock_book_detail_response
    ):
        """测试成功爬取书籍详情"""
        mock_config = mock_config_class.return_value
        mock_config.templates = {"novel_detail": "https://api.example.com/novel/{novel_id}"}
        mock_config.params = {}
        
        mock_client = mock_client_class.return_value
        mock_client.get.return_value = mock_book_detail_response
        
        mock_parser = mock_parser_class.return_value
        mock_parser.parse.return_value = [
            ParsedItem(DataType.BOOK, {"novel_id": 12345, "title": "测试小说"})
        ]
        
        flow = CrawlFlow()
        books = await flow._crawl_books_details(["12345"])
        
        assert len(books) == 1
        assert books[0]["novel_id"] == 12345
        assert flow.stats["books_crawled"] == 1

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    async def test_crawl_books_details_empty_list(
        self, 
        mock_parser_class, 
        mock_client_class, 
        mock_config_class
    ):
        """测试爬取空书籍ID列表"""
        flow = CrawlFlow()
        books = await flow._crawl_books_details([])
        
        assert books == []

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    async def test_crawl_single_book_detail_success(
        self, 
        mock_parser_class, 
        mock_client_class, 
        mock_config_class,
        mock_book_detail_response
    ):
        """测试成功爬取单个书籍详情"""
        mock_config = mock_config_class.return_value
        mock_config.templates = {"novel_detail": "https://api.example.com/novel/{novel_id}"}
        mock_config.params = {}
        
        mock_client = mock_client_class.return_value
        mock_client.get.return_value = mock_book_detail_response
        
        mock_parser = mock_parser_class.return_value
        mock_parser.parse.return_value = [
            ParsedItem(DataType.BOOK, {"novel_id": 12345, "title": "测试小说"})
        ]
        
        flow = CrawlFlow()
        book = await flow._crawl_single_book_detail("12345")
        
        assert book["novel_id"] == 12345
        assert flow.stats["total_requests"] == 1

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    async def test_crawl_single_book_detail_failed(
        self, 
        mock_parser_class, 
        mock_client_class, 
        mock_config_class
    ):
        """测试爬取单个书籍详情失败"""
        mock_config = mock_config_class.return_value
        mock_config.templates = {"novel_detail": "https://api.example.com/novel/{novel_id}"}
        mock_config.params = {}
        
        mock_client = mock_client_class.return_value
        mock_client.get.side_effect = Exception("Network error")
        
        flow = CrawlFlow()
        book = await flow._crawl_single_book_detail("12345")
        
        assert book is None

    def test_create_success_result(self):
        """测试创建成功结果"""
        with patch('app.crawl.crawl_flow.CrawlConfig'), \
             patch('app.crawl.crawl_flow.HttpClient'), \
             patch('app.crawl.crawl_flow.Parser'):
            
            flow = CrawlFlow()
            rankings = [{"rank_id": 1001}]
            books = [{"novel_id": 12345}]
            
            result = flow._create_success_result("test_task", "https://api.example.com", rankings, books)
            
            assert result["success"] is True
            assert result["task_id"] == "test_task"
            assert result["url"] == "https://api.example.com"
            assert result["rankings"] == rankings
            assert result["books"] == books

    def test_create_error_result(self):
        """测试创建错误结果"""
        with patch('app.crawl.crawl_flow.CrawlConfig'), \
             patch('app.crawl.crawl_flow.HttpClient'), \
             patch('app.crawl.crawl_flow.Parser'):
            
            flow = CrawlFlow()
            result = flow._create_error_result("test_task", "Test error")
            
            assert result["success"] is False
            assert result["task_id"] == "test_task"
            assert result["error"] == "Test error"

    def test_get_all_data(self):
        """测试获取所有数据"""
        with patch('app.crawl.crawl_flow.CrawlConfig'), \
             patch('app.crawl.crawl_flow.HttpClient'), \
             patch('app.crawl.crawl_flow.Parser'):
            
            flow = CrawlFlow()
            flow.books_data = [{"novel_id": 12345}]
            
            data = flow.get_all_data()
            
            assert data["books"] == [{"novel_id": 12345}]

    def test_get_stats(self):
        """测试获取统计信息"""
        with patch('app.crawl.crawl_flow.CrawlConfig'), \
             patch('app.crawl.crawl_flow.HttpClient'), \
             patch('app.crawl.crawl_flow.Parser'):
            
            flow = CrawlFlow()
            flow.stats["start_time"] = 1234567890.0
            flow.stats["end_time"] = 1234567895.0
            flow.books_data = [{"novel_id": 12345}]
            
            stats = flow.get_stats()
            
            assert stats["execution_time"] == 5.0
            assert stats["total_data_items"] == 1

    @patch('app.crawl.crawl_flow.CrawlConfig')
    @patch('app.crawl.crawl_flow.HttpClient')
    @patch('app.crawl.crawl_flow.Parser')
    async def test_close(self, mock_parser_class, mock_client_class, mock_config_class):
        """测试关闭资源"""
        mock_client = mock_client_class.return_value
        mock_client.close = AsyncMock()
        
        flow = CrawlFlow()
        await flow.close()
        
        mock_client.close.assert_called_once()