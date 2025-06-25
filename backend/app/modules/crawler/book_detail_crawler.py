"""
书籍详情爬虫模块

专门负责获取书籍的详细统计信息：
- 点击量、收藏量、评论数等统计数据
- 章节数、字数等基本信息
- 支持批量获取多本书籍详情
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from urllib.parse import quote

from app.utils.http_client import HTTPClient
from app.modules.models import BookSnapshot

logger = logging.getLogger(__name__)


class BookDetailResult(NamedTuple):
    """书籍详情获取结果"""
    snapshot: BookSnapshot
    vip_chapter_count: int


class BookDetailCrawler:
    """
    书籍详情爬虫
    
    专门获取书籍的详细统计信息，包括：
    - 点击量 (novelScore)
    - 收藏量 (novelbefavoritedcount)
    - 评论数 (comment_count)
    - 章节数 (novelChapterCount)
    - 字数 (novelSize)
    """
    
    def __init__(self, http_client: HTTPClient = None):
        """
        初始化书籍详情爬虫
        
        Args:
            http_client: HTTP客户端实例，如果未提供则创建新实例
        """
        self.http_client = http_client or HTTPClient(
            timeout=30,
            rate_limit_delay=1.0
        )
        # 书籍详情API URL模板
        self.novel_api_url = "https://app-cdn.jjwxc.com/androidapi/novelbasicinfo?novelId={}"
    
    async def fetch_book_details(self, book_ids: List[str], snapshot_time: datetime = None) -> List[BookDetailResult]:
        """
        批量获取书籍详情并创建快照
        
        Args:
            book_ids: 书籍ID列表
            snapshot_time: 快照时间，默认为当前时间
            
        Returns:
            List[BookDetailResult]: 书籍详情结果列表（包含快照和VIP章节数）
        """
        if snapshot_time is None:
            snapshot_time = datetime.now()
        
        logger.info(f"开始获取 {len(book_ids)} 本书籍的详情信息")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for i, book_id in enumerate(book_ids):
            try:
                # 获取单本书籍详情
                result = await self._fetch_single_book_detail(book_id, snapshot_time)
                if result:
                    results.append(result)
                    successful_count += 1
                else:
                    failed_count += 1
                    
                # 进度日志
                if (i + 1) % 10 == 0:
                    logger.info(f"详情获取进度: {i + 1}/{len(book_ids)}, 成功: {successful_count}, 失败: {failed_count}")
                
                # 避免请求过于频繁，每个请求间隔1秒
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"获取书籍 {book_id} 详情失败: {e}")
                failed_count += 1
                continue
        
        logger.info(f"书籍详情获取完成: 成功 {successful_count} 本, 失败 {failed_count} 本")
        return results
    
    async def _fetch_single_book_detail(self, book_id: str, snapshot_time: datetime) -> Optional[BookDetailResult]:
        """
        获取单本书籍的详情信息
        
        Args:
            book_id: 书籍ID
            snapshot_time: 快照时间
            
        Returns:
            BookDetailResult: 书籍详情结果，如果获取失败返回None
        """
        try:
            # 构建请求URL
            url = self.novel_api_url.format(quote(book_id))
            
            # 发送请求
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            # 解析响应数据
            data = response.json()
            
            # 提取统计数据
            snapshot, vip_chapter_count = self._parse_book_detail(data, book_id, snapshot_time)
            
            return BookDetailResult(
                snapshot=snapshot,
                vip_chapter_count=vip_chapter_count
            )
            
        except Exception as e:
            logger.error(f"获取书籍 {book_id} 详情失败: {e}")
            return None
    
    def _parse_book_detail(self, data: Dict[str, Any], book_id: str, snapshot_time: datetime) -> Tuple[BookSnapshot, int]:
        """
        解析书籍详情数据
        
        Args:
            data: API响应数据
            book_id: 书籍ID
            snapshot_time: 快照时间
            
        Returns:
            Tuple[BookSnapshot, int]: 书籍快照和VIP章节数
        """
        # 解析非V章点击量 - novip_clicks格式: "247,737(章均)"
        novip_clicks = self._parse_clicks_field(data.get('novip_clicks', '0'))
        
        # 解析收藏量 - novelbefavoritedcount格式: "253062"
        favorites = self._parse_number_field(data.get('novelbefavoritedcount', '0'))
        
        # 解析评论数 - comment_count格式: "137,649"
        comment_count = self._parse_number_field(data.get('comment_count', '0'))
        
        # 解析总章节数 - novelChapterCount格式: "81"
        chapter_count = self._parse_number_field(data.get('novelChapterCount', '0'))
        
        # 解析VIP章节数 - vipChapterid格式: "19" (作为静态属性返回)
        vip_chapter_count = self._parse_number_field(data.get('vipChapterid', '0'))
        
        # 解析字数 - novelSize格式: "502,038"
        word_count = self._parse_number_field(data.get('novelSize', '0'))
        
        # 解析营养液数量 - nutrition_novel格式: "243219"
        nutrition_count = self._parse_number_field(data.get('nutrition_novel', '0'))
        
        logger.debug(f"书籍 {book_id} 详情: 点击{novip_clicks}, 收藏{favorites}, 评论{comment_count}, 总章节{chapter_count}, VIP章节{vip_chapter_count}, 字数{word_count}, 营养液{nutrition_count}")
        
        snapshot = BookSnapshot(
            book_id=book_id,
            novip_clicks=novip_clicks,
            favorites=favorites,
            comment_count=comment_count,
            chapter_count=chapter_count,
            word_count=word_count,
            nutrition_count=nutrition_count,
            snapshot_time=snapshot_time
        )
        
        return snapshot, vip_chapter_count
    
    def _parse_clicks_field(self, clicks_str: str) -> int:
        """
        解析点击量字段（格式: "247,737(章均)"）
        
        Args:
            clicks_str: 点击量字符串
            
        Returns:
            int: 解析后的点击量
        """
        if not clicks_str or clicks_str == '0':
            return 0
        
        try:
            # 移除"(章均)"后缀
            if '(' in clicks_str:
                clicks_str = clicks_str.split('(')[0]
            
            # 去除逗号
            clicks_str = clicks_str.replace(',', '')
            
            # 处理"亿"单位
            if '亿' in clicks_str:
                base_num = float(clicks_str.replace('亿', ''))
                return int(base_num * 100000000)
            
            # 处理"万"单位
            if '万' in clicks_str:
                base_num = float(clicks_str.replace('万', ''))
                return int(base_num * 10000)
            
            # 处理"千"单位
            if '千' in clicks_str:
                base_num = float(clicks_str.replace('千', ''))
                return int(base_num * 1000)
            
            # 直接数字
            return int(float(clicks_str))
            
        except (ValueError, TypeError) as e:
            logger.warning(f"解析点击量失败: {clicks_str}, 错误: {e}")
            return 0
    
    def _parse_score_field(self, score_str: str) -> int:
        """
        解析点击量字段（格式: "4953.9万"）
        
        Args:
            score_str: 点击量字符串
            
        Returns:
            int: 解析后的点击量
        """
        if not score_str or score_str == '0':
            return 0
        
        try:
            # 去除逗号
            score_str = score_str.replace(',', '')
            
            # 处理"亿"单位
            if '亿' in score_str:
                base_num = float(score_str.replace('亿', ''))
                return int(base_num * 100000000)
            
            # 处理"万"单位
            if '万' in score_str:
                base_num = float(score_str.replace('万', ''))
                return int(base_num * 10000)
            
            # 处理"千"单位
            if '千' in score_str:
                base_num = float(score_str.replace('千', ''))
                return int(base_num * 1000)
            
            # 直接数字
            return int(float(score_str))
            
        except (ValueError, TypeError) as e:
            logger.warning(f"解析点击量失败: {score_str}, 错误: {e}")
            return 0
    
    def _parse_number_field(self, number_str: str) -> int:
        """
        解析数字字段（格式: "2,437" 或 "36"）
        
        Args:
            number_str: 数字字符串
            
        Returns:
            int: 解析后的数字
        """
        if not number_str:
            return 0
        
        try:
            # 去除逗号和空格
            clean_str = str(number_str).replace(',', '').replace(' ', '')
            
            # 处理"亿"单位
            if '亿' in clean_str:
                base_num = float(clean_str.replace('亿', ''))
                return int(base_num * 100000000)
            
            # 处理"万"单位
            if '万' in clean_str:
                base_num = float(clean_str.replace('万', ''))
                return int(base_num * 10000)
            
            # 处理"千"单位
            if '千' in clean_str:
                base_num = float(clean_str.replace('千', ''))
                return int(base_num * 1000)
            
            return int(float(clean_str))
            
        except (ValueError, TypeError) as e:
            logger.warning(f"解析数字失败: {number_str}, 错误: {e}")
            return 0
    
    async def close(self):
        """关闭爬虫资源"""
        if self.http_client:
            await self.http_client.close()
        logger.debug("书籍详情爬虫已关闭")