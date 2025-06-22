"""
分类页面爬虫单元测试

测试 app.modules.crawler.page_crawler 模块的所有功能
"""
import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, mock_open
from app.modules.crawler.page_crawler import PageCrawler
from app.modules.models import Book, BookSnapshot


class TestPageCrawlerInitialization:
    """分类页面爬虫初始化测试"""
    
    @patch('app.modules.crawler.page_crawler.DataParser')
    @patch('builtins.open', new_callable=mock_open, read_data='{"base_url": "https://test.com", "version": "v1"}')
    def test_init_with_default_http_client(self, mock_file, mock_parser):
        """测试使用默认HTTP客户端初始化"""
        crawler = PageCrawler()
        
        assert crawler.http_client is not None
        assert crawler.parser is not None
        assert crawler.url_config is not None
    
    @patch('app.modules.crawler.page_crawler.DataParser')
    @patch('builtins.open', new_callable=mock_open, read_data='{"base_url": "https://test.com", "version": "v1"}')
    def test_init_with_custom_http_client(self, mock_file, mock_parser):
        """测试使用自定义HTTP客户端初始化"""
        mock_http_client = Mock()
        
        crawler = PageCrawler(http_client=mock_http_client)
        
        assert crawler.http_client is mock_http_client
        assert crawler.parser is not None
        assert crawler.url_config is not None


class TestURLBuilding:
    """URL构建测试"""
    
    def test_build_url_success(self):
        """测试成功构建URL"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v2"
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = PageCrawler()
            
            url = crawler._build_url("yq")
            
            assert url == "https://api.test.com/ranking/yq/v2"
    
    def test_build_url_with_complex_channel(self):
        """测试复杂频道标识的URL构建"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1"
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = PageCrawler()
            
            url = crawler._build_url("yq_gy")
            
            assert url == "https://api.test.com/ranking/yq_gy/v1"
    
    def test_build_url_missing_config(self):
        """测试配置不完整时的URL构建"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}"
            # 缺少 version
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = PageCrawler()
            
            url = crawler._build_url("yq")
            
            assert url == ""  # 应该返回空字符串
    
    def test_build_url_format_error(self):
        """测试URL格式错误"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}",  # 只有一个占位符
            "version": "v1"
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = PageCrawler()
            
            url = crawler._build_url("yq")
            
            assert url == ""  # 格式错误时应该返回空字符串


class TestPageCrawling:
    """分类页面爬取测试"""
    
    @pytest.fixture
    def mock_crawler(self):
        """创建模拟的爬虫实例"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1"
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            mock_http_client = AsyncMock()
            mock_parser = Mock()
            
            crawler = PageCrawler(http_client=mock_http_client)
            crawler.parser = mock_parser
            
            return crawler, mock_http_client, mock_parser
    
    @pytest.mark.asyncio
    async def test_crawl_success(self):
        """测试成功爬取分类页面数据"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1"
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            mock_http_client = AsyncMock()
            mock_parser = Mock()
            
            # 设置返回数据
            mock_raw_data = {"code": "200", "data": {"list": []}}
            mock_http_client.get.return_value = mock_raw_data
            
            mock_books = [
                Book(book_id="1", title="言情小说1", author_id="1", author_name="作者1"),
                Book(book_id="2", title="言情小说2", author_id="2", author_name="作者2")
            ]
            mock_snapshots = [
                BookSnapshot(book_id="1", total_clicks=2000, total_favorites=800),
                BookSnapshot(book_id="2", total_clicks=1500, total_favorites=600)
            ]
            
            crawler = PageCrawler(http_client=mock_http_client)
            crawler.parser = mock_parser
            crawler.parser.parse_page_data.return_value = (mock_books, mock_snapshots)
            
            # 执行爬取
            books, snapshots = await crawler.crawl("yq")
            
            # 验证结果
            assert len(books) == 2
            assert len(snapshots) == 2
            assert books[0].title == "言情小说1"
            assert snapshots[0].total_clicks == 2000
            
            # 验证调用
            expected_url = "https://api.test.com/ranking/yq/v1"
            mock_http_client.get.assert_called_once_with(expected_url)
            crawler.parser.parse_page_data.assert_called_once_with(mock_raw_data)
    
    @pytest.mark.asyncio
    async def test_crawl_empty_result(self):
        """测试爬取结果为空"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1"
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            mock_http_client = AsyncMock()
            mock_parser = Mock()
            
            mock_http_client.get.return_value = {"code": "200", "data": {"list": []}}
            
            crawler = PageCrawler(http_client=mock_http_client)
            crawler.parser = mock_parser
            crawler.parser.parse_page_data.return_value = ([], [])  # 空结果
            
            books, snapshots = await crawler.crawl("cy")
            
            assert books == []
            assert snapshots == []
    
    @pytest.mark.asyncio
    async def test_crawl_invalid_channel(self):
        """测试无效频道"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}"
            # 缺少version，会导致URL构建失败
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = PageCrawler()
            
            with pytest.raises(ValueError, match="无法构建频道URL"):
                await crawler.crawl("invalid_channel")
    
    @pytest.mark.asyncio
    async def test_crawl_data_inconsistency(self):
        """测试书籍和快照数据不一致"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1"
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            mock_http_client = AsyncMock()
            mock_parser = Mock()
            
            mock_http_client.get.return_value = {"code": "200", "data": {"list": []}}
            
            # 书籍和快照数量不一致
            mock_books = [
                Book(book_id="1", title="测试书籍", author_id="1", author_name="作者")
            ]
            mock_snapshots = [
                BookSnapshot(book_id="1", total_clicks=1000, total_favorites=500),
                BookSnapshot(book_id="2", total_clicks=800, total_favorites=300),  # 多一个快照
                BookSnapshot(book_id="3", total_clicks=600, total_favorites=200)   # 又多一个
            ]
            
            crawler = PageCrawler(http_client=mock_http_client)
            crawler.parser = mock_parser
            crawler.parser.parse_page_data.return_value = (mock_books, mock_snapshots)
            
            # 应该仍然返回数据，但会记录警告
            books, snapshots = await crawler.crawl("yq")
            
            assert len(books) == 1
            assert len(snapshots) == 3
    
    @pytest.mark.asyncio
    async def test_crawl_http_error(self):
        """测试HTTP请求失败"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1"
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            mock_http_client = AsyncMock()
            mock_http_client.get.side_effect = Exception("网络连接失败")
            
            crawler = PageCrawler(http_client=mock_http_client)
            
            with pytest.raises(Exception, match="网络连接失败"):
                await crawler.crawl("yq")
    
    @pytest.mark.asyncio
    async def test_crawl_parse_error(self):
        """测试数据解析失败"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1"
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            mock_http_client = AsyncMock()
            mock_parser = Mock()
            
            mock_http_client.get.return_value = {"code": "200", "data": {"list": []}}
            mock_parser.parse_page_data.side_effect = Exception("解析失败")
            
            crawler = PageCrawler(http_client=mock_http_client)
            crawler.parser = mock_parser
            
            with pytest.raises(Exception, match="解析失败"):
                await crawler.crawl("yq")


class TestAvailableChannels:
    """可用频道测试"""
    
    @pytest.mark.asyncio
    async def test_get_available_channels_success(self):
        """测试成功获取可用频道"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1",
            "content": {
                "pages": {
                    "yq": {
                        "short_name": "yq",
                        "zh_name": "言情",
                        "type": "daily",
                        "frequency": "daily"
                    },
                    "cy": {
                        "short_name": "cy",
                        "zh_name": "纯爱",
                        "type": "daily",
                        "frequency": "daily",
                        "sub_pages": {
                            "modern": {
                                "short_name": "modern",
                                "zh_name": "现代",
                                "frequency": "daily"
                            },
                            "ancient": {
                                "short_name": "ancient",
                                "zh_name": "古代",
                                "frequency": "weekly"
                            }
                        }
                    }
                }
            }
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = PageCrawler()
            
            channels = await crawler.get_available_channels()
            
            # 验证主页面
            yq_channel = next((c for c in channels if c["short_name"] == "yq"), None)
            assert yq_channel is not None
            assert yq_channel["zh_name"] == "言情"
            assert yq_channel["frequency"] == "daily"
            
            cy_channel = next((c for c in channels if c["short_name"] == "cy"), None)
            assert cy_channel is not None
            assert cy_channel["zh_name"] == "纯爱"
            
            # 验证子页面
            modern_channel = next((c for c in channels if c["short_name"] == "cy.modern"), None)
            assert modern_channel is not None
            assert modern_channel["zh_name"] == "纯爱 - 现代"
            
            ancient_channel = next((c for c in channels if c["short_name"] == "cy.ancient"), None)
            assert ancient_channel is not None
            assert ancient_channel["zh_name"] == "纯爱 - 古代"
            assert ancient_channel["frequency"] == "weekly"
    
    @pytest.mark.asyncio
    async def test_get_available_channels_missing_pages(self):
        """测试配置中缺少pages"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1",
            "content": {
                "other": {}
            }
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = PageCrawler()
            
            channels = await crawler.get_available_channels()
            
            # 应该返回默认的言情频道
            assert len(channels) == 1
            assert channels[0]["short_name"] == "yq"
            assert channels[0]["zh_name"] == "言情"
    
    @pytest.mark.asyncio
    async def test_get_available_channels_invalid_page_format(self):
        """测试无效的页面格式"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1",
            "content": {
                "pages": {
                    "yq": "invalid_format",  # 不是字典格式
                    "cy": {
                        "short_name": "cy",
                        "zh_name": "纯爱",
                        "frequency": "daily"
                    }
                }
            }
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = PageCrawler()
            
            channels = await crawler.get_available_channels()
            
            # 应该只包含有效的cy频道
            cy_channel = next((c for c in channels if c["short_name"] == "cy"), None)
            assert cy_channel is not None
            
            # 无效的yq频道应该被跳过
            yq_channel = next((c for c in channels if c["short_name"] == "yq"), None)
            assert yq_channel is None
    
    @pytest.mark.asyncio
    async def test_get_available_channels_with_default_type(self):
        """测试使用默认type的频道"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1",
            "content": {
                "pages": {
                    "test": {
                        "short_name": "test",
                        "zh_name": "测试频道",
                        "frequency": "hourly"
                        # 没有指定type，应该使用默认值
                    }
                }
            }
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            crawler = PageCrawler()
            
            channels = await crawler.get_available_channels()
            
            test_channel = next((c for c in channels if c["short_name"] == "test"), None)
            assert test_channel is not None
            assert test_channel["type"] == "daily"  # 默认值


class TestCrawlerLifecycle:
    """爬虫生命周期测试"""
    
    @pytest.mark.asyncio
    async def test_close_crawler(self):
        """测试关闭爬虫"""
        with patch('builtins.open', new_callable=mock_open, read_data='{"base_url": "test", "version": "v1"}'):
            mock_http_client = AsyncMock()
            crawler = PageCrawler(http_client=mock_http_client)
            
            await crawler.close()
            
            mock_http_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_crawler_no_client(self):
        """测试关闭爬虫但没有HTTP客户端"""
        with patch('builtins.open', new_callable=mock_open, read_data='{"base_url": "test", "version": "v1"}'):
            crawler = PageCrawler()
            crawler.http_client = None
            
            # 应该不会抛出异常
            await crawler.close()


class TestURLConfigLoading:
    """URL配置加载测试"""
    
    @patch('builtins.open', side_effect=FileNotFoundError("配置文件不存在"))
    def test_load_url_config_file_not_found(self, mock_file):
        """测试配置文件不存在"""
        with pytest.raises(FileNotFoundError):
            PageCrawler()
    
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_url_config_invalid_json(self, mock_file):
        """测试无效JSON配置"""
        with pytest.raises(json.JSONDecodeError):
            PageCrawler()
    
    @patch('builtins.open', side_effect=PermissionError("权限不足"))
    def test_load_url_config_permission_error(self, mock_file):
        """测试权限错误"""
        with pytest.raises(PermissionError):
            PageCrawler()


class TestIntegrationScenarios:
    """集成场景测试"""
    
    @pytest.mark.asyncio
    async def test_full_page_crawl_workflow(self):
        """测试完整的分类页面爬取工作流"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1",
            "content": {
                "pages": {
                    "yq": {
                        "short_name": "yq",
                        "zh_name": "言情",
                        "type": "daily",
                        "frequency": "daily"
                    }
                }
            }
        }
        
        mock_response_data = {
            "code": "200",
            "data": {
                "list": [
                    {
                        "novelId": "123",
                        "novelName": "言情小说",
                        "authorId": "456",
                        "authorName": "言情作者",
                        "totalClicks": "2000",
                        "totalFavorites": "800"
                    }
                ]
            }
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            mock_http_client = AsyncMock()
            mock_parser = Mock()
            
            mock_http_client.get.return_value = mock_response_data
            
            # 模拟解析结果
            test_book = Book(
                book_id="123",
                title="言情小说",
                author_id="456",
                author_name="言情作者"
            )
            test_snapshot = BookSnapshot(
                book_id="123",
                total_clicks=2000,
                total_favorites=800
            )
            
            mock_parser.parse_page_data.return_value = ([test_book], [test_snapshot])
            
            crawler = PageCrawler(http_client=mock_http_client)
            crawler.parser = mock_parser
            
            # 1. 获取可用频道
            channels = await crawler.get_available_channels()
            yq_channel = next((c for c in channels if c["short_name"] == "yq"), None)
            assert yq_channel is not None
            
            # 2. 执行爬取
            books, snapshots = await crawler.crawl("yq")
            assert len(books) == 1
            assert len(snapshots) == 1
            assert books[0].book_id == "123"
            
            # 3. 关闭爬虫
            await crawler.close()
            
            # 验证调用序列
            expected_url = "https://api.test.com/ranking/yq/v1"
            mock_http_client.get.assert_called_once_with(expected_url)
            mock_parser.parse_page_data.assert_called_once_with(mock_response_data)
            mock_http_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multiple_channels_crawl(self):
        """测试多个频道的爬取"""
        test_config = {
            "base_url": "https://api.test.com/ranking/{}/{}",
            "version": "v1",
            "content": {
                "pages": {
                    "yq": {
                        "short_name": "yq",
                        "zh_name": "言情",
                        "frequency": "daily"
                    },
                    "cy": {
                        "short_name": "cy", 
                        "zh_name": "纯爱",
                        "frequency": "daily"
                    }
                }
            }
        }
        
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(test_config)):
            mock_http_client = AsyncMock()
            mock_parser = Mock()
            
            # 设置不同频道返回不同数据
            def mock_get_side_effect(url):
                if "yq" in url:
                    return {"code": "200", "data": {"list": [{"novelId": "yq1"}]}}
                elif "cy" in url:
                    return {"code": "200", "data": {"list": [{"novelId": "cy1"}]}}
                return {"code": "200", "data": {"list": []}}
            
            mock_http_client.get.side_effect = mock_get_side_effect
            
            def mock_parse_side_effect(raw_data):
                if raw_data.get("data", {}).get("list"):
                    novel_id = raw_data["data"]["list"][0]["novelId"]
                    book = Book(book_id=novel_id, title=f"书籍{novel_id}", author_id="1", author_name="作者")
                    snapshot = BookSnapshot(book_id=novel_id, total_clicks=1000, total_favorites=500)
                    return ([book], [snapshot])
                return ([], [])
            
            mock_parser.parse_page_data.side_effect = mock_parse_side_effect
            
            crawler = PageCrawler(http_client=mock_http_client)
            crawler.parser = mock_parser
            
            # 爬取不同频道
            yq_books, yq_snapshots = await crawler.crawl("yq")
            cy_books, cy_snapshots = await crawler.crawl("cy")
            
            assert len(yq_books) == 1
            assert yq_books[0].book_id == "yq1"
            
            assert len(cy_books) == 1
            assert cy_books[0].book_id == "cy1"
            
            # 验证调用了两次HTTP请求
            assert mock_http_client.get.call_count == 2