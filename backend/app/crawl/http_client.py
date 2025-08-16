#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTTP客户端模块 - 优化的异步HTTP请求客户端

提供高性能的HTTP请求功能，支持并发和顺序两种模式。
重试逻辑由上层CrawlFlow处理，本模块专注于基础HTTP请求。

Author: Leeby Gu
Date: 2025/7/23 23:46
"""

import asyncio
import json
from typing import Any, Dict, List, Union

from httpx import AsyncClient, RequestError, Limits, Timeout, HTTPStatusError

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class HttpClient:
    """
    统一HTTP客户端 - 专注基础HTTP请求功能
    
    特性:
    - 连接池优化，支持keep-alive
    - 统一的错误处理和结果格式
    - 自动JSON解析
    - 并发控制由上层CrawlFlow统一管理
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
            max_keepalive_connections=20,
            max_connections=30,
            keepalive_expiry=30
        )

        # 超时配置
        timeout = Timeout(
            connect=10.0,
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

    async def _ensure_client(self):
        """
        确保客户端已创建（延迟创建模式）
        """
        if self._client is None:
            self._client = self._create_http_client()
            logger.debug("创建新的AsyncClient实例")

    async def _request_single(self, url: str) -> Dict[str, Any]:
        """
        执行单个HTTP请求
        :param url: 目标URL
        :return: 响应数据字典或错误信息
        """
        try:
            # 延迟创建客户端，确保在正确的事件循环上下文中
            await self._ensure_client()
            response = await self._client.get(url)
            response.raise_for_status()
            return json.loads(response.content)
        except (RequestError, json.JSONDecodeError, HTTPStatusError) as e:
            logger.debug(f"HTTP请求失败 {url}: {e}")
            return {"status": "error", "url": url, "error": str(e)}

    async def _request_sequential(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        顺序执行多个HTTP请求
        :param urls: URL列表
        :return: 响应数据列表
        """
        results = []
        for i, url in enumerate(urls):
            if i > 0:  # 第一个请求不需要延迟
                await asyncio.sleep(self._config.request_delay)
            result = await self._request_single(url)
            results.append(result)
        return results
