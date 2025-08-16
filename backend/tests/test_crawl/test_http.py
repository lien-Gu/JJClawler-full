"""
HttpClient模块测试

测试app/crawl/http.py的HttpClient类功能，包括HTTP请求、错误处理、资源管理等
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from app.config import settings
from app.crawl.http_client import HttpClient

default_config = settings.crawler


class TestHttpClient:
    """HttpClient测试类"""

    @pytest_asyncio.fixture
    async def async_client(self):
        """创建HttpClient实例 - 异步fixture"""
        client = HttpClient()
        yield client
        await client.close()

    @pytest.fixture
    def mock_response(self):
        """Mock HTTP响应"""
        response = MagicMock()
        response.status_code = 200
        response.content = '{"success": true, "data": "test"}'
        response.raise_for_status = MagicMock()
        return response

    @pytest.fixture
    def mock_error_response(self):
        """Mock HTTP错误响应"""
        response = MagicMock()
        response.status_code = 404
        response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("404 Not Found", request=None, response=response))
        return response

    @pytest.mark.asyncio
    async def test_create_http_client_configuration(self, async_client):
        """测试HTTP客户端配置"""
        http_client = async_client._client

        # 验证配置有效性
        assert isinstance(http_client, httpx.AsyncClient)
        assert http_client.timeout.read == default_config.timeout
        assert http_client.trust_env == False

        res = await http_client.get(url="http://www.baidu.com")
        assert isinstance(res, httpx.Response)
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_run_single_url_success(self, async_client, mock_response):
        """测试单个URL请求 - 成功场景"""
        test_url = "http://example.com/api"
        expected_data = {"success": True, "data": "test"}

        with patch.object(async_client._client, 'get', return_value=mock_response) as mock_get:
            result = await async_client.run(test_url)

            assert result == expected_data
            mock_get.assert_called_once_with(test_url)
            mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_empty_url_list(self, async_client):
        """测试空URL列表"""
        result = await async_client.run([])
        assert result == []

    @pytest.mark.asyncio
    async def test_run_single_url_http_error(self, async_client, mock_error_response):
        """测试单个URL请求 - HTTP错误"""
        test_url = "http://example.com/not-found"

        with patch.object(async_client._client, 'get', return_value=mock_error_response):
            result = await async_client.run(test_url)

            assert result["status"] == "error"
            assert result["url"] == test_url
            assert "404 Not Found" in result["error"]

    @pytest.mark.asyncio
    async def test_run_single_url_json_decode_error(self, async_client):
        """测试单个URL请求 - JSON解析错误"""
        test_url = "http://example.com/invalid-json"

        mock_response = MagicMock()
        mock_response.content = "invalid json content"
        mock_response.raise_for_status = MagicMock()

        with patch.object(async_client._client, 'get', return_value=mock_response):
            result = await async_client.run(test_url)

            assert result["status"] == "error"
            assert result["url"] == test_url
            # JSON解析错误消息可能不包含'json'字样，检查基本错误格式
            assert "error" in result["error"].lower() or "expecting" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_multiple_urls_mixed_results(self, async_client):
        """测试多个URL请求 - 混合成功和失败"""
        test_urls = ["http://example.com/success", "http://example.com/error"]

        # 第一个请求成功
        success_response = MagicMock()
        success_response.content = '{"success": true}'
        success_response.raise_for_status = MagicMock()

        # 第二个请求失败
        error_response = MagicMock()
        error_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("500 Server Error", request=None, response=error_response)
        )

        responses = [success_response, error_response]

        with patch.object(async_client._client, 'get', side_effect=responses), \
                patch('asyncio.sleep', new_callable=AsyncMock):
            result = await async_client.run(test_urls)

            assert len(result) == 2
            assert result[0] == {"success": True}
            assert result[1]["status"] == "error"
            assert result[1]["url"] == test_urls[1]

    @pytest.mark.asyncio
    async def test_request_sequential_with_delay(self, async_client, mock_response):
        """测试顺序请求的延迟机制"""
        test_urls = ["http://example.com/1", "http://example.com/2", "http://example.com/3"]

        with patch.object(async_client._client, 'get', return_value=mock_response), \
                patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await async_client.run(test_urls)

            # 验证延迟调用次数：n个URL应该有n-1次延迟
            assert mock_sleep.call_count == len(test_urls) - 1

            # 验证延迟时间
            for call in mock_sleep.call_args_list:
                assert call[0][0] == async_client._config.request_delay

    @pytest.mark.asyncio
    async def test_real_json_parsing(self, async_client):
        """测试真实的JSON解析"""
        test_url = "http://example.com/json"
        test_data = {"message": "hello", "count": 42, "items": [1, 2, 3]}

        mock_response = MagicMock()
        mock_response.content = json.dumps(test_data)
        mock_response.raise_for_status = MagicMock()

        with patch.object(async_client._client, 'get', return_value=mock_response):
            result = await async_client.run(test_url)

            assert result == test_data
