"""
甲子榜爬虫模块

专门负责晋江文学城甲子榜的数据抓取：
- 甲子榜数据抓取
- URL配置管理
- 数据验证和处理
"""

import json
import logging
import os
from typing import List, Tuple, Dict, Any

from app.utils.http_client import HTTPClient
from .parser import DataParser
from app.modules.models import Book, BookSnapshot

logger = logging.getLogger(__name__)


class JiaziCrawler:
    """
    甲子榜爬虫
    
    专门处理甲子榜数据抓取：
    - 配置管理
    - 数据抓取
    - 结果验证
    """
    
    def __init__(self, http_client: HTTPClient = None):
        """
        初始化甲子榜爬虫
        
        Args:
            http_client: HTTP客户端实例，如果未提供则创建新实例
        """
        self.http_client = http_client or HTTPClient(
            timeout=30,
            max_retries=3,
            retry_delay=1.0,
            rate_limit_delay=1.0
        )
        self.parser = DataParser()
        self.url_config = self._load_url_config()
    
    def _load_url_config(self) -> Dict[str, Any]:
        """
        加载URL配置
        
        Returns:
            URL配置字典
        """
        try:
            config_path = os.path.join(os.getcwd(), 'data', 'urls.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.debug("甲子榜URL配置加载成功")
                return config
        except Exception as e:
            logger.error(f"甲子榜URL配置加载失败: {e}")
            raise
    
    async def crawl(self) -> Tuple[List[Book], List[BookSnapshot]]:
        """
        抓取甲子榜数据
        
        Returns:
            (books, book_snapshots): 书籍信息和快照数据
        """
        logger.info("开始抓取甲子榜数据")
        
        try:
            # 获取甲子榜URL
            jiazi_config = self.url_config['content']['jiazi']
            url = jiazi_config['url']
            
            # 发送请求
            raw_data = await self.http_client.get(url)
            
            # 解析数据
            books, snapshots = self.parser.parse_jiazi_data(raw_data)
            
            # 验证结果
            if not books or not snapshots:
                logger.warning("甲子榜抓取结果为空")
                return [], []
            
            if len(books) != len(snapshots):
                logger.warning(f"数据不一致: 书籍 {len(books)} 本, 快照 {len(snapshots)} 条")
            
            logger.info(f"甲子榜抓取完成: {len(books)} 本书籍")
            return books, snapshots
            
        except Exception as e:
            logger.error(f"甲子榜抓取失败: {e}")
            raise
    
    async def get_config_info(self) -> Dict[str, Any]:
        """
        获取甲子榜配置信息
        
        Returns:
            配置信息字典
        """
        try:
            jiazi_config = self.url_config['content']['jiazi']
            return {
                'short_name': jiazi_config['short_name'],
                'zh_name': jiazi_config['zh_name'],
                'type': jiazi_config['type'],
                'frequency': jiazi_config['frequency'],
                'url': jiazi_config['url']
            }
        except Exception as e:
            logger.error(f"获取甲子榜配置失败: {e}")
            return {
                'short_name': 'jiazi',
                'zh_name': '甲子榜',
                'type': 'hourly',
                'frequency': 'hourly',
                'url': ''
            }
    
    async def close(self):
        """关闭爬虫资源"""
        if self.http_client:
            await self.http_client.close()
        logger.debug("甲子榜爬虫已关闭")