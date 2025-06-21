"""
爬虫模块 - 核心数据抓取功能

提供晋江文学城数据抓取的完整解决方案，包括：
- HTTP客户端管理（重试、速率限制、错误处理）
- 甲子榜数据抓取和解析
- 分类页面数据抓取
- 书籍详情获取
- 数据标准化和清洗

设计原则：
1. 模块化设计：HTTP客户端、数据解析器、爬虫控制器分离
2. 异步支持：使用httpx异步HTTP客户端
3. 错误处理：完整的重试机制和异常处理
4. 速率限制：尊重目标网站的访问频率
5. 数据标准化：统一的数据格式和清洗逻辑
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin

import httpx
from app.config import get_settings
from app.modules.models import Book, BookSnapshot, Ranking, RankingSnapshot

# 配置日志
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


class DataParser:
    """
    数据解析器
    
    负责将API响应数据转换为标准化的模型对象：
    - 甲子榜数据解析
    - 分类页面数据解析
    - 书籍信息标准化
    - 数据清洗和验证
    """
    
    @staticmethod
    def parse_jiazi_data(raw_data: Dict[str, Any]) -> Tuple[List[Book], List[BookSnapshot]]:
        """
        解析甲子榜数据
        
        Args:
            raw_data: API原始响应数据
            
        Returns:
            (books, book_snapshots): 书籍信息和快照数据
        """
        books = []
        snapshots = []
        
        try:
            # 检查响应结构
            if raw_data.get('code') != '200':
                raise ValueError(f"API响应错误: {raw_data.get('message', '未知错误')}")
            
            book_list = raw_data.get('data', {}).get('list', [])
            current_time = datetime.now()
            
            for item in book_list:
                # 解析书籍基本信息
                book = DataParser._parse_book_info(item)
                books.append(book)
                
                # 解析书籍快照数据
                snapshot = DataParser._parse_book_snapshot(item, current_time)
                snapshots.append(snapshot)
                
        except Exception as e:
            logger.error(f"甲子榜数据解析失败: {e}")
            raise
        
        logger.info(f"甲子榜数据解析完成: {len(books)} 本书籍")
        return books, snapshots
    
    @staticmethod
    def parse_page_data(raw_data: Dict[str, Any]) -> Tuple[List[Book], List[BookSnapshot]]:
        """
        解析分类页面数据
        
        Args:
            raw_data: API原始响应数据
            
        Returns:
            (books, book_snapshots): 书籍信息和快照数据
        """
        books = []
        snapshots = []
        
        try:
            # 检查响应结构
            if raw_data.get('code') != '200':
                raise ValueError(f"API响应错误: {raw_data.get('message', '未知错误')}")
            
            # 分类页面可能有多个区块
            data_section = raw_data.get('data', {})
            current_time = datetime.now()
            
            # 处理不同的数据结构
            if 'list' in data_section:
                # 单一列表结构
                book_list = data_section['list']
            elif 'blocks' in data_section:
                # 多区块结构
                book_list = []
                for block in data_section['blocks']:
                    if 'list' in block:
                        book_list.extend(block['list'])
            else:
                logger.warning("未识别的页面数据结构")
                return books, snapshots
            
            for item in book_list:
                # 解析书籍基本信息
                book = DataParser._parse_book_info(item)
                books.append(book)
                
                # 解析书籍快照数据
                snapshot = DataParser._parse_book_snapshot(item, current_time)
                snapshots.append(snapshot)
                
        except Exception as e:
            logger.error(f"分类页面数据解析失败: {e}")
            raise
        
        logger.info(f"分类页面数据解析完成: {len(books)} 本书籍")
        return books, snapshots
    
    @staticmethod
    def _parse_book_info(item: Dict[str, Any]) -> Book:
        """
        解析单本书籍的基本信息
        
        Args:
            item: 书籍数据项
            
        Returns:
            Book: 标准化的书籍模型
        """
        # 处理字段名的多种变体（API返回可能不一致）
        book_id = str(item.get('novelId') or item.get('novelid', ''))
        title = item.get('novelName') or item.get('novelname', '')
        author_id = str(item.get('authorId') or item.get('authorid', ''))
        author_name = item.get('authorName') or item.get('authorname', '')
        novel_class = item.get('novelClass') or item.get('novelclass', '')
        tags = item.get('tags', '')
        
        # 数据清洗
        if not book_id or not title:
            raise ValueError(f"书籍数据不完整: ID={book_id}, Title={title}")
        
        return Book(
            book_id=book_id,
            title=title.strip(),
            author_id=author_id,
            author_name=author_name.strip() if author_name else '',
            novel_class=novel_class.strip() if novel_class else '',
            tags=tags.strip() if tags else '',
            first_seen=datetime.now(),
            last_updated=datetime.now()
        )
    
    @staticmethod
    def _parse_book_snapshot(item: Dict[str, Any], snapshot_time: datetime) -> BookSnapshot:
        """
        解析书籍快照数据
        
        Args:
            item: 书籍数据项
            snapshot_time: 快照时间
            
        Returns:
            BookSnapshot: 书籍快照模型
        """
        book_id = str(item.get('novelId') or item.get('novelid', ''))
        
        # 解析统计数据（可能为字符串格式，需要转换）
        total_clicks = DataParser._parse_numeric_field(item, ['totalClicks', 'totalclicks'], 0)
        total_favorites = DataParser._parse_numeric_field(item, ['totalFavorites', 'totalfavorites'], 0)
        comment_count = DataParser._parse_numeric_field(item, ['commentCount', 'commentcount'], 0)
        chapter_count = DataParser._parse_numeric_field(item, ['chapterCount', 'chaptercount'], 0)
        
        return BookSnapshot(
            book_id=book_id,
            total_clicks=total_clicks,
            total_favorites=total_favorites,
            comment_count=comment_count,
            chapter_count=chapter_count,
            snapshot_time=snapshot_time
        )
    
    @staticmethod
    def _parse_numeric_field(item: Dict[str, Any], field_names: List[str], default: int = 0) -> int:
        """
        解析数值字段（处理字符串格式的数字）
        
        Args:
            item: 数据项
            field_names: 可能的字段名列表
            default: 默认值
            
        Returns:
            解析后的数值
        """
        for field_name in field_names:
            value = item.get(field_name)
            if value is not None:
                try:
                    # 处理字符串格式的数字（如 "1.2万" -> 12000）
                    if isinstance(value, str):
                        value = value.replace(',', '').replace('万', '0000').replace('千', '000')
                        # 处理小数点形式的万（如 "1.2万" -> "12000"）
                        if '.' in value and value.endswith('0000'):
                            parts = value[:-4].split('.')
                            if len(parts) == 2:
                                value = parts[0] + parts[1] + '000'
                    
                    return int(float(value))
                except (ValueError, TypeError):
                    continue
        
        return default


class CrawlerController:
    """
    爬虫控制器
    
    协调HTTP客户端和数据解析器，提供高级爬虫功能：
    - 甲子榜数据抓取
    - 分类页面数据抓取
    - 书籍详情获取
    - 批量抓取管理
    """
    
    def __init__(self):
        """初始化爬虫控制器"""
        self.settings = get_settings()
        self.http_client = HTTPClient(
            timeout=30,
            max_retries=3,
            retry_delay=1.0,
            rate_limit_delay=1.0  # 1秒间隔，尊重网站
        )
        self.data_parser = DataParser()
        self._load_url_config()
    
    def _load_url_config(self):
        """加载URL配置"""
        try:
            import os
            config_path = os.path.join(os.getcwd(), 'data', 'urls.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                self.url_config = json.load(f)
                logger.info("URL配置加载成功")
        except Exception as e:
            logger.error(f"URL配置加载失败: {e}")
            raise
    
    async def crawl_jiazi_ranking(self) -> Tuple[List[Book], List[BookSnapshot]]:
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
            books, snapshots = self.data_parser.parse_jiazi_data(raw_data)
            
            logger.info(f"甲子榜抓取完成: {len(books)} 本书籍")
            return books, snapshots
            
        except Exception as e:
            logger.error(f"甲子榜抓取失败: {e}")
            raise
    
    async def crawl_page_ranking(self, channel: str) -> Tuple[List[Book], List[BookSnapshot]]:
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
            base_url = self.url_config['base_url']
            version = self.url_config['version']
            url = base_url.format(channel, version)
            
            # 发送请求
            raw_data = await self.http_client.get(url)
            
            # 解析数据
            books, snapshots = self.data_parser.parse_page_data(raw_data)
            
            logger.info(f"分类页面抓取完成 ({channel}): {len(books)} 本书籍")
            return books, snapshots
            
        except Exception as e:
            logger.error(f"分类页面抓取失败 ({channel}): {e}")
            raise
    
    async def crawl_book_detail(self, book_id: str) -> Optional[Dict[str, Any]]:
        """
        抓取单本书籍详细信息
        
        Args:
            book_id: 书籍ID
            
        Returns:
            书籍详细信息字典
        """
        logger.info(f"开始抓取书籍详情: {book_id}")
        
        try:
            # 构建书籍详情URL
            novel_url_template = self.url_config['novel_url']
            url = novel_url_template.format(book_id)
            
            # 发送请求
            raw_data = await self.http_client.get(url)
            
            # 检查响应
            if raw_data.get('code') != '200':
                logger.warning(f"书籍详情获取失败: {book_id} - {raw_data.get('message')}")
                return None
            
            logger.debug(f"书籍详情抓取完成: {book_id}")
            return raw_data.get('data')
            
        except Exception as e:
            logger.error(f"书籍详情抓取失败 ({book_id}): {e}")
            return None
    
    async def get_available_channels(self) -> List[Dict[str, str]]:
        """
        获取可用的抓取频道列表
        
        Returns:
            频道信息列表
        """
        channels = []
        
        try:
            # 添加甲子榜
            jiazi_config = self.url_config['content']['jiazi']
            channels.append({
                'short_name': jiazi_config['short_name'],
                'zh_name': jiazi_config['zh_name'],
                'type': jiazi_config['type'],
                'frequency': jiazi_config['frequency']
            })
            
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
            # 返回基本的甲子榜频道
            channels = [{
                'short_name': 'jiazi',
                'zh_name': '甲子榜',
                'type': 'hourly',
                'frequency': 'hourly'
            }]
        
        return channels
    
    async def close(self):
        """关闭爬虫资源"""
        await self.http_client.close()
        logger.info("爬虫控制器已关闭")


# 便捷函数
async def create_crawler() -> CrawlerController:
    """
    创建爬虫控制器实例
    
    Returns:
        CrawlerController: 爬虫控制器实例
    """
    return CrawlerController()


async def crawl_jiazi() -> Tuple[List[Book], List[BookSnapshot]]:
    """
    便捷函数：抓取甲子榜数据
    
    Returns:
        (books, book_snapshots): 书籍信息和快照数据
    """
    crawler = await create_crawler()
    try:
        return await crawler.crawl_jiazi_ranking()
    finally:
        await crawler.close()


async def crawl_page(channel: str) -> Tuple[List[Book], List[BookSnapshot]]:
    """
    便捷函数：抓取分类页面数据
    
    Args:
        channel: 分类频道标识
        
    Returns:
        (books, book_snapshots): 书籍信息和快照数据
    """
    crawler = await create_crawler()
    try:
        return await crawler.crawl_page_ranking(channel)
    finally:
        await crawler.close()