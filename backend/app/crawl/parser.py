"""
统一数据解析器 - 简化版本
"""

from enum import Enum
from typing import Any, Optional, Dict, List
from ..utils import update_dict
from datetime import datetime


class DataType(Enum):
    """数据类型枚举"""

    PAGE = "page"
    RANKING = "ranking"
    BOOK = "book"


class RankingParseInfo:
    def __init__(self, page_id: str):
        self.ranking_info = {}
        self.books: List[BookParseInfo] = []
        self.sub_rankings: List = []
        self.has_sub_ranking = False
        self.page_id = page_id

    def parse_ranking_info(self, raw_data: Dict, parent_ranking_info: Optional[Dict] = None):
        """
        从页面原始数据中解析出榜单数据
        :param page_id:
        :param raw_data:
        :param parent_ranking_info:
        :return:
        """
        # 构造榜单信息
        self.ranking_info = self.jiazi_info() if self.page_id == "page_id" else {
            "rank_id": str(raw_data.get("rankid", None)),
            "rank_name": raw_data.get("channelName", None),
            "rank_group_type": str(raw_data.get("rank_group_type", None)),
            "page_id": self.page_id,
        }

        data_list = self._get_ranking_data(raw_data)
        if self.has_sub_ranking:
            self.sub_rankings = data_list
            return
        # 如果是一个嵌套榜单的子榜单，需要结合母榜单的信息构造榜单信息
        if parent_ranking_info:
            self.ranking_info = update_dict(parent_ranking_info, self.ranking_info)
        # 解析榜单书籍信息
        for index, book in enumerate(data_list):
            self.books.append(BookParseInfo(index, book))

    def _get_ranking_data(self, raw_data: Dict) -> List[Dict]:
        """
        检查data结构体

        :param raw_data:
        :return:
        """

        data_list = raw_data.get("data", [])
        if not data_list:
            data_list = raw_data.get("list", [])
        if not data_list:
            raise ValueError("该榜单中内容为空")
        if not isinstance(raw_data, list) and not isinstance(raw_data[0], dict):
            raise TypeError("响应体data结构错误")
        if "channelName" in data_list[0]:
            self.has_sub_ranking = True
        return data_list

    @staticmethod
    def jiazi_info() -> Dict:
        """
        夹子榜单固定信息
        :return:
        """
        return {
            "rank_id": "jiazi",
            "rank_name": "夹子榜单",
            "rank_group_type": None,
            "page_id": "jiazi"
        }


class BookParseInfo:
    def __init__(self, index, raw_basic_data: Dict):
        self.book_basic_info = {}
        self.book_detail = {}

        self._parse_book_basic_info(index, raw_basic_data)

    def _parse_book_basic_info(self, index, raw_basic_data: Dict):
        self.book_basic_info = {
            "position": index,
            "novel_id": raw_basic_data.get("novelId", None),
            "title": raw_basic_data.get("novelName", None),
            "author_id": raw_basic_data.get("authorid", None),
            "snapshot_time": datetime.now()
        }

    def parse_book_info(self, raw_detail_data: Dict):
        pass

    @classmethod
    def unique_book_items(cls, book_list: List["BookParseInfo"]) -> List["BookParseInfo"]:
        valid_books = [b for b in book_list if b.book_basic_info.get("novel_id") is not None]
        unique_dict = {book.book_basic_info["novel_id"]: book
                       for book in valid_books}
        return list(unique_dict.values())


class ParsedItem:
    """解析结果项"""

    def __init__(self, data_type: DataType, data: RankingParseInfo | Any):
        self.data_type = data_type
        self.data = data


class Parser:
    """统一数据解析器"""

    def parse(self, raw_data: dict, page_id: str, data_type: DataType = DataType.PAGE) -> list:
        """
        解析原始数据，自动识别数据类型

        :param raw_data: 原始API响应数据
        :param page_id: 爬取网页id，仅在data_type为PAGE时有效
        :param data_type: 解析的数据类型
        :return: 解析后的数据项列表
        """
        if not raw_data:
            raise ValueError("解析原始数据不存在")
        if data_type == DataType.PAGE:
            return self._parse_page_data(raw_data, page_id)
        elif data_type == DataType.RANKING:
            return self._parse_ranking_data(raw_data)
        elif data_type == DataType.BOOK:
            return self._parse_book_data(raw_data)

        return []

    @staticmethod
    def _parse_page_data(
            raw_data: dict, page_id: Optional[str] = None
    ) -> list[RankingParseInfo]:
        """
        解析页面数据

        :param raw_data:
        :param page_id:
        :return:
        """
        try:
            result = []
            data_list = raw_data.get("data", [])
            if isinstance(data_list, dict):
                data_list = [data_list]
            for ranking_data in data_list:
                rank_info = RankingParseInfo(page_id)
                rank_info.parse_ranking_info(ranking_data)
                if not rank_info.has_sub_ranking:
                    result.append(rank_info)
                    continue
                for sub_ranking_data in rank_info.sub_rankings:
                    sub_rank_info = RankingParseInfo(page_id)
                    sub_rank_info.parse_ranking_info(sub_ranking_data, rank_info.ranking_info)
                    result.append(sub_rank_info)
            return result
        except Exception as e:
            print(f"⚠️ 页面数据解析失败: {e}")
            import traceback

            traceback.print_exc()
            return []

    def _parse_ranking_data(
            self, raw_data: dict, context: dict = None
    ) -> list[ParsedItem]:
        """解析榜单数据（夹子榜）"""
        try:
            # 新数据结构：data.list
            data_section = raw_data.get("data", {})
            books_data = data_section.get("list", [])
            books = []

            for position, book_item in enumerate(books_data, 1):
                book_info = self._parse_book_basic(book_item, position)
                if book_info:
                    books.append(book_info)

            # 从上下文获取page_id
            page_id = "jiazi"  # 默认值
            if context and "page_id" in context:
                page_id = context["page_id"]

            ranking_info = {
                "rank_id": "jiazi",  # 使用"jiazi"作为夹子榜的固定ID
                "rank_name": "夹子榜",
                "page_id": page_id,
                "books": books,
            }

            return [ParsedItem(DataType.RANKING, ranking_info)]

        except Exception as e:
            print(f"⚠️ 榜单数据解析失败: {e}")
            return []

    def _parse_book_data(self, raw_data: dict) -> list[ParsedItem]:
        """解析书籍详情数据"""
        try:
            book_info = {
                "book_id": self._get_field(raw_data, ["novelId", "book_id"]),
                "title": self._get_field(raw_data, ["novelName", "novel_name"]),
                # "author_id": self._get_field(raw_data, ["authorId", "author_id"]),
                # "author_name": self._get_field(raw_data, ["authorName", "author_name"]),
                # "category": self._get_field(raw_data, ["novelClass", "novel_class"]),
                # "status": self._get_field(raw_data, ["novelStep", "novel_step"]),
                # "word_count": self._get_field(raw_data, ["novelSize", "novel_size"]),
                # "summary": self._get_field(raw_data, ["novelIntro", "novel_intro"]),
                # "tags": self._get_field(raw_data, ["novelTags", "novel_tags"], []),
                "clicks": self._get_field(
                    raw_data, ["novelClickCount", "novip_clicks"], 0
                ),
                "favorites": self._get_field(
                    raw_data, ["novelFavoriteCount", "novel_favorite_count"], 0
                ),
                # "chapters": self._get_field(raw_data, ["novelChapterCount", "novel_chapter_count"], 0),
                "comments": self._get_field(
                    raw_data, ["CommentCount", "comment_count"], 0
                ),
                "nutrition": self._get_field(
                    raw_data, ["nutritionNovel", "nutrition_novel"], 0
                ),
            }

            return [ParsedItem(DataType.BOOK, book_info)]

        except Exception as e:
            print(f"⚠️ 书籍数据解析失败: {e}")
            return []

    def _parse_book_basic(self, book_item: dict, position: int) -> dict:
        """解析书籍基础信息"""
        try:
            return {
                "book_id": self._get_field(book_item, ["novelId", "book_id"]),
                "title": self._get_field(book_item, ["novelName", "novel_name"]),
                "position": position,
                "clicks": self._get_field(
                    book_item, ["novelClickCount", "novel_click_count"], 0
                ),
                "favorites": self._get_field(
                    book_item, ["novelFavoriteCount", "novel_favorite_count"], 0
                ),
            }
        except Exception:
            return None

    def _get_field(
            self, data: dict, field_names: list[str], default: Any = None
    ) -> Any:
        """获取字段值，支持多种字段名"""
        for field_name in field_names:
            if field_name in data:
                return data[field_name]
        return default
