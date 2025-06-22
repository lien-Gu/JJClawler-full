"""
爬虫基础模块单元测试

测试 app.modules.crawler.base 模块的所有功能
"""
import pytest
import os
import tempfile
from app.modules.crawler.base import (
    get_crawler_config,
    validate_crawl_result,
    get_default_headers,
    extract_book_id_from_url,
    build_ranking_url,
    CrawlerStats
)
from .conftest import TEST_DEFAULT_HEADERS, CRAWLER_STATS_TEST_DATA


class TestCrawlerConfig:
    """爬虫配置测试"""
    
    def test_get_crawler_config_success(self, mocker, mock_urls_config):
        """测试成功获取爬虫配置"""
        mock_settings = type('Settings', (), {'URLS_CONFIG_FILE': '/test/urls.json'})()
        mocker.patch('app.modules.crawler.base.get_settings', return_value=mock_settings)
        mocker.patch('app.modules.crawler.base.read_json_file', return_value=mock_urls_config)
        
        result = get_crawler_config()
        
        assert result == mock_urls_config
    
    def test_get_crawler_config_empty_file(self, mocker):
        """测试配置文件为空的情况"""
        mock_settings = type('Settings', (), {'URLS_CONFIG_FILE': '/test/urls.json'})()
        mocker.patch('app.modules.crawler.base.get_settings', return_value=mock_settings)
        mocker.patch('app.modules.crawler.base.read_json_file', return_value={})
        
        result = get_crawler_config()
        
        assert result == {}
    
    def test_get_crawler_config_file_not_exists(self, mocker):
        """测试配置文件不存在的情况"""
        mock_settings = type('Settings', (), {'URLS_CONFIG_FILE': '/test/urls.json'})()
        mocker.patch('app.modules.crawler.base.get_settings', return_value=mock_settings)
        mocker.patch('app.modules.crawler.base.read_json_file', return_value={})  # 返回默认值
        
        result = get_crawler_config()
        
        assert result == {}


class TestDataValidation:
    """数据验证测试"""
    
    def test_validate_crawl_result_valid_dict(self):
        """测试有效的字典数据"""
        valid_data = {
            "code": "200",
            "data": {"list": [{"title": "test"}]}
        }
        
        assert validate_crawl_result(valid_data) is True
    
    def test_validate_crawl_result_missing_required_fields(self):
        """测试缺少必需字段"""
        invalid_data = {"code": "200"}  # 缺少 data 字段
        
        assert validate_crawl_result(invalid_data) is False
        
        invalid_data2 = {"data": {"list": []}}  # 缺少 code 字段
        
        assert validate_crawl_result(invalid_data2) is False
    
    def test_validate_crawl_result_empty_data(self):
        """测试空数据"""
        assert validate_crawl_result(None) is False
        assert validate_crawl_result({}) is False
        assert validate_crawl_result("") is False
        assert validate_crawl_result([]) is False
    
    def test_validate_crawl_result_non_dict(self):
        """测试非字典类型数据"""
        assert validate_crawl_result("invalid") is False
        assert validate_crawl_result(123) is False
        assert validate_crawl_result([1, 2, 3]) is False


class TestHeaders:
    """请求头测试"""
    
    def test_get_default_headers(self):
        """测试获取默认请求头"""
        headers = get_default_headers()
        
        assert isinstance(headers, dict)
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "Accept-Encoding" in headers
        assert "Connection" in headers
        
        # 验证 User-Agent 包含 iPhone 信息
        assert "iPhone" in headers["User-Agent"]
        assert "Mozilla" in headers["User-Agent"]


class TestURLUtils:
    """URL工具函数测试"""
    
    def test_extract_book_id_from_url_with_test_cases(self, book_url_test_cases):
        """测试使用预定义测试用例提取书籍ID"""
        for url, expected_id in book_url_test_cases:
            result = extract_book_id_from_url(url)
            assert result == expected_id, f"URL: {url}, 期望: {expected_id}, 实际: {result}"
    
    def test_extract_book_id_from_url_trailing_number(self):
        """测试从URL末尾提取书籍ID"""
        url = "https://example.com/book/123456/"
        assert extract_book_id_from_url(url) == "123456"
        
        url2 = "https://example.com/novel/789012"
        assert extract_book_id_from_url(url2) == "789012"
    
    def test_extract_book_id_from_url_bookid_param(self):
        """测试从bookid参数提取书籍ID"""
        url = "https://example.com/book?bookid=123456&other=value"
        assert extract_book_id_from_url(url) == "123456"
    
    def test_extract_book_id_from_url_novelid_param(self):
        """测试从novelid参数提取书籍ID"""
        url = "https://example.com/read?novelid=789012"
        assert extract_book_id_from_url(url) == "789012"
    
    def test_extract_book_id_from_url_book_path(self):
        """测试从/book/路径提取书籍ID"""
        url = "https://example.com/book/345678/chapter/1"
        assert extract_book_id_from_url(url) == "345678"
    
    def test_extract_book_id_from_url_no_match(self):
        """测试无法匹配的URL"""
        url = "https://example.com/invalid/path"
        assert extract_book_id_from_url(url) is None
        
        url2 = "https://example.com/book/abc"  # 非数字ID
        assert extract_book_id_from_url(url2) is None
    
    def test_build_ranking_url_basic(self):
        """测试基本的榜单URL构建"""
        base_url = "https://api.example.com/ranking"
        channel = "yq"
        
        result = build_ranking_url(base_url, channel)
        
        assert "channel=yq" in result
        assert base_url in result
    
    def test_build_ranking_url_with_params(self):
        """测试带参数的榜单URL构建"""
        base_url = "https://api.example.com/ranking"
        channel = "yq"
        params = {"limit": 50, "type": "daily"}
        
        result = build_ranking_url(base_url, channel, **params)
        
        assert "channel=yq" in result
        assert "limit=50" in result
        assert "type=daily" in result
    
    def test_build_ranking_url_existing_params(self):
        """测试已有参数的URL"""
        base_url = "https://api.example.com/ranking?existing=value"
        channel = "cy"
        
        result = build_ranking_url(base_url, channel)
        
        assert "existing=value" in result
        assert "channel=cy" in result
        assert "&" in result  # 应该用&连接参数
    
    def test_build_ranking_url_override_channel(self):
        """测试覆盖频道参数"""
        base_url = "https://api.example.com/ranking"
        channel = "yq"
        params = {"channel": "cy"}  # 手动指定的频道
        
        result = build_ranking_url(base_url, channel, **params)
        
        # 手动指定的频道应该被保留
        assert "channel=cy" in result


class TestCrawlerStats:
    """爬虫统计测试"""
    
    def test_crawler_stats_initialization(self):
        """测试统计对象初始化"""
        stats = CrawlerStats()
        
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.books_crawled == 0
        assert stats.errors == []
    
    def test_add_request_success(self):
        """测试添加成功请求"""
        stats = CrawlerStats()
        
        stats.add_request(success=True)
        
        assert stats.total_requests == 1
        assert stats.successful_requests == 1
        assert stats.failed_requests == 0
    
    def test_add_request_failure(self):
        """测试添加失败请求"""
        stats = CrawlerStats()
        
        stats.add_request(success=False)
        
        assert stats.total_requests == 1
        assert stats.successful_requests == 0
        assert stats.failed_requests == 1
    
    def test_add_books(self):
        """测试添加书籍数量"""
        stats = CrawlerStats()
        
        stats.add_books(25)
        assert stats.books_crawled == 25
        
        stats.add_books(15)
        assert stats.books_crawled == 40
    
    def test_add_error(self):
        """测试添加错误记录"""
        stats = CrawlerStats()
        
        stats.add_error("连接超时")
        assert len(stats.errors) == 1
        assert stats.errors[0] == "连接超时"
        
        stats.add_error("解析失败")
        assert len(stats.errors) == 2
    
    def test_add_error_limit(self):
        """测试错误记录数量限制"""
        stats = CrawlerStats()
        
        # 添加超过100个错误
        for i in range(120):
            stats.add_error(f"错误{i}")
        
        # 应该只保留最后100个
        assert len(stats.errors) == 100
        assert stats.errors[0] == "错误20"  # 前20个被删除
        assert stats.errors[-1] == "错误119"
    
    def test_get_success_rate(self):
        """测试成功率计算"""
        stats = CrawlerStats()
        
        # 没有请求时成功率为0
        assert stats.get_success_rate() == 0.0
        
        # 添加请求后计算成功率
        stats.add_request(success=True)
        stats.add_request(success=True)
        stats.add_request(success=False)
        
        # 2/3 = 0.6666...
        success_rate = stats.get_success_rate()
        assert abs(success_rate - 0.6666666666666666) < 0.0001
    
    def test_reset(self):
        """测试重置统计"""
        stats = CrawlerStats()
        
        # 添加一些数据
        stats.add_request(success=True)
        stats.add_books(10)
        stats.add_error("测试错误")
        
        # 重置
        stats.reset()
        
        # 验证所有数据被清零
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.books_crawled == 0
        assert stats.errors == []
    
    def test_crawler_stats_with_test_data(self):
        """使用预定义测试数据测试爬虫统计"""
        stats = CrawlerStats()
        
        # 使用成功场景的测试数据
        success_data = CRAWLER_STATS_TEST_DATA["success_scenario"]
        
        # 模拟成功和失败的请求
        for _ in range(success_data["successful_requests"]):
            stats.add_request(success=True)
        for _ in range(success_data["failed_requests"]):
            stats.add_request(success=False)
        
        # 添加爬取的书籍数量
        stats.add_books(success_data["books_crawled"])
        
        # 添加错误
        for error in success_data["errors"]:
            stats.add_error(error)
        
        # 验证统计结果
        assert stats.successful_requests == success_data["successful_requests"]
        assert stats.failed_requests == success_data["failed_requests"]
        assert stats.books_crawled == success_data["books_crawled"]
        assert len(stats.errors) == len(success_data["errors"])
        
        # 验证成功率计算
        expected_rate = success_data["successful_requests"] / (success_data["successful_requests"] + success_data["failed_requests"])
        assert abs(stats.get_success_rate() - expected_rate) < 0.001
    
    def test_get_summary(self):
        """测试获取统计摘要"""
        stats = CrawlerStats()
        
        # 添加测试数据
        stats.add_request(success=True)
        stats.add_request(success=True)
        stats.add_request(success=False)
        stats.add_books(25)
        stats.add_error("错误1")
        stats.add_error("错误2")
        
        summary = stats.get_summary()
        
        assert summary["total_requests"] == 3
        assert summary["successful_requests"] == 2
        assert summary["failed_requests"] == 1
        assert summary["success_rate"] == "66.67%"
        assert summary["books_crawled"] == 25
        assert summary["error_count"] == 2
        assert summary["recent_errors"] == ["错误1", "错误2"]
    
    def test_get_summary_many_errors(self):
        """测试多错误情况下的摘要"""
        stats = CrawlerStats()
        
        # 添加10个错误
        for i in range(10):
            stats.add_error(f"错误{i}")
        
        summary = stats.get_summary()
        
        # 应该只显示最近5个错误
        assert len(summary["recent_errors"]) == 5
        assert summary["recent_errors"] == ["错误5", "错误6", "错误7", "错误8", "错误9"]
        assert summary["error_count"] == 10