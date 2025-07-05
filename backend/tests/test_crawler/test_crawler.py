"""
爬虫模块测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import httpx
from datetime import datetime
import asyncio
from typing import List, Dict, Any, Optional


class TestCrawler:
    """爬虫测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_crawler(self):
        """设置测试爬虫"""
        from app.crawler.crawler import Crawler
        self.crawler = Crawler()
    
    @pytest.mark.asyncio
    async def test_crawl_page_success(self):
        """测试成功爬取页面"""
        # 模拟HTTP响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <body>
        <table>
        <tr>
            <td>测试小说</td>
            <td>测试作者</td>
            <td>1000</td>
        </tr>
        </table>
        </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get', return_value=mock_response) as mock_get:
            # 执行爬取
            result = await self.crawler.crawl_page("https://example.com")
            
            # 验证结果
            assert result is not None
            assert result["status"] == "success"
            assert "content" in result
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_crawl_page_timeout(self):
        """测试爬取页面超时"""
        with patch('httpx.AsyncClient.get', side_effect=httpx.TimeoutException("Timeout")) as mock_get:
            # 执行爬取
            result = await self.crawler.crawl_page("https://example.com")
            
            # 验证结果
            assert result is not None
            assert result["status"] == "error"
            assert "timeout" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_crawl_page_http_error(self):
        """测试爬取页面HTTP错误"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        with patch('httpx.AsyncClient.get', return_value=mock_response) as mock_get:
            # 执行爬取
            result = await self.crawler.crawl_page("https://example.com")
            
            # 验证结果
            assert result is not None
            assert result["status"] == "error"
            assert result["status_code"] == 404
    
    @pytest.mark.asyncio
    async def test_crawl_page_network_error(self):
        """测试爬取页面网络错误"""
        with patch('httpx.AsyncClient.get', side_effect=httpx.NetworkError("Network error")) as mock_get:
            # 执行爬取
            result = await self.crawler.crawl_page("https://example.com")
            
            # 验证结果
            assert result is not None
            assert result["status"] == "error"
            assert "network" in result["error"].lower()
    
    def test_validate_url(self):
        """测试URL验证"""
        # 测试有效URL
        assert self.crawler.validate_url("https://www.jjwxc.net/topten.php") is True
        assert self.crawler.validate_url("http://example.com") is True
        
        # 测试无效URL
        assert self.crawler.validate_url("invalid-url") is False
        assert self.crawler.validate_url("") is False
        assert self.crawler.validate_url(None) is False
    
    def test_get_user_agent(self):
        """测试获取User-Agent"""
        user_agent = self.crawler.get_user_agent()
        assert user_agent is not None
        assert isinstance(user_agent, str)
        assert len(user_agent) > 0
    
    def test_get_headers(self):
        """测试获取请求头"""
        headers = self.crawler.get_headers()
        assert isinstance(headers, dict)
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
    
    @pytest.mark.asyncio
    async def test_crawl_with_delay(self):
        """测试带延迟的爬取"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        
        with patch('httpx.AsyncClient.get', return_value=mock_response), \
             patch('asyncio.sleep') as mock_sleep:
            
            # 执行爬取
            await self.crawler.crawl_page("https://example.com", delay=2)
            
            # 验证延迟
            mock_sleep.assert_called_once_with(2)
    
    @pytest.mark.asyncio
    async def test_crawl_with_retries(self):
        """测试带重试的爬取"""
        # 模拟前两次失败，第三次成功
        mock_responses = [
            httpx.TimeoutException("Timeout"),
            httpx.NetworkError("Network error"),
            Mock(status_code=200, text="<html><body>Success</body></html>")
        ]
        
        with patch('httpx.AsyncClient.get', side_effect=mock_responses) as mock_get:
            # 执行爬取
            result = await self.crawler.crawl_page("https://example.com", retries=3)
            
            # 验证结果
            assert result["status"] == "success"
            assert mock_get.call_count == 3
    
    @pytest.mark.asyncio
    async def test_crawl_jiazi_ranking(self):
        """测试爬取夹子榜"""
        # 模拟夹子榜页面内容
        mock_html = """
        <html>
        <body>
        <table class="cytable">
        <tr>
            <td>1</td>
            <td><a href="/book/123">测试小说1</a></td>
            <td>作者1</td>
            <td>现代言情</td>
            <td>完结</td>
            <td>1000</td>
        </tr>
        <tr>
            <td>2</td>
            <td><a href="/book/456">测试小说2</a></td>
            <td>作者2</td>
            <td>古代言情</td>
            <td>连载</td>
            <td>900</td>
        </tr>
        </table>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            # 执行爬取
            result = await self.crawler.crawl_jiazi_ranking()
            
            # 验证结果
            assert result["status"] == "success"
            assert "books" in result
            assert len(result["books"]) == 2
            assert result["books"][0]["title"] == "测试小说1"
            assert result["books"][1]["title"] == "测试小说2"
    
    @pytest.mark.asyncio
    async def test_crawl_category_ranking(self):
        """测试爬取分类榜单"""
        category = "现代言情"
        
        # 模拟分类榜单页面内容
        mock_html = """
        <html>
        <body>
        <div class="rankinglist">
        <div class="book">
            <h3>分类小说1</h3>
            <p>作者: 分类作者1</p>
            <p>收藏: 2000</p>
        </div>
        <div class="book">
            <h3>分类小说2</h3>
            <p>作者: 分类作者2</p>
            <p>收藏: 1800</p>
        </div>
        </div>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            # 执行爬取
            result = await self.crawler.crawl_category_ranking(category)
            
            # 验证结果
            assert result["status"] == "success"
            assert "books" in result
            assert result["category"] == category
    
    @pytest.mark.asyncio
    async def test_crawl_book_detail(self):
        """测试爬取书籍详情"""
        novel_id = 12345
        
        # 模拟书籍详情页面内容
        mock_html = """
        <html>
        <body>
        <div class="novelinfo">
            <h1>详细小说标题</h1>
            <div class="author">作者: 详细作者</div>
            <div class="intro">这是小说的详细介绍</div>
            <div class="stats">
                <span>收藏: 5000</span>
                <span>点击: 10000</span>
                <span>评论: 500</span>
            </div>
        </div>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            # 执行爬取
            result = await self.crawler.crawl_book_detail(novel_id)
            
            # 验证结果
            assert result["status"] == "success"
            assert "book" in result
            assert result["book"]["novel_id"] == novel_id
    
    def test_rate_limiting(self):
        """测试速率限制"""
        # 测试速率限制器
        rate_limiter = self.crawler.get_rate_limiter()
        assert rate_limiter is not None
        
        # 检查是否允许请求
        assert rate_limiter.allow_request() is True
    
    @pytest.mark.asyncio
    async def test_concurrent_crawling(self):
        """测试并发爬取"""
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3"
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        
        with patch('httpx.AsyncClient.get', return_value=mock_response) as mock_get:
            # 执行并发爬取
            results = await self.crawler.crawl_multiple_pages(urls)
            
            # 验证结果
            assert len(results) == 3
            assert all(result["status"] == "success" for result in results)
            assert mock_get.call_count == 3
    
    def test_robots_txt_compliance(self):
        """测试robots.txt遵守"""
        # 测试是否遵守robots.txt
        url = "https://www.jjwxc.net/topten.php"
        assert self.crawler.is_allowed_by_robots(url) is True
        
        # 测试被禁止的URL
        forbidden_url = "https://www.jjwxc.net/admin/"
        assert self.crawler.is_allowed_by_robots(forbidden_url) is False
    
    def test_cookie_handling(self):
        """测试Cookie处理"""
        # 测试Cookie管理
        cookies = self.crawler.get_cookies()
        assert isinstance(cookies, dict)
        
        # 测试设置Cookie
        self.crawler.set_cookie("test_key", "test_value")
        assert self.crawler.get_cookie("test_key") == "test_value"
    
    def test_session_management(self):
        """测试会话管理"""
        # 测试会话创建
        session = self.crawler.create_session()
        assert session is not None
        
        # 测试会话清理
        self.crawler.close_session()
    
    @pytest.mark.asyncio
    async def test_proxy_support(self):
        """测试代理支持"""
        proxy_url = "http://proxy.example.com:8080"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get_by_id.return_value = mock_response
            
            # 执行带代理的爬取
            result = await self.crawler.crawl_page("https://example.com", proxy=proxy_url)
            
            # 验证代理配置
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            assert "proxies" in call_args.kwargs
    
    def test_error_recovery(self):
        """测试错误恢复"""
        # 测试错误记录
        error = Exception("Test error")
        self.crawler.record_error("https://example.com", error)
        
        # 验证错误记录
        errors = self.crawler.get_errors()
        assert len(errors) > 0
        assert "https://example.com" in errors
    
    def test_crawl_statistics(self):
        """测试爬取统计"""
        # 测试统计信息
        stats = self.crawler.get_statistics()
        assert isinstance(stats, dict)
        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert "average_response_time" in stats
    
    @pytest.mark.asyncio
    async def test_custom_headers(self):
        """测试自定义请求头"""
        custom_headers = {
            "Custom-Header": "Custom-Value",
            "Authorization": "Bearer token123"
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        
        with patch('httpx.AsyncClient.get', return_value=mock_response) as mock_get:
            # 执行带自定义头的爬取
            result = await self.crawler.crawl_page(
                "https://example.com", 
                headers=custom_headers
            )
            
            # 验证自定义头
            call_args = mock_get.call_args
            assert "headers" in call_args.kwargs
            headers = call_args.kwargs["headers"]
            assert "Custom-Header" in headers
            assert headers["Custom-Header"] == "Custom-Value"
    
    def test_url_normalization(self):
        """测试URL标准化"""
        # 测试URL标准化
        urls = [
            "http://example.com/path",
            "http://example.com/path/",
            "http://example.com/path?param=value",
            "http://example.com/path#fragment"
        ]
        
        for url in urls:
            normalized = self.crawler.normalize_url(url)
            assert normalized is not None
            assert isinstance(normalized, str)
    
    @pytest.mark.asyncio
    async def test_content_filtering(self):
        """测试内容过滤"""
        # 模拟包含敏感内容的页面
        sensitive_html = """
        <html>
        <body>
        <div>正常内容</div>
        <script>alert('xss')</script>
        <div>更多正常内容</div>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sensitive_html
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            # 执行爬取
            result = await self.crawler.crawl_page("https://example.com", filter_content=True)
            
            # 验证内容过滤
            assert result["status"] == "success"
            assert "<script>" not in result["content"]
    
    def test_crawl_configuration(self):
        """测试爬虫配置"""
        # 测试配置加载
        config = self.crawler.get_config()
        assert isinstance(config, dict)
        assert "timeout" in config
        assert "retries" in config
        assert "delay" in config
        assert "user_agent" in config
        
        # 测试配置更新
        new_config = {
            "timeout": 20,
            "retries": 5,
            "delay": 2
        }
        self.crawler.update_config(new_config)
        
        updated_config = self.crawler.get_config()
        assert updated_config["timeout"] == 20
        assert updated_config["retries"] == 5
        assert updated_config["delay"] == 2 