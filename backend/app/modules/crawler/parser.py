"""
数据解析模块

负责将API响应数据转换为标准化的模型对象：
- 夹子榜数据解析
- 分类页面数据解析
- 书籍信息标准化
- 数据清洗和验证
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple

from app.modules.models import Book, BookSnapshot

logger = logging.getLogger(__name__)


class DataParser:
    """
    数据解析器
    
    负责将API响应数据转换为标准化的模型对象：
    - 夹子榜数据解析
    - 分类页面数据解析
    - 书籍信息标准化
    - 数据清洗和验证
    """
    
    @staticmethod
    def parse_jiazi_data(raw_data: Dict[str, Any]) -> Tuple[List[Book], List[BookSnapshot]]:
        """
        解析夹子榜数据
        
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
            logger.error(f"夹子榜数据解析失败: {e}")
            raise
        
        logger.info(f"夹子榜数据解析完成: {len(books)} 本书籍")
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