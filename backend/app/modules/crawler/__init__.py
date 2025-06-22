"""
爬虫模块 - 晋江文学城数据抓取

本模块提供完整的数据抓取解决方案，采用模块化设计：
- parser: 数据解析和清洗
- jiazi_crawler: 甲子榜专用爬虫
- page_crawler: 分类页面爬虫

HTTP客户端现在统一使用 app.utils.http_client.HTTPClient

设计原则：
1. 单一职责：每个模块负责特定功能
2. 高效简洁：优化性能，减少资源消耗
3. 易于维护：清晰的模块边界和接口
4. 可扩展性：支持新增爬虫类型
"""

from app.utils.http_client import HTTPClient
from .parser import DataParser
from .jiazi_crawler import JiaziCrawler
from .page_crawler import PageCrawler

__all__ = [
    'HTTPClient',
    'DataParser', 
    'JiaziCrawler',
    'PageCrawler'
]