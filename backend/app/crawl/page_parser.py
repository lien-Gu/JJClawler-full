"""
分类页面数据解析器
"""
from typing import Dict, List, Optional
from .base import BaseParser


class PageParser(BaseParser):
    """分类页面数据解析器"""
    
    def parse(self, raw_data: Dict) -> List[Dict]:
        """
        解析分类页面原始数据
        
        Args:
            raw_data: 原始API响应数据
            
        Returns:
            解析后的榜单和书籍数据列表
        """
        try:
            # 检查响应结构
            if not self._validate_response_structure(raw_data):
                return []
            
            # 获取数据列表
            data_list = raw_data.get("content", {}).get("data", [])
            
            parsed_data = []
            for ranking_data in data_list:
                parsed_ranking = self._parse_ranking_data(ranking_data)
                if parsed_ranking:
                    parsed_data.extend(parsed_ranking)
            
            return parsed_data
            
        except Exception as e:
            print(f"分类页面数据解析失败: {e}")
            return []
    
    def _validate_response_structure(self, raw_data: Dict) -> bool:
        """验证响应数据结构"""
        try:
            content = raw_data.get("content", {})
            if content.get("code") != "200":
                return False
            
            if not isinstance(content.get("data"), list):
                return False
            
            return True
        except:
            return False
    
    def _parse_ranking_data(self, ranking_data: Dict) -> List[Dict]:
        """
        解析单个榜单数据
        
        Args:
            ranking_data: 原始榜单数据
            
        Returns:
            解析后的书籍数据列表
        """
        try:
            # 提取榜单信息
            rank_id = ranking_data.get("rankid")
            channel_name = ranking_data.get("channelName", "")
            rank_group_type = ranking_data.get("rank_group_type", "")
            channel_more_id = ranking_data.get("channelMoreId", "")
            
            # 获取书籍列表
            books_data = ranking_data.get("data", [])
            
            parsed_books = []
            for position, book_item in enumerate(books_data, 1):
                parsed_book = self._parse_book_item(
                    book_item, 
                    position, 
                    rank_id, 
                    channel_name,
                    rank_group_type,
                    channel_more_id
                )
                if parsed_book:
                    parsed_books.append(parsed_book)
            
            return parsed_books
            
        except Exception as e:
            print(f"解析榜单数据失败: {e}, 数据: {ranking_data}")
            return []
    
    def _parse_book_item(self, book_item: Dict, position: int, rank_id: str, 
                        channel_name: str, rank_group_type: str, channel_more_id: str) -> Optional[Dict]:
        """
        解析单个书籍条目
        
        Args:
            book_item: 原始书籍数据
            position: 在榜单中的位置
            rank_id: 榜单ID
            channel_name: 频道名称
            rank_group_type: 榜单分组类型
            channel_more_id: 频道更多ID
            
        Returns:
            解析后的书籍数据
        """
        try:
            # 提取基础字段
            novel_id = book_item.get("novelId")
            novel_name = book_item.get("novelName")
            author_name = book_item.get("authorName")
            
            # 必填字段检查
            if not all([novel_id, novel_name]):
                return None
            
            # 构建标准化数据
            parsed_data = {
                # 基础信息
                "book_id": str(novel_id),
                "title": str(novel_name),
                "author_name": str(author_name) if author_name else None,
                
                # 榜单信息
                "position": position,
                "ranking_type": "page",
                "rank_id": str(rank_id) if rank_id else None,
                "channel_name": channel_name,
                "rank_group_type": rank_group_type,
                "channel_more_id": channel_more_id,
                
                # 状态信息
                "novel_step": self._parse_novel_step(book_item.get("novelStep")),
                "vip_flag": book_item.get("vip_flag"),
                "vip_date": book_item.get("vipdate"),
                "type_id": book_item.get("type_id"),
                
                # 封面信息
                "cover": book_item.get("cover"),
                "ebook_url": book_item.get("ebookurl"),
                "local_img": book_item.get("localImg"),
                "cover_id": book_item.get("coverid"),
                
                # 其他信息
                "intro_short": book_item.get("novelIntroShort"),
                "is_vip_month": book_item.get("isVipMonth"),
                "local": book_item.get("local"),
                
                # 推荐信息
                "recommend_info": self._parse_recommend_info(
                    book_item.get("recommendInfo")
                ),
                
                # 原始数据（用于调试）
                "_raw_data": book_item
            }
            
            return parsed_data
            
        except Exception as e:
            print(f"解析书籍条目失败: {e}, 数据: {book_item}")
            return None
    
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
        required_fields = ["book_id", "title", "ranking_type"]
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
        
        # ranking_type必须是page
        if parsed_data.get("ranking_type") != "page":
            return False
        
        return True