"""
数据转换工具模块

提供统一的数据转换和格式化功能
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from app.modules.models import Book, BookSnapshot, Ranking, RankingSnapshot, BookDetail


def book_to_detail(
    book: Book, 
    latest_snapshot: Optional[BookSnapshot] = None
) -> BookDetail:
    """
    将Book和BookSnapshot转换为BookDetail
    
    统一的BookDetail构建逻辑，避免重复代码
    
    Args:
        book: 书籍基础信息
        latest_snapshot: 最新的书籍快照
        
    Returns:
        BookDetail对象
    """
    return BookDetail(
        id=book.id,
        book_id=book.book_id,
        title=book.title,
        author_id=book.author_id,
        author_name=book.author_name,
        novel_class=book.novel_class,
        tags=book.tags,
        first_seen=book.first_seen,
        last_updated=book.last_updated,
        latest_clicks=latest_snapshot.total_clicks if latest_snapshot else None,
        latest_favorites=latest_snapshot.total_favorites if latest_snapshot else None,
        latest_comments=latest_snapshot.comment_count if latest_snapshot else None,
        latest_chapters=latest_snapshot.chapter_count if latest_snapshot else None
    )


def calculate_position_change(
    current_position: Optional[int], 
    previous_position: Optional[int]
) -> int:
    """
    计算位置变化
    
    Args:
        current_position: 当前位置
        previous_position: 之前位置
        
    Returns:
        位置变化值（正数为上升，负数为下降，0为无变化）
    """
    if current_position is None or previous_position is None:
        return 0
    
    # 位置变化：之前位置 - 当前位置（因为位置数字越小排名越高）
    return previous_position - current_position


def format_ranking_item(
    book: Book,
    snapshot: BookSnapshot,
    position: int,
    position_change: int = 0
) -> Dict[str, Any]:
    """
    格式化排行榜项目
    
    Args:
        book: 书籍信息
        snapshot: 书籍快照
        position: 排名位置
        position_change: 位置变化
        
    Returns:
        格式化后的排行榜项目
    """
    return {
        "book_id": book.book_id,
        "title": book.title,
        "author_name": book.author_name,
        "position": position,
        "position_change": position_change,
        "total_clicks": snapshot.total_clicks,
        "total_favorites": snapshot.total_favorites,
        "comment_count": snapshot.comment_count,
        "chapter_count": snapshot.chapter_count,
        "snapshot_time": snapshot.snapshot_time
    }


def extract_numeric_value(text: str, default: int = 0) -> int:
    """
    从文本中提取数字值
    
    处理各种格式的数字文本（如 "1.2万"、"3千"）
    
    Args:
        text: 包含数字的文本
        default: 默认值
        
    Returns:
        提取的数字值
    """
    if not text or not isinstance(text, str):
        return default
    
    # 移除空白字符
    text = text.strip()
    
    # 处理空字符串
    if not text:
        return default
    
    try:
        # 处理万、千等单位
        if '万' in text:
            num_part = text.replace('万', '').replace(',', '')
            return int(float(num_part) * 10000)
        elif '千' in text:
            num_part = text.replace('千', '').replace(',', '')
            return int(float(num_part) * 1000)
        else:
            # 移除逗号并转换为整数
            return int(text.replace(',', ''))
    except (ValueError, TypeError):
        return default


def normalize_datetime(dt: Any) -> Optional[datetime]:
    """
    标准化日期时间对象
    
    Args:
        dt: 日期时间对象（可能是字符串、datetime等）
        
    Returns:
        标准化的datetime对象或None
    """
    if dt is None:
        return None
    
    if isinstance(dt, datetime):
        return dt
    
    if isinstance(dt, str):
        try:
            # 尝试解析ISO格式
            return datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            try:
                # 尝试其他常见格式
                return datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    
    return None


def format_crawl_result(
    books_new: int = 0,
    books_updated: int = 0,
    snapshots_created: int = 0,
    ranking_snapshots: int = 0,
    **kwargs
) -> Dict[str, Any]:
    """
    格式化爬取结果
    
    Args:
        books_new: 新增书籍数
        books_updated: 更新书籍数
        snapshots_created: 创建快照数
        ranking_snapshots: 排行榜快照数
        **kwargs: 其他参数
        
    Returns:
        格式化的爬取结果
    """
    return {
        "books_new": books_new,
        "books_updated": books_updated,
        "books_total": books_new + books_updated,
        "snapshots_created": snapshots_created,
        "ranking_snapshots": ranking_snapshots,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    }