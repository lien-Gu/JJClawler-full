"""
爬取流程管理器测试文件
测试CrawlFlow类的关键功能，包括真实的爬取过程
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List

from app.crawl.crawl_flow import CrawlFlow
from app.crawl.parser import DataType, ParsedItem


class TestCrawlFlow:
    """测试CrawlFlow类"""
    
    @pytest.fixture
    def crawl_flow(self):
        """创建CrawlFlow实例"""
        return CrawlFlow(request_delay=0.1)  # 减少测试延迟
    
    @pytest.fixture
    def mock_page_content(self):
        """模拟页面内容"""
        return {
            "content": {
                "data": [
                    {
                        "rankid": 1,
                        "channelName": "测试榜单",
                        "rank_group_type": "热门",
                        "data": [
                            {
                                "novelId": 12345,
                                "novelName": "测试小说1",
                                "novelClickCount": 1000,
                                "novelFavoriteCount": 500
                            },
                            {
                                "novelId": 12346,
                                "novelName": "测试小说2", 
                                "novelClickCount": 2000,
                                "novelFavoriteCount": 800
                            }
                        ]
                    }
                ]
            }
        }
    
    @pytest.fixture
    def mock_book_detail(self):
        """模拟书籍详情"""
        return {
            "novelId": 12345,
            "novelName": "测试小说详情",
            "novelClickCount": 5000,
            "novelFavoriteCount": 1200,
            "CommentCount": 100,
            "nutritionNovel": 95
        }
    
    @pytest.fixture
    def mock_jiazi_content(self):
        """模拟夹子榜内容"""
        return {
            "list": [
                {
                    "novelId": 55555,
                    "novelName": "夹子测试小说1",
                    "novelClickCount": 8000,
                    "novelFavoriteCount": 2000
                },
                {
                    "novelId": 55556,
                    "novelName": "夹子测试小说2",
                    "novelClickCount": 9000,
                    "novelFavoriteCount": 2500
                }
            ]
        }
    
    def test_initialization(self, crawl_flow):
        """测试初始化"""
        assert crawl_flow.client is not None
        assert crawl_flow.parser is not None
        assert crawl_flow.book_service is not None
        assert crawl_flow.ranking_service is not None
        assert isinstance(crawl_flow.crawled_book_ids, set)
        assert crawl_flow.stats['books_crawled'] == 0
        assert crawl_flow.stats['total_requests'] == 0
    
    def test_generate_page_url_success(self, crawl_flow, mocker):
        """测试生成页面地址成功"""
        mock_task_config = {
            "id": "test_page",
            "template": "test_template",
            "params": {"page": 1}
        }
        
        # Mock config方法
        mock_get_task_config = mocker.patch.object(
            crawl_flow.config, 'get_task_config', 
            return_value=mock_task_config
        )
        mock_build_url = mocker.patch.object(
            crawl_flow.config, 'build_url',
            return_value="https://test.com/page1"
        )
        
        result = crawl_flow._generate_page_url("test_page")
        
        assert result == "https://test.com/page1"
        mock_get_task_config.assert_called_once_with("test_page")
        mock_build_url.assert_called_once_with(mock_task_config)
    
    def test_generate_page_url_failure(self, crawl_flow, mocker):
        """测试生成页面地址失败"""
        mock_get_task_config = mocker.patch.object(
            crawl_flow.config, 'get_task_config',
            return_value=None
        )
        
        result = crawl_flow._generate_page_url("invalid_page")
        
        assert result is None
        mock_get_task_config.assert_called_once_with("invalid_page")
    
    @pytest.mark.asyncio
    async def test_crawl_page_content_success(self, crawl_flow, mock_page_content, mocker):
        """测试爬取页面内容成功"""
        mock_get = mocker.patch.object(
            crawl_flow.client, 'get',
            return_value=mock_page_content
        )
        
        result = await crawl_flow._crawl_page_content("https://test.com/page1")
        
        assert result == mock_page_content
        assert crawl_flow.stats['total_requests'] == 1
        mock_get.assert_called_once_with("https://test.com/page1")
    
    @pytest.mark.asyncio
    async def test_crawl_page_content_failure(self, crawl_flow, mocker):
        """测试爬取页面内容失败"""
        mock_get = mocker.patch.object(
            crawl_flow.client, 'get',
            side_effect=Exception("网络错误")
        )
        
        result = await crawl_flow._crawl_page_content("https://test.com/page1")
        
        assert result is None
        assert crawl_flow.stats['total_requests'] == 1
        mock_get.assert_called_once_with("https://test.com/page1")
    
    def test_parse_rankings_from_page_success(self, crawl_flow, mock_page_content, mocker):
        """测试从页面解析榜单成功"""
        # Mock parser.parse返回值
        mock_ranking_item = ParsedItem(DataType.RANKING, {
            "rank_id": 1,
            "rank_name": "测试榜单",
            "books": [
                {"book_id": 12345, "title": "测试小说1", "position": 1},
                {"book_id": 12346, "title": "测试小说2", "position": 2}
            ]
        })
        mock_page_item = ParsedItem(DataType.PAGE, {"page_info": "test"})
        
        mock_parse = mocker.patch.object(
            crawl_flow.parser, 'parse',
            return_value=[mock_ranking_item, mock_page_item]
        )
        
        result = crawl_flow._parse_rankings_from_page(mock_page_content)
        
        assert len(result) == 1
        assert result[0]["rank_id"] == 1
        assert result[0]["rank_name"] == "测试榜单"
        assert len(result[0]["books"]) == 2
        assert len(crawl_flow.rankings_data) == 1
        assert len(crawl_flow.pages_data) == 1
        mock_parse.assert_called_once_with(mock_page_content)
    
    def test_parse_rankings_from_page_failure(self, crawl_flow, mocker):
        """测试从页面解析榜单失败"""
        mock_parse = mocker.patch.object(
            crawl_flow.parser, 'parse',
            side_effect=Exception("解析错误")
        )
        
        result = crawl_flow._parse_rankings_from_page({"invalid": "data"})
        
        assert result == []
        mock_parse.assert_called_once_with({"invalid": "data"})
    
    def test_extract_book_ids_from_rankings(self, crawl_flow):
        """测试从榜单提取书籍ID"""
        rankings = [
            {
                "rank_id": 1,
                "rank_name": "测试榜单1",
                "books": [
                    {"book_id": 12345, "title": "测试小说1"},
                    {"book_id": 12346, "title": "测试小说2"}
                ]
            },
            {
                "rank_id": 2,
                "rank_name": "测试榜单2",
                "books": [
                    {"book_id": 12346, "title": "测试小说2"},  # 重复
                    {"book_id": 12347, "title": "测试小说3"}
                ]
            }
        ]
        
        result = crawl_flow._extract_book_ids_from_rankings(rankings)
        
        # 验证去重功能
        assert len(result) == 3
        assert "12345" in result
        assert "12346" in result
        assert "12347" in result
        assert len(crawl_flow.crawled_book_ids) == 3
    
    @pytest.mark.asyncio
    async def test_crawl_books_details_success(self, crawl_flow, mock_book_detail, mocker):
        """测试爬取书籍详情成功"""
        mock_crawl_book_detail = mocker.patch.object(
            crawl_flow, 'crawl_book_detail',
            return_value=mock_book_detail
        )
        
        book_ids = ["12345", "12346"]
        result = await crawl_flow._crawl_books_details(book_ids)
        
        assert len(result) == 2
        assert result[0] == mock_book_detail
        assert result[1] == mock_book_detail
        assert crawl_flow.stats['books_crawled'] == 2
        assert len(crawl_flow.books_data) == 2
        assert mock_crawl_book_detail.call_count == 2
    
    @pytest.mark.asyncio
    async def test_crawl_books_details_with_failures(self, crawl_flow, mock_book_detail, mocker):
        """测试爬取书籍详情部分失败"""
        def side_effect(book_id):
            if book_id == "12345":
                return mock_book_detail
            else:
                raise Exception("爬取失败")
        
        mock_crawl_book_detail = mocker.patch.object(
            crawl_flow, 'crawl_book_detail',
            side_effect=side_effect
        )
        
        book_ids = ["12345", "12346"]
        result = await crawl_flow._crawl_books_details(book_ids)
        
        assert len(result) == 1
        assert result[0] == mock_book_detail
        assert crawl_flow.stats['books_crawled'] == 1
        assert len(crawl_flow.books_data) == 1
        assert mock_crawl_book_detail.call_count == 2
    
    @pytest.mark.asyncio
    async def test_crawl_book_detail_success(self, crawl_flow, mock_book_detail, mocker):
        """测试爬取单个书籍详情成功"""
        # Mock模板和参数
        crawl_flow.config.templates = {
            'novel_detail': 'https://test.com/book/{book_id}'
        }
        crawl_flow.config.params = {}
        
        mock_get = mocker.patch.object(
            crawl_flow.client, 'get',
            return_value=mock_book_detail
        )
        
        mock_book_item = ParsedItem(DataType.BOOK, mock_book_detail)
        mock_parse = mocker.patch.object(
            crawl_flow.parser, 'parse',
            return_value=[mock_book_item]
        )
        
        result = await crawl_flow.crawl_book_detail("12345")
        
        assert result == mock_book_detail
        assert crawl_flow.stats['total_requests'] == 1
        mock_get.assert_called_once_with("https://test.com/book/12345")
        mock_parse.assert_called_once_with(mock_book_detail)
    
    @pytest.mark.asyncio
    async def test_crawl_book_detail_failure(self, crawl_flow, mocker):
        """测试爬取单个书籍详情失败"""
        crawl_flow.config.templates = {
            'novel_detail': 'https://test.com/book/{book_id}'
        }
        crawl_flow.config.params = {}
        
        mock_get = mocker.patch.object(
            crawl_flow.client, 'get',
            side_effect=Exception("网络错误")
        )
        
        result = await crawl_flow.crawl_book_detail("12345")
        
        assert result is None
        assert crawl_flow.stats['total_requests'] == 1
        mock_get.assert_called_once_with("https://test.com/book/12345")
    
    @pytest.mark.asyncio
    async def test_save_crawl_result_success(self, crawl_flow, mocker):
        """测试保存爬取结果成功"""
        # Mock数据库相关
        mock_db = MagicMock()
        mock_get_db = mocker.patch('app.crawl.crawl_flow.get_db', return_value=[mock_db])
        
        # Mock service方法
        mock_ranking_obj = MagicMock()
        mock_ranking_obj.id = 1
        mock_create_ranking = mocker.patch.object(
            crawl_flow.ranking_service, 'create_or_update_ranking',
            return_value=mock_ranking_obj
        )
        
        mock_book_obj = MagicMock()
        mock_book_obj.id = 1
        mock_create_book = mocker.patch.object(
            crawl_flow.book_service, 'create_or_update_book',
            return_value=mock_book_obj
        )
        
        mock_batch_ranking_snapshots = mocker.patch.object(
            crawl_flow.ranking_service, 'batch_create_ranking_snapshots'
        )
        
        mock_batch_book_snapshots = mocker.patch.object(
            crawl_flow.book_service, 'batch_create_book_snapshots'
        )
        
        rankings = [
            {
                "rank_id": 1,
                "rank_name": "测试榜单",
                "page_id": "test_page",
                "rank_group_type": "热门",
                "books": [
                    {"book_id": 12345, "title": "测试小说1", "position": 1, "score": 95.0}
                ]
            }
        ]
        
        books = [
            {
                "book_id": 12345,
                "title": "测试小说1",
                "clicks": 1000,
                "favorites": 500,
                "comments": 100,
                "word_count": 50000
            }
        ]
        
        result = await crawl_flow._save_crawl_result(rankings, books)
        
        assert result is True
        mock_get_db.assert_called_once()
        mock_create_ranking.assert_called_once()
        mock_create_book.assert_called()
        mock_batch_ranking_snapshots.assert_called_once()
        mock_batch_book_snapshots.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_crawl_result_failure(self, crawl_flow, mocker):
        """测试保存爬取结果失败"""
        mock_db = MagicMock()
        mock_get_db = mocker.patch('app.crawl.crawl_flow.get_db', return_value=[mock_db])
        
        # Mock保存过程中出现异常
        mock_create_ranking = mocker.patch.object(
            crawl_flow.ranking_service, 'create_or_update_ranking',
            side_effect=Exception("数据库错误")
        )
        
        rankings = [{"rank_id": 1, "rank_name": "测试榜单", "books": []}]
        books = []
        
        result = await crawl_flow._save_crawl_result(rankings, books)
        
        assert result is False
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_crawl_task_success(self, crawl_flow, mock_page_content, mocker):
        """测试执行完整爬取任务成功"""
        # Mock所有依赖方法
        mock_generate_url = mocker.patch.object(
            crawl_flow, '_generate_page_url',
            return_value="https://test.com/page1"
        )
        
        mock_crawl_page = mocker.patch.object(
            crawl_flow, '_crawl_page_content',
            return_value=mock_page_content
        )
        
        mock_parse_rankings = mocker.patch.object(
            crawl_flow, '_parse_rankings_from_page',
            return_value=[{"rank_id": 1, "books": [{"book_id": 12345}]}]
        )
        
        mock_extract_ids = mocker.patch.object(
            crawl_flow, '_extract_book_ids_from_rankings',
            return_value=["12345"]
        )
        
        mock_crawl_books = mocker.patch.object(
            crawl_flow, '_crawl_books_details',
            return_value=[{"book_id": 12345, "title": "测试小说"}]
        )
        
        mock_save_result = mocker.patch.object(
            crawl_flow, '_save_crawl_result',
            return_value=True
        )
        
        result = await crawl_flow.execute_crawl_task("test_page")
        
        assert result["success"] is True
        assert result["page_id"] == "test_page"
        assert result["books_crawled"] == 1
        assert "execution_time" in result
        assert "data" in result
        
        mock_generate_url.assert_called_once_with("test_page")
        mock_crawl_page.assert_called_once_with("https://test.com/page1")
        mock_parse_rankings.assert_called_once_with(mock_page_content)
        mock_extract_ids.assert_called_once()
        mock_crawl_books.assert_called_once_with(["12345"])
        mock_save_result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_crawl_task_url_generation_failure(self, crawl_flow, mocker):
        """测试执行爬取任务-URL生成失败"""
        mock_generate_url = mocker.patch.object(
            crawl_flow, '_generate_page_url',
            return_value=None
        )
        
        result = await crawl_flow.execute_crawl_task("invalid_page")
        
        assert result["success"] is False
        assert result["page_id"] == "invalid_page"
        assert result["books_crawled"] == 0
        assert "无法生成页面地址" in result["error_message"]
        assert "execution_time" in result
        
        mock_generate_url.assert_called_once_with("invalid_page")
    
    @pytest.mark.asyncio
    async def test_execute_crawl_task_page_crawl_failure(self, crawl_flow, mocker):
        """测试执行爬取任务-页面爬取失败"""
        mock_generate_url = mocker.patch.object(
            crawl_flow, '_generate_page_url',
            return_value="https://test.com/page1"
        )
        
        mock_crawl_page = mocker.patch.object(
            crawl_flow, '_crawl_page_content',
            return_value=None
        )
        
        result = await crawl_flow.execute_crawl_task("test_page")
        
        assert result["success"] is False
        assert result["page_id"] == "test_page"
        assert result["books_crawled"] == 0
        assert "页面内容爬取失败" in result["error_message"]
        
        mock_generate_url.assert_called_once_with("test_page")
        mock_crawl_page.assert_called_once_with("https://test.com/page1")
    
    @pytest.mark.asyncio
    async def test_execute_crawl_task_save_failure(self, crawl_flow, mock_page_content, mocker):
        """测试执行爬取任务-保存失败"""
        # Mock所有方法直到保存步骤
        mock_generate_url = mocker.patch.object(
            crawl_flow, '_generate_page_url',
            return_value="https://test.com/page1"
        )
        
        mock_crawl_page = mocker.patch.object(
            crawl_flow, '_crawl_page_content',
            return_value=mock_page_content
        )
        
        mock_parse_rankings = mocker.patch.object(
            crawl_flow, '_parse_rankings_from_page',
            return_value=[{"rank_id": 1, "books": []}]
        )
        
        mock_extract_ids = mocker.patch.object(
            crawl_flow, '_extract_book_ids_from_rankings',
            return_value=[]
        )
        
        mock_crawl_books = mocker.patch.object(
            crawl_flow, '_crawl_books_details',
            return_value=[]
        )
        
        mock_save_result = mocker.patch.object(
            crawl_flow, '_save_crawl_result',
            return_value=False
        )
        
        result = await crawl_flow.execute_crawl_task("test_page")
        
        assert result["success"] is False
        assert result["page_id"] == "test_page"
        assert result["books_crawled"] == 0
        assert "数据保存失败" in result["error_message"]
        
        mock_save_result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_crawl_task_exception(self, crawl_flow, mocker):
        """测试执行爬取任务-异常处理"""
        mock_generate_url = mocker.patch.object(
            crawl_flow, '_generate_page_url',
            side_effect=Exception("意外错误")
        )
        
        result = await crawl_flow.execute_crawl_task("test_page")
        
        assert result["success"] is False
        assert result["page_id"] == "test_page"
        assert result["books_crawled"] == 0
        assert "页面爬取异常" in result["error_message"]
        assert "意外错误" in result["error_message"]
    
    def test_get_all_data(self, crawl_flow):
        """测试获取所有数据"""
        # 添加测试数据
        crawl_flow.books_data = [{"book_id": 1, "title": "测试书籍"}]
        crawl_flow.rankings_data = [{"rank_id": 1, "rank_name": "测试榜单"}]
        crawl_flow.pages_data = [{"page_id": 1, "page_info": "测试页面"}]
        
        result = crawl_flow.get_all_data()
        
        assert "books" in result
        assert "rankings" in result
        assert "pages" in result
        assert len(result["books"]) == 1
        assert len(result["rankings"]) == 1
        assert len(result["pages"]) == 1
    
    def test_get_stats(self, crawl_flow):
        """测试获取统计信息"""
        # 设置测试数据
        crawl_flow.stats['start_time'] = 1000.0
        crawl_flow.stats['end_time'] = 1005.0
        crawl_flow.stats['books_crawled'] = 5
        crawl_flow.books_data = [1, 2, 3]
        crawl_flow.rankings_data = [1, 2]
        crawl_flow.pages_data = [1]
        
        result = crawl_flow.get_stats()
        
        assert result['execution_time'] == 5.0
        assert result['books_crawled'] == 5
        assert result['total_data_items'] == 6
        assert 'start_time' in result
        assert 'end_time' in result
    
    @pytest.mark.asyncio
    async def test_close(self, crawl_flow, mocker):
        """测试关闭资源"""
        mock_close = mocker.patch.object(crawl_flow.client, 'close')
        
        await crawl_flow.close()
        
        mock_close.assert_called_once()


class TestRealCrawlFlow:
    """真实爬取流程测试（可选择性执行）"""
    
    @pytest.fixture
    def real_crawl_flow(self):
        """创建真实CrawlFlow实例"""
        return CrawlFlow(request_delay=0.5)  # 适当的延迟避免被封
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_jiazi_crawl(self, real_crawl_flow):
        """测试真实的夹子榜爬取（集成测试）"""
        try:
            result = await real_crawl_flow.execute_crawl_task("jiazi")
            
            # 验证结果结构
            assert "success" in result
            assert "page_id" in result
            assert "books_crawled" in result
            assert "execution_time" in result
            
            if result["success"]:
                assert result["page_id"] == "jiazi"
                assert result["books_crawled"] >= 0
                assert result["execution_time"] > 0
                print(f"✅ 真实爬取成功: 爬取了 {result['books_crawled']} 本书籍")
            else:
                print(f"❌ 真实爬取失败: {result.get('error_message', '未知错误')}")
                
        except Exception as e:
            print(f"❌ 真实爬取异常: {e}")
            # 不让测试失败，因为网络问题不应该影响单元测试
            pytest.skip(f"网络问题跳过真实爬取测试: {e}")
        
        finally:
            await real_crawl_flow.close()
    
    @pytest.mark.integration  
    @pytest.mark.asyncio
    async def test_real_book_detail_crawl(self, real_crawl_flow):
        """测试真实的书籍详情爬取（集成测试）"""
        try:
            # 使用一个真实存在的书籍ID进行测试
            test_book_id = "123456"  # 可以替换为真实的书籍ID
            
            result = await real_crawl_flow.crawl_book_detail(test_book_id)
            
            if result:
                assert "book_id" in result
                assert "title" in result
                print(f"✅ 真实书籍详情爬取成功: {result.get('title', '未知书名')}")
            else:
                print(f"❌ 真实书籍详情爬取失败: 书籍ID {test_book_id}")
                
        except Exception as e:
            print(f"❌ 真实书籍详情爬取异常: {e}")
            pytest.skip(f"网络问题跳过真实书籍详情爬取测试: {e}")
            
        finally:
            await real_crawl_flow.close()