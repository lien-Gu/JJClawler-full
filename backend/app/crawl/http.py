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


class HttpClient:
    def __init__(self, concurrent: bool = None):
        config = settings.crawler
        self.limits = config.concurrent_requests
        self.concurrent = concurrent if concurrent is not None else self.limits > 1
        self.delay = config.request_delay
        self.timeout = config.timeout
        self.retries = config.retry_times
        self.client = httpx.Client()
        self.async_client = httpx.AsyncClient()

    async def run(self, urls: str | List[str]) -> Dict | List[Dict]:
        """
        运行爬取网页
        :param urls:
        :return:
        """
        if isinstance(urls, str):
            return self._request_and_get_content_sync(urls)
        if not self.concurrent:
            return self.run_synchronously(urls)
        return await self.run_concurrently(urls)

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

    def run_synchronously(self, urls: List[str]) -> List[Dict]:
        """
        同步顺序爬取
        :param urls:
        :return:
        """
        results = []
        for url in urls:
            result = self._request_and_get_content_sync(url)
            results.append(result)
        return results

    async def _request_and_get_content_async(
            self, url: str, semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """
        异步获取单个URL并解析内容
        :param url:
        :param semaphore:
        :return:
        """
        async with semaphore:
            try:
                await asyncio.sleep(self.delay)
                response = await self.async_client.get(url, timeout=self.timeout)
                response.raise_for_status()
                return json.loads(response.content)
            except (httpx.RequestError, json.JSONDecodeError) as e:
                print(f"并发爬取失败: {url} - 错误: {e}")
                return {"status": "error", "url": url, "error": str(e)}

    def _request_and_get_content_sync(self, url: str) -> Dict[str, Any]:
        """
        同步获取单个URL并解析内容

        :param url:
        :return:
        """
        response = self.client.get(url, timeout=self.timeout)
        response.raise_for_status()
        return json.loads(response.content)

    async def close(self):
        """
        关闭请求连接池
        :return:
        """
        self.client.close()
        await self.async_client.aclose()
