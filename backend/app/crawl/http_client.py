#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTTP客户端模块 - 集成熔断器和重试机制的HTTP客户端

提供高性能的HTTP请求功能，内置熔断器保护和网络错误重试机制。
所有网络请求都会经过熔断器判断和重试保护。

Author: Leeby Gu
Date: 2025/7/23 23:46
Updated: 2025/8/20 - 集成熔断器和重试机制
"""

import asyncio
import json
from typing import Any, Dict, List, Union

from httpx import AsyncClient, HTTPError, HTTPStatusError, Limits, Timeout
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import settings
from app.crawl.circuit_breaker import CircuitBreakerOpenException, prepare_for_request, report_request_success, \
    report_service_error
from app.logger import get_logger

logger = get_logger(__name__)


def should_retry_request(exception) -> bool:
    """
    判断是否应该重试请求
    
    重试策略：
    - 服务错误（503）：可重试，但需先报告给熔断器
    - 网络错误：可重试
    - 熔断器开启：不重试（由熔断器管理）
    - 其他错误：不重试
    """
    # 检查是否为服务不可用错误（503）
    if isinstance(exception, HTTPStatusError) and exception.response.status_code == 503:
        # 在异步环境中报告服务错误给熔断器
        logger.error(f"HTTP客户端检测到服务错误: {exception}")
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(report_service_error())
        else:
            asyncio.run(report_service_error())
        logger.info("服务不可用错误，将在熔断器恢复后重试")
        return True

    if isinstance(exception, CircuitBreakerOpenException):
        return False  # 熔断器开启时不重试

    # 检查是否为可重试的网络错误
    if isinstance(exception, (ValueError, KeyError, HTTPError, TimeoutError, json.JSONDecodeError)):
        logger.info(f"网络错误，将进行重试: {type(exception).__name__}")
        return True

    logger.warning(f"不可重试错误: {type(exception).__name__}")
    return False


class HttpClient:
    """
    统一HTTP客户端 - 集成熔断器和重试机制
    
    特性:
    - 连接池优化，支持keep-alive
    - 内置熔断器保护，自动处理503错误
    - 网络错误自动重试机制
    - 统一的错误处理和结果格式
    - 自动JSON解析
    """

    def __init__(self):
        """
        初始化HTTP客户端
        """
        self._config = settings.crawler
        self._client = None  # 延迟创建，避免事件循环绑定问题

    async def run(self, urls: Union[str, List[str]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        执行HTTP请求 - 唯一的对外接口

        :param urls:  单个URL字符串或URL列表
        :return: 单个URL返回Dict，多个URL返回List[Dict].
        错误格式: {"status": "error", "url": url, "error": error_msg}
        """

        if isinstance(urls, str):
            return await self._execute_single_request(urls)
        if not urls:
            return []
        # 统一使用顺序处理，并发由上层控制
        return await self._request_sequential(urls)

    async def close(self):
        """关闭HTTP客户端连接池"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.debug("AsyncClient已关闭")

    # ==================== 私有方法 ====================

    def _create_http_client(self) -> AsyncClient | None:
        """创建优化的HTTP客户端"""
        # 连接池配置
        limits = Limits(
            max_keepalive_connections=10,  # 降低连接池大小
            max_connections=15,
            keepalive_expiry=30
        )

        # 超时配置
        timeout = Timeout(
            connect=15.0,  # 增加连接超时
            read=self._config.timeout,
            write=10.0,
            pool=5.0
        )

        client = AsyncClient(
            limits=limits,
            timeout=timeout,
            follow_redirects=True,
            headers=self._config.user_agent,
            trust_env=False,
        )

        return client

    @staticmethod
    def _parse_json_response(self, response) -> Dict[str, Any]:
        """解析JSON响应内容"""
        return json.loads(response.content)

    async def _ensure_client_ready(self):
        """确保 HTTP 客户端已初始化并准备就绪"""
        if self._client is None:
            self._client = self._create_http_client()

    @retry(
        retry=retry_if_exception(should_retry_request),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True
    )
    async def _execute_single_request(self, url: str) -> Dict[str, Any]:
        """
        执行单个HTTP请求
        
        请求流程：
        1. 检查熔断器状态，等待恢复如有需要
        2. 执行HTTP请求
        3. 解析响应并记录成功
        """
        # 检查熔断器状态，等待恢复如有需要
        await prepare_for_request()

        # 确保客户端已创建
        await self._ensure_client_ready()

        # 执行HTTP请求
        response = await self._client.get(url)
        response.raise_for_status()

        # 解析响应内容
        result = self._parse_json_response(response)

        # 报告请求成功
        await report_request_success()

        return result

    async def _request_sequential(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        顺序执行多个HTTP请求 - 每个请求都经过熔断器和重试机制
        :param urls: URL列表
        :return: 响应数据列表
        """
        results = []
        for i, url in enumerate(urls):
            if i > 0:  # 第一个请求不需要延迟
                await asyncio.sleep(self._config.request_delay)

            # 每个请求都经过熔断器和重试保护
            result = await self._execute_single_request(url)
            results.append(result)
        return results
