"""
爬取流程测试 - 使用 pytest-mock，专注逻辑验证
"""
import pytest
from typing import Dict, Any

from app.crawl.crawl_flow import CrawlFlow
from app.crawl.parser import DataType, ParsedItem


class TestCrawlFlow:
    """爬取流程测试类"""

    def test_init(self, mock_crawl_flow_dependencies):
        """测试爬取流程初始化"""
        flow = CrawlFlow()
        
        assert flow is not None
        assert flow.crawled_book_ids == set()
        assert flow.books_data == []
        assert flow.pages_data == []
        assert flow.rankings_data == []
        assert isinstance(flow.stats, dict)

    @pytest.mark.asyncio
    async def test_execute_crawl_task_success(self, mock_crawl_flow_dependencies, mock_page_response, mock_book_detail_response):
        """测试成功执行爬取任务"""
        deps = mock_crawl_flow_dependencies
        
        # 配置mock行为
        deps['client'].get.side_effect = [mock_page_response, mock_book_detail_response]
        deps['parser'].parse.side_effect = [
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
        flow.config = deps['config']
        flow.client = deps['client'] 
        flow.parser = deps['parser']
        
        result = await flow.execute_crawl_task("test_task")
        
        assert result["success"] is True
        assert result["task_id"] == "test_task"
        assert len(result["rankings"]) == 1
        assert len(result["books"]) == 1

    @pytest.mark.asyncio
    async def test_execute_crawl_task_invalid_task_id(self, mock_crawl_flow_dependencies):
        """测试执行无效任务ID的爬取任务"""
        deps = mock_crawl_flow_dependencies
        deps['config'].get_task_config.return_value = None

        flow = CrawlFlow()
        flow.config = deps['config']
        
        result = await flow.execute_crawl_task("invalid_task")

        assert result["success"] is False
        assert result["error"] == "无法生成页面地址"

    @pytest.mark.asyncio
    async def test_execute_crawl_task_page_content_fail(self, mock_crawl_flow_dependencies):
        """测试页面内容爬取失败的情况"""
        deps = mock_crawl_flow_dependencies
        deps['client'].get.return_value = None

        flow = CrawlFlow()
        flow.config = deps['config']
        flow.client = deps['client']
        
        result = await flow.execute_crawl_task("test_task")

        assert result["success"] is False
        assert result["error"] == "页面内容爬取失败"

    @pytest.mark.asyncio
    async def test_execute_crawl_task_exception(self, mock_crawl_flow_dependencies):
        """测试执行任务时出现异常"""
        deps = mock_crawl_flow_dependencies
        deps['config'].get_task_config.side_effect = Exception("Test exception")

        flow = CrawlFlow()
        flow.config = deps['config']
        
        result = await flow.execute_crawl_task("test_task")

        assert result["success"] is False
        assert result["error"] == "无法生成页面地址"

    @pytest.mark.asyncio
    async def test_execute_multiple_tasks_success(self, mocker):
        """测试并发执行多个任务成功"""
        # Mock CrawlFlow class to control individual task execution
        mock_crawl_flow_class = mocker.patch('app.crawl.crawl_flow.CrawlFlow')
        
        # Create mock instances for each task
        mock_flow1 = mocker.AsyncMock()
        mock_flow2 = mocker.AsyncMock()
        mock_crawl_flow_class.side_effect = [mock_flow1, mock_flow2]
        
        # Mock task results
        mock_result1 = {"task_id": "task1", "success": True, "books_crawled": 5}
        mock_result2 = {"task_id": "task2", "success": True, "books_crawled": 3}
        
        mock_flow1.execute_crawl_task.return_value = mock_result1
        mock_flow2.execute_crawl_task.return_value = mock_result2

        # Create original flow instance (not mocked)
        original_flow = CrawlFlow.__new__(CrawlFlow)  # Create without calling __init__
        original_flow._create_error_result = lambda task_id, error: {
            "task_id": task_id, "success": False, "error": error
        }

        results = await original_flow.execute_multiple_tasks(["task1", "task2"])

        assert len(results) == 2
        assert results[0] == mock_result1
        assert results[1] == mock_result2

    @pytest.mark.asyncio
    async def test_execute_multiple_tasks_with_exception(self, mocker):
        """测试并发执行任务时有异常"""
        # Mock CrawlFlow class
        mock_crawl_flow_class = mocker.patch('app.crawl.crawl_flow.CrawlFlow')
        
        mock_flow1 = mocker.AsyncMock()
        mock_flow2 = mocker.AsyncMock()
        mock_crawl_flow_class.side_effect = [mock_flow1, mock_flow2]
        
        # First task succeeds, second task raises exception
        mock_result1 = {"task_id": "task1", "success": True, "books_crawled": 5}
        mock_flow1.execute_crawl_task.return_value = mock_result1
        mock_flow2.execute_crawl_task.side_effect = Exception("Task failed")

        # Create original flow instance
        original_flow = CrawlFlow.__new__(CrawlFlow)
        original_flow._create_error_result = lambda task_id, error: {
            "task_id": task_id, "success": False, "error": error
        }

        results = await original_flow.execute_multiple_tasks(["task1", "task2"])

        assert len(results) == 2
        assert results[0] == mock_result1
        assert results[1]["success"] is False
        assert "任务执行异常" in results[1]["error"]

    def test_generate_page_url_success(self, mock_crawl_flow_dependencies):
        """测试成功生成页面地址"""
        deps = mock_crawl_flow_dependencies

        flow = CrawlFlow()
        flow.config = deps['config']
        
        url = flow._generate_page_url("test_task")

        assert url == "https://api.example.com/page"
        deps['config'].get_task_config.assert_called_once_with("test_task")
        deps['config'].build_url.assert_called_once()

    def test_generate_page_url_no_config(self, mock_crawl_flow_dependencies):
        """测试无法获取任务配置时生成页面地址"""
        deps = mock_crawl_flow_dependencies
        deps['config'].get_task_config.return_value = None

        flow = CrawlFlow()
        flow.config = deps['config']
        
        url = flow._generate_page_url("invalid_task")

        assert url is None

    def test_generate_page_url_exception(self, mock_crawl_flow_dependencies):
        """测试生成页面地址时出现异常"""
        deps = mock_crawl_flow_dependencies
        deps['config'].get_task_config.side_effect = Exception("Config error")

        flow = CrawlFlow()
        flow.config = deps['config']
        
        url = flow._generate_page_url("test_task")

        assert url is None

    @pytest.mark.asyncio
    async def test_crawl_page_content_success(self, mock_crawl_flow_dependencies, mock_page_response):
        """测试成功爬取页面内容"""
        deps = mock_crawl_flow_dependencies
        deps['client'].get.return_value = mock_page_response

        flow = CrawlFlow()
        flow.client = deps['client']
        
        content = await flow._crawl_page_content("https://api.example.com/page")

        assert content == mock_page_response
        assert flow.stats["total_requests"] == 1
        deps['client'].get.assert_called_once_with("https://api.example.com/page")

    @pytest.mark.asyncio
    async def test_crawl_page_content_exception(self, mock_crawl_flow_dependencies):
        """测试爬取页面内容时出现异常"""
        deps = mock_crawl_flow_dependencies
        deps['client'].get.side_effect = Exception("Network error")

        flow = CrawlFlow()
        flow.client = deps['client']
        
        content = await flow._crawl_page_content("https://api.example.com/page")

        assert content is None

    def test_parse_rankings_from_page_success(self, mock_crawl_flow_dependencies, mock_page_response):
        """测试成功从页面解析榜单"""
        deps = mock_crawl_flow_dependencies
        
        # Mock parsed items
        page_item = ParsedItem(DataType.PAGE, {"page_id": 1})
        ranking_item = ParsedItem(DataType.RANKING, {"rank_id": 1001, "rank_name": "测试榜单"})
        deps['parser'].parse.return_value = [page_item, ranking_item]

        flow = CrawlFlow()
        flow.parser = deps['parser']
        
        rankings = flow._parse_rankings_from_page(mock_page_response)

        assert len(rankings) == 1
        assert rankings[0]["rank_id"] == 1001
        assert len(flow.pages_data) == 1
        assert len(flow.rankings_data) == 1

    def test_parse_rankings_from_page_exception(self, mock_crawl_flow_dependencies, mock_page_response):
        """测试解析榜单时出现异常"""
        deps = mock_crawl_flow_dependencies
        deps['parser'].parse.side_effect = Exception("Parse error")

        flow = CrawlFlow()
        flow.parser = deps['parser']
        
        rankings = flow._parse_rankings_from_page(mock_page_response)

        assert rankings == []

    def test_extract_book_ids_from_rankings(self, mock_crawl_flow_dependencies):
        """测试从榜单中提取书籍ID"""
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

    def test_extract_book_ids_from_rankings_empty(self, mock_crawl_flow_dependencies):
        """测试从空榜单中提取书籍ID"""
        flow = CrawlFlow()
        rankings = []

        book_ids = flow._extract_book_ids_from_rankings(rankings)

        assert book_ids == []

    def test_extract_book_ids_with_missing_books(self, mock_crawl_flow_dependencies):
        """测试从包含缺失书籍信息的榜单中提取ID"""
        flow = CrawlFlow()
        rankings = [
            {
                "books": [
                    {"book_id": 12345},
                    {"title": "No ID"},  # 缺少 book_id
                    {"book_id": None},   # book_id 为 None
                    {"book_id": 12346}
                ]
            }
        ]

        book_ids = flow._extract_book_ids_from_rankings(rankings)

        assert book_ids == ["12345", "12346"]

    def test_deduplicate_book_ids(self, mock_crawl_flow_dependencies):
        """测试书籍ID去重"""
        flow = CrawlFlow()
        book_ids = ["12345", "12346", "12345", "12347", "12346"]

        unique_ids = flow._deduplicate_book_ids(book_ids)

        assert unique_ids == ["12345", "12346", "12347"]
        assert flow.crawled_book_ids == {"12345", "12346", "12347"}

    def test_deduplicate_book_ids_empty(self, mock_crawl_flow_dependencies):
        """测试空书籍ID列表去重"""
        flow = CrawlFlow()
        book_ids = []

        unique_ids = flow._deduplicate_book_ids(book_ids)

        assert unique_ids == []
        assert flow.crawled_book_ids == set()

    @pytest.mark.asyncio
    async def test_crawl_books_details_success(self, mock_crawl_flow_dependencies, mock_book_detail_response):
        """测试成功批量爬取书籍详情"""
        deps = mock_crawl_flow_dependencies
        deps['client'].get.return_value = mock_book_detail_response
        deps['parser'].parse.return_value = [
            ParsedItem(DataType.BOOK, {"novel_id": 12345, "title": "测试小说"})
        ]

        flow = CrawlFlow()
        flow.config = deps['config']
        flow.client = deps['client']
        flow.parser = deps['parser']
        
        books = await flow._crawl_books_details(["12345", "12346"])

        assert len(books) == 2  # 因为两个ID都会返回相同的mock结果
        assert flow.stats["books_crawled"] == 2
        assert len(flow.books_data) == 2

    @pytest.mark.asyncio
    async def test_crawl_books_details_empty_list(self, mock_crawl_flow_dependencies):
        """测试空书籍ID列表的批量爬取"""
        flow = CrawlFlow()
        books = await flow._crawl_books_details([])

        assert books == []

    @pytest.mark.asyncio
    async def test_crawl_books_details_with_failures(self, mock_crawl_flow_dependencies, mock_book_detail_response):
        """测试批量爬取书籍详情时有失败的情况"""
        deps = mock_crawl_flow_dependencies
        # 第一个成功，第二个失败
        deps['client'].get.side_effect = [mock_book_detail_response, Exception("Network error")]
        deps['parser'].parse.return_value = [
            ParsedItem(DataType.BOOK, {"novel_id": 12345, "title": "测试小说"})
        ]

        flow = CrawlFlow()
        flow.config = deps['config']
        flow.client = deps['client']
        flow.parser = deps['parser']
        
        books = await flow._crawl_books_details(["12345", "12346"])

        assert len(books) == 1  # 只有一个成功
        assert flow.stats["books_crawled"] == 1

    @pytest.mark.asyncio
    async def test_crawl_single_book_detail_success(self, mock_crawl_flow_dependencies, mock_book_detail_response):
        """测试成功爬取单个书籍详情"""
        deps = mock_crawl_flow_dependencies
        deps['client'].get.return_value = mock_book_detail_response
        deps['parser'].parse.return_value = [
            ParsedItem(DataType.BOOK, {"novel_id": 12345, "title": "测试小说"})
        ]

        flow = CrawlFlow()
        flow.config = deps['config']
        flow.client = deps['client']
        flow.parser = deps['parser']
        
        book = await flow.crawl_book_detail("12345")

        assert book["novel_id"] == 12345
        assert flow.stats["total_requests"] == 1

    @pytest.mark.asyncio
    async def test_crawl_single_book_detail_no_book_data(self, mock_crawl_flow_dependencies, mock_book_detail_response):
        """测试爬取单个书籍详情时没有书籍数据"""
        deps = mock_crawl_flow_dependencies
        deps['client'].get.return_value = mock_book_detail_response
        # 返回非书籍类型的数据
        deps['parser'].parse.return_value = [
            ParsedItem(DataType.PAGE, {"page_id": 1})
        ]

        flow = CrawlFlow()
        flow.config = deps['config']
        flow.client = deps['client']
        flow.parser = deps['parser']
        
        book = await flow.crawl_book_detail("12345")

        assert book is None

    @pytest.mark.asyncio
    async def test_crawl_single_book_detail_exception(self, mock_crawl_flow_dependencies):
        """测试爬取单个书籍详情时出现异常"""
        deps = mock_crawl_flow_dependencies
        deps['client'].get.side_effect = Exception("Network error")

        flow = CrawlFlow()
        flow.config = deps['config']
        flow.client = deps['client']
        
        book = await flow.crawl_book_detail("12345")

        assert book is None

    def test_create_success_result(self, mock_crawl_flow_dependencies):
        """测试创建成功结果"""
        flow = CrawlFlow()
        rankings = [{"rank_id": 1001}]
        books = [{"novel_id": 12345}]

        result = flow._create_success_result("test_task", "https://api.example.com", rankings, books)

        assert result["success"] is True
        assert result["task_id"] == "test_task"
        assert result["url"] == "https://api.example.com"
        assert result["rankings"] == rankings
        assert result["books"] == books
        assert result["books_crawled"] == 1
        assert "stats" in result
        assert "timestamp" in result

    def test_create_error_result(self, mock_crawl_flow_dependencies):
        """测试创建错误结果"""
        flow = CrawlFlow()
        result = flow._create_error_result("test_task", "Test error")

        assert result["success"] is False
        assert result["task_id"] == "test_task"
        assert result["error"] == "Test error"
        assert "stats" in result
        assert "timestamp" in result

    def test_get_all_data(self, mock_crawl_flow_dependencies):
        """测试获取所有数据"""
        flow = CrawlFlow()
        flow.books_data = [{"novel_id": 12345, "title": "测试小说"}]

        data = flow.get_all_data()

        assert "books" in data
        assert len(data["books"]) == 1
        assert data["books"][0]["novel_id"] == 12345

    def test_get_stats_without_timing(self, mock_crawl_flow_dependencies):
        """测试获取统计信息（无时间信息）"""
        flow = CrawlFlow()
        flow.stats = {
            'books_crawled': 5,
            'total_requests': 10,
            'start_time': None,
            'end_time': None
        }
        flow.books_data = [{"novel_id": 1}, {"novel_id": 2}]
        flow.pages_data = [{"page_id": 1}]
        flow.rankings_data = [{"rank_id": 1}]

        stats = flow.get_stats()

        assert stats["books_crawled"] == 5
        assert stats["total_requests"] == 10
        assert stats["total_data_items"] == 4  # 2 books + 1 page + 1 ranking
        assert "execution_time" not in stats

    def test_get_stats_with_timing(self, mock_crawl_flow_dependencies):
        """测试获取统计信息（含时间信息）"""
        flow = CrawlFlow()
        flow.stats = {
            'books_crawled': 5,
            'total_requests': 10,
            'start_time': 1000.0,
            'end_time': 1005.0
        }

        stats = flow.get_stats()

        assert stats["books_crawled"] == 5
        assert stats["total_requests"] == 10
        assert stats["execution_time"] == 5.0

    @pytest.mark.asyncio
    async def test_close(self, mock_crawl_flow_dependencies):
        """测试关闭资源"""
        deps = mock_crawl_flow_dependencies

        flow = CrawlFlow()
        flow.client = deps['client']
        
        await flow.close()

        deps['client'].close.assert_called_once()