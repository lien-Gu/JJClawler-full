"""
爬虫基础组件测试
"""
import pytest
import asyncio
import json
import httpx

from app.crawl.base import CrawlConfig, HttpClient


class TestCrawlConfig:
    """爬取配置测试类"""

    def test_init_with_valid_config(self, mock_urls_config, mocker):
        """测试使用有效配置初始化"""
        mock_config_content = json.dumps(mock_urls_config)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        
        assert config.params == mock_urls_config["global"]["params"]
        assert config.templates == mock_urls_config["global"]["templates"]
        assert config._config == mock_urls_config

    def test_init_with_missing_file(self, mocker):
        """测试文件不存在时的初始化"""
        mocker.patch("builtins.open", side_effect=FileNotFoundError("File not found"))
        with pytest.raises(Exception, match="配置文件加载失败"):
            CrawlConfig()

    def test_init_with_invalid_json(self, mocker):
        """测试无效JSON文件的初始化"""
        invalid_json = "{ invalid json }"
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=invalid_json))
        with pytest.raises(Exception, match="配置文件加载失败"):
            CrawlConfig()

    def test_init_with_empty_global_section(self, mocker):
        """测试空global配置段的初始化"""
        config_data = {"global": {}, "crawl_tasks": []}
        mock_config_content = json.dumps(config_data)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        
        assert config.params == {}
        assert config.templates == {}

    def test_get_task_config_existing_task(self, mock_urls_config, mocker):
        """测试获取存在的任务配置"""
        mock_config_content = json.dumps(mock_urls_config)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        task_config = config.get_task_config("test_task_1")
        
        assert task_config is not None
        assert task_config["id"] == "test_task_1"
        assert task_config["template"] == "page_rank"

    def test_get_task_config_nonexistent_task(self, mock_urls_config, mocker):
        """测试获取不存在的任务配置"""
        mock_config_content = json.dumps(mock_urls_config)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        task_config = config.get_task_config("nonexistent_task")
        
        assert task_config is None

    def test_get_all_tasks(self, mock_urls_config, mocker):
        """测试获取所有任务配置"""
        mock_config_content = json.dumps(mock_urls_config)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        
        assert len(all_tasks) == 2
        assert all_tasks[0]["id"] == "test_task_1"
        assert all_tasks[1]["id"] == "jiazi"

    def test_get_all_tasks_empty_config(self, mocker):
        """测试获取空任务配置"""
        config_data = {"global": {}, "crawl_tasks": []}
        mock_config_content = json.dumps(config_data)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        
        assert all_tasks == []

    def test_get_all_tasks_missing_crawl_tasks(self, mocker):
        """测试缺少crawl_tasks配置"""
        config_data = {"global": {}}
        mock_config_content = json.dumps(config_data)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        
        assert all_tasks == []

    def test_build_url_success(self, mock_urls_config, mocker):
        """测试成功构建URL"""
        mock_config_content = json.dumps(mock_urls_config)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        task_config = {
            "template": "page_rank",
            "params": {"channelId": "romance"}
        }
        
        url = config.build_url(task_config)
        expected_url = "https://api.example.com/page?channelId=romance&size=20"
        assert url == expected_url

    def test_build_url_with_override_params(self, mock_urls_config, mocker):
        """测试使用覆盖参数构建URL"""
        mock_config_content = json.dumps(mock_urls_config)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        task_config = {
            "template": "page_rank",
            "params": {
                "channelId": "fantasy",
                "size": "50"  # 覆盖全局参数
            }
        }
        
        url = config.build_url(task_config)
        expected_url = "https://api.example.com/page?channelId=fantasy&size=50"
        assert url == expected_url

    def test_build_url_nonexistent_template(self, mock_urls_config, mocker):
        """测试使用不存在的模板构建URL"""
        mock_config_content = json.dumps(mock_urls_config)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        task_config = {
            "template": "nonexistent_template",
            "params": {}
        }
        
        with pytest.raises(ValueError, match="模板不存在"):
            config.build_url(task_config)

    def test_build_url_no_params(self, mock_urls_config, mocker):
        """测试无额外参数构建URL"""
        mock_config_content = json.dumps(mock_urls_config)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        task_config = {
            "template": "page_rank"
            # 没有params字段
        }
        
        url = config.build_url(task_config)
        expected_url = "https://api.example.com/page?channelId=test_channel&size=20"
        assert url == expected_url

    def test_build_url_novel_detail_template(self, mock_urls_config, mocker):
        """测试构建书籍详情URL"""
        mock_config_content = json.dumps(mock_urls_config)
        
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_config_content))
        config = CrawlConfig()
        task_config = {
            "template": "novel_detail",
            "params": {"novel_id": "12345"}
        }
        
        url = config.build_url(task_config)
        expected_url = "https://api.example.com/novel/12345?channelId=test_channel"
        assert url == expected_url


class TestHttpClient:
    """HTTP客户端测试类"""

    def test_init_default_delay(self):
        """测试默认延迟初始化"""
        client = HttpClient()
        
        assert client.request_delay == 1.0
        assert isinstance(client.session, httpx.AsyncClient)

    def test_init_custom_delay(self):
        """测试自定义延迟初始化"""
        client = HttpClient(request_delay=2.5)
        
        assert client.request_delay == 2.5

    @pytest.mark.asyncio
    async def test_get_success(self, mocker):
        """测试成功GET请求"""
        mock_response_data = {"status": "success", "data": []}
        
        mock_get = mocker.patch('httpx.AsyncClient.get')
        mock_response = mocker.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = HttpClient(request_delay=0.1)  # 减少测试时间
        result = await client.get("https://api.example.com/test")
        
        assert result == mock_response_data
        mock_get.assert_called_once_with("https://api.example.com/test")
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_http_error(self, mocker):
        """测试HTTP错误"""
        mock_get = mocker.patch('httpx.AsyncClient.get')
        mock_response = mocker.Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=mocker.Mock(), response=mocker.Mock()
        )
        mock_get.return_value = mock_response
        
        client = HttpClient(request_delay=0.1)
        
        with pytest.raises(Exception, match="请求失败"):
            await client.get("https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_get_network_error(self, mocker):
        """测试网络错误"""
        mock_get = mocker.patch('httpx.AsyncClient.get')
        mock_get.side_effect = httpx.ConnectError("Connection failed")
        
        client = HttpClient(request_delay=0.1)
        
        with pytest.raises(Exception, match="请求失败"):
            await client.get("https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_get_json_decode_error(self, mocker):
        """测试JSON解码错误"""
        mock_get = mocker.patch('httpx.AsyncClient.get')
        mock_response = mocker.Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        client = HttpClient(request_delay=0.1)
        
        with pytest.raises(Exception, match="请求失败"):
            await client.get("https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_get_timeout_error(self, mocker):
        """测试请求超时"""
        mock_get = mocker.patch('httpx.AsyncClient.get')
        mock_get.side_effect = httpx.TimeoutException("Request timeout")
        
        client = HttpClient(request_delay=0.1)
        
        with pytest.raises(Exception, match="请求失败"):
            await client.get("https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_request_delay(self, mocker):
        """测试请求延迟功能"""
        import time
        
        mock_get = mocker.patch('httpx.AsyncClient.get')
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = HttpClient(request_delay=0.2)
        
        start_time = time.time()
        await client.get("https://api.example.com/test")
        end_time = time.time()
        
        # 验证延迟至少为设定的时间
        assert end_time - start_time >= 0.2

    @pytest.mark.asyncio
    async def test_close(self, mocker):
        """测试关闭连接"""
        mock_close = mocker.patch('httpx.AsyncClient.aclose')
        client = HttpClient()
        await client.close()
        
        mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_requests_delay(self, mocker):
        """测试多个请求之间的延迟"""
        import time
        
        mock_get = mocker.patch('httpx.AsyncClient.get')
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = HttpClient(request_delay=0.1)
        
        start_time = time.time()
        await client.get("https://api.example.com/test1")
        await client.get("https://api.example.com/test2")
        end_time = time.time()
        
        # 验证总时间包含两次延迟
        assert end_time - start_time >= 0.2

    def test_session_configuration(self):
        """测试会话配置"""
        client = HttpClient()
        
        assert client.session.timeout.read == 30.0
        assert "User-Agent" in client.session.headers
        assert "Mozilla" in client.session.headers["User-Agent"]

    @pytest.mark.asyncio
    async def test_get_with_valid_json_response(self, mocker):
        """测试有效JSON响应"""
        expected_data = {
            "status": "success",
            "data": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"}
            ]
        }
        
        mock_get = mocker.patch('httpx.AsyncClient.get')
        mock_response = mocker.Mock()
        mock_response.json.return_value = expected_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = HttpClient(request_delay=0.1)
        result = await client.get("https://api.example.com/test")
        
        assert result == expected_data
        assert result["status"] == "success"
        assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_get_empty_response(self, mocker):
        """测试空响应"""
        mock_get = mocker.patch('httpx.AsyncClient.get')
        mock_response = mocker.Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = HttpClient(request_delay=0.1)
        result = await client.get("https://api.example.com/test")
        
        assert result == {}