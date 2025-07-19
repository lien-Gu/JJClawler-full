"""
统一数据解析器 - 简化版本
"""

from enum import Enum
from typing import Any


class DataType(Enum):
    """数据类型枚举"""

    PAGE = "page"
    RANKING = "ranking"
    BOOK = "book"


class ParsedItem:
    """解析结果项"""

    def __init__(self, data_type: DataType, data: dict):
        self.data_type = data_type
        self.data = data


class Parser:
    """统一数据解析器"""

    def parse(self, raw_data: dict, context: dict = None) -> list[ParsedItem]:
        """
        解析原始数据，自动识别数据类型

        Args:
            raw_data: 原始API响应数据
            context: 解析上下文（包含page_id等信息）

        Returns:
            解析后的数据项列表
        """
        if not raw_data:
            return []

        data_type = self._identify_data_type(raw_data)

        if data_type == DataType.PAGE:
            return self._parse_page_data(raw_data, context)
        elif data_type == DataType.RANKING:
            return self._parse_ranking_data(raw_data, context)
        elif data_type == DataType.BOOK:
            return self._parse_book_data(raw_data)

        return []

    def _identify_data_type(self, data: dict) -> DataType:
        """识别数据类型"""
        if not isinstance(data, dict):
            return DataType.PAGE

        # 检查是否为夹子榜数据（直接在data字段中有list）
        if "data" in data and isinstance(data["data"], dict):
            if "list" in data["data"]:
                return DataType.RANKING

        # 检查是否为页面数据（两种结构）
        # 结构1: content.data结构（旧版本）
        content = data.get("content", {})
        if isinstance(content, dict) and "data" in content:
            if isinstance(content["data"], list):
                return DataType.PAGE

        # 结构2: 直接data结构（新版本index页面）
        if "data" in data and isinstance(data["data"], list):
            # 检查data数组中的第一个元素是否有榜单特征
            data_list = data["data"]
            if data_list and isinstance(data_list[0], dict):
                if "rankid" in data_list[0] and "channelName" in data_list[0]:
                    return DataType.PAGE

        # 检查是否为书籍详情数据
        if "novelId" in data or "book_id" in data:
            return DataType.BOOK

        # 默认返回页面类型
        return DataType.PAGE

    def _parse_page_data(
        self, raw_data: dict, context: dict = None
    ) -> list[ParsedItem]:
        """解析页面数据"""
        try:
            # 支持两种数据结构
            # 结构1: content.data（旧版本）
            data_list = raw_data.get("content", {}).get("data", [])
            # 结构2: 直接data（新版本index页面）
            if not data_list:
                data_list = raw_data.get("data", [])

            parsed_items = []

            for ranking_data in data_list:
                # 处理榜单基础信息
                rank_id = ranking_data.get("rankid")
                rank_name = ranking_data.get("channelName")
                rank_group_type = ranking_data.get("rank_group_type")

                # 如果没有rank_group_type，尝试从rank_id推导
                if not rank_group_type and rank_id:
                    rank_group_type = rank_id

                # 从上下文获取page_id，如果没有则使用默认值
                page_id = "index"  # 默认值
                if context and "page_id" in context:
                    page_id = context["page_id"]

                # 检查是否为嵌套榜单
                nested_rankings = ranking_data.get("data", [])
                if nested_rankings and "channelName" in nested_rankings[0]:
                    # 这是嵌套榜单结构，处理子榜单
                    for idx, sub_ranking in enumerate(nested_rankings):
                        sub_rank_id = sub_ranking.get("rankid")
                        sub_rank_name = sub_ranking.get("channelName")

                        # 如果子榜单没有channelName，跳过
                        if not sub_rank_name:
                            continue

                        # 生成唯一的rank_id：如果没有sub_rank_id，则使用父榜单ID + 索引
                        if not sub_rank_id:
                            if isinstance(rank_id, list):
                                # 如果父榜单ID是列表，使用列表中的第一个
                                base_id = rank_id[0] if rank_id else "0"
                            else:
                                base_id = rank_id if rank_id else "0"
                            # 生成唯一的字符串ID：父榜单ID + "_" + 索引
                            sub_rank_id = f"{base_id}_{idx}"
                        else:
                            # 确保sub_rank_id是字符串类型
                            sub_rank_id = str(sub_rank_id)

                        sub_ranking_info = {
                            "rank_id": sub_rank_id,
                            "rank_name": rank_name,  # 使用父榜单名称作为主榜单名称
                            "rank_group_type": rank_group_type,
                            "page_id": page_id,
                            "sub_ranking_name": sub_rank_name,  # 设置子榜单名称
                            "books": [],
                        }

                        # 解析子榜单中的书籍
                        sub_books_data = sub_ranking.get("data", [])
                        for position, book_item in enumerate(sub_books_data, 1):
                            book_info = self._parse_book_basic(book_item, position)
                            if book_info:
                                sub_ranking_info["books"].append(book_info)

                        # 只有当子榜单信息完整时才添加
                        if sub_rank_id and sub_rank_name:
                            parsed_items.append(
                                ParsedItem(DataType.RANKING, sub_ranking_info)
                            )
                else:
                    # 常规榜单结构
                    # 确保rank_id是字符串类型
                    rank_id = str(rank_id) if rank_id else "0"

                    ranking_info = {
                        "rank_id": rank_id,
                        "rank_name": rank_name,
                        "rank_group_type": rank_group_type,
                        "page_id": page_id,
                        "books": [],
                    }

                    # 解析榜单中的书籍
                    books_data = ranking_data.get("data", [])
                    for position, book_item in enumerate(books_data, 1):
                        book_info = self._parse_book_basic(book_item, position)
                        if book_info:
                            ranking_info["books"].append(book_info)

                    # 只有当榜单信息完整时才添加
                    if rank_id and rank_name:
                        parsed_items.append(ParsedItem(DataType.RANKING, ranking_info))

            return parsed_items

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
