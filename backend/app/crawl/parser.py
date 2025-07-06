"""
统一数据解析器，支持三种数据类型：页面、榜单、书籍
"""
import json
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from .base import BaseParser


class DataType(Enum):
    """数据类型枚举"""
    PAGE = "page"          # 页面数据（包含多个榜单）
    RANKING = "ranking"    # 榜单数据（包含多本书籍）
    BOOK = "book"          # 书籍详情数据


class ParsedItem:
    """解析结果项"""
    
    def __init__(self, data_type: DataType, data: Dict, nested_tasks: List[Dict] = None):
        self.data_type = data_type
        self.data = data
        self.nested_tasks = nested_tasks or []  # 需要进一步爬取的嵌套任务


class UnifiedParser(BaseParser):
    """统一数据解析器"""
    
    def __init__(self):
        """初始化统一解析器"""
        self.field_mappers = {
            # 支持多种字段名映射
            "novel_id": ["novelId", "novelid"],
            "novel_name": ["novelName", "novelname"],
            "author_id": ["authorId", "authorid"],
            "author_name": ["authorName", "authorname"],
            "novel_class": ["novelClass", "novelclass"],
            "novel_step": ["novelStep", "novelstep"],
            "novel_size": ["novelSizeformat", "novelsizeformat"],
            "intro_short": ["novelIntroShort", "novelintroshort"],
            "local_img": ["localImg", "localimg"],
            "recommend_info": ["recommendInfo", "recommendinfo"]
        }
    
    def parse(self, raw_data: Dict) -> List[ParsedItem]:
        """
        解析原始数据，自动识别数据类型
        
        Args:
            raw_data: 原始API响应数据
            
        Returns:
            解析后的数据项列表
        """
        try:
            # 检查响应结构
            if not self._validate_response_structure(raw_data):
                return []
            
            # 识别数据类型并解析
            data_type = self._identify_data_type(raw_data)
            
            if data_type == DataType.PAGE:
                return self._parse_page_data(raw_data)
            elif data_type == DataType.RANKING:
                return self._parse_ranking_data(raw_data)
            elif data_type == DataType.BOOK:
                return self._parse_book_data(raw_data)
            else:
                print(f"未知数据类型: {raw_data}")
                return []
                
        except Exception as e:
            print(f"数据解析失败: {e}")
            return []
    
    def _identify_data_type(self, raw_data: Dict) -> DataType:
        """
        识别数据类型
        
        Args:
            raw_data: 原始响应数据
            
        Returns:
            数据类型
        """
        content = raw_data.get("content", {})
        data = content.get("data")
        
        # 检查是否为书籍详情数据
        if isinstance(data, dict) and "novelId" in data:
            return DataType.BOOK
        
        # 检查是否为页面数据（包含多个榜单）
        if isinstance(data, list) and data:
            first_item = data[0]
            if "rankid" in first_item and "channelName" in first_item:
                return DataType.PAGE
        
        # 检查是否为夹子榜数据（单一榜单）
        if isinstance(data, dict) and "list" in data:
            return DataType.RANKING
        
        # 默认返回页面类型
        return DataType.PAGE
    
    def _parse_page_data(self, raw_data: Dict) -> List[ParsedItem]:
        """
        解析页面数据（包含多个榜单）
        
        Args:
            raw_data: 原始页面数据
            
        Returns:
            解析后的榜单列表和嵌套任务
        """
        try:
            data_list = raw_data.get("content", {}).get("data", [])
            parsed_items = []
            
            for ranking_data in data_list:
                # 解析榜单基础信息
                ranking_info = self._extract_ranking_info(ranking_data)
                
                # 解析榜单中的书籍
                books_data = ranking_data.get("data", [])
                parsed_books = []
                nested_tasks = []
                
                for position, book_item in enumerate(books_data, 1):
                    book_info = self._parse_book_item_basic(book_item, position, ranking_info)
                    if book_info:
                        parsed_books.append(book_info)
                        
                        # 生成书籍详情爬取任务
                        book_detail_task = self._create_book_detail_task(book_info["book_id"])
                        if book_detail_task:
                            nested_tasks.append(book_detail_task)
                
                # 创建榜单数据项
                ranking_item = ParsedItem(
                    data_type=DataType.RANKING,
                    data={
                        **ranking_info,
                        "books": parsed_books,
                        "total_books": len(parsed_books)
                    },
                    nested_tasks=nested_tasks
                )
                parsed_items.append(ranking_item)
            
            return parsed_items
            
        except Exception as e:
            print(f"解析页面数据失败: {e}")
            return []
    
    def _parse_ranking_data(self, raw_data: Dict) -> List[ParsedItem]:
        """
        解析榜单数据（如夹子榜）
        
        Args:
            raw_data: 原始榜单数据
            
        Returns:
            解析后的书籍列表和嵌套任务
        """
        try:
            book_list = raw_data.get("content", {}).get("data", {}).get("list", [])
            parsed_books = []
            nested_tasks = []
            
            for position, book_item in enumerate(book_list, 1):
                book_info = self._parse_book_item_full(book_item, position, "jiazi")
                if book_info:
                    parsed_books.append(book_info)
                    
                    # 生成书籍详情爬取任务（如果需要更多信息）
                    book_detail_task = self._create_book_detail_task(book_info["book_id"])
                    if book_detail_task:
                        nested_tasks.append(book_detail_task)
            
            # 创建榜单数据项
            ranking_item = ParsedItem(
                data_type=DataType.RANKING,
                data={
                    "ranking_type": "jiazi",
                    "ranking_name": "夹子榜",
                    "books": parsed_books,
                    "total_books": len(parsed_books)
                },
                nested_tasks=nested_tasks
            )
            
            return [ranking_item]
            
        except Exception as e:
            print(f"解析榜单数据失败: {e}")
            return []
    
    def _parse_book_data(self, raw_data: Dict) -> List[ParsedItem]:
        """
        解析书籍详情数据
        
        Args:
            raw_data: 原始书籍数据
            
        Returns:
            解析后的书籍详情
        """
        try:
            book_data = raw_data.get("content", {})
            
            # 解析完整书籍信息
            parsed_book = self._parse_book_detail(book_data)
            if not parsed_book:
                return []
            
            # 创建书籍数据项
            book_item = ParsedItem(
                data_type=DataType.BOOK,
                data=parsed_book
            )
            
            return [book_item]
            
        except Exception as e:
            print(f"解析书籍数据失败: {e}")
            return []
    
    def _extract_ranking_info(self, ranking_data: Dict) -> Dict:
        """提取榜单基础信息"""
        return {
            "rank_id": str(ranking_data.get("rankid", "")),
            "channel_name": ranking_data.get("channelName", ""),
            "rank_group_type": ranking_data.get("rank_group_type", ""),
            "channel_more_id": ranking_data.get("channelMoreId", ""),
            "ranking_type": "page"
        }
    
    def _parse_book_item_basic(self, book_item: Dict, position: int, ranking_info: Dict) -> Optional[Dict]:
        """解析榜单中的书籍基础信息"""
        try:
            novel_id = book_item.get("novelId")
            novel_name = book_item.get("novelName")
            
            if not all([novel_id, novel_name]):
                return None
            
            return {
                "book_id": str(novel_id),
                "title": str(novel_name),
                "author_name": book_item.get("authorName"),
                "position": position,
                "novel_step": self._parse_novel_step(book_item.get("novelStep")),
                "vip_flag": book_item.get("vip_flag"),
                "cover": book_item.get("cover"),
                "intro_short": book_item.get("novelIntroShort"),
                "recommend_info": self._parse_recommend_info(book_item.get("recommendInfo")),
                "ranking_info": ranking_info,
                "_raw_data": book_item
            }
            
        except Exception as e:
            print(f"解析书籍基础信息失败: {e}")
            return None
    
    def _parse_book_item_full(self, book_item: Dict, position: int, ranking_type: str) -> Optional[Dict]:
        """解析完整书籍信息（如夹子榜中的书籍）"""
        try:
            novel_id = self._get_field_value(book_item, self.field_mappers["novel_id"])
            novel_name = self._get_field_value(book_item, self.field_mappers["novel_name"])
            
            if not all([novel_id, novel_name]):
                return None
            
            return {
                "book_id": str(novel_id),
                "title": str(novel_name),
                "author_id": self._get_field_value(book_item, self.field_mappers["author_id"]),
                "author_name": self._get_field_value(book_item, self.field_mappers["author_name"]),
                "position": position,
                "ranking_type": ranking_type,
                "novel_class": self._get_field_value(book_item, self.field_mappers["novel_class"]),
                "tags": self._parse_tags(book_item.get("tags", "")),
                "novel_step": self._parse_novel_step(
                    self._get_field_value(book_item, self.field_mappers["novel_step"])
                ),
                "vip_flag": book_item.get("vip_flag"),
                "age": book_item.get("age"),
                "novel_size": self._get_field_value(book_item, self.field_mappers["novel_size"]),
                "cover": book_item.get("cover"),
                "local_img": self._get_field_value(book_item, self.field_mappers["local_img"]),
                "intro_short": self._get_field_value(book_item, self.field_mappers["intro_short"]),
                "fit_fenzhan": book_item.get("fit_fenzhan", []),
                "recommend_info": self._parse_recommend_info(
                    self._get_field_value(book_item, self.field_mappers["recommend_info"])
                ),
                "_raw_data": book_item
            }
            
        except Exception as e:
            print(f"解析完整书籍信息失败: {e}")
            return None
    
    def _parse_book_detail(self, book_data: Dict) -> Optional[Dict]:
        """解析书籍详情数据"""
        try:
            novel_id = book_data.get("novelId")
            novel_name = book_data.get("novelName")
            
            if not all([novel_id, novel_name]):
                return None
            
            return {
                "book_id": str(novel_id),
                "title": str(novel_name),
                "author_id": book_data.get("authorId"),
                "author_name": book_data.get("authorName"),
                "novel_class": book_data.get("novelClass"),
                "novel_tags": book_data.get("novelTags"),
                "novel_tags_id": book_data.get("novelTagsId"),
                "novel_cover": book_data.get("novelCover"),
                "novel_step": self._parse_novel_step(book_data.get("novelStep")),
                "novel_intro": book_data.get("novelIntro"),
                "intro_short": book_data.get("novelIntroShort"),
                "is_vip": book_data.get("isVip"),
                "novel_size": book_data.get("novelSize"),
                "novel_size_format": book_data.get("novelsizeformat"),
                "chapter_count": book_data.get("novelChapterCount"),
                "renew_date": book_data.get("renewDate"),
                "novel_score": book_data.get("novelScore"),
                "favorited_count": book_data.get("novelbefavoritedcount"),
                "comment_count": book_data.get("comment_count"),
                "nutrition_novel": book_data.get("nutrition_novel"),
                "ranking": book_data.get("ranking"),
                "clicks": book_data.get("novip_clicks"),
                "is_sign": book_data.get("isSign"),
                "protagonist": book_data.get("protagonist"),
                "costar": book_data.get("costar"),
                "other": book_data.get("other"),
                "_raw_data": book_data
            }
            
        except Exception as e:
            print(f"解析书籍详情失败: {e}")
            return None
    
    def _create_book_detail_task(self, book_id: str) -> Optional[Dict]:
        """
        创建书籍详情爬取任务
        
        Args:
            book_id: 书籍ID
            
        Returns:
            书籍详情爬取任务配置
        """
        if not book_id:
            return None
        
        return {
            "id": f"book_detail_{book_id}",
            "name": f"书籍详情_{book_id}",
            "type": "book_detail",
            "template": "novel_detail",
            "params": {
                "novel_id": book_id
            },
            "priority": "low"  # 书籍详情爬取优先级较低
        }
    
    def _validate_response_structure(self, raw_data: Dict) -> bool:
        """验证响应数据结构"""
        try:
            content = raw_data.get("content", {})
            return content.get("code") == "200"
        except:
            return False
    
    def _get_field_value(self, data: Dict, field_names: List[str]) -> Optional[str]:
        """获取字段值（支持多个字段名）"""
        for field_name in field_names:
            value = data.get(field_name)
            if value is not None:
                return value
        return None
    
    def _parse_tags(self, tags_str: str) -> List[str]:
        """解析标签字符串"""
        if not tags_str:
            return []
        return [tag.strip() for tag in tags_str.split(",") if tag.strip()]
    
    def _parse_novel_step(self, step_value) -> Optional[str]:
        """解析小说状态"""
        if step_value is None:
            return None
        
        step_map = {
            "1": "连载中",
            "2": "已完成", 
            "3": "暂停更新"
        }
        
        return step_map.get(str(step_value), str(step_value))
    
    def _parse_recommend_info(self, recommend_str: Optional[str]) -> Optional[Dict]:
        """解析推荐信息JSON字符串"""
        if not recommend_str:
            return None
        
        try:
            return json.loads(recommend_str)
        except:
            return None
    
    def validate(self, parsed_data: Dict) -> bool:
        """
        验证解析后的数据
        
        Args:
            parsed_data: 解析后的数据
            
        Returns:
            数据是否有效
        """
        # 必填字段检查
        if not parsed_data.get("book_id") or not parsed_data.get("title"):
            return False
        
        # book_id必须是数字字符串
        try:
            int(parsed_data["book_id"])
        except (ValueError, TypeError):
            return False
        
        return True