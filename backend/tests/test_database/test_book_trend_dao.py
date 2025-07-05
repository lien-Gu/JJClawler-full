"""
书籍趋势数据DAO测试（重构后的独立函数）
"""
import pytest
from datetime import datetime, timedelta

from app.database.dao.book_dao import BookSnapshotDAO


class TestBookSnapshotTrendDAO:
    """书籍快照趋势数据DAO测试"""
    
    @pytest.fixture
    def snapshot_dao(self):
        """创建快照DAO实例"""
        return BookSnapshotDAO()
    
    @pytest.fixture
    def time_range(self):
        """创建测试时间范围"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        return start_time, end_time
    
    def test_get_hourly_trend_by_book_id(self, test_db, sample_book, snapshot_dao, time_range):
        """测试按小时获取趋势数据"""
        start_time, end_time = time_range
        
        trend_data = snapshot_dao.get_hourly_trend_by_book_id(
            test_db, sample_book.id, start_time, end_time
        )
        
        assert isinstance(trend_data, list)
        
        # 验证返回数据结构
        if trend_data:
            data_point = trend_data[0]
            required_fields = [
                "time_period", "avg_favorites", "avg_clicks", "avg_comments",
                "avg_recommendations", "max_favorites", "max_clicks", 
                "min_favorites", "min_clicks", "snapshot_count",
                "period_start", "period_end"
            ]
            
            for field in required_fields:
                assert field in data_point
            
            # 验证数据类型
            assert isinstance(data_point["avg_favorites"], float)
            assert isinstance(data_point["max_favorites"], int)
            assert isinstance(data_point["snapshot_count"], int)
            assert isinstance(data_point["period_start"], datetime)
    
    def test_get_daily_trend_by_book_id(self, test_db, sample_book, snapshot_dao, time_range):
        """测试按天获取趋势数据"""
        start_time, end_time = time_range
        
        trend_data = snapshot_dao.get_daily_trend_by_book_id(
            test_db, sample_book.id, start_time, end_time
        )
        
        assert isinstance(trend_data, list)
        
        # 验证时间周期格式（按天应该是YYYY-MM-DD格式）
        if trend_data:
            time_period = trend_data[0]["time_period"]
            assert len(time_period) == 10  # YYYY-MM-DD
            assert "-" in time_period
    
    def test_get_weekly_trend_by_book_id(self, test_db, sample_book, snapshot_dao, time_range):
        """测试按周获取趋势数据"""
        start_time, end_time = time_range
        
        trend_data = snapshot_dao.get_weekly_trend_by_book_id(
            test_db, sample_book.id, start_time, end_time
        )
        
        assert isinstance(trend_data, list)
        
        # 验证时间周期格式（按周应该是YYYY-WWW格式）
        if trend_data:
            time_period = trend_data[0]["time_period"]
            assert "W" in time_period  # 包含周标识符
    
    def test_get_monthly_trend_by_book_id(self, test_db, sample_book, snapshot_dao, time_range):
        """测试按月获取趋势数据"""
        start_time, end_time = time_range
        
        trend_data = snapshot_dao.get_monthly_trend_by_book_id(
            test_db, sample_book.id, start_time, end_time
        )
        
        assert isinstance(trend_data, list)
        
        # 验证时间周期格式（按月应该是YYYY-MM格式）
        if trend_data:
            time_period = trend_data[0]["time_period"]
            assert len(time_period) == 7  # YYYY-MM
            assert time_period.count("-") == 1
    
    def test_get_trend_by_book_id_with_interval(self, test_db, sample_book, snapshot_dao, time_range):
        """测试通用间隔趋势数据获取函数"""
        start_time, end_time = time_range
        
        # 测试所有支持的间隔
        intervals = ["hour", "day", "week", "month"]
        
        for interval in intervals:
            trend_data = snapshot_dao.get_trend_by_book_id_with_interval(
                test_db, sample_book.id, start_time, end_time, interval
            )
            
            assert isinstance(trend_data, list)
            
            # 验证每种间隔都能正确调用对应的专门函数
            if trend_data:
                # 验证时间周期格式符合对应间隔的要求
                time_period = trend_data[0]["time_period"]
                
                if interval == "hour":
                    assert len(time_period) == 13  # YYYY-MM-DD HH
                elif interval == "day":
                    assert len(time_period) == 10  # YYYY-MM-DD
                elif interval == "week":
                    assert "W" in time_period
                elif interval == "month":
                    assert len(time_period) == 7  # YYYY-MM
        
        # 测试无效间隔
        with pytest.raises(ValueError, match="不支持的时间间隔"):
            snapshot_dao.get_trend_by_book_id_with_interval(
                test_db, sample_book.id, start_time, end_time, "invalid"
            )
    
    def test_execute_trend_query_private_method(self, test_db, sample_book, snapshot_dao, time_range):
        """测试私有方法_execute_trend_query"""
        start_time, end_time = time_range
        
        # 测试日级时间分组
        time_group = "strftime('%Y-%m-%d', BookSnapshot.snapshot_time)"
        
        trend_data = snapshot_dao._execute_trend_query(
            test_db, sample_book.id, start_time, end_time, time_group
        )
        
        assert isinstance(trend_data, list)
        
        # 验证聚合计算的准确性
        if trend_data:
            data_point = trend_data[0]
            
            # 验证最大值 >= 平均值 >= 最小值
            assert data_point["max_favorites"] >= data_point["avg_favorites"]
            assert data_point["avg_favorites"] >= data_point["min_favorites"]
            assert data_point["max_clicks"] >= data_point["avg_clicks"]
            assert data_point["avg_clicks"] >= data_point["min_clicks"]
            
            # 验证快照数量为正数
            assert data_point["snapshot_count"] > 0
            
            # 验证时间范围合理
            assert data_point["period_start"] <= data_point["period_end"]
    
    def test_trend_data_aggregation_accuracy(self, test_db, sample_book, sample_book_snapshots, snapshot_dao):
        """测试趋势数据聚合的准确性"""
        # 使用sample_book_snapshots提供的测试数据进行验证
        start_time = datetime.now() - timedelta(days=10)
        end_time = datetime.now()
        
        trend_data = snapshot_dao.get_daily_trend_by_book_id(
            test_db, sample_book.id, start_time, end_time
        )
        
        if trend_data:
            # 验证聚合数据的合理性
            for data_point in trend_data:
                # 平均值应该在最大值和最小值之间
                assert data_point["min_favorites"] <= data_point["avg_favorites"] <= data_point["max_favorites"]
                assert data_point["min_clicks"] <= data_point["avg_clicks"] <= data_point["max_clicks"]
                
                # 快照数量应该为正数
                assert data_point["snapshot_count"] > 0
                
                # 平均值应该是合理的数值（不是NaN或无穷大）
                assert data_point["avg_favorites"] >= 0
                assert data_point["avg_clicks"] >= 0
    
    def test_trend_data_time_ordering(self, test_db, sample_book, sample_book_snapshots, snapshot_dao):
        """测试趋势数据时间排序"""
        start_time = datetime.now() - timedelta(days=10)
        end_time = datetime.now()
        
        trend_data = snapshot_dao.get_daily_trend_by_book_id(
            test_db, sample_book.id, start_time, end_time
        )
        
        if len(trend_data) > 1:
            # 验证按时间降序排列（最新的在前面）
            for i in range(len(trend_data) - 1):
                current_start = trend_data[i]["period_start"]
                next_start = trend_data[i + 1]["period_start"]
                assert current_start >= next_start
    
    def test_trend_data_empty_result(self, test_db, snapshot_dao):
        """测试没有数据时的情况"""
        # 使用不存在的书籍ID
        fake_book_id = 99999
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now()
        
        trend_data = snapshot_dao.get_daily_trend_by_book_id(
            test_db, fake_book_id, start_time, end_time
        )
        
        # 应该返回空列表而不是抛出异常
        assert isinstance(trend_data, list)
        assert len(trend_data) == 0
    
    def test_trend_data_time_range_filtering(self, test_db, sample_book, sample_book_snapshots, snapshot_dao):
        """测试时间范围过滤"""
        # 测试非常窄的时间范围
        narrow_start = datetime.now() - timedelta(hours=1)
        narrow_end = datetime.now()
        
        trend_data = snapshot_dao.get_hourly_trend_by_book_id(
            test_db, sample_book.id, narrow_start, narrow_end
        )
        
        # 应该能正确处理窄时间范围
        assert isinstance(trend_data, list)
        
        # 如果有数据，验证时间范围正确
        if trend_data:
            for data_point in trend_data:
                assert data_point["period_start"] >= narrow_start
                assert data_point["period_end"] <= narrow_end