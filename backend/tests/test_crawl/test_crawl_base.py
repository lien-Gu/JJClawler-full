"""
爬虫基础模块测试文件
测试crawl.base模块的核心功能
"""
import pytest
from pytest_mock import MockerFixture

from app.crawl.base import CrawlConfig, HttpClient


def create_mock_config(mocker: MockerFixture, config_data: dict):
    """创建模拟配置对象"""
    mocker.patch('builtins.open', mocker.mock_open())
    mocker.patch('json.load', return_value=config_data)


class TestCrawlConfig:
    """测试CrawlConfig类"""

    def test_initialization_success(self, mocker: MockerFixture, sample_config_data):
        """测试配置初始化成功"""
        create_mock_config(mocker, sample_config_data)

        config = CrawlConfig()

        assert config.params == sample_config_data["global"]["params"]
        assert config.templates == sample_config_data["global"]["templates"]
        assert config._config == sample_config_data

    def test_initialization_file_not_found(self, mocker: MockerFixture):
        """测试配置文件不存在"""
        mocker.patch('builtins.open', side_effect=FileNotFoundError)

        with pytest.raises(Exception, match="配置文件加载失败"):
            CrawlConfig()

    def test_get_task_config(self, mocker: MockerFixture, sample_config_data):
        """测试获取任务配置"""
        create_mock_config(mocker, sample_config_data)
        config = CrawlConfig()

        # 存在的任务
        jiazi_config = config.get_task_config("jiazi")
        assert jiazi_config["id"] == "jiazi"

        # 不存在的任务
        assert config.get_task_config("nonexistent") is None

    def test_build_url(self, mocker: MockerFixture, sample_config_data):
        """测试URL构建"""
        create_mock_config(mocker, sample_config_data)
        config = CrawlConfig()

        # jiazi任务
        jiazi_task = sample_config_data["crawl_tasks"][0]
        url = config.build_url(jiazi_task)
        assert url == "https://api.example.com/jiazi?page=1"

        # category任务
        index_task = sample_config_data["crawl_tasks"][1]
        url = config.build_url(index_task)
        assert url == "https://api.example.com/category/index?page=1"

    def test_determine_page_ids(self, mocker: MockerFixture, sample_config_data):
        """测试页面ID确定"""
        create_mock_config(mocker, sample_config_data)
        config = CrawlConfig()

        # jiazi特殊字符
        assert config.determine_page_ids(["jiazi"]) == ["jiazi"]

        # category特殊字符
        category_ids = config.determine_page_ids(["category"])
        assert "index" in category_ids
        assert "yq" in category_ids
        assert "jiazi" not in category_ids  # 排除jiazi

        # all特殊字符
        all_ids = config.determine_page_ids(["all"])
        assert len(all_ids) == 3

    def test_validate_page_id(self, mocker: MockerFixture, sample_config_data):
        """测试页面ID验证"""
        create_mock_config(mocker, sample_config_data)
        config = CrawlConfig()

        assert config.validate_page_id("jiazi") is True
        assert config.validate_page_id("invalid") is False


class TestHttpClient:
    """测试HttpClient类"""

    @pytest.mark.asyncio
    async def test_get_success(self, mocker: MockerFixture, mock_http_response):
        """测试GET请求成功"""
        # Mock asyncio.sleep
        mocker.patch('asyncio.sleep')

        # Mock httpx.AsyncClient
        mock_response = mocker.Mock()
        mock_response.json.return_value = mock_http_response["success"]
        mock_response.raise_for_status.return_value = None

        mock_session = mocker.Mock()
        mock_session.get = mocker.AsyncMock(return_value=mock_response)

        client = HttpClient(request_delay=0.1)
        client.session = mock_session

        result = await client.get("https://test.com")

        assert result == mock_http_response["success"]
        mock_session.get.assert_called_once_with("https://test.com")

    @pytest.mark.asyncio
    async def test_get_failure(self, mocker: MockerFixture):
        """测试GET请求失败"""
        mocker.patch('asyncio.sleep')

        mock_session = mocker.Mock()
        mock_session.get = mocker.AsyncMock(side_effect=Exception("Network error"))

        client = HttpClient()
        client.session = mock_session

        with pytest.raises(Exception, match="请求失败"):
            await client.get("https://test.com")

    @pytest.mark.asyncio
    async def test_close(self, mocker: MockerFixture):
        """测试关闭连接"""
        mock_session = mocker.Mock()
        mock_session.aclose = mocker.AsyncMock()

        client = HttpClient()
        client.session = mock_session

        await client.close()
        mock_session.aclose.assert_called_once()


class TestIntegration:
    """集成测试"""

    def test_config_url_building_integration(self, mocker: MockerFixture):
        """测试配置和URL构建集成"""
        config_data = {
            "global": {
                "params": {"page": 1},
                "templates": {"test": "https://api.com/{category}?page={page}"}
            },
            "crawl_tasks": [
                {"id": "test", "template": "test", "params": {"category": "books"}}
            ]
        }

        create_mock_config(mocker, config_data)
        config = CrawlConfig()

        task = config.get_task_config("test")
        url = config.build_url(task)

        assert url == "https://api.com/books?page=1"
