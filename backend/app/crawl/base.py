"""
爬虫基础类，提供通用爬取功能
"""
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import httpx
import asyncio
from pathlib import Path

from app.config import settings


class CrawlConfig:
    """爬取配置类"""

    def __init__(self):
        self.urls_file = Path(__file__).parent.parent.parent / "data" / "urls.json"
        self._config = None
        self.params = None
        self.templates = None
        self._load_config()

    def _load_config(self):
        """加载URL配置文件"""
        try:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            self.params = self._config.get("global", {}).get("params")
            self.templates = self._config.get("global", {}).get("templates")
        except FileNotFoundError:
            raise Exception(f"配置文件不存在: {self.urls_file}")
        except json.JSONDecodeError:
            raise Exception(f"配置文件格式错误: {self.urls_file}")

    def get_task_config(self, task_id: str) -> Optional[Dict]:
        """获取特定任务的配置"""
        for task in self._config.get("crawl_tasks", []):
            if task["id"] == task_id:
                return task
        return None

    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务配置"""
        return self._config.get("crawl_tasks", [])

    def build_url(self, task_config: Dict) -> str:
        """根据任务配置构建URL"""
        template_name = task_config["template"]
        template_url = self.templates.get(template_name)

        if not template_url:
            raise ValueError(f"模板不存在: {template_name}")

        # 合并全局参数和任务参数
        params = {**self.params, **task_config["params"]}

        try:
            return template_url.format(**params)
        except KeyError as e:
            raise ValueError(f"URL模板参数缺失: {e}")


class HttpClient:
    """HTTP客户端工具类"""

    def __init__(self, timeout: int = None, request_delay: float = None):
        """
        初始化HTTP客户端
        
        Args:
            timeout: 请求超时时间（秒）
            rate_limit: 请求间隔时间（秒）
        """
        craw_setting = settings.crawler
        self.timeout = timeout if timeout else craw_setting.timeout
        self.request_delay = request_delay if request_delay else craw_setting.request_delay
        self.last_request_time = 0

        # 配置客户端
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=craw_setting.user_agent
        )

    async def get(self, url: str, **kwargs) -> Dict:
        """
        发送GET请求
        
        Args:
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            解析后的JSON响应
        """
        await self._request_limit()

        try:
            response = await self.client.get(url, **kwargs)
            response.raise_for_status()

            # 尝试解析JSON
            return response.json()

        except httpx.HTTPError as e:
            raise Exception(f"HTTP请求失败: {url}, 错误: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON解析失败: {url}, 错误: {e}")

    async def _request_limit(self):
        """实现请求速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)

        self.last_request_time = time.time()

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()


class BaseParser(ABC):
    """数据解析器基类"""

    @abstractmethod
    def parse(self, raw_data: Dict) -> List[Dict]:
        """
        解析原始数据
        
        Args:
            raw_data: 原始响应数据
            
        Returns:
            解析后的数据列表
        """
        pass

    @abstractmethod
    def validate(self, parsed_data: Dict) -> bool:
        """
        验证解析后的数据
        
        Args:
            parsed_data: 解析后的单条数据
            
        Returns:
            数据是否有效
        """
        pass


class BaseCrawler:
    """基础爬虫类"""

    def __init__(self, parser: BaseParser, request_delay: float = 1.0):
        """
        初始化爬虫
        
        Args:
            parser: 数据解析器
            request_delay: 请求间隔时间（秒）
        """
        self.parser = parser
        self.config = CrawlConfig()
        self.client = HttpClient(request_delay=request_delay)
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_items': 0,
            'valid_items': 0,
        }

    async def crawl_task(self, task_id: str) -> Dict[str, Any]:
        """
        爬取特定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            爬取结果
        """
        task_config = self.config.get_task_config(task_id)
        if not task_config:
            raise ValueError(f"任务配置不存在: {task_id}")

        url = self.config.build_url(task_config)

        try:
            # 发送请求
            self.stats['total_requests'] += 1
            raw_data = await self.client.get(url)
            self.stats['successful_requests'] += 1

            # 解析数据
            parsed_items = self.parser.parse(raw_data)
            self.stats['total_items'] += len(parsed_items)

            # 验证数据
            valid_items = []
            for item in parsed_items:
                if self.parser.validate(item):
                    valid_items.append(item)
                    self.stats['valid_items'] += 1

            return {
                'task_id': task_id,
                'task_config': task_config,
                'url': url,
                'success': True,
                'total_items': len(parsed_items),
                'valid_items': len(valid_items),
                'data': valid_items,
                'timestamp': time.time()
            }

        except Exception as e:
            self.stats['failed_requests'] += 1
            return {
                'task_id': task_id,
                'task_config': task_config,
                'url': url,
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }

    async def crawl_multiple_tasks(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """
        并发爬取多个任务
        
        Args:
            task_ids: 任务ID列表
            
        Returns:
            爬取结果列表
        """
        tasks = [self.crawl_task(task_id) for task_id in task_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'task_id': task_ids[i],
                    'success': False,
                    'error': str(result),
                    'timestamp': time.time()
                })
            else:
                processed_results.append(result)

        return processed_results

    def get_stats(self) -> Dict[str, int]:
        """获取爬取统计信息"""
        return self.stats.copy()

    async def close(self):
        """关闭爬虫连接"""
        await self.client.close()
