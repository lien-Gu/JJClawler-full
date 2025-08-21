"""
API模块测试配置文件
提供API测试专用的fixtures和mock数据
"""

from datetime import date, datetime

import pytest

from app.database.db.book import Book, BookSnapshot
from app.database.db.ranking import Ranking

# ==================== API专用Mock数据 ====================


@pytest.fixture
def mock_book_data():
    """模拟书籍数据"""
    return {
        "book": {
            "id": 1,
            "novel_id": 12345,
            "title": "测试小说",
            "author_id": 101,
            "novel_class": "现代言情",
            "tags": "都市,甜文",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime(2024, 1, 15, 12, 0, 0),
        },
        "book_list": [
            {
                "id": 1,
                "novel_id": 12345,
                "title": "测试小说1",
                "author_id": 101,
                "novel_class": "现代言情",
                "tags": "都市,甜文",
            },
            {
                "id": 2,
                "novel_id": 12346,
                "title": "测试小说2",
                "author_id": 102,
                "novel_class": "古代言情",
                "tags": "宫廷,重生",
            },
        ],
    }


@pytest.fixture
def mock_book_snapshot_data():
    """模拟书籍快照数据"""
    return {
        "latest_snapshot": {
            "id": 1,
            "book_id": 1,
            "clicks": 50000,
            "favorites": 1500,
            "comments": 800,
            "snapshot_time": datetime(2024, 1, 15, 12, 0, 0),
        },
        "trend_snapshots": [
            {
                "id": 1,
                "book_id": 1,
                "clicks": 48000,
                "favorites": 1400,
                "comments": 750,
                "snapshot_time": datetime(2024, 1, 14, 12, 0, 0),
            },
            {
                "id": 2,
                "book_id": 1,
                "clicks": 50000,
                "favorites": 1500,
                "comments": 800,
                "snapshot_time": datetime(2024, 1, 15, 12, 0, 0),
            },
        ],
        "aggregated_data": [
            {
                "time_period": "2024-01-14",
                "avg_favorites": 1400.0,
                "avg_clicks": 48000.0,
                "avg_comments": 750.0,
                "max_favorites": 1400,
                "max_clicks": 48000,
                "min_favorites": 1400,
                "min_clicks": 48000,
                "snapshot_count": 1,
                "period_start": datetime(2024, 1, 14, 0, 0, 0),
                "period_end": datetime(2024, 1, 14, 23, 59, 59),
            }
        ],
    }


@pytest.fixture
def mock_ranking_data():
    """模拟榜单数据"""
    return {
        "ranking": {
            "rank_id": "1",
            "name": "测试榜单",
            "page_id": "test_ranking",
            "rank_group_type": "热门",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        },
        "ranking_list": [
            {
                "rank_id": "1",
                "name": "热门榜单",
                "page_id": "hot_ranking",
                "rank_group_type": "热门",
                "created_at": datetime(2024, 1, 1, 12, 0, 0),
            },
            {
                "rank_id": "2",
                "name": "新书榜单",
                "page_id": "new_ranking",
                "rank_group_type": "新书",
                "created_at": datetime(2024, 1, 1, 12, 0, 0),
            },
        ],
        "ranking_detail": {
            "ranking": {
                "rank_id": "1",
                "name": "测试榜单",
                "page_id": "test_ranking",
                "rank_group_type": "热门",
            },
            "books": [
                {"book_id": 1, "title": "测试小说1", "position": 1, "score": 95.5},
                {"book_id": 2, "title": "测试小说2", "position": 2, "score": 89.2},
            ],
            "snapshot_time": datetime(2024, 1, 15, 12, 0, 0),
            "total_books": 2,
        },
    }


@pytest.fixture
def mock_pagination_data():
    """模拟分页数据"""
    books = [
        Book(id=1, novel_id=12345, title="测试小说1"),
        Book(id=2, novel_id=12346, title="测试小说2"),
    ]
    pagination_info = {"total": 50, "page": 1, "size": 20, "total_pages": 3}
    # 返回tuple以匹配API期望的返回值格式 (books, pagination_info)
    return (books, pagination_info)


@pytest.fixture
def mock_search_results():
    """模拟搜索结果"""
    return [
        Book(id=1, novel_id=12345, title="搜索结果1"),
        Book(id=2, novel_id=12346, title="搜索结果2"),
    ]


@pytest.fixture
def mock_ranking_history_data():
    """模拟榜单历史数据"""
    return [
        {
            "ranking_id": 1,
            "ranking_name": "测试榜单",
            "position": 1,
            "snapshot_time": datetime(2024, 1, 14, 12, 0, 0),
        },
        {
            "ranking_id": 1,
            "ranking_name": "测试榜单",
            "position": 2,
            "snapshot_time": datetime(2024, 1, 15, 12, 0, 0),
        },
    ]


@pytest.fixture
def mock_ranking_stats():
    """模拟榜单统计数据"""
    return {
        "total_snapshots": 100,
        "unique_books": 50,
        "first_snapshot_time": datetime(2024, 1, 1, 12, 0, 0),
        "last_snapshot_time": datetime(2024, 1, 15, 12, 0, 0),
    }


@pytest.fixture
def mock_comparison_data():
    """模拟榜单对比数据"""
    return {
        "rankings": [
            {"ranking_id": 1, "name": "榜单1", "page_id": "ranking1"},
            {"ranking_id": 2, "name": "榜单2", "page_id": "ranking2"},
        ],
        "ranking_data": {
            1: [{"book_id": 1, "title": "书籍1", "position": 1, "score": 95.5}],
            2: [{"book_id": 1, "title": "书籍1", "position": 2, "score": 89.2}],
        },
        "common_books": [{"id": 1, "title": "共同书籍1"}],
        "comparison_date": date(2024, 1, 15),
        "stats": {"total_unique_books": 10},
    }


# ==================== SQLAlchemy模型Mock ====================


@pytest.fixture
def mock_book_models(mock_book_data):
    """模拟Book模型实例"""
    book_data = mock_book_data["book"]
    book = Book(
        id=book_data["id"],
        book_id=book_data["book_id"],
        title=book_data["title"],
        author_id=book_data["author_id"],
        novel_class=book_data["novel_class"],
        tags=book_data["tags"],
        created_at=book_data["created_at"],
        updated_at=book_data["updated_at"],
    )
    return book


@pytest.fixture
def mock_book_snapshot_models(mock_book_snapshot_data):
    """模拟BookSnapshot模型实例"""
    snapshot_data = mock_book_snapshot_data["latest_snapshot"]
    snapshot = BookSnapshot(
        id=snapshot_data["id"],
        book_id=snapshot_data["book_id"],
        clicks=snapshot_data["clicks"],
        favorites=snapshot_data["favorites"],
        comments=snapshot_data["comments"],
        snapshot_time=snapshot_data["snapshot_time"],
    )
    return snapshot


@pytest.fixture
def mock_ranking_models(mock_ranking_data):
    """模拟Ranking模型实例"""
    ranking_data = mock_ranking_data["ranking"]
    ranking = Ranking(
        rank_id=ranking_data["rank_id"],
        name=ranking_data["name"],
        page_id=ranking_data["page_id"],
        rank_group_type=ranking_data["rank_group_type"],
        created_at=ranking_data["created_at"],
    )
    return ranking


# ==================== API请求参数 ====================


@pytest.fixture
def api_query_params():
    """API查询参数"""
    return {
        "pagination": {"page": 1, "size": 20},
        "search": {"keyword": "测试", "page": 1, "size": 20},
        "trend": {"days": 7},
        "trend_hourly": {"hours": 24},
        "trend_daily": {"days": 7},
        "trend_weekly": {"weeks": 4},
        "trend_monthly": {"months": 3},
        "trend_aggregated": {"period_count": 7, "interval": "day"},
        "ranking_history": {"ranking_id": 1, "days": 30},
        "ranking_filter": {"group_type": "热门"},
        "ranking_compare": {"ranking_ids": [1, 2], "date": date(2024, 1, 15)},
    }


# ==================== HTTP异常Mock ====================


@pytest.fixture
def mock_http_exceptions():
    """模拟HTTP异常"""
    from fastapi import HTTPException

    return {
        "not_found": HTTPException(status_code=404, detail="资源不存在"),
        "bad_request": HTTPException(status_code=400, detail="请求参数错误"),
        "internal_error": HTTPException(status_code=500, detail="内部服务器错误"),
    }


# ==================== 数据库Session Mock ====================


@pytest.fixture
def mock_db_session(mocker):
    """模拟数据库Session"""
    return mocker.Mock()


# ==================== Service Mock ====================


@pytest.fixture
def mock_book_service(mocker):
    """模拟BookService"""
    service = mocker.Mock()

    # 设置常用方法的返回值
    service.get_book_by_id.return_value = None
    service.get_books_with_pagination.return_value = {
        "books": [],
        "total": 0,
        "page": 1,
        "size": 20,
        "total_pages": 0,
    }
    service.search_books.return_value = []
    service.get_book_detail_by_novel_id.return_value = None
    service.get_book_trend.return_value = []
    service.get_book_trend_hourly.return_value = []
    service.get_book_trend_daily.return_value = []
    service.get_book_trend_weekly.return_value = []
    service.get_book_trend_monthly.return_value = []
    service.get_book_trend_with_interval.return_value = []

    return service


@pytest.fixture
def mock_ranking_service(mocker):
    """模拟RankingService"""
    service = mocker.Mock()

    # 设置常用方法的返回值
    service.get_all_rankings.return_value = {"rankings": [], "total": 0}
    service.get_ranking_detail_by_day.return_value = None
    service.get_ranking_history.return_value = {"trend_data": []}
    service.get_ranking_by_id.return_value = None
    service.get_ranking_statistics.return_value = {}
    service.compare_rankings.return_value = {
        "rankings": [],
        "ranking_data": {},
        "common_books": [],
        "comparison_date": date.today(),
        "stats": {"total_unique_books": 0},
    }
    service.get_book_ranking_history.return_value = []

    return service
