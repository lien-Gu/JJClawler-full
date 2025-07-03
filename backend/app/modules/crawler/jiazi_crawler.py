"""
夹子榜爬虫模块

专门负责晋江文学城夹子榜的数据抓取和解析
"""
import json
from typing import Dict, Any, Tuple, List
from datetime import datetime

from app.utils.http_client import HTTPClient
from app.utils.log_utils import get_logger
from app.modules.models import Book, BookSnapshot
from app.modules.dao import BookDAO
from app.modules.database.connection import get_session

logger = get_logger(__name__)


class JiaziCrawler:
    """夹子榜爬虫"""
    
    def __init__(self):
        self.http_client = HTTPClient(
            timeout=30.0,
            rate_limit_delay=1.0
        )
        self.url = "https://app-cdn.jjwxc.com/bookstore/favObservationByDate?day=today&use_cdn=1&version=19"
    
    async def crawl(self) -> Dict[str, Any]:
        """执行夹子榜爬取"""
        try:
            logger.info("开始爬取夹子榜数据")
            
            # 获取数据
            response = await self.http_client.get(self.url)
            response.raise_for_status()
            
            # 解析JSON响应
            data = response.json()
            
            # 解析书籍数据
            books, snapshots = self._parse_jiazi_data(data)
            
            # 保存到数据库
            saved_books, saved_snapshots = await self._save_data(books, snapshots)
            
            result = {
                "success": True,
                "books_new": len([b for b in saved_books if b]),
                "books_updated": len(saved_books) - len([b for b in saved_books if b]),
                "total_books": len(books),
                "snapshots_created": len(saved_snapshots)
            }
            
            logger.info(f"夹子榜爬取完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"夹子榜爬取失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "books_new": 0,
                "books_updated": 0,
                "total_books": 0
            }
    
    def _parse_jiazi_data(self, data: Dict[str, Any]) -> Tuple[List[Book], List[BookSnapshot]]:
        """解析夹子榜API响应数据"""
        books = []
        snapshots = []
        
        try:
            # 检查API响应状态
            if data.get('code') != '200':
                raise ValueError(f"API响应错误: {data.get('message', '未知错误')}")
            
            book_list = data.get('data', {}).get('list', [])
            current_time = datetime.now()
            
            for item in book_list:
                try:
                    # 解析书籍基本信息
                    book = self._parse_book_info(item)
                    books.append(book)
                    
                    # 解析书籍快照数据
                    snapshot = self._parse_book_snapshot(item, current_time)
                    snapshots.append(snapshot)
                    
                except Exception as e:
                    logger.warning(f"解析单本书籍失败: {e}, 书籍数据: {item.get('novelId', 'unknown')}")
                    continue
                    
        except Exception as e:
            logger.error(f"夹子榜数据解析失败: {e}")
            raise
        
        logger.info(f"夹子榜数据解析完成: {len(books)} 本书籍")
        return books, snapshots
    
    def _parse_book_info(self, item: Dict[str, Any]) -> Book:
        """解析单本书籍的基本信息"""
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
    
    def _parse_book_snapshot(self, item: Dict[str, Any], snapshot_time: datetime) -> BookSnapshot:
        """解析书籍快照数据"""
        book_id = str(item.get('novelId') or item.get('novelid', ''))
        
        # 解析统计数据（夹子榜API中通常不包含详细统计数据）
        # 但可以尝试解析已有字段
        total_clicks = self._parse_numeric_field(item, ['novelScore'], 0)
        total_favorites = self._parse_numeric_field(item, ['favCount', 'totalFavorites'], 0)
        comment_count = self._parse_numeric_field(item, ['commentCount'], 0)
        chapter_count = self._parse_numeric_field(item, ['chapterCount'], 0)
        word_count = self._parse_word_count(item.get('novelSizeformat', ''))
        
        return BookSnapshot(
            book_id=book_id,
            total_clicks=total_clicks,
            total_favorites=total_favorites,
            comment_count=comment_count,
            chapter_count=chapter_count,
            word_count=word_count,
            snapshot_time=snapshot_time
        )
    
    def _parse_numeric_field(self, item: Dict[str, Any], field_names: List[str], default: int = 0) -> int:
        """解析数值字段（处理字符串格式的数字）"""
        for field_name in field_names:
            value = item.get(field_name)
            if value is not None:
                try:
                    # 处理字符串格式的数字
                    if isinstance(value, str):
                        # 去除逗号
                        value = value.replace(',', '')
                        
                        # 处理"亿"单位
                        if '亿' in value:
                            base_num = float(value.replace('亿', ''))
                            return int(base_num * 100000000)
                        
                        # 处理"万"单位
                        if '万' in value:
                            base_num = float(value.replace('万', ''))
                            return int(base_num * 10000)
                        
                        # 处理"千"单位  
                        if '千' in value:
                            base_num = float(value.replace('千', ''))
                            return int(base_num * 1000)
                    
                    return int(float(value))
                except (ValueError, TypeError):
                    continue
        
        return default
    
    def _parse_word_count(self, size_format: str) -> int:
        """解析字数格式，如 '10.14万' -> 101400"""
        if not size_format:
            return 0
        
        try:
            # 去除多余空格
            size_format = size_format.strip()
            
            # 处理"万"单位
            if '万' in size_format:
                base_num = float(size_format.replace('万', ''))
                return int(base_num * 10000)
            
            # 处理纯数字
            return int(float(size_format))
            
        except (ValueError, TypeError):
            logger.warning(f"无法解析字数格式: {size_format}")
            return 0
    
    async def _save_data(self, books: List[Book], snapshots: List[BookSnapshot]) -> Tuple[List[Book], List[BookSnapshot]]:
        """保存数据到数据库"""
        saved_books = []
        saved_snapshots = []
        
        try:
            async with get_session() as session:
                book_dao = BookDAO(session)
                
                # 保存或更新书籍信息
                for book in books:
                    try:
                        book_data = {
                            "book_id": book.book_id,
                            "title": book.title,
                            "author_id": book.author_id,
                            "author_name": book.author_name,
                            "novel_class": book.novel_class,
                            "tags": book.tags,
                            "first_seen": book.first_seen,
                            "last_updated": book.last_updated
                        }
                        saved_book = book_dao.create_or_update(book_data)
                        saved_books.append(saved_book)
                    except Exception as e:
                        logger.error(f"保存书籍失败 {book.book_id}: {e}")
                        saved_books.append(None)
                
                # 批量保存快照
                try:
                    snapshots_data = []
                    for snapshot in snapshots:
                        snapshot_data = {
                            "book_id": snapshot.book_id,
                            "total_clicks": snapshot.total_clicks,
                            "total_favorites": snapshot.total_favorites,
                            "comment_count": snapshot.comment_count,
                            "chapter_count": snapshot.chapter_count,
                            "word_count": snapshot.word_count,
                            "snapshot_time": snapshot.snapshot_time
                        }
                        snapshots_data.append(snapshot_data)
                    
                    saved_snapshots = book_dao.batch_create_snapshots(snapshots_data)
                except Exception as e:
                    logger.error(f"批量保存快照失败: {e}")
                
                session.commit()
                
        except Exception as e:
            logger.error(f"数据保存失败: {e}")
            raise
        
        logger.info(f"数据保存完成: {len(saved_books)} 本书籍, {len(saved_snapshots)} 个快照")
        return saved_books, saved_snapshots
    
    async def close(self):
        """关闭资源"""
        await self.http_client.close()