"""
爬虫模块 - 晋江文学城数据抓取

本模块提供完整的数据抓取解决方案，采用模块化设计：
- jiazi_crawler: 夹子榜专用爬虫
- page_crawler: 分类页面爬虫  
- crawler_manager: 统一爬虫管理器
- parser: 数据解析和清洗（已废弃，解析逻辑整合到各爬虫中）

HTTP客户端统一使用 app.utils.http_client.HTTPClient

设计原则：
1. 单一职责：每个模块负责特定功能
2. 高效简洁：优化性能，减少资源消耗
3. 易于维护：清晰的模块边界和接口
4. 可扩展性：支持新增爬虫类型
"""

from .jiazi_crawler import JiaziCrawler
from .page_crawler import PageCrawler
from .crawler_manager import CrawlerManager, get_crawler_manager

__all__ = [
    'JiaziCrawler',
    'PageCrawler', 
    'CrawlerManager',
    'get_crawler_manager'
]