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
from app.crawl.circuit_breaker import CircuitBreakerOpenException, record_error, wait_for_circuit_recovery, get_global_circuit_breaker
from app.logger import get_logger

logger = get_logger(__name__)


def should_retry_network_error(exception):
    """重试条件：网络错误和503错误都可以重试，熔断器异常不重试"""
    # 先处理503错误 - 触发熔断器并允许重试
    if isinstance(exception, HTTPStatusError) and exception.response.status_code == 503:
        logger.error("HTTP客户端检测到503错误，触发熔断器")
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(record_error())
        else:
            asyncio.run(record_error())
        # 503错误应该可以重试（熔断器恢复后）
        logger.info("503错误将在熔断器恢复后重试")
        return True
    
    # 熔断器异常不重试（让熔断器恢复机制处理）
    if isinstance(exception, CircuitBreakerOpenException):
        return False
    
    # 判断是否为网络错误
    if isinstance(exception, (ValueError, KeyError, HTTPError, TimeoutError, json.JSONDecodeError)):
        logger.info(f"网络错误，将进行重试: {type(exception).__name__}: {str(exception)}")
        return True

    # 其他错误不重试
    logger.warning(f"非网络错误，不进行重试: {type(exception).__name__}: {str(exception)}")
    return False


# 创建网络层重试装饰器
network_retry = retry(
    retry=retry_if_exception(should_retry_network_error),
    stop=stop_after_attempt(3),
    # 对于503错误，等待时间由熔断器控制；对于其他网络错误，使用指数退避
    wait=wait_exponential(multiplier=1, min=1, max=5),  # 缩短最大等待时间，因为熔断器会控制503错误的等待
    reraise=True
)


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
            return await self._request_single(urls)
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

        # 模拟Chrome浏览器的完整HTTP头部
        browser_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Connection": "keep-alive"
        }

        client = AsyncClient(
            limits=limits,
            timeout=timeout,
            follow_redirects=True,
            headers=browser_headers,
            trust_env=False,
        )

        return client

    async def _ensure_client(self):
        """
        确保客户端已创建（延迟创建模式）
        """
        if self._client is None:
            self._client = self._create_http_client()
            logger.debug("创建新的AsyncClient实例")
    

    @network_retry
    async def _request_single(self, url: str) -> Dict[str, Any]:
        """
        执行单个HTTP请求 - 集成熔断器和重试机制
        :param url: 目标URL
        :return: 响应数据字典或错误信息
        """
        # 等待熔断器恢复（如果开启的话）- 使用熔断器模块的统一接口
        await wait_for_circuit_recovery()

        # 延迟创建客户端，确保在正确的事件循环上下文中
        await self._ensure_client()

        # 执行HTTP请求
        response = await self._client.get(url)
        response.raise_for_status()

        # 解析JSON响应
        result = json.loads(response.content)
        
        # 记录成功请求（用于半开状态的恢复判断）
        circuit_breaker = await get_global_circuit_breaker()
        await circuit_breaker._record_success()
        
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

            # 每个请求都会经过_request_single的熔断器和重试保护
            result = await self._request_single(url)
            results.append(result)
        return results
