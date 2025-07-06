"""
统一数据解析器 - 简化版本
"""
from enum import Enum
from typing import Dict, List, Any


class DataType(Enum):
    """数据类型枚举"""
    PAGE = "page"
    RANKING = "ranking"
    BOOK = "book"


class ParsedItem:
    """解析结果项"""
    
    def __init__(self, data_type: DataType, data: Dict):
        self.data_type = data_type
        self.data = data


class Parser:
    """统一数据解析器"""
    
    def parse(self, raw_data: Dict) -> List[ParsedItem]:
        """
        解析原始数据，自动识别数据类型
        
        Args:
            raw_data: 原始API响应数据
            
        Returns:
            解析后的数据项列表
        """
        if not raw_data:
            return []
        
        data_type = self._identify_data_type(raw_data)
        
        if data_type == DataType.PAGE:
            return self._parse_page_data(raw_data)
        elif data_type == DataType.RANKING:
            return self._parse_ranking_data(raw_data)
        elif data_type == DataType.BOOK:
            return self._parse_book_data(raw_data)
        
        return []
    
    def _identify_data_type(self, data: Dict) -> DataType:
        """识别数据类型"""
        if not isinstance(data, dict):
            return DataType.PAGE
        
        # 检查是否为夹子榜数据（单一榜单）
        if "list" in data:
            return DataType.RANKING

        # 检查是否为书籍详情数据
        if "novelId" in data or "novel_id" in data:
            return DataType.BOOK
        # 默认返回页面类型
        return DataType.PAGE
    
    def _parse_page_data(self, raw_data: Dict) -> List[ParsedItem]:
        """解析页面数据"""
        try:
            data_list = raw_data.get("content", {}).get("data", [])
            parsed_items = []
            
            for ranking_data in data_list:
                ranking_info = {
                    "rank_id": ranking_data.get("rankid"),
                    "rank_name": ranking_data.get("channelName"),
                    "rank_group_type":ranking_data.get("rank_group_type"),
                    "books": []
                }
                
                # 解析榜单中的书籍
                books_data = ranking_data.get("data", [])
                for position, book_item in enumerate(books_data, 1):
                    book_info = self._parse_book_basic(book_item, position)
                    if book_info:
                        ranking_info["books"].append(book_info)
                
                parsed_items.append(ParsedItem(DataType.RANKING, ranking_info))
            
            return parsed_items
            
        except Exception as e:
            print(f"⚠️ 页面数据解析失败: {e}")
            return []
    
    def _parse_ranking_data(self, raw_data: Dict) -> List[ParsedItem]:
        """解析榜单数据"""
        try:
            books_data = raw_data.get("list", [])
            books = []
            
            for position, book_item in enumerate(books_data, 1):
                book_info = self._parse_book_basic(book_item, position)
                if book_info:
                    books.append(book_info)
            
            ranking_info = {
                "ranking_id": "jiazi",
                "ranking_name": "夹子榜",
                "books": books
            }
            
            return [ParsedItem(DataType.RANKING, ranking_info)]
            
        except Exception as e:
            print(f"⚠️ 榜单数据解析失败: {e}")
            return []
    
    def _parse_book_data(self, raw_data: Dict) -> List[ParsedItem]:
        """解析书籍详情数据"""
        try:
            book_info = {
                "novel_id": self._get_field(raw_data, ["novelId", "novel_id"]),
                "title": self._get_field(raw_data, ["novelName", "novel_name"]),
                # "author_id": self._get_field(raw_data, ["authorId", "author_id"]),
                # "author_name": self._get_field(raw_data, ["authorName", "author_name"]),
                # "category": self._get_field(raw_data, ["novelClass", "novel_class"]),
                # "status": self._get_field(raw_data, ["novelStep", "novel_step"]),
                # "word_count": self._get_field(raw_data, ["novelSize", "novel_size"]),
                # "summary": self._get_field(raw_data, ["novelIntro", "novel_intro"]),
                # "tags": self._get_field(raw_data, ["novelTags", "novel_tags"], []),
                "clicks": self._get_field(raw_data, ["novelClickCount", "novip_clicks"], 0),
                "favorites": self._get_field(raw_data, ["novelFavoriteCount", "novel_favorite_count"], 0),
                # "chapters": self._get_field(raw_data, ["novelChapterCount", "novel_chapter_count"], 0),
                "comments": self._get_field(raw_data, ["CommentCount", "comment_count"], 0),
                "nutrition":  self._get_field(raw_data, ["nutritionNovel", "nutrition_novel"], 0)
            }
            
            return [ParsedItem(DataType.BOOK, book_info)]
            
        except Exception as e:
            print(f"⚠️ 书籍数据解析失败: {e}")
            return []
    
    def _parse_book_basic(self, book_item: Dict, position: int) -> Dict:
        """解析书籍基础信息"""
        try:
            return {
                "book_id": self._get_field(book_item, ["novelId", "novel_id"]),
                "title": self._get_field(book_item, ["novelName", "novel_name"]),
                "position": position,
                "clicks": self._get_field(book_item, ["novelClickCount", "novel_click_count"], 0),
                "favorites": self._get_field(book_item, ["novelFavoriteCount", "novel_favorite_count"], 0)
            }
        except Exception:
            return None
    
    def _get_field(self, data: Dict, field_names: List[str], default: Any = None) -> Any:
        """获取字段值，支持多种字段名"""
        for field_name in field_names:
            if field_name in data:
                return data[field_name]
        return default