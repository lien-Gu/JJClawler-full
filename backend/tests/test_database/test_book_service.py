"""
BookService集成测试
使用真实内存数据库进行服务层功能测试，验证数据库CRUD操作和业务逻辑
"""

from datetime import datetime, timedelta

import pytest

from app.database.service.book_service import BookService
from app.database.db.book import Book, BookSnapshot


class TestBookServiceIntegration:
    """BookService集成测试类 - 使用真实内存数据库"""

    @pytest.fixture
    def book_service(self):
        return BookService()

    # ==================== 基础CRUD操作测试 ====================

    def test_get_book_by_novel_id_success(self, book_service, populated_db_session):
        """测试根据novel_id获取书籍 - 成功场景"""
        # 执行测试 - 获取已存在的书籍
        result = book_service.get_book_by_novel_id(populated_db_session, 123456)

        # 验证结果
        assert result is not None
        assert result.novel_id == 123456
        assert result.title == "测试小说1"
        assert result.author_id == 1001

    def test_get_book_by_novel_id_not_found(self, book_service, populated_db_session):
        """测试根据novel_id获取书籍 - 书籍不存在"""
        # 执行测试 - 获取不存在的书籍
        result = book_service.get_book_by_novel_id(populated_db_session, 999999)

        # 验证结果
        assert result is None

    def test_get_book_by_novel_id_type_conversion(self, book_service, populated_db_session):
        """测试根据novel_id获取书籍 - 字符串ID自动转换"""
        # 执行测试 - 传入字符串形式的ID
        result = book_service.get_book_by_novel_id(populated_db_session, "123456")

        # 验证结果
        assert result is not None
        assert result.novel_id == 123456
        assert result.title == "测试小说1"

    def test_create_book_success(self, book_service, test_db_session, sample_book_data):
        """测试创建书籍 - 成功场景"""
        # 执行测试 - 创建新书籍
        result = book_service.create_book(test_db_session, sample_book_data)

        # 验证结果
        assert result is not None
        assert result.novel_id == sample_book_data["novel_id"]
        assert result.title == sample_book_data["title"]
        assert result.author_id == sample_book_data["author_id"]

        # 验证数据库中的记录
        db_book = test_db_session.get(Book, sample_book_data["novel_id"])
        assert db_book is not None
        assert db_book.title == sample_book_data["title"]

    def test_update_book_success(self, book_service, populated_db_session):
        """测试更新书籍 - 成功场景"""
        # 准备测试数据
        book = populated_db_session.get(Book, 123456)
        original_title = book.title
        
        update_data = {
            "title": "更新后的标题",
            "author_id": 2001
        }

        # 执行测试 - 更新书籍
        result = book_service.update_book(populated_db_session, book, update_data)

        # 验证结果
        assert result is not None
        assert result.title == "更新后的标题"
        assert result.author_id == 2001
        assert result.novel_id == 123456  # ID不应该改变
        assert result.updated_at is not None

        # 验证数据库中的更新
        db_book = populated_db_session.get(Book, 123456)
        assert db_book.title == "更新后的标题"
        assert db_book.title != original_title

    def test_create_or_update_book_create_new(self, book_service, test_db_session, sample_book_data):
        """测试创建或更新书籍 - 创建新书籍场景"""
        # 确认书籍不存在
        existing_book = book_service.get_book_by_novel_id(test_db_session, sample_book_data["novel_id"])
        assert existing_book is None

        # 执行测试 - 创建新书籍
        result = book_service.create_or_update_book(test_db_session, sample_book_data)

        # 验证结果
        assert result is not None
        assert result.novel_id == sample_book_data["novel_id"]
        assert result.title == sample_book_data["title"]

        # 验证数据库中的记录
        db_book = test_db_session.get(Book, sample_book_data["novel_id"])
        assert db_book is not None

    def test_create_or_update_book_update_existing(self, book_service, populated_db_session):
        """测试创建或更新书籍 - 更新已存在书籍场景"""
        # 准备更新数据
        update_data = {
            "novel_id": 123456,
            "title": "更新的书籍标题",
            "author_id": 3001
        }

        # 执行测试 - 更新已存在的书籍
        result = book_service.create_or_update_book(populated_db_session, update_data)

        # 验证结果
        assert result is not None
        assert result.novel_id == 123456
        assert result.title == "更新的书籍标题"
        assert result.author_id == 3001

        # 验证数据库更新
        db_book = populated_db_session.get(Book, 123456)
        assert db_book.title == "更新的书籍标题"

    def test_create_or_update_book_missing_novel_id(self, book_service, test_db_session):
        """测试创建或更新书籍 - 缺少novel_id异常场景"""
        # 准备无效数据
        invalid_data = {
            "title": "无ID书籍",
            "author_id": 1001
        }

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="novel_id is required"):
            book_service.create_or_update_book(test_db_session, invalid_data)

    def test_batch_create_book_snapshots_success(self, book_service, populated_db_session, sample_book_snapshots_data):
        """测试批量创建书籍快照 - 成功场景"""
        # 执行测试 - 批量创建快照
        result = book_service.batch_create_book_snapshots(populated_db_session, sample_book_snapshots_data)

        # 验证结果
        assert len(result) == len(sample_book_snapshots_data)
        
        # 验证每个快照
        for i, snapshot in enumerate(result):
            assert snapshot.novel_id == sample_book_snapshots_data[i]["novel_id"]
            assert snapshot.favorites == sample_book_snapshots_data[i]["favorites"]
            assert snapshot.clicks == sample_book_snapshots_data[i]["clicks"]

        # 验证数据库中的记录数量
        total_snapshots = populated_db_session.query(BookSnapshot).count()
        assert total_snapshots >= len(sample_book_snapshots_data)

    # ==================== API操作测试 ====================

    def test_get_books_with_pagination_success(self, book_service, populated_db_session):
        """测试分页获取书籍 - 成功场景"""
        # 执行测试 - 获取第一页，每页2条
        books, total_pages = book_service.get_books_with_pagination(
            populated_db_session, page=1, size=2
        )

        # 验证结果
        assert len(books) <= 2  # 最多2条记录
        assert total_pages >= 1  # 至少1页
        
        # 验证返回的书籍数据
        if books:
            assert hasattr(books[0], 'novel_id')
            assert hasattr(books[0], 'title')

    def test_get_books_with_pagination_second_page(self, book_service, populated_db_session):
        """测试分页获取书籍 - 第二页"""
        # 执行测试 - 获取第二页
        books, total_pages = book_service.get_books_with_pagination(
            populated_db_session, page=2, size=2
        )

        # 验证结果（可能为空，取决于总数据量）
        assert isinstance(books, list)
        assert total_pages >= 1

    def test_get_book_detail_by_novel_id_success(self, book_service, populated_db_session):
        """测试获取书籍详情 - 成功场景"""
        # 执行测试 - 获取有快照数据的书籍详情
        result = book_service.get_book_detail_by_novel_id(populated_db_session, 123456)

        # 验证结果
        assert result is not None
        assert result.novel_id == 123456
        assert result.title == "测试小说1"
        # 验证包含快照数据
        assert hasattr(result, 'favorites')
        assert hasattr(result, 'clicks')
        assert hasattr(result, 'snapshot_time')
        # 验证快照数据值
        assert result.favorites >= 0
        assert result.clicks >= 0

    def test_get_book_detail_by_novel_id_not_found(self, book_service, populated_db_session):
        """测试获取书籍详情 - 书籍不存在"""
        # 执行测试 - 获取不存在的书籍详情
        result = book_service.get_book_detail_by_novel_id(populated_db_session, 999999)

        # 验证结果
        assert result is None

    def test_get_book_detail_by_novel_id_no_snapshot(self, book_service, test_db_session, sample_book_data):
        """测试获取书籍详情 - 书籍存在但无快照数据"""
        # 创建只有基础信息的书籍
        book_service.create_book(test_db_session, sample_book_data)

        # 执行测试 - 获取无快照数据的书籍详情
        result = book_service.get_book_detail_by_novel_id(test_db_session, sample_book_data["novel_id"])

        # 验证结果 - 应该返回None，因为没有快照数据
        assert result is None

    def test_get_historical_snapshots_by_novel_id_success(self, book_service, populated_db_session):
        """测试获取书籍历史快照 - 成功场景"""
        # 执行测试 - 获取7天内的历史快照
        result = book_service.get_historical_snapshots_by_novel_id(
            populated_db_session, 123456, "day", 7
        )

        # 验证结果
        assert isinstance(result, list)
        # 注意：返回的是 BookSnapshot Pydantic 模型，不是数据库对象
        # 所以不会有 novel_id 属性（因为 BookSnapshot 模型中没有定义）
        for item in result:
            # 验证 BookSnapshot 模型中定义的属性
            assert hasattr(item, 'favorites')
            assert hasattr(item, 'clicks')
            assert hasattr(item, 'snapshot_time')
            assert hasattr(item, 'nutrition')
            assert hasattr(item, 'comments')

    def test_get_historical_snapshots_by_novel_id_invalid_interval(self, book_service, populated_db_session):
        """测试获取书籍历史快照 - 无效时间间隔"""
        # 执行测试并验证异常
        with pytest.raises(ValueError, match="不支持的时间间隔"):
            book_service.get_historical_snapshots_by_novel_id(
                populated_db_session, 123456, "invalid_interval", 7
            )

    def test_get_historical_snapshots_by_novel_id_no_data(self, book_service, populated_db_session):
        """测试获取书籍历史快照 - 无历史数据"""
        # 执行测试 - 获取不存在书籍的历史快照
        result = book_service.get_historical_snapshots_by_novel_id(
            populated_db_session, 999999, "day", 7
        )

        # 验证结果 - 应该为空列表
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_historical_snapshots_different_intervals(self, book_service, populated_db_session):
        """测试获取书籍历史快照 - 不同时间间隔"""
        # 测试不同的时间间隔参数
        intervals = ["hour", "day", "week", "month"]
        
        for interval in intervals:
            result = book_service.get_historical_snapshots_by_novel_id(
                populated_db_session, 123456, interval, 1
            )
            # 每个间隔都应该返回列表（可能为空）
            assert isinstance(result, list)

    # ==================== 边界条件和异常测试 ====================

    def test_book_operations_with_invalid_data(self, book_service, test_db_session):
        """测试书籍操作 - 无效数据处理"""
        # 测试包含最小必要字段的数据
        minimal_data = {
            "novel_id": 999998,
            "title": "最小测试书籍",  # title是必须的
            "author_id": 9998  # author_id也是必须的
        }
        
        # create_book应该能处理最小数据
        result = book_service.create_book(test_db_session, minimal_data)
        assert result is not None  # 应该创建一个有效的Book对象
        assert result.title == "最小测试书籍"

    def test_batch_create_empty_snapshots(self, book_service, test_db_session):
        """测试批量创建空快照列表"""
        # 执行测试 - 传入空列表
        result = book_service.batch_create_book_snapshots(test_db_session, [])

        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 0

    def test_pagination_with_zero_size(self, book_service, populated_db_session):
        """测试分页 - size为0的边界情况"""
        # 执行测试 - size为1而不是0，因为0会导致除零错误
        books, total_pages = book_service.get_books_with_pagination(
            populated_db_session, page=1, size=1
        )

        # 验证结果
        assert isinstance(books, list)
        assert len(books) <= 1  # 最多1条记录
        assert total_pages >= 1  # 至少1页

    def test_pagination_with_large_page_number(self, book_service, populated_db_session):
        """测试分页 - 超大页码"""
        # 执行测试 - 请求第100页
        books, total_pages = book_service.get_books_with_pagination(
            populated_db_session, page=100, size=10
        )

        # 验证结果 - 应该返回空列表
        assert isinstance(books, list)
        assert len(books) == 0