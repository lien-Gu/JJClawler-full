"""
夹子榜数据解析器
"""
from typing import Dict, List, Optional
from .base import BaseParser


class JiaziParser(BaseParser):
    """夹子榜数据解析器"""
    
    def parse(self, raw_data: Dict) -> List[Dict]:
        """
        解析夹子榜原始数据
        
        Args:
            raw_data: 原始API响应数据
            
        Returns:
            解析后的书籍数据列表
        """
        try:
            # 检查响应结构
            if not self._validate_response_structure(raw_data):
                return []
            
            # 获取书籍列表
            book_list = raw_data.get("content", {}).get("data", {}).get("list", [])
            
            parsed_books = []
            for position, book_item in enumerate(book_list, 1):
                parsed_book = self._parse_book_item(book_item, position)
                if parsed_book:
                    parsed_books.append(parsed_book)
            
            return parsed_books
            
        except Exception as e:
            print(f"夹子榜数据解析失败: {e}")
            return []
    
    def _validate_response_structure(self, raw_data: Dict) -> bool:
        """验证响应数据结构"""
        try:
            content = raw_data.get("content", {})
            if content.get("code") != "200":
                return False
            
            data = content.get("data", {})
            if not isinstance(data.get("list"), list):
                return False
            
            return True
        except:
            return False
    
    def _parse_book_item(self, book_item: Dict, position: int) -> Optional[Dict]:
        """
        解析单个书籍条目
        
        Args:
            book_item: 原始书籍数据
            position: 在榜单中的位置
            
        Returns:
            解析后的书籍数据
        """
        try:
            # 提取基础字段（支持两种字段名格式）
            novel_id = self._get_field_value(book_item, ["novelId", "novelid"])
            novel_name = self._get_field_value(book_item, ["novelName", "novelname"])
            author_id = self._get_field_value(book_item, ["authorId", "authorid"])
            author_name = self._get_field_value(book_item, ["authorName", "authorname"])
            
            # 必填字段检查
            if not all([novel_id, novel_name]):
                return None
            
            # 构建标准化数据
            parsed_data = {
                # 基础信息
                "book_id": str(novel_id),
                "title": str(novel_name),
                "author_id": str(author_id) if author_id else None,
                "author_name": str(author_name) if author_name else None,
                
                # 榜单信息
                "position": position,
                "ranking_type": "jiazi",
                
                # 分类信息
                "novel_class": self._get_field_value(book_item, ["novelClass", "novelclass"]),
                "tags": self._parse_tags(book_item.get("tags", "")),
                
                # 状态信息
                "novel_step": self._parse_novel_step(book_item.get("novelStep", book_item.get("novelstep"))),
                "vip_flag": book_item.get("vip_flag"),
                "age": book_item.get("age"),
                
                # 统计信息（这些可能不在夹子榜数据中）
                "novel_size": self._get_field_value(book_item, ["novelSizeformat", "novelsizeformat"]),
                
                # 封面信息
                "cover": book_item.get("cover"),
                "local_img": self._get_field_value(book_item, ["localImg", "localimg"]),
                
                # 其他信息
                "intro_short": self._get_field_value(book_item, ["novelIntroShort", "novelintroshort"]),
                "fit_fenzhan": book_item.get("fit_fenzhan", []),
                
                # 推荐信息
                "recommend_info": self._parse_recommend_info(
                    book_item.get("recommendInfo", book_item.get("recommendinfo"))
                ),
                
                # 原始数据（用于调试）
                "_raw_data": book_item
            }
            
            return parsed_data
            
        except Exception as e:
            print(f"解析书籍条目失败: {e}, 数据: {book_item}")
            return None
    
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
        
        # 标签用逗号分隔
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        return tags
    
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
            import json
            return json.loads(recommend_str)
        except:
            return None
    
    def validate(self, parsed_data: Dict) -> bool:
        """
        验证解析后的数据
        
        Args:
            parsed_data: 解析后的书籍数据
            
        Returns:
            数据是否有效
        """
        # 必填字段检查
        required_fields = ["book_id", "title"]
        for field in required_fields:
            if not parsed_data.get(field):
                return False
        
        # 数据类型检查
        if not isinstance(parsed_data.get("position"), int):
            return False
        
        if parsed_data.get("position") <= 0:
            return False
        
        # book_id必须是数字字符串
        try:
            int(parsed_data["book_id"])
        except (ValueError, TypeError):
            return False
        
        return True