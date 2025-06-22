"""
HTTP客户端工具

提供统一的HTTP请求封装，包括重试机制、错误处理和请求限流
"""
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx
from httpx import Response, RequestError, HTTPStatusError
from app.utils.log_utils import get_logger
from app.config import get_settings

logger = get_logger(__name__)


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: Optional[int] = None
    base_delay: float = 1.0  # 基础延迟（秒）
    max_delay: float = 60.0  # 最大延迟（秒）
    backoff_factor: float = 2.0  # 退避因子
    retry_status_codes: List[int] = None  # 需要重试的状态码
    
    def __post_init__(self):
        if self.max_retries is None:
            settings = get_settings()
            self.max_retries = settings.MAX_RETRIES
        if self.retry_status_codes is None:
            self.retry_status_codes = [429, 502, 503, 504]


class HTTPClient:
    """
    HTTP客户端封装
    
    提供以下功能：
    - 自动重试机制
    - 请求限流
    - 统一错误处理
    - 请求统计
    """
    
    def __init__(
        self,
        timeout: Optional[float] = None,
        rate_limit_delay: Optional[float] = None,
        retry_config: Optional[RetryConfig] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        初始化HTTP客户端
        
        Args:
            timeout: 请求超时时间（秒）
            rate_limit_delay: 请求间隔限制（秒）
            retry_config: 重试配置
            headers: 默认请求头
        """
        settings = get_settings()
        self.timeout = timeout if timeout is not None else settings.REQUEST_TIMEOUT
        self.rate_limit_delay = rate_limit_delay if rate_limit_delay is not None else settings.CRAWL_DELAY
        self.retry_config = retry_config or RetryConfig()
        
        # 默认请求头
        default_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
                         "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        }
        if headers:
            default_headers.update(headers)
        
        # 创建httpx客户端
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers=default_headers,
            follow_redirects=True
        )
        
        # 请求统计
        self.stats = {
            "total_requests": 0,
            "success_requests": 0,
            "failed_requests": 0,
            "retry_requests": 0,
            "last_request_time": None
        }
        
        # 用于请求限流
        self._last_request_time: Optional[datetime] = None
    
    async def get(
        self, 
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Response:
        """发送GET请求"""
        return await self._request("GET", url, params=params, headers=headers, **kwargs)
    
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Response:
        """发送POST请求"""
        return await self._request("POST", url, data=data, json=json, headers=headers, **kwargs)
    
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Response:
        """
        执行HTTP请求（带重试机制）
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            Response: HTTP响应对象
            
        Raises:
            HTTPStatusError: HTTP状态错误
            RequestError: 请求错误
        """
        # 请求限流
        await self._rate_limit()
        
        self.stats["total_requests"] += 1
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                logger.debug(f"请求 {method} {url} (尝试 {attempt + 1})")
                
                response = await self.client.request(method, url, **kwargs)
                
                # 检查状态码
                if response.status_code in self.retry_config.retry_status_codes:
                    raise HTTPStatusError(
                        f"HTTP {response.status_code}", 
                        request=response.request, 
                        response=response
                    )
                
                # 请求成功
                self.stats["success_requests"] += 1
                self.stats["last_request_time"] = datetime.now().isoformat()
                
                logger.debug(f"请求成功: {method} {url} -> {response.status_code}")
                return response
                
            except (RequestError, HTTPStatusError) as e:
                last_exception = e
                
                # 如果是最后一次尝试，直接抛出异常
                if attempt == self.retry_config.max_retries:
                    break
                
                # 计算重试延迟
                delay = min(
                    self.retry_config.base_delay * (self.retry_config.backoff_factor ** attempt),
                    self.retry_config.max_delay
                )
                
                logger.warning(f"请求失败，{delay}秒后重试: {e}")
                self.stats["retry_requests"] += 1
                
                await asyncio.sleep(delay)
        
        # 所有重试都失败了
        self.stats["failed_requests"] += 1
        logger.error(f"请求最终失败: {method} {url}")
        raise last_exception
    
    async def _rate_limit(self):
        """实施请求限流"""
        if self._last_request_time is not None:
            elapsed = datetime.now() - self._last_request_time
            delay_needed = self.rate_limit_delay - elapsed.total_seconds()
            
            if delay_needed > 0:
                logger.debug(f"请求限流: 等待 {delay_needed:.2f} 秒")
                await asyncio.sleep(delay_needed)
        
        self._last_request_time = datetime.now()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取请求统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "success_requests": 0,
            "failed_requests": 0,
            "retry_requests": 0,
            "last_request_time": None
        }
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
        logger.debug("HTTP客户端已关闭")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 便捷函数
async def create_http_client(
    timeout: float = 30.0,
    rate_limit_delay: float = 1.0,
    max_retries: int = 3
) -> HTTPClient:
    """
    创建HTTP客户端的便捷函数
    
    Args:
        timeout: 请求超时时间
        rate_limit_delay: 请求间隔
        max_retries: 最大重试次数
        
    Returns:
        HTTPClient: 配置好的HTTP客户端
    """
    retry_config = RetryConfig(max_retries=max_retries)
    return HTTPClient(
        timeout=timeout,
        rate_limit_delay=rate_limit_delay,
        retry_config=retry_config
    )