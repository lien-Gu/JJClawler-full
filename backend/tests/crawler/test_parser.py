"""
数据解析器单元测试

测试 app.modules.crawler.parser 模块的所有功能
"""
import pytest
from datetime import datetime
from app.modules.crawler.parser import DataParser
from app.modules.models import Book, BookSnapshot


class TestJiaziDataParsing:
    """夹子榜数据解析测试"""
    
    def test_parse_jiazi_data_success(self, sample_jiazi_response_data):
        """测试成功解析夹子榜数据"""
        books, snapshots = DataParser.parse_jiazi_data(sample_jiazi_response_data)
        
        # 验证解析结果数量
        assert len(books) == 3
        assert len(snapshots) == 3
        
        # 验证第一本书的数据
        first_book = books[0]
        assert first_book.book_id == "5485513"
        assert first_book.title == "重生九零：福运娇妻美又飒"
        assert first_book.author_name == "青丝如墨"
        assert first_book.novel_class == "言情"
        assert first_book.tags == "现代,重生,系统,甜文"
        
        # 验证第一个快照的数据
        first_snapshot = snapshots[0]
        assert first_snapshot.book_id == "5485513"
        assert first_snapshot.total_clicks == 1256000  # 125.6万
        assert first_snapshot.total_favorites == 452000  # 45.2万
    
    def test_parse_jiazi_data_success_manual(self):
        """测试成功解析夹子榜数据（手动数据）"""
        raw_data = {
            "code": "200",
            "data": {
                "list": [
                    {
                        "novelId": "123456",
                        "novelName": "测试小说1",
                        "authorId": "789",
                        "authorName": "测试作者1",
                        "novelClass": "言情",
                        "tags": "现代,都市",
                        "totalClicks": "10000",
                        "totalFavorites": "5000",
                        "commentCount": "200",
                        "chapterCount": "100"
                    },
                    {
                        "novelId": "654321",
                        "novelName": "测试小说2",
                        "authorId": "987",
                        "authorName": "测试作者2",
                        "novelClass": "纯爱",
                        "tags": "古代,宫廷",
                        "totalClicks": "8000",
                        "totalFavorites": "3000",
                        "commentCount": "150",
                        "chapterCount": "80"
                    }
                ]
            }
        }
        
        books, snapshots = DataParser.parse_jiazi_data(raw_data)
        
        # 验证书籍数据
        assert len(books) == 2
        assert books[0].book_id == "123456"
        assert books[0].title == "测试小说1"
        assert books[0].author_id == "789"
        assert books[0].author_name == "测试作者1"
        assert books[0].novel_class == "言情"
        assert books[0].tags == "现代,都市"
        
        assert books[1].book_id == "654321"
        assert books[1].title == "测试小说2"
        
        # 验证快照数据
        assert len(snapshots) == 2
        assert snapshots[0].book_id == "123456"
        assert snapshots[0].total_clicks == 10000
        assert snapshots[0].total_favorites == 5000
        assert snapshots[0].comment_count == 200
        assert snapshots[0].chapter_count == 100
        
        assert snapshots[1].book_id == "654321"
        assert snapshots[1].total_clicks == 8000
    
    def test_parse_jiazi_data_api_error(self):
        """测试API返回错误"""
        raw_data = {
            "code": "500",
            "message": "服务器内部错误"
        }
        
        with pytest.raises(ValueError, match="API响应错误: 服务器内部错误"):
            DataParser.parse_jiazi_data(raw_data)
    
    def test_parse_jiazi_data_api_error_no_message(self):
        """测试API返回错误但没有消息"""
        raw_data = {
            "code": "404"
        }
        
        with pytest.raises(ValueError, match="API响应错误: 未知错误"):
            DataParser.parse_jiazi_data(raw_data)
    
    def test_parse_jiazi_data_empty_list(self):
        """测试空的书籍列表"""
        raw_data = {
            "code": "200",
            "data": {
                "list": []
            }
        }
        
        books, snapshots = DataParser.parse_jiazi_data(raw_data)
        
        assert books == []
        assert snapshots == []
    
    def test_parse_jiazi_data_missing_data_section(self):
        """测试缺少data部分"""
        raw_data = {
            "code": "200"
        }
        
        books, snapshots = DataParser.parse_jiazi_data(raw_data)
        
        assert books == []
        assert snapshots == []
    
    def test_parse_jiazi_data_missing_list(self):
        """测试缺少list部分"""
        raw_data = {
            "code": "200",
            "data": {}
        }
        
        books, snapshots = DataParser.parse_jiazi_data(raw_data)
        
        assert books == []
        assert snapshots == []


class TestPageDataParsing:
    """分类页面数据解析测试"""
    
    def test_parse_page_data_single_list_structure(self, sample_single_list_response_data):
        """测试单一列表结构"""
        books, snapshots = DataParser.parse_page_data(sample_single_list_response_data)
        
        assert len(books) == 2
        assert len(snapshots) == 2
        
        # 验证第一本书
        first_book = books[0]
        assert first_book.book_id == "6001234"
        assert first_book.title == "纯爱校园文"
        assert first_book.novel_class == "纯爱"
        
    def test_parse_page_data_single_list_structure_manual(self):
        """测试单一列表结构（手动数据）"""
        raw_data = {
            "code": "200",
            "data": {
                "list": [
                    {
                        "novelId": "111",
                        "novelName": "言情小说",
                        "authorId": "222",
                        "authorName": "言情作者",
                        "totalClicks": "15000",
                        "totalFavorites": "7000"
                    }
                ]
            }
        }
        
        books, snapshots = DataParser.parse_page_data(raw_data)
        
        assert len(books) == 1
        assert books[0].book_id == "111"
        assert books[0].title == "言情小说"
        
        assert len(snapshots) == 1
        assert snapshots[0].book_id == "111"
        assert snapshots[0].total_clicks == 15000
    
    def test_parse_page_data_blocks_structure(self):
        """测试多区块结构"""
        raw_data = {
            "code": "200",
            "data": {
                "blocks": [
                    {
                        "name": "热门榜",
                        "list": [
                            {
                                "novelId": "333",
                                "novelName": "热门小说1",
                                "authorId": "444",
                                "authorName": "热门作者1",
                                "totalClicks": "20000",
                                "totalFavorites": "10000"
                            }
                        ]
                    },
                    {
                        "name": "新书榜",
                        "list": [
                            {
                                "novelId": "555",
                                "novelName": "新书小说1",
                                "authorId": "666",
                                "authorName": "新书作者1",
                                "totalClicks": "5000",
                                "totalFavorites": "2000"
                            },
                            {
                                "novelId": "777",
                                "novelName": "新书小说2",
                                "authorId": "888",
                                "authorName": "新书作者2",
                                "totalClicks": "3000",
                                "totalFavorites": "1000"
                            }
                        ]
                    }
                ]
            }
        }
        
        books, snapshots = DataParser.parse_page_data(raw_data)
        
        # 应该包含所有区块的书籍
        assert len(books) == 3
        assert books[0].book_id == "333"
        assert books[1].book_id == "555"
        assert books[2].book_id == "777"
        
        assert len(snapshots) == 3
        assert snapshots[0].total_clicks == 20000
        assert snapshots[1].total_clicks == 5000
        assert snapshots[2].total_clicks == 3000
    
    def test_parse_page_data_blocks_no_list(self):
        """测试区块中没有list"""
        raw_data = {
            "code": "200",
            "data": {
                "blocks": [
                    {
                        "name": "空区块"
                        # 没有list字段
                    },
                    {
                        "name": "有效区块",
                        "list": [
                            {
                                "novelId": "999",
                                "novelName": "有效小说",
                                "authorId": "000",
                                "authorName": "有效作者",
                                "totalClicks": "1000",
                                "totalFavorites": "500"
                            }
                        ]
                    }
                ]
            }
        }
        
        books, snapshots = DataParser.parse_page_data(raw_data)
        
        # 应该只包含有效区块的书籍
        assert len(books) == 1
        assert books[0].book_id == "999"
    
    def test_parse_page_data_unrecognized_structure(self):
        """测试未识别的数据结构"""
        raw_data = {
            "code": "200",
            "data": {
                "unknown_structure": {}
            }
        }
        
        books, snapshots = DataParser.parse_page_data(raw_data)
        
        assert books == []
        assert snapshots == []
    
    def test_parse_page_data_api_error(self):
        """测试API错误"""
        raw_data = {
            "code": "403",
            "message": "访问被拒绝"
        }
        
        with pytest.raises(ValueError, match="API响应错误: 访问被拒绝"):
            DataParser.parse_page_data(raw_data)


class TestBookInfoParsing:
    """书籍信息解析测试"""
    
    def test_parse_book_info_success(self):
        """测试成功解析书籍信息"""
        item = {
            "novelId": "12345",
            "novelName": "测试小说",
            "authorId": "67890",
            "authorName": "测试作者",
            "novelClass": "言情",
            "tags": "现代,都市,豪门"
        }
        
        book = DataParser._parse_book_info(item)
        
        assert book.book_id == "12345"
        assert book.title == "测试小说"
        assert book.author_id == "67890"
        assert book.author_name == "测试作者"
        assert book.novel_class == "言情"
        assert book.tags == "现代,都市,豪门"
        assert isinstance(book.first_seen, datetime)
        assert isinstance(book.last_updated, datetime)
    
    def test_parse_book_info_alternative_field_names(self):
        """测试备用字段名"""
        item = {
            "novelid": "11111",  # 小写
            "novelname": "备用字段小说",  # 小写
            "authorid": "22222",  # 小写
            "authorname": "备用字段作者",  # 小写
            "novelclass": "纯爱",  # 小写
            "tags": "古代,宫廷"
        }
        
        book = DataParser._parse_book_info(item)
        
        assert book.book_id == "11111"
        assert book.title == "备用字段小说"
        assert book.author_id == "22222"
        assert book.author_name == "备用字段作者"
        assert book.novel_class == "纯爱"
    
    def test_parse_book_info_missing_required_fields(self):
        """测试缺少必需字段"""
        # 缺少book_id
        item1 = {
            "novelName": "无ID小说",
            "authorId": "123",
            "authorName": "作者"
        }
        
        with pytest.raises(ValueError, match="书籍数据不完整"):
            DataParser._parse_book_info(item1)
        
        # 缺少title
        item2 = {
            "novelId": "123",
            "authorId": "456",
            "authorName": "作者"
        }
        
        with pytest.raises(ValueError, match="书籍数据不完整"):
            DataParser._parse_book_info(item2)
    
    def test_parse_book_info_empty_strings(self):
        """测试空字符串字段"""
        item = {
            "novelId": "12345",
            "novelName": "  测试小说  ",  # 有空格
            "authorId": "",  # 空字符串
            "authorName": "  测试作者  ",  # 有空格
            "novelClass": "",  # 空字符串
            "tags": "  现代,都市  "  # 有空格
        }
        
        book = DataParser._parse_book_info(item)
        
        assert book.title == "测试小说"  # 应该去除空格
        assert book.author_id == ""
        assert book.author_name == "测试作者"  # 应该去除空格
        assert book.novel_class == ""
        assert book.tags == "现代,都市"  # 应该去除空格
    
    def test_parse_book_info_none_values(self):
        """测试None值"""
        item = {
            "novelId": "12345",
            "novelName": "测试小说",
            "authorId": None,
            "authorName": None,
            "novelClass": None,
            "tags": None
        }
        
        book = DataParser._parse_book_info(item)
        
        assert book.book_id == "12345"
        assert book.title == "测试小说"
        assert book.author_id == ""  # None应该转为空字符串
        assert book.author_name == ""
        assert book.novel_class == ""
        assert book.tags == ""


class TestBookSnapshotParsing:
    """书籍快照解析测试"""
    
    def test_parse_book_snapshot_success(self):
        """测试成功解析书籍快照"""
        item = {
            "novelId": "12345",
            "totalClicks": "10000",
            "totalFavorites": "5000",
            "commentCount": "200",
            "chapterCount": "100"
        }
        snapshot_time = datetime(2024, 1, 1, 12, 0, 0)
        
        snapshot = DataParser._parse_book_snapshot(item, snapshot_time)
        
        assert snapshot.book_id == "12345"
        assert snapshot.total_clicks == 10000
        assert snapshot.total_favorites == 5000
        assert snapshot.comment_count == 200
        assert snapshot.chapter_count == 100
        assert snapshot.snapshot_time == snapshot_time
    
    def test_parse_book_snapshot_alternative_field_names(self):
        """测试备用字段名"""
        item = {
            "novelid": "11111",  # 小写
            "totalclicks": "8000",  # 小写
            "totalfavorites": "4000",  # 小写
            "commentcount": "150",  # 小写
            "chaptercount": "80"  # 小写
        }
        snapshot_time = datetime(2024, 1, 1, 12, 0, 0)
        
        snapshot = DataParser._parse_book_snapshot(item, snapshot_time)
        
        assert snapshot.book_id == "11111"
        assert snapshot.total_clicks == 8000
        assert snapshot.total_favorites == 4000
        assert snapshot.comment_count == 150
        assert snapshot.chapter_count == 80
    
    def test_parse_book_snapshot_missing_fields(self):
        """测试缺少字段时使用默认值"""
        item = {
            "novelId": "12345"
            # 缺少所有统计字段
        }
        snapshot_time = datetime(2024, 1, 1, 12, 0, 0)
        
        snapshot = DataParser._parse_book_snapshot(item, snapshot_time)
        
        assert snapshot.book_id == "12345"
        assert snapshot.total_clicks == 0
        assert snapshot.total_favorites == 0
        assert snapshot.comment_count == 0
        assert snapshot.chapter_count == 0


class TestNumericFieldParsing:
    """数值字段解析测试"""
    
    def test_parse_numeric_field_with_test_cases(self, numeric_field_test_cases):
        """测试使用预定义测试用例解析数值字段"""
        from app.modules.crawler.parser import DataParser
        
        for input_value, expected_result in numeric_field_test_cases:
            test_item = {"test_field": input_value}
            result = DataParser._parse_numeric_field(test_item, ["test_field"], 0)
            assert result == expected_result, f"输入: '{input_value}', 期望: {expected_result}, 实际: {result}"
    
    def test_parse_numeric_field_simple_numbers(self):
        """测试简单数字"""
        item = {"field1": "123", "field2": "456"}
        
        result = DataParser._parse_numeric_field(item, ["field1"], 0)
        assert result == 123
        
        result = DataParser._parse_numeric_field(item, ["field2"], 0)
        assert result == 456
    
    def test_parse_numeric_field_with_commas(self):
        """测试带逗号的数字"""
        item = {"clicks": "1,234,567"}
        
        result = DataParser._parse_numeric_field(item, ["clicks"], 0)
        assert result == 1234567
    
    def test_parse_numeric_field_wan_format(self):
        """测试"万"格式"""
        item = {
            "field1": "1万",
            "field2": "5万",
            "field3": "10万"
        }
        
        assert DataParser._parse_numeric_field(item, ["field1"], 0) == 10000
        assert DataParser._parse_numeric_field(item, ["field2"], 0) == 50000
        assert DataParser._parse_numeric_field(item, ["field3"], 0) == 100000
    
    def test_parse_numeric_field_decimal_wan_format(self):
        """测试小数"万"格式"""
        item = {
            "field1": "1.5万",
            "field2": "2.3万",
            "field3": "0.8万"
        }
        
        assert DataParser._parse_numeric_field(item, ["field1"], 0) == 15000
        assert DataParser._parse_numeric_field(item, ["field2"], 0) == 23000
        assert DataParser._parse_numeric_field(item, ["field3"], 0) == 8000
    
    def test_parse_numeric_field_qian_format(self):
        """测试"千"格式"""
        item = {
            "field1": "1千",
            "field2": "5千",
            "field3": "10千"
        }
        
        assert DataParser._parse_numeric_field(item, ["field1"], 0) == 1000
        assert DataParser._parse_numeric_field(item, ["field2"], 0) == 5000
        assert DataParser._parse_numeric_field(item, ["field3"], 0) == 10000
    
    def test_parse_numeric_field_multiple_field_names(self):
        """测试多个字段名"""
        item = {
            "totalClicks": "1000",
            "total_clicks": "2000",
            "clicks": "3000"
        }
        
        # 应该返回找到的第一个字段的值
        result = DataParser._parse_numeric_field(item, ["totalClicks", "total_clicks", "clicks"], 0)
        assert result == 1000
        
        # 如果第一个字段不存在，使用第二个
        result = DataParser._parse_numeric_field(item, ["nonexistent", "total_clicks", "clicks"], 0)
        assert result == 2000
    
    def test_parse_numeric_field_invalid_values(self):
        """测试无效值"""
        item = {
            "field1": "abc",
            "field2": "",
            "field3": None,
            "field4": "1000"
        }
        
        # 无效值应该跳过，使用下一个字段或默认值
        result = DataParser._parse_numeric_field(item, ["field1", "field2", "field3", "field4"], 999)
        assert result == 1000
        
        # 所有字段都无效时使用默认值
        result = DataParser._parse_numeric_field(item, ["field1", "field2", "field3"], 999)
        assert result == 999
    
    def test_parse_numeric_field_field_not_found(self):
        """测试字段不存在"""
        item = {"other_field": "123"}
        
        result = DataParser._parse_numeric_field(item, ["nonexistent"], 999)
        assert result == 999
    
    def test_parse_numeric_field_integer_values(self):
        """测试整数值（非字符串）"""
        item = {
            "field1": 123,
            "field2": 456.78
        }
        
        assert DataParser._parse_numeric_field(item, ["field1"], 0) == 123
        assert DataParser._parse_numeric_field(item, ["field2"], 0) == 456


class TestParsingErrorHandling:
    """解析错误处理测试"""
    
    def test_parse_jiazi_data_invalid_book_data(self):
        """测试无效的书籍数据"""
        raw_data = {
            "code": "200",
            "data": {
                "list": [
                    {
                        "novelId": "123",
                        "novelName": "有效小说",
                        "authorId": "456",
                        "authorName": "有效作者"
                    },
                    {
                        # 缺少必需字段的无效数据
                        "novelName": "无效小说"
                    }
                ]
            }
        }
        
        with pytest.raises(ValueError, match="书籍数据不完整"):
            DataParser.parse_jiazi_data(raw_data)
    
    def test_parse_page_data_invalid_book_data(self):
        """测试分类页面解析中的无效书籍数据"""
        raw_data = {
            "code": "200",
            "data": {
                "list": [
                    {
                        "novelId": "123",
                        "novelName": "有效小说",
                        "authorId": "456",
                        "authorName": "有效作者"
                    },
                    {
                        # 缺少必需字段的无效数据
                        "authorId": "789"
                    }
                ]
            }
        }
        
        with pytest.raises(ValueError, match="书籍数据不完整"):
            DataParser.parse_page_data(raw_data)
    
    def test_parse_complex_numeric_formats(self):
        """测试复杂的数字格式"""
        item = {
            "field1": "1.23万",
            "field2": "45.67万",
            "field3": "0.1万",
            "field4": "100.0万"
        }
        
        assert DataParser._parse_numeric_field(item, ["field1"], 0) == 12300
        assert DataParser._parse_numeric_field(item, ["field2"], 0) == 456700
        assert DataParser._parse_numeric_field(item, ["field3"], 0) == 1000
        assert DataParser._parse_numeric_field(item, ["field4"], 0) == 1000000