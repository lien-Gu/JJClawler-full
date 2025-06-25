"""
夹子榜爬虫模块

专门负责晋江文学城夹子榜的数据抓取：
- 夹子榜数据抓取
- URL配置管理
- 数据验证和处理
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Tuple, Dict, Any

from app.utils.http_client import HTTPClient
from .parser import DataParser
from .book_detail_crawler import BookDetailCrawler
from app.modules.models import Book, BookSnapshot

logger = logging.getLogger(__name__)


class JiaziCrawler:
    """
    夹子榜爬虫
    
    专门处理夹子榜数据抓取：
    - 配置管理
    - 数据抓取
    - 结果验证
    """
    
    def __init__(self, http_client: HTTPClient = None):
        """
        初始化夹子榜爬虫
        
        Args:
            http_client: HTTP客户端实例，如果未提供则创建新实例
        """
        self.http_client = http_client or HTTPClient(
            timeout=30,
            rate_limit_delay=1.0
        )
        self.parser = DataParser()
        self.book_detail_crawler = BookDetailCrawler(self.http_client)
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
                logger.debug("夹子榜URL配置加载成功")
                return config
        except Exception as e:
            logger.error(f"夹子榜URL配置加载失败: {e}")
            raise
    
    async def crawl(self) -> Tuple[List[Book], List[BookSnapshot]]:
        """
        抓取夹子榜数据
        
        Returns:
            (books, book_snapshots): 书籍信息和快照数据
        """
        logger.info("开始抓取夹子榜数据")
        
        try:
            # 获取夹子榜URL
            jiazi_config = self.url_config['content']['jiazi']
            url = jiazi_config['url']
            
            # 发送请求
            response = await self.http_client.get(url)
            
            # 检查响应状态
            response.raise_for_status()
            
            # 提取JSON数据
            raw_data = response.json()
            
            # 解析基础数据
            try:
                books, base_snapshots = self.parser.parse_jiazi_data(raw_data)
            except Exception as parse_error:
                # 解析失败，但爬取成功，抛出特定异常
                from app.utils.failure_storage import get_failure_storage
                task_id = f"jiazi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                get_failure_storage().store_parse_failure(
                    task_id=task_id,
                    task_type="jiazi",
                    error_message=f"夹子榜数据解析失败: {str(parse_error)}",
                    raw_data=raw_data,
                    url=url
                )
                logger.error(f"夹子榜数据解析失败，原始数据已保存: {parse_error}")
                raise parse_error
            
            # 获取书籍详情数据（包含统计信息）
            book_ids = [book.book_id for book in books]
            current_time = datetime.now()
            
            logger.info(f"开始获取 {len(book_ids)} 本书籍的详细统计数据...")
            detailed_snapshots = await self.book_detail_crawler.fetch_book_details(book_ids, current_time)
            
            # 如果详情获取失败，使用基础快照（虽然统计数据为0）
            snapshots = detailed_snapshots if detailed_snapshots else base_snapshots
            
            # 验证结果
            if not books or not snapshots:
                logger.warning("夹子榜抓取结果为空")
                return [], []
            
            if len(books) != len(snapshots):
                logger.warning(f"数据不一致: 书籍 {len(books)} 本, 快照 {len(snapshots)} 条")
            
            logger.info(f"夹子榜抓取完成: {len(books)} 本书籍")
            return books, snapshots
            
        except Exception as e:
            logger.error(f"夹子榜抓取失败: {e}")
            raise
    
    async def get_config_info(self) -> Dict[str, Any]:
        """
        获取夹子榜配置信息
        
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
            logger.error(f"获取夹子榜配置失败: {e}")
            return {
                'short_name': 'jiazi',
                'zh_name': '夹子榜',
                'type': 'hourly',
                'frequency': 'hourly',
                'url': ''
            }
    
    async def close(self):
        """关闭爬虫资源"""
        if self.book_detail_crawler:
            await self.book_detail_crawler.close()
        if self.http_client:
            await self.http_client.close()
        logger.debug("夹子榜爬虫已关闭")