"""
统一数据解析器 - 简化版本
"""
import itertools
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils import extract_number, update_dict


class RankingParser:
    """
    榜单书籍解析
    """

    def __init__(self, page_id: str):
        self.ranking_info = {}
        self.book_snapshots: List[Dict] = []
        self.sub_rankings: List = []
        self.has_sub_ranking = False
        self.page_id = page_id

    def get_novel_ids(self) -> List[str]:
        """
        获取榜单中的所有书籍novel_id
        :return:
        """
        return [i.get("novel_id") for i in self.book_snapshots]

    def parse_ranking_info(self, raw_data: Dict, parent_ranking_info: Optional[Dict] = None):
        """
        从页面原始数据中解析出榜单数据
        :param raw_data:
        :param parent_ranking_info:
        :return:
        """
        # 构造榜单信息
        if parent_ranking_info:
            # 如果是一个嵌套榜单的子榜单，需要结合母榜单的信息构造榜单信息
            self.ranking_info = self._parse_ranking_info(raw_data, is_sub_ranking=True)
            self.ranking_info = update_dict(parent_ranking_info, self.ranking_info)

        else:
            self.ranking_info = self._parse_ranking_info(raw_data, is_sub_ranking=False)
        data_list = self._get_ranking_data(raw_data)
        if self.has_sub_ranking:
            self.sub_rankings = data_list
            return

        # 解析榜单书籍信息
        for index, book_data in enumerate(data_list):
            self.book_snapshots.append(self._parse_book_basic_info(index, book_data))

    def _get_ranking_data(self, raw_data: Dict) -> List[Dict]:
        """
        检查data结构体

        :param raw_data:
        :return:
        """

        data_list = raw_data.get("data", [])
        
        # 处理嵌套结构（如夹子榜的 data.list 格式）
        if isinstance(data_list, dict) and "list" in data_list:
            data_list = data_list["list"]
        
        # 如果data字段为空，尝试直接获取list字段
        if not data_list:
            data_list = raw_data.get("list", [])
            
        if not data_list:
            raise ValueError("该榜单中内容为空")
            
        if not isinstance(data_list, list) or not isinstance(data_list[0], dict):
            raise TypeError("响应体data结构错误")
            
        if "channelName" in data_list[0]:
            self.has_sub_ranking = True
            
        return data_list

    def _parse_ranking_info(self, raw_ranking_data: Dict, is_sub_ranking: bool = False) -> Dict[str, Any]:
        res = self._jiazi_info() if self.page_id == "jiazi" else {
            "rank_id": str(raw_ranking_data.get("rankid", "未知榜单")),
            "rank_group_type": str(raw_ranking_data.get("rank_group_type", "其他")),
            "channel_id": raw_ranking_data.get("channelMoreId", None),
            "page_id": self.page_id,
        }
        if is_sub_ranking:
            res["sub_channel_name"] = raw_ranking_data.get("channelName", "未知子榜单")
        else:
            # 确保channel_name始终有值，避免数据库NOT NULL约束错误
            # 对于jiazi页面，不覆盖_jiazi_info()中已设置的channel_name
            if self.page_id != "jiazi" or not res.get("channel_name"):
                res["channel_name"] = raw_ranking_data.get("channelName", f"{self.page_id}页面榜单")
        return res

    @staticmethod
    def _parse_book_basic_info(index: int, raw_basic_data: Dict) -> Dict:
        """
        解析书籍基础信息
        :param index:
        :param raw_basic_data:
        :return:
        """
        return {
            "position": index,
            "novel_id": raw_basic_data.get("novelId", ""),
            "title": raw_basic_data.get("novelName", ""),
            "author_id": raw_basic_data.get("authorid") or 0,  # 修复：None值设为0
            "snapshot_time": datetime.now()
        }

    @staticmethod
    def _jiazi_info() -> Dict:
        """
        夹子榜单固定信息
        :return:
        """
        return {
            "rank_id": "jiazi",
            "channel_name": "夹子相关",  # 修复缺失的channel_name字段
            "rank_group_type": "热门",   # 设置合理的默认值
            "page_id": "jiazi"
        }


class PageParser:
    """
    解析榜单页面爬取信息
    """

    def __init__(self, raw_page_data: Dict = None, page_id: str = None):
        self.rankings: List[RankingParser] = []
        if raw_page_data and page_id:
            self.parse_page_data(raw_page_data, page_id)

    def parse_page_data(self, raw_page_data: Dict, page_id: str):
        """
        解析页面数据

        :param raw_page_data:
        :param page_id:
        :return:
        """
        result = []
        data_list = raw_page_data.get("data", [])
        # 夹子页面只有夹子榜单一个
        if isinstance(data_list, dict):
            data_list = [data_list]
        for ranking_data in data_list:
            rank_info = RankingParser(page_id)
            rank_info.parse_ranking_info(ranking_data)
            if not rank_info.has_sub_ranking:
                result.append(rank_info)
                continue
            for sub_ranking_data in rank_info.sub_rankings:
                sub_rank_info = RankingParser(page_id)
                sub_rank_info.parse_ranking_info(sub_ranking_data, rank_info.ranking_info)
                result.append(sub_rank_info)
        self.rankings = result

    def get_novel_ids(self) -> List[str]:
        res = set()
        for ranking in self.rankings:
            res.update(ranking.get_novel_ids())
        return list(res)



class NovelPageParser:
    """
    解析书籍详情网页爬取信息
    """

    def __init__(self, raw_detail_data: Dict = None):
        self.book_detail = {}
        if raw_detail_data:
            self.parse_novel_info(raw_detail_data)

    def parse_novel_info(self, raw_detail_data: Dict):
        """
        解析信息
        :param raw_detail_data:
        :return:
        """
        # 安全处理clicks字段，避免None对象切片错误
        novip_clicks = raw_detail_data.get("novip_clicks", "0")
        if novip_clicks and len(str(novip_clicks)) > 4:
            clicks_value = str(novip_clicks)[:-4]
        else:
            clicks_value = str(novip_clicks) if novip_clicks else "0"
            
        self.book_detail = {
            "novel_id": raw_detail_data.get("novelId", None),
            "title": raw_detail_data.get("novelName", None),
            "author_id": raw_detail_data.get("authorId") or 0,  # 修复：None值设为0
            "status": raw_detail_data.get("series", None),
            "word_counts": raw_detail_data.get("novelSize", None),
            "chapter_counts": raw_detail_data.get("novelChapterCount", None),
            "vip_chapter_id": extract_number(raw_detail_data.get("vipChapterid", "0")),
            "favorites": raw_detail_data.get("novelbefavoritedcount", None),
            "clicks": clicks_value,
            "comments": raw_detail_data.get("comment_count", None),
            "nutrition": raw_detail_data.get("nutrition_novel", None),
            "snapshot_time": datetime.now()
        }
