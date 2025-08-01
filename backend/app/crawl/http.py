#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
# @Project: PyCharm
# @File    : http.py
# @Time: 2025/7/23 23:46
# @Author  : Leeby Gu
'''
import asyncio
import json
from typing import Any, Dict, List

import httpx

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class HttpClient:
    def __init__(self, concurrent: bool = None):
        config = settings.crawler
        self.limits = config.concurrent_requests
        self.concurrent = concurrent if concurrent is not None else self.limits > 1
        self.delay = config.request_delay
        self.timeout = config.timeout
        self.retries = config.retry_times

        # 创建优化的HTTP客户端
        self._create_optimized_clients()

    def _create_optimized_clients(self):
        """创建优化的HTTP客户端连接池"""

        # 连接池配置
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=30,
            keepalive_expiry=30
        )

        # 超时配置
        timeout = httpx.Timeout(
            connect=10.0,
            read=self.timeout,
            write=10.0,
            pool=5.0
        )

        # 异步客户端（移除同步客户端，统一使用异步）
        self.async_client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            follow_redirects=True,
            headers=settings.crawler.user_agent
        )

    async def run(self, urls: str | List[str]) -> Dict | List[Dict]:
        """
        运行爬取网页 - 优化版本
        :param urls:
        :return:
        """
        if isinstance(urls, str):
            return await self._request_single_with_retry(urls)

        if not self.concurrent:
            return await self.run_synchronously(urls)

        return await self.run_concurrently(urls)

    async def _request_single_with_retry(self, url: str) -> Dict[str, Any]:
        """
        带重试的单个请求
        :param url:
        :return:
        """
        last_exception = None

        for attempt in range(self.retries + 1):
            try:
                response = await self.async_client.get(url)
                response.raise_for_status()
                return json.loads(response.content)

            except (httpx.RequestError, json.JSONDecodeError, httpx.HTTPStatusError) as e:
                last_exception = e
                if attempt < self.retries:
                    retry_delay = self.delay * (2 ** attempt)  # 指数退避
                    logger.debug(f"请求失败 {url}, 第 {attempt + 1} 次重试，延迟 {retry_delay:.1f}s")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"请求最终失败 {url}: {e}")

        return {"status": "error", "url": url, "error": str(last_exception)}

    async def run_concurrently(self, urls: List[str]) -> List[Dict]:
        """
        异步并发爬取网页
        :param urls:
        :return:
        """
        semaphore = asyncio.Semaphore(self.limits)
        tasks = [self._request_and_get_content_async(url, semaphore) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def run_synchronously(self, urls: List[str]) -> List[Dict]:
        """
        异步顺序爬取 - 支持重试机制
        :param urls:
        :return:
        """
        results = []
        for url in urls:
            await asyncio.sleep(self.delay)  # 请求间隔
            result = await self._request_single_with_retry(url)
            results.append(result)
        return results

    async def _request_and_get_content_async(
            self, url: str, semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """
        带信号量控制的异步请求 - 使用统一的重试机制
        :param url:
        :param semaphore:
        :return:
        """
        async with semaphore:
            await asyncio.sleep(self.delay)  # 请求间隔控制
            return await self._request_single_with_retry(url)

    async def close(self):
        """
        关闭请求连接池
        :return:
        """
        await self.async_client.aclose()
