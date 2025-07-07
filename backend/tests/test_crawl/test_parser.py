"""
解析器测试
"""
from typing import Dict, Any

from app.crawl.parser import DataType, ParsedItem


class TestParser:
    """解析器测试类"""

    def test_init(self, real_parser):
        """测试解析器初始化"""
        assert real_parser is not None

    def test_identify_data_type_page(self, real_parser, mock_page_response: Dict[str, Any]):
        """测试识别页面数据类型"""
        data_type = real_parser._identify_data_type(mock_page_response)
        assert data_type == DataType.PAGE

    def test_identify_data_type_ranking(self, real_parser, mock_jiazi_response: Dict[str, Any]):
        """测试识别榜单数据类型"""
        data_type = real_parser._identify_data_type(mock_jiazi_response)
        assert data_type == DataType.RANKING

    def test_identify_data_type_book(self, real_parser, mock_book_detail_response: Dict[str, Any]):
        """测试识别书籍数据类型"""
        data_type = real_parser._identify_data_type(mock_book_detail_response)
        assert data_type == DataType.BOOK

    def test_identify_data_type_default(self, real_parser):
        """测试默认数据类型识别"""
        data_type = real_parser._identify_data_type({"unknown": "data"})
        assert data_type == DataType.PAGE

    def test_identify_data_type_invalid_input(self, real_parser):
        """测试无效输入的数据类型识别"""
        data_type = real_parser._identify_data_type("invalid")
        assert data_type == DataType.PAGE

    def test_parse_empty_data(self, real_parser):
        """测试解析空数据"""
        result = real_parser.parse({})
        assert result == []

    def test_parse_none_data(self, real_parser):
        """测试解析None数据"""
        result = real_parser.parse(None)
        assert result == []

    def test_parse_page_data(self, real_parser, mock_page_response: Dict[str, Any]):
        """测试解析页面数据"""
        result = real_parser.parse(mock_page_response)
        
        assert len(result) == 1
        assert result[0].data_type == DataType.RANKING
        
        ranking_data = result[0].data
        assert ranking_data["rank_id"] == 1001
        assert ranking_data["rank_name"] == "言情榜单"
        assert ranking_data["rank_group_type"] == "romance"
        assert len(ranking_data["books"]) == 2
        
        # 检查第一本书
        book1 = ranking_data["books"][0]
        assert book1["book_id"] == 12345
        assert book1["title"] == "测试小说1"
        assert book1["position"] == 1
        assert book1["clicks"] == 1000
        assert book1["favorites"] == 500

    def test_parse_jiazi_data(self, real_parser, mock_jiazi_response: Dict[str, Any]):
        """测试解析夹子榜数据"""
        result = real_parser.parse(mock_jiazi_response)
        
        assert len(result) == 1
        assert result[0].data_type == DataType.RANKING
        
        ranking_data = result[0].data
        assert ranking_data["rank_id"] == "jiazi"
        assert ranking_data["rank_name"] == "夹子榜"
        assert len(ranking_data["books"]) == 2
        
        # 检查书籍数据
        book1 = ranking_data["books"][0]
        assert book1["book_id"] == 11111
        assert book1["title"] == "夹子榜小说1"

    def test_parse_book_data(self, real_parser, mock_book_detail_response: Dict[str, Any]):
        """测试解析书籍详情数据"""
        result = real_parser.parse(mock_book_detail_response)
        
        assert len(result) == 1
        assert result[0].data_type == DataType.BOOK
        
        book_data = result[0].data
        assert book_data["novel_id"] == 12345
        assert book_data["title"] == "测试小说详情"
        assert book_data["clicks"] == 10000
        assert book_data["favorites"] == 5000
        assert book_data["comments"] == 200
        assert book_data["nutrition"] == 95

    def test_parse_page_data_empty_content(self, real_parser):
        """测试解析空内容的页面数据"""
        empty_page = {"content": {"data": []}}
        result = real_parser.parse(empty_page)
        assert result == []

    def test_parse_page_data_missing_content(self, real_parser):
        """测试解析缺少内容的页面数据"""
        incomplete_page = {"some_other_field": "value"}
        result = real_parser.parse(incomplete_page)
        assert result == []

    def test_parse_jiazi_data_empty_list(self, real_parser):
        """测试解析空列表的夹子榜数据"""
        empty_jiazi = {"list": []}
        result = real_parser.parse(empty_jiazi)
        
        assert len(result) == 1
        assert result[0].data_type == DataType.RANKING
        ranking_data = result[0].data
        assert ranking_data["rank_id"] == "jiazi"
        assert len(ranking_data["books"]) == 0

    def test_parse_book_basic_complete_data(self, real_parser):
        """测试解析完整的书籍基础信息"""
        book_item = {
            "novelId": 12345,
            "novelName": "测试小说",
            "novelClickCount": 1000,
            "novelFavoriteCount": 500
        }
        result = real_parser._parse_book_basic(book_item, 1)
        
        assert result["book_id"] == 12345
        assert result["title"] == "测试小说"
        assert result["position"] == 1
        assert result["clicks"] == 1000
        assert result["favorites"] == 500

    def test_parse_book_basic_missing_fields(self, real_parser):
        """测试解析缺少字段的书籍基础信息"""
        book_item = {"novelId": 12345}
        result = real_parser._parse_book_basic(book_item, 1)
        
        assert result["book_id"] == 12345
        assert result["title"] is None
        assert result["position"] == 1
        assert result["clicks"] == 0
        assert result["favorites"] == 0

    def test_parse_book_basic_invalid_data(self, real_parser):
        """测试解析无效的书籍基础信息"""
        result = real_parser._parse_book_basic(None, 1)
        assert result is None

    def test_get_field_first_match(self, real_parser):
        """测试获取字段值 - 第一个匹配"""
        data = {"field1": "value1", "field2": "value2"}
        result = real_parser._get_field(data, ["field1", "field2"])
        assert result == "value1"

    def test_get_field_second_match(self, real_parser):
        """测试获取字段值 - 第二个匹配"""
        data = {"field2": "value2"}
        result = real_parser._get_field(data, ["field1", "field2"])
        assert result == "value2"

    def test_get_field_no_match(self, real_parser):
        """测试获取字段值 - 无匹配"""
        data = {"other_field": "value"}
        result = real_parser._get_field(data, ["field1", "field2"])
        assert result is None

    def test_get_field_with_default(self, real_parser):
        """测试获取字段值 - 使用默认值"""
        data = {"other_field": "value"}
        result = real_parser._get_field(data, ["field1", "field2"], "default")
        assert result == "default"

    def test_get_field_empty_field_names(self, real_parser):
        """测试获取字段值 - 空字段名列表"""
        data = {"field1": "value1"}
        result = real_parser._get_field(data, [])
        assert result is None


class TestParsedItem:
    """解析结果项测试类"""

    def test_parsed_item_creation(self):
        """测试创建解析结果项"""
        data = {"test": "data"}
        item = ParsedItem(DataType.BOOK, data)
        
        assert item.data_type == DataType.BOOK
        assert item.data == data

    def test_parsed_item_page_type(self):
        """测试页面类型的解析结果项"""
        data = {"page": "data"}
        item = ParsedItem(DataType.PAGE, data)
        
        assert item.data_type == DataType.PAGE
        assert item.data == data

    def test_parsed_item_ranking_type(self):
        """测试榜单类型的解析结果项"""
        data = {"ranking": "data"}
        item = ParsedItem(DataType.RANKING, data)
        
        assert item.data_type == DataType.RANKING
        assert item.data == data


class TestDataType:
    """数据类型枚举测试类"""

    def test_data_type_values(self):
        """测试数据类型枚举值"""
        assert DataType.PAGE.value == "page"
        assert DataType.RANKING.value == "ranking"
        assert DataType.BOOK.value == "book"

    def test_data_type_comparison(self):
        """测试数据类型比较"""
        assert DataType.PAGE != DataType.RANKING
        assert DataType.RANKING != DataType.BOOK
        assert DataType.PAGE == DataType.PAGE