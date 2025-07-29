"""
爬虫基础模块测试
测试 CrawlConfig、HttpClient 和 Parser 的核心功能
"""

import pytest
import json
from unittest.mock import Mock, mock_open
import httpx

from app.crawl_config import CrawlConfig
from app.crawl.http import HttpClient
from app.crawl.parser import RankingParser, PageParser, NovelPageParser


class TestCrawlConfig:
    """测试爬虫配置类"""

    def test_config_initialization_success(self, mocker, sample_config_data):
        """测试配置文件加载成功"""
        # Mock文件读取
        mocker.patch("builtins.open", mock_open(read_data=json.dumps(sample_config_data)))
        
        config = CrawlConfig()
        
        assert config.params == sample_config_data["global"]["base_params"]
        assert config.templates == sample_config_data["global"]["templates"]
        assert len(config.get_all_tasks()) == 3

    def test_config_file_load_failure(self, mocker):
        """测试配置文件加载失败"""  
        mocker.patch("builtins.open", side_effect=FileNotFoundError("File not found"))
        
        with pytest.raises(Exception, match="配置文件加载失败"):
            CrawlConfig()

    def test_get_task_config(self, mocker, sample_config_data):
        """测试获取任务配置"""
        mocker.patch("builtins.open", mock_open(read_data=json.dumps(sample_config_data)))
        config = CrawlConfig()
        
        # 测试存在的任务
        jiazi_task = config.get_task_config("jiazi")
        assert jiazi_task["id"] == "jiazi"
        assert jiazi_task["template"] == "jiazi_ranking"
        
        # 测试不存在的任务
        assert config.get_task_config("nonexistent") is None

    def test_build_url(self, mocker, sample_config_data):
        """测试URL构建"""
        mocker.patch("builtins.open", mock_open(read_data=json.dumps(sample_config_data)))
        config = CrawlConfig()
        
        # 测试夹子榜URL构建
        jiazi_url = config.build_url("jiazi") 
        expected_url = "https://app-cdn.jjwxc.com/bookstore/favObservationByDate?day=today&use_cdn=1&version=20"
        assert jiazi_url == expected_url
        
        # 测试页面URL构建
        index_url = config.build_url("index")
        expected_index_url = "https://app-cdn.jjwxc.com/bookstore/getFullPageV1?channel=index&version=20&use_cdn=1"
        assert index_url == expected_index_url

    def test_build_novel_url(self, mocker, sample_config_data):
        """测试书籍详情URL构建"""
        mocker.patch("builtins.open", mock_open(read_data=json.dumps(sample_config_data)))
        config = CrawlConfig()
        
        novel_url = config.build_novel_url("123456")
        expected_url = "https://app-cdn.jjwxc.com/androidapi/novelbasicinfo?novelId=123456"
        assert novel_url == expected_url

    def test_determine_page_ids(self, mocker, sample_config_data):
        """测试页面ID确定逻辑"""
        mocker.patch("builtins.open", mock_open(read_data=json.dumps(sample_config_data)))
        config = CrawlConfig()
        
        # 测试单个页面ID
        assert config.determine_page_ids(["jiazi"]) == ["jiazi"]
        
        # 测试特殊关键字
        category_ids = config.determine_page_ids(["category"])
        assert "index" in category_ids
        assert "yq" in category_ids
        assert "jiazi" not in category_ids  # 分类页面应排除jiazi
        
        # 测试all关键字
        all_ids = config.determine_page_ids(["all"])
        assert len(all_ids) == 3
        assert "jiazi" in all_ids

    def test_validate_page_id(self, mocker, sample_config_data):
        """测试页面ID验证"""
        mocker.patch("builtins.open", mock_open(read_data=json.dumps(sample_config_data)))
        config = CrawlConfig()
        
        assert config.validate_page_id("jiazi") is True
        assert config.validate_page_id("index") is True
        assert config.validate_page_id("invalid_id") is False


class TestHttpClient:
    """测试HTTP客户端"""

    @pytest.mark.asyncio
    async def test_single_url_request(self, mocker, mock_jiazi_response):
        """测试单个URL请求"""
        # Mock httpx.Client
        mock_response = Mock()
        mock_response.content = json.dumps(mock_jiazi_response).encode()
        mock_response.raise_for_status.return_value = None
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        
        mocker.patch("httpx.Client", return_value=mock_client)
        mocker.patch("httpx.AsyncClient", return_value=Mock())
        
        client = HttpClient()
        result = await client.run("https://test.com/api")
        
        assert result == mock_jiazi_response
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio  
    async def test_multiple_urls_concurrent(self, mocker, mock_jiazi_response):
        """测试多个URL并发请求"""
        # Mock AsyncClient
        mock_response = Mock()
        mock_response.content = json.dumps(mock_jiazi_response).encode()
        mock_response.raise_for_status.return_value = None
        
        mock_async_client = Mock()
        mock_async_client.get = Mock(return_value=mock_response)
        
        mocker.patch("httpx.AsyncClient", return_value=mock_async_client)
        mocker.patch("httpx.Client", return_value=Mock())
        mocker.patch("asyncio.sleep")  # Mock延时
        
        client = HttpClient(concurrent=True)
        urls = ["https://test1.com", "https://test2.com"]
        
        results = await client.run(urls)
        
        assert len(results) == 2
        assert mock_async_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_http_error_handling(self, mocker):
        """测试HTTP错误处理"""
        # Mock网络错误
        mock_client = Mock() 
        mock_client.get.side_effect = httpx.RequestError("Network error")
        
        mocker.patch("httpx.Client", return_value=mock_client)
        
        client = HttpClient()
        
        # 同步请求应该抛出异常
        with pytest.raises(httpx.RequestError):
            await client.run("https://error.com")


class TestRankingParser:
    """测试榜单解析器"""

    def test_jiazi_ranking_parse(self, mock_jiazi_response):
        """测试夹子榜解析"""
        parser = RankingParser("jiazi")
        parser.parse_ranking_info(mock_jiazi_response)
        
        # 验证榜单信息
        assert parser.ranking_info["rank_id"] == "jiazi"
        assert parser.ranking_info["page_id"] == "jiazi"
        
        # 验证书籍快照
        assert len(parser.book_snapshots) == 2
        assert parser.book_snapshots[0]["novel_id"] == "123456"
        assert parser.book_snapshots[0]["title"] == "测试小说1"
        assert parser.book_snapshots[0]["position"] == 0

    def test_page_ranking_parse(self, mock_page_response):
        """测试页面榜单解析"""
        parser = RankingParser("index")
        ranking_data = mock_page_response["data"][0]
        parser.parse_ranking_info(ranking_data)
        
        # 验证榜单信息
        assert parser.ranking_info["rank_id"] == "hottest"
        assert parser.ranking_info["channel_name"] == "热门榜单"
        assert parser.ranking_info["page_id"] == "index"
        
        # 验证书籍数据
        assert len(parser.book_snapshots) == 2
        novel_ids = parser.get_novel_ids()
        assert "789101" in novel_ids
        assert "789102" in novel_ids


class TestPageParser:
    """测试页面解析器"""

    def test_parse_page_data(self, mock_page_response):
        """测试页面数据解析"""
        parser = PageParser(mock_page_response, "index")
        
        assert len(parser.rankings) == 1
        ranking = parser.rankings[0]
        assert ranking.ranking_info["rank_id"] == "hottest"
        assert len(ranking.book_snapshots) == 2

    def test_parse_jiazi_page(self, mock_jiazi_response):
        """测试解析夹子榜页面"""
        parser = PageParser(mock_jiazi_response, "jiazi")
        
        assert len(parser.rankings) == 1
        ranking = parser.rankings[0]
        assert ranking.ranking_info["rank_id"] == "jiazi"
        assert len(ranking.book_snapshots) == 2


class TestNovelPageParser:
    """测试书籍详情解析器"""

    def test_parse_novel_info(self, mock_book_detail_response):
        """测试书籍详情解析"""
        parser = NovelPageParser(mock_book_detail_response)
        
        book_detail = parser.book_detail
        assert book_detail["novel_id"] == "123456"
        assert book_detail["title"] == "测试小说详情"
        assert book_detail["author_id"] == "1001"
        assert book_detail["status"] == "连载中"
        assert book_detail["word_counts"] == 50000
        assert book_detail["chapter_counts"] == 25
        assert book_detail["favorites"] == 1200
        assert book_detail["clicks"] == 5000
        assert book_detail["comments"] == 100
        assert book_detail["nutrition"] == 95


class TestIntegration:
    """集成测试"""

    def test_config_and_parser_integration(self, mocker, sample_config_data, mock_jiazi_response):
        """测试配置和解析器集成"""
        # Mock配置
        mocker.patch("builtins.open", mock_open(read_data=json.dumps(sample_config_data)))
        config = CrawlConfig()
        
        # 构建URL
        url = config.build_url("jiazi")
        assert "favObservationByDate" in url
        
        # 解析数据  
        parser = PageParser(mock_jiazi_response, "jiazi")
        assert len(parser.rankings) == 1
        
        # 获取书籍ID
        ranking = parser.rankings[0]
        novel_ids = ranking.get_novel_ids()
        
        # 构建书籍详情URL
        book_urls = [config.build_novel_url(nid) for nid in novel_ids]
        assert len(book_urls) == 2
        assert "novelbasicinfo" in book_urls[0]