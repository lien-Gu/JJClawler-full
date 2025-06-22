"""
爬虫基础模块

提供爬虫相关的基础功能和配置：
- 爬虫配置管理
- 数据验证
- 公共工具函数

注意：HTTP客户端功能已迁移至 app.utils.http_client.HTTPClient
"""

from typing import Dict, Optional, Any

from app.utils.file_utils import read_json_file
from app.utils.log_utils import get_logger
from app.config import get_settings

logger = get_logger(__name__)


def get_crawler_config() -> Dict[str, Any]:
    """
    获取爬虫配置
    
    Returns:
        Dict[str, Any]: 爬虫配置字典
    """
    settings = get_settings()
    config = read_json_file(settings.URLS_CONFIG_FILE, default={})
    
    if not config:
        logger.warning("爬虫配置文件为空或不存在")
    
    return config


def validate_crawl_result(data: Any) -> bool:
    """
    验证爬取结果的基本格式
    
    Args:
        data: 爬取到的数据
        
    Returns:
        bool: 数据是否有效
    """
    if not data:
        return False
    
    # 基本的数据格式验证
    if isinstance(data, dict):
        # 检查是否有必要的字段
        required_fields = ['code', 'data']
        return all(field in data for field in required_fields)
    
    return False


def get_default_headers() -> Dict[str, str]:
    """
    获取默认的HTTP请求头
    
    Returns:
        Dict[str, str]: 默认请求头
    """
    return {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
                     "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }


def extract_book_id_from_url(url: str) -> Optional[str]:
    """
    从URL中提取书籍ID
    
    Args:
        url: 书籍URL
        
    Returns:
        Optional[str]: 书籍ID，失败时返回None
    """
    import re
    
    # 常见的书籍ID模式
    patterns = [
        r'/(\d+)/?$',           # 末尾的数字ID
        r'bookid=(\d+)',        # bookid参数
        r'novelid=(\d+)',       # novelid参数
        r'/book/(\d+)',         # /book/数字 格式
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def build_ranking_url(base_url: str, channel: str, **params) -> str:
    """
    构建榜单URL
    
    Args:
        base_url: 基础URL
        channel: 频道标识
        **params: 其他参数
        
    Returns:
        str: 构建好的URL
    """
    from urllib.parse import urlencode
    
    # 添加频道参数
    if 'channel' not in params:
        params['channel'] = channel
    
    # 构建查询字符串
    if params:
        query_string = urlencode(params)
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}{query_string}"
    
    return base_url


class CrawlerStats:
    """
    爬虫统计信息管理
    """
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置统计信息"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.books_crawled = 0
        self.errors = []
    
    def add_request(self, success: bool = True):
        """添加请求记录"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def add_books(self, count: int):
        """添加爬取的书籍数量"""
        self.books_crawled += count
    
    def add_error(self, error: str):
        """添加错误记录"""
        self.errors.append(error)
        if len(self.errors) > 100:  # 限制错误记录数量
            self.errors = self.errors[-100:]
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{self.get_success_rate():.2%}",
            "books_crawled": self.books_crawled,
            "error_count": len(self.errors),
            "recent_errors": self.errors[-5:] if self.errors else []
        }