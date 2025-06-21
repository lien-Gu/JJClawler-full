"""
HTTP客户端基础模块

提供统一的HTTP请求管理：
- 连接池管理
- 重试机制
- 速率限制
- 错误处理和日志记录
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Any

import httpx

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    HTTP客户端管理器
    
    负责处理所有HTTP请求，包括：
    - 连接管理和配置
    - 重试机制
    - 速率限制
    - 错误处理和日志记录
    """
    
    def __init__(self, 
                 timeout: int = 30,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 rate_limit_delay: float = 1.0):
        """
        初始化HTTP客户端
        
        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
            rate_limit_delay: 请求间隔（秒）
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0.0
        
        # 配置HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 JJNovel/5.8.3',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            },
            follow_redirects=True
        )
    
    async def get(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发送GET请求并返回JSON数据
        
        Args:
            url: 请求URL
            params: 查询参数
            
        Returns:
            解析后的JSON数据
            
        Raises:
            httpx.HTTPError: HTTP请求异常
            json.JSONDecodeError: JSON解析异常
        """
        # 实施速率限制
        await self._apply_rate_limit()
        
        # 执行重试逻辑
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"正在请求 {url} (尝试 {attempt + 1}/{self.max_retries + 1})")
                
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                
                # 记录请求成功
                self.last_request_time = time.time()
                
                # 解析JSON响应
                json_data = response.json()
                logger.debug(f"请求成功: {url}")
                
                return json_data
                
            except httpx.HTTPError as e:
                logger.warning(f"HTTP请求失败 (尝试 {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                else:
                    logger.error(f"HTTP请求最终失败: {url}")
                    raise
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                raise
    
    async def _apply_rate_limit(self):
        """应用速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug(f"速率限制: 等待 {sleep_time:.2f} 秒")
            await asyncio.sleep(sleep_time)
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()