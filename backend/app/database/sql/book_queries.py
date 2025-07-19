"""
书籍相关SQL查询语句

包含所有与书籍数据操作相关的SQL查询，主要用于BookService。
所有查询都支持SQLAlchemy的参数化查询（使用:参数名格式）。
"""

# 按小时获取快照的SQL查询
BOOK_HOURLY_SNAPSHOTS_QUERY = """
SELECT bs.*
FROM book_snapshots bs
INNER JOIN (
    SELECT 
        strftime('%Y-%m-%d %H', snapshot_time) as hour_key,
        MIN(ABS(strftime('%M', snapshot_time) * 60 + strftime('%S', snapshot_time))) as min_seconds_from_hour,
        MIN(snapshot_time) as first_snapshot_time
    FROM book_snapshots
    WHERE book_id = :book_id 
        AND snapshot_time >= :start_time 
        AND snapshot_time <= :end_time
    GROUP BY strftime('%Y-%m-%d %H', snapshot_time)
) hourly_min ON strftime('%Y-%m-%d %H', bs.snapshot_time) = hourly_min.hour_key
    AND ABS(strftime('%M', bs.snapshot_time) * 60 + strftime('%S', bs.snapshot_time)) = hourly_min.min_seconds_from_hour
    AND bs.snapshot_time = hourly_min.first_snapshot_time
WHERE bs.book_id = :book_id
    AND bs.snapshot_time >= :start_time 
    AND bs.snapshot_time <= :end_time
ORDER BY bs.snapshot_time DESC
"""

# 按天获取1点快照的SQL查询
BOOK_DAILY_ONE_OCLOCK_SNAPSHOTS_QUERY = """
SELECT bs.*
FROM book_snapshots bs
INNER JOIN (
    SELECT 
        DATE(snapshot_time) as date_key,
        MIN(ABS(
            (strftime('%H', snapshot_time) * 60 + strftime('%M', snapshot_time)) - 60
        )) as min_minutes_from_1pm,
        MIN(snapshot_time) as first_snapshot_time
    FROM book_snapshots
    WHERE book_id = :book_id 
        AND snapshot_time >= :start_time 
        AND snapshot_time <= :end_time
    GROUP BY DATE(snapshot_time)
) daily_min ON DATE(bs.snapshot_time) = daily_min.date_key
    AND ABS(
        (strftime('%H', bs.snapshot_time) * 60 + strftime('%M', bs.snapshot_time)) - 60
    ) = daily_min.min_minutes_from_1pm
    AND bs.snapshot_time = daily_min.first_snapshot_time
WHERE bs.book_id = :book_id
    AND bs.snapshot_time >= :start_time 
    AND bs.snapshot_time <= :end_time
ORDER BY bs.snapshot_time DESC
"""


# 聚合趋势数据的SQL查询模板
# 注意：这个查询需要动态插入time_format，所以设计为函数
def get_aggregated_trend_query(time_format: str) -> str:
    """
    获取聚合趋势数据的SQL查询

    Args:
        time_format: SQLite strftime格式字符串，如'%Y-%m-%d %H'、'%Y-%m-%d'等

    Returns:
        str: 格式化后的SQL查询字符串
    """
    return f"""
SELECT 
    strftime('{time_format}', snapshot_time) as time_period,
    AVG(favorites) as avg_favorites,
    AVG(clicks) as avg_clicks,
    AVG(comments) as avg_comments,
    MAX(favorites) as max_favorites,
    MAX(clicks) as max_clicks,
    MIN(favorites) as min_favorites,
    MIN(clicks) as min_clicks,
    COUNT(*) as snapshot_count,
    MIN(snapshot_time) as period_start,
    MAX(snapshot_time) as period_end
FROM book_snapshots
WHERE book_id = :book_id 
    AND snapshot_time >= :start_time 
    AND snapshot_time <= :end_time
GROUP BY strftime('{time_format}', snapshot_time)
ORDER BY period_start DESC
"""


# 获取书籍基本信息的查询
BOOK_BY_ID_QUERY = """
SELECT * FROM books WHERE id = :book_id
"""

BOOK_BY_NOVEL_ID_QUERY = """
SELECT * FROM books WHERE novel_id = :novel_id
"""

# 获取书籍快照相关查询
LATEST_SNAPSHOT_BY_BOOK_ID_QUERY = """
SELECT * FROM book_snapshots 
WHERE book_id = :book_id 
ORDER BY snapshot_time DESC 
LIMIT 1
"""

BOOK_STATISTICS_QUERY = """
SELECT 
    COUNT(id) as total_snapshots,
    MAX(favorites) as max_favorites,
    MAX(clicks) as max_clicks,
    MAX(comments) as max_comments,
    MIN(snapshot_time) as first_snapshot_time,
    MAX(snapshot_time) as last_snapshot_time
FROM book_snapshots
WHERE book_id = :book_id
"""

# 书籍搜索查询
SEARCH_BOOKS_QUERY = """
SELECT * FROM books 
WHERE title LIKE :keyword
LIMIT :limit
"""

# 分页查询书籍
BOOKS_WITH_PAGINATION_QUERY = """
SELECT * FROM books 
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset
"""

BOOKS_COUNT_QUERY = """
SELECT COUNT(*) FROM books
"""
