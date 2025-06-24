"""
分类页面爬虫模块

负责抓取晋江文学城各分类页面的榜单数据：
- 分类页面数据抓取
- 多种页面结构支持
- 频道配置管理
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Tuple, Dict, Any

from app.utils.http_client import HTTPClient
from .parser import DataParser
from app.modules.models import Book, BookSnapshot

logger = logging.getLogger(__name__)


class PageCrawler:
    """
    分类页面爬虫
    
    处理各种分类页面的数据抓取：
    - 言情、纯爱、衍生等分类
    - 动态URL构建
    - 多种数据结构支持
    """
    
    def __init__(self, http_client: HTTPClient = None):
        """
        初始化分类页面爬虫
        
        Args:
            http_client: HTTP客户端实例，如果未提供则创建新实例
        """
        self.http_client = http_client or HTTPClient(
            timeout=30,
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
                logger.debug("分类页面URL配置加载成功")
                return config
        except Exception as e:
            logger.error(f"分类页面URL配置加载失败: {e}")
            raise
    
    async def crawl(self, channel: str) -> Tuple[List[Book], List[BookSnapshot]]:
        """
        抓取指定分类页面数据
        
        Args:
            channel: 分类频道标识
            
        Returns:
            (books, book_snapshots): 书籍信息和快照数据
        """
        logger.info(f"开始抓取分类页面数据: {channel}")
        
        try:
            # 构建URL
            url = self._build_url(channel)
            if not url:
                raise ValueError(f"无法构建频道URL: {channel}")
            
            # 发送请求
            response = await self.http_client.get(url)
            
            # 检查响应状态
            response.raise_for_status()
            
            # 提取JSON数据
            raw_data = response.json()
            
            # 解析数据
            try:
                books, snapshots = self.parser.parse_page_data(raw_data)
            except Exception as parse_error:
                # 解析失败，但爬取成功，抛出特定异常
                from app.utils.failure_storage import get_failure_storage
                task_id = f"page_{channel}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                get_failure_storage().store_parse_failure(
                    task_id=task_id,
                    task_type="page",
                    error_message=f"分类页面数据解析失败: {str(parse_error)}",
                    raw_data=raw_data,
                    url=url,
                    channel=channel
                )
                logger.error(f"分类页面数据解析失败，原始数据已保存: {parse_error}")
                raise parse_error
            
            # 验证结果
            if not books or not snapshots:
                logger.warning(f"分类页面抓取结果为空: {channel}")
                return [], []
            
            if len(books) != len(snapshots):
                logger.warning(f"数据不一致 ({channel}): 书籍 {len(books)} 本, 快照 {len(snapshots)} 条")
            
            logger.info(f"分类页面抓取完成 ({channel}): {len(books)} 本书籍")
            return books, snapshots
            
        except Exception as e:
            logger.error(f"分类页面抓取失败 ({channel}): {e}")
            raise
    
    def _build_url(self, channel: str) -> str:
        """
        根据频道构建URL
        
        Args:
            channel: 频道标识
            
        Returns:
            构建的URL
        """
        try:
            base_url = self.url_config['base_url']
            version = self.url_config['version']
            
            # 使用模板构建URL
            url = base_url.format(channel, version)
            logger.debug(f"构建URL成功: {channel} -> {url}")
            return url
            
        except Exception as e:
            logger.error(f"构建URL失败: {channel} - {e}")
            return ""
    
    async def get_available_channels(self) -> List[Dict[str, str]]:
        """
        获取可用的抓取频道列表
        
        Returns:
            频道信息列表
        """
        channels = []
        
        try:
            # 添加分类页面
            pages_config = self.url_config['content']['pages']
            for page_key, page_info in pages_config.items():
                if isinstance(page_info, dict):  # 确保是字典类型
                    channels.append({
                        'short_name': page_info['short_name'],
                        'zh_name': page_info['zh_name'],
                        'type': page_info.get('type', 'daily'),
                        'frequency': page_info['frequency']
                    })
                    
                    # 添加子页面
                    if 'sub_pages' in page_info:
                        for sub_key, sub_info in page_info['sub_pages'].items():
                            if isinstance(sub_info, dict):  # 确保是字典类型
                                channels.append({
                                    'short_name': f"{page_info['short_name']}.{sub_info['short_name']}",
                                    'zh_name': f"{page_info['zh_name']} - {sub_info['zh_name']}",
                                    'type': sub_info.get('type', 'daily'),
                                    'frequency': sub_info['frequency']
                                })
            
        except Exception as e:
            logger.error(f"解析频道配置失败: {e}")
            # 返回基本的频道列表
            channels = [{
                'short_name': 'yq',
                'zh_name': '言情',
                'type': 'daily',
                'frequency': 'daily'
            }]
        
        return channels
    
    async def close(self):
        """关闭爬虫资源"""
        if self.http_client:
            await self.http_client.close()
        logger.debug("分类页面爬虫已关闭")