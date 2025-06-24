"""
夹子榜爬虫单元测试

测试 app.modules.crawler.jiazi_crawler 模块的所有功能
"""
import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, mock_open
from app.modules.crawler.jiazi_crawler import JiaziCrawler
from app.modules.models import Book, BookSnapshot


class TestJiaziCrawlerInitialization:
    """夹子榜爬虫初始化测试"""
    
    def test_init_with_default_http_client(self, mocker):
        """测试使用默认HTTP客户端初始化"""
        mocker.patch('app.modules.crawler.jiazi_crawler.DataParser')
        mocker.patch('builtins.open', mocker.mock_open(read_data='{"content": {"jiazi": {"url": "test-url"}}}'))
        
        crawler = JiaziCrawler()
        
        assert crawler.http_client is not None
        assert crawler.parser is not None
        assert crawler.url_config is not None
    
    def test_init_with_custom_http_client(self, mocker, mock_http_client):
        """测试使用自定义HTTP客户端初始化"""
        mocker.patch('app.modules.crawler.jiazi_crawler.DataParser')
        mocker.patch('builtins.open', mocker.mock_open(read_data='{"content": {"jiazi": {"url": "test-url"}}}'))
        
        crawler = JiaziCrawler(http_client=mock_http_client)
        
        assert crawler.http_client is mock_http_client
        assert crawler.parser is not None
        assert crawler.url_config is not None


class TestURLConfigLoading:
    """URL配置加载测试"""
    
    def test_load_url_config_success(self, mocker):
        """测试成功加载URL配置"""
        mocker.patch('os.getcwd', return_value="/test/project")
        mocker.patch('os.path.join', return_value="/test/project/data/urls.json")
        mocker.patch('builtins.open', mocker.mock_open(read_data='{"content": {"jiazi": {"url": "https://test.com/jiazi"}}}'))
        
        crawler = JiaziCrawler()
        
        assert crawler.url_config["content"]["jiazi"]["url"] == "https://test.com/jiazi"
    
    def test_load_url_config_file_not_found(self, mocker):
        """测试配置文件不存在"""
        mocker.patch('builtins.open', side_effect=FileNotFoundError("配置文件不存在"))
        with pytest.raises(FileNotFoundError):
            JiaziCrawler()
    
    def test_load_url_config_invalid_json(self, mocker):
        """测试无效JSON配置"""
        mocker.patch('builtins.open', mocker.mock_open(read_data='invalid json'))
        with pytest.raises(json.JSONDecodeError):
            JiaziCrawler()
    
    def test_load_url_config_permission_error(self, mocker):
        """测试权限错误"""
        mocker.patch('builtins.open', side_effect=PermissionError("权限不足"))
        with pytest.raises(PermissionError):
            JiaziCrawler()


class TestJiaziCrawling:
    """夹子榜爬取测试"""
    
    @pytest.fixture
    def mock_crawler(self, mocker):
        """创建模拟的爬虫实例"""
        mocker.patch('builtins.open', mocker.mock_open(
            read_data='{"content": {"jiazi": {"url": "https://test.com/jiazi"}}}'))
        mock_http_client = mocker.AsyncMock()
        mock_parser = mocker.Mock()
        
        crawler = JiaziCrawler(http_client=mock_http_client)
        crawler.parser = mock_parser
        
        return crawler, mock_http_client, mock_parser
    
    @pytest.mark.asyncio
    async def test_crawl_success(self, mocker):
        """测试成功爬取夹子榜数据"""
        mocker.patch('builtins.open', mocker.mock_open(
            read_data='{"content": {"jiazi": {"url": "https://test.com/jiazi"}}}'))
        
        # 创建模拟对象
        mock_http_client = mocker.AsyncMock()
        mock_parser = mocker.Mock()
        
        # 设置返回数据
        mock_raw_data = {"code": "200", "data": {"list": []}}
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_raw_data
        mock_http_client.get.return_value = mock_response
        
        mock_books = [
            Book(book_id="1", title="测试书籍1", author_id="1", author_name="作者1"),
            Book(book_id="2", title="测试书籍2", author_id="2", author_name="作者2")
        ]
        mock_snapshots = [
            BookSnapshot(book_id="1", total_clicks=1000, total_favorites=500),
            BookSnapshot(book_id="2", total_clicks=800, total_favorites=300)
        ]
        
        # 创建爬虫实例
        crawler = JiaziCrawler(http_client=mock_http_client)
        crawler.parser = mock_parser
        crawler.parser.parse_jiazi_data.return_value = (mock_books, mock_snapshots)
        
        # 执行爬取
        books, snapshots = await crawler.crawl()
        
        # 验证结果
        assert len(books) == 2
        assert len(snapshots) == 2
        assert books[0].title == "测试书籍1"
        assert snapshots[0].total_clicks == 1000
        
        # 验证调用
        mock_http_client.get.assert_called_once_with("https://test.com/jiazi")
        crawler.parser.parse_jiazi_data.assert_called_once_with(mock_raw_data)
    
    @pytest.mark.asyncio
    async def test_crawl_empty_result(self):
        """测试爬取结果为空"""
        with patch('builtins.open', new_callable=mock_open, 
                  read_data='{"content": {"jiazi": {"url": "https://test.com/jiazi"}}}'):
            
            mock_http_client = AsyncMock()
            mock_parser = Mock()
            
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"code": "200", "data": {"list": []}}
            mock_http_client.get.return_value = mock_response
            
            crawler = JiaziCrawler(http_client=mock_http_client)
            crawler.parser = mock_parser
            crawler.parser.parse_jiazi_data.return_value = ([], [])  # 空结果
            
            books, snapshots = await crawler.crawl()
            
            assert books == []
            assert snapshots == []
    
    @pytest.mark.asyncio
    async def test_crawl_data_inconsistency(self):
        """测试书籍和快照数据不一致"""
        with patch('builtins.open', new_callable=mock_open, 
                  read_data='{"content": {"jiazi": {"url": "https://test.com/jiazi"}}}'):
            
            mock_http_client = AsyncMock()
            mock_parser = Mock()
            
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"code": "200", "data": {"list": []}}
            mock_http_client.get.return_value = mock_response
            
            # 书籍和快照数量不一致
            mock_books = [Book(book_id="1", title="测试书籍", author_id="1", author_name="作者")]
            mock_snapshots = [
                BookSnapshot(book_id="1", total_clicks=1000, total_favorites=500),
                BookSnapshot(book_id="2", total_clicks=800, total_favorites=300)  # 多一个快照
            ]
            
            crawler = JiaziCrawler(http_client=mock_http_client)
            crawler.parser = mock_parser
            crawler.parser.parse_jiazi_data.return_value = (mock_books, mock_snapshots)
            
            # 应该仍然返回数据，但会记录警告
            books, snapshots = await crawler.crawl()
            
            assert len(books) == 1
            assert len(snapshots) == 2
    
    @pytest.mark.asyncio
    async def test_crawl_http_error(self):
        """测试HTTP请求失败"""
        with patch('builtins.open', new_callable=mock_open, 
                  read_data='{"content": {"jiazi": {"url": "https://test.com/jiazi"}}}'):
            
            mock_http_client = AsyncMock()
            mock_http_client.get.side_effect = Exception("网络连接失败")
            
            crawler = JiaziCrawler(http_client=mock_http_client)
            
            with pytest.raises(Exception, match="网络连接失败"):
                await crawler.crawl()
    
    @pytest.mark.asyncio
    async def test_crawl_parse_error(self):
        """测试数据解析失败"""
        with patch('builtins.open', new_callable=mock_open, 
                  read_data='{"content": {"jiazi": {"url": "https://test.com/jiazi"}}}'):
            
            mock_http_client = AsyncMock()
            mock_parser = Mock()
            
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"code": "200", "data": {"list": []}}
            mock_http_client.get.return_value = mock_response
            mock_parser.parse_jiazi_data.side_effect = Exception("解析失败")
            
            crawler = JiaziCrawler(http_client=mock_http_client)
            crawler.parser = mock_parser
            
            with pytest.raises(Exception, match="解析失败"):
                await crawler.crawl()


class TestConfigInfo:
    """配置信息测试"""
    
    @pytest.mark.asyncio
    async def test_get_config_info_success(self):
        """测试成功获取配置信息"""
        test_config = {
            "content": {
                "jiazi": {
                    "short_name": "jiazi",
                    "zh_name": "夹子榜",
                    "type": "hourly", 
                    "frequency": "hourly",
                    "url": "https://test.com/jiazi"
                }
            }
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = JiaziCrawler()
            
            config_info = await crawler.get_config_info()
            
            assert config_info["short_name"] == "jiazi"
            assert config_info["zh_name"] == "夹子榜"
            assert config_info["type"] == "hourly"
            assert config_info["frequency"] == "hourly"
            assert config_info["url"] == "https://test.com/jiazi"
    
    @pytest.mark.asyncio
    async def test_get_config_info_missing_jiazi(self):
        """测试配置中缺少夹子榜配置"""
        test_config = {
            "content": {
                "other": {
                    "short_name": "other",
                    "zh_name": "其他榜单"
                }
            }
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = JiaziCrawler()
            
            config_info = await crawler.get_config_info()
            
            # 应该返回默认配置
            assert config_info["short_name"] == "jiazi"
            assert config_info["zh_name"] == "夹子榜"
            assert config_info["url"] == ""
    
    @pytest.mark.asyncio 
    async def test_get_config_info_partial_config(self):
        """测试部分配置信息"""
        test_config = {
            "content": {
                "jiazi": {
                    "short_name": "jiazi",
                    "zh_name": "夹子榜"
                    # 缺少其他字段
                }
            }
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = JiaziCrawler()
            
            with pytest.raises(KeyError):
                await crawler.get_config_info()


class TestCrawlerLifecycle:
    """爬虫生命周期测试"""
    
    @pytest.mark.asyncio
    async def test_close_crawler(self):
        """测试关闭爬虫"""
        with patch('builtins.open', new_callable=mock_open, 
                  read_data='{"content": {"jiazi": {"url": "test-url"}}}'):
            
            mock_http_client = AsyncMock()
            crawler = JiaziCrawler(http_client=mock_http_client)
            
            await crawler.close()
            
            mock_http_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_crawler_no_client(self):
        """测试关闭爬虫但没有HTTP客户端"""
        with patch('builtins.open', new_callable=mock_open, 
                  read_data='{"content": {"jiazi": {"url": "test-url"}}}'):
            
            crawler = JiaziCrawler()
            crawler.http_client = None
            
            # 应该不会抛出异常
            await crawler.close()


class TestIntegrationScenarios:
    """集成场景测试"""
    
    @pytest.mark.asyncio
    async def test_full_crawl_workflow(self):
        """测试完整的爬取工作流"""
        test_config = {
            "content": {
                "jiazi": {
                    "short_name": "jiazi",
                    "zh_name": "夹子榜",
                    "type": "hourly",
                    "frequency": "hourly", 
                    "url": "https://test.com/jiazi"
                }
            }
        }
        
        mock_response_data = {
            "code": "200",
            "data": {
                "list": [
                    {
                        "novelId": "123",
                        "novelName": "测试小说",
                        "authorId": "456",
                        "authorName": "测试作者",
                        "totalClicks": "1000",
                        "totalFavorites": "500"
                    }
                ]
            }
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            mock_http_client = AsyncMock()
            mock_parser = Mock()
            
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_response_data
            mock_http_client.get.return_value = mock_response
            
            # 模拟解析结果
            test_book = Book(
                book_id="123",
                title="测试小说",
                author_id="456", 
                author_name="测试作者"
            )
            test_snapshot = BookSnapshot(
                book_id="123",
                total_clicks=1000,
                total_favorites=500
            )
            
            mock_parser.parse_jiazi_data.return_value = ([test_book], [test_snapshot])
            
            crawler = JiaziCrawler(http_client=mock_http_client)
            crawler.parser = mock_parser
            
            # 1. 获取配置信息
            config_info = await crawler.get_config_info()
            assert config_info["short_name"] == "jiazi"
            
            # 2. 执行爬取
            books, snapshots = await crawler.crawl()
            assert len(books) == 1
            assert len(snapshots) == 1
            assert books[0].book_id == "123"
            
            # 3. 关闭爬虫
            await crawler.close()
            
            # 验证调用序列
            mock_http_client.get.assert_called_once_with("https://test.com/jiazi")
            mock_parser.parse_jiazi_data.assert_called_once_with(mock_response_data)
            mock_http_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """测试错误恢复工作流"""
        with patch('builtins.open', new_callable=mock_open, 
                  read_data='{"content": {"jiazi": {"url": "https://test.com/jiazi"}}}'):
            
            mock_http_client = AsyncMock()
            
            # 第一次请求失败
            mock_http_client.get.side_effect = [
                Exception("网络错误"),
                {"code": "200", "data": {"list": []}}  # 第二次成功
            ]
            
            crawler = JiaziCrawler(http_client=mock_http_client)
            
            # 第一次爬取失败
            with pytest.raises(Exception, match="网络错误"):
                await crawler.crawl()
            
            # 重置mock副作用，模拟第二次成功
            mock_http_client.get.side_effect = None
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"code": "200", "data": {"list": []}}
            mock_http_client.get.return_value = mock_response
            crawler.parser.parse_jiazi_data.return_value = ([], [])
            
            # 第二次爬取应该成功
            books, snapshots = await crawler.crawl()
            assert books == []
            assert snapshots == []