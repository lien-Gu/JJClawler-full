"""
爬虫基础模块测试文件
测试crawl.base模块的关键功能
"""
import pytest
import json

from app.crawl.base import CrawlConfig, HttpClient


class TestCrawlConfig:
    """测试CrawlConfig类"""
    
    def test_config_loading_success(self, mocker, sample_config_data):
        """测试配置文件加载成功"""
        mock_file_open = mocker.patch('builtins.open', mocker.mock_open())
        mock_json_load = mocker.patch('json.load', return_value=sample_config_data)
        
        config = CrawlConfig()
        
        # 验证配置加载
        assert config.params == sample_config_data["global"]["params"]
        assert config.templates == sample_config_data["global"]["templates"]
        assert config._config == sample_config_data
        
        # 验证文件打开
        mock_file_open.assert_called_once()
        mock_json_load.assert_called_once()
    
    def test_config_loading_file_not_found(self, mocker):
        """测试配置文件不存在"""
        mocker.patch('builtins.open', side_effect=FileNotFoundError)
        
        with pytest.raises(Exception) as exc_info:
            CrawlConfig()
        
        assert "配置文件加载失败" in str(exc_info.value)
    
    def test_config_loading_invalid_json(self, mocker):
        """测试配置文件JSON格式错误"""
        mocker.patch('builtins.open', mocker.mock_open())
        mocker.patch('json.load', side_effect=json.JSONDecodeError("test", "test", 0))
        
        with pytest.raises(Exception) as exc_info:
            CrawlConfig()
        
        assert "配置文件加载失败" in str(exc_info.value)
    
    def test_get_task_config_success(self, mocker, sample_config_data):
        """测试获取任务配置成功"""
        mocker.patch('builtins.open', mocker.mock_open())
        mocker.patch('json.load', return_value=sample_config_data)
        
        config = CrawlConfig()
        
        # 测试获取存在的任务配置
        jiazi_config = config.get_task_config("jiazi")
        assert jiazi_config is not None
        assert jiazi_config["id"] == "jiazi"
        assert jiazi_config["template"] == "jiazi"
        
        # 测试获取不存在的任务配置
        nonexistent_config = config.get_task_config("nonexistent")
        assert nonexistent_config is None
    
    def test_get_all_tasks(self, mocker, sample_config_data):
        """测试获取所有任务配置"""
        mocker.patch('builtins.open', mocker.mock_open())
        mocker.patch('json.load', return_value=sample_config_data)
        
        config = CrawlConfig()
        
        all_tasks = config.get_all_tasks()
        assert len(all_tasks) == 3
        assert all_tasks[0]["id"] == "jiazi"
        assert all_tasks[1]["id"] == "index"
        assert all_tasks[2]["id"] == "yq"
    
    def test_build_url_success(self, mocker, sample_config_data):
        """测试URL构建成功"""
        mocker.patch('builtins.open', mocker.mock_open())
        mocker.patch('json.load', return_value=sample_config_data)
        
        config = CrawlConfig()
        
        # 测试jiazi模板
        jiazi_task = sample_config_data["crawl_tasks"][0]
        jiazi_url = config.build_url(jiazi_task)
        assert jiazi_url == "https://api.example.com/jiazi?page=1"
        
        # 测试category模板
        index_task = sample_config_data["crawl_tasks"][1]
        index_url = config.build_url(index_task)
        assert index_url == "https://api.example.com/category/index?page=1"
    
    def test_determine_page_ids_special_chars(self, mocker, sample_config_data, test_page_ids):
        """测试特殊字符页面ID处理"""
        mocker.patch('builtins.open', mocker.mock_open())
        mocker.patch('json.load', return_value=sample_config_data)
        
        config = CrawlConfig()
        
        # 测试jiazi特殊字符
        jiazi_ids = config.determine_page_ids(["jiazi"])
        assert jiazi_ids == ["jiazi"]
        
        # 测试category特殊字符
        category_ids = config.determine_page_ids(["category"])
        assert len(category_ids) == 2  # index和yq，排除jiazi
        assert "index" in category_ids
        assert "yq" in category_ids
        assert "jiazi" not in category_ids
        
        # 测试all特殊字符
        all_ids = config.determine_page_ids(["all"])
        assert len(all_ids) == 3
        assert all(task_id in all_ids for task_id in ["jiazi", "index", "yq"])
    
    def test_validate_page_id(self, mocker, sample_config_data):
        """测试页面ID验证"""
        mocker.patch('builtins.open', mocker.mock_open())
        mocker.patch('json.load', return_value=sample_config_data)
        
        config = CrawlConfig()
        
        # 测试有效的页面ID
        assert config.validate_page_id("jiazi") is True
        assert config.validate_page_id("index") is True
        assert config.validate_page_id("yq") is True
        
        # 测试无效的页面ID
        assert config.validate_page_id("invalid") is False
        assert config.validate_page_id("nonexistent") is False


class TestHttpClient:
    """测试HttpClient类"""
    
    @pytest.fixture
    def http_client(self):
        """创建HttpClient实例"""
        return HttpClient(request_delay=0.1)
    
    @pytest.mark.asyncio
    async def test_get_request_success(self, http_client, mocker, mock_http_response):
        """测试GET请求成功"""
        # 设置模拟
        mock_sleep = mocker.patch('asyncio.sleep')
        mock_client_class = mocker.patch('httpx.AsyncClient')
        
        mock_response = mocker.Mock()
        mock_response.json.return_value = mock_http_response["success"]
        mock_response.raise_for_status.return_value = None
        
        mock_client = mocker.Mock()
        mock_client.get = mocker.AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        http_client.session = mock_client
        
        # 执行请求
        result = await http_client.get("https://api.example.com/test")
        
        # 验证结果
        assert result == mock_http_response["success"]
        
        # 验证调用
        mock_sleep.assert_called_once_with(0.1)
        mock_client.get.assert_called_once_with("https://api.example.com/test")
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_request_http_error(self, http_client, mocker):
        """测试GET请求HTTP错误"""
        # 设置模拟
        mock_sleep = mocker.patch('asyncio.sleep')
        mock_client_class = mocker.patch('httpx.AsyncClient')
        
        mock_response = mocker.Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 404 Not Found")
        
        mock_client = mocker.Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        http_client.session = mock_client
        
        # 执行请求并验证异常
        with pytest.raises(Exception) as exc_info:
            await http_client.get("https://api.example.com/test")
        
        assert "请求失败" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_close_session(self, http_client, mocker):
        """测试关闭会话"""
        # 设置模拟session
        mock_session = mocker.Mock()
        mock_session.aclose = mocker.AsyncMock()
        http_client.session = mock_session
        
        # 执行关闭
        await http_client.close()
        
        # 验证调用
        mock_session.aclose.assert_called_once()
    
    def test_initialization_default_delay(self):
        """测试默认延迟初始化"""
        client = HttpClient()
        assert client.request_delay == 1.0
    
    def test_initialization_custom_delay(self):
        """测试自定义延迟初始化"""
        client = HttpClient(request_delay=0.5)
        assert client.request_delay == 0.5


class TestIntegration:
    """集成测试"""
    
    def test_config_and_url_building_integration(self, mocker):
        """测试配置加载和URL构建的集成"""
        sample_config = {
            "global": {
                "params": {"page": 1, "pageSize": 20},
                "templates": {
                    "jiazi": "https://api.example.com/jiazi?page={page}&pageSize={pageSize}",
                    "category": "https://api.example.com/category/{category}?page={page}"
                }
            },
            "crawl_tasks": [
                {
                    "id": "jiazi",
                    "template": "jiazi",
                    "params": {"page": 1}
                },
                {
                    "id": "index",
                    "template": "category", 
                    "params": {"category": "index", "page": 2}
                }
            ]
        }
        
        mocker.patch('builtins.open', mocker.mock_open())
        mocker.patch('json.load', return_value=sample_config)
        
        config = CrawlConfig()
        
        # 测试jiazi任务URL构建
        jiazi_task = config.get_task_config("jiazi")
        jiazi_url = config.build_url(jiazi_task)
        assert jiazi_url == "https://api.example.com/jiazi?page=1&pageSize=20"
        
        # 测试index任务URL构建
        index_task = config.get_task_config("index")
        index_url = config.build_url(index_task)
        assert index_url == "https://api.example.com/category/index?page=2"