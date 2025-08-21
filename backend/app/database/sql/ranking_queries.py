"""
榜单相关SQL查询语句

包含所有与榜单数据操作相关的SQL查询，主要用于RankingService。
所有查询都支持SQLAlchemy的参数化查询（使用:参数名格式）。
"""

# 获取榜单基本信息
RANKING_BY_ID_QUERY = """
SELECT * FROM rankings WHERE rank_id = :rank_id
"""

RANKINGS_LIST_QUERY = """
SELECT * FROM rankings 
ORDER BY created_at DESC
"""

# 获取榜单快照相关查询
RANKING_LATEST_SNAPSHOT_QUERY = """
SELECT * FROM ranking_snapshots 
WHERE ranking_id = :ranking_id 
ORDER BY snapshot_time DESC 
LIMIT 1
"""

RANKING_SNAPSHOTS_BY_TIME_RANGE_QUERY = """
SELECT * FROM ranking_snapshots 
WHERE ranking_id = :ranking_id 
    AND snapshot_time >= :start_time 
    AND snapshot_time <= :end_time
ORDER BY snapshot_time DESC
"""

# 获取书籍在榜单中的历史排名
BOOK_RANKING_HISTORY_QUERY = """
SELECT 
    rs.ranking_id,
    r.name as ranking_name,
    rs.position,
    rs.snapshot_time
FROM ranking_snapshots rs
JOIN rankings r ON rs.ranking_id = r.rank_id
WHERE rs.book_id = :book_id
    AND rs.snapshot_time >= :start_time
    AND rs.snapshot_time <= :end_time
ORDER BY rs.snapshot_time DESC
"""

# 特定榜单的书籍排名历史
BOOK_RANKING_HISTORY_IN_SPECIFIC_RANKING_QUERY = """
SELECT 
    rs.ranking_id,
    r.name as ranking_name,
    rs.position,
    rs.snapshot_time
FROM ranking_snapshots rs
JOIN rankings r ON rs.ranking_id = r.rank_id
WHERE rs.book_id = :book_id
    AND rs.ranking_id = :ranking_id
    AND rs.snapshot_time >= :start_time
    AND rs.snapshot_time <= :end_time
ORDER BY rs.snapshot_time DESC
"""

# 榜单统计信息
RANKING_STATISTICS_QUERY = """
SELECT 
    COUNT(*) as total_snapshots,
    COUNT(DISTINCT book_id) as unique_books,
    MIN(snapshot_time) as first_snapshot_time,
    MAX(snapshot_time) as last_snapshot_time
FROM ranking_snapshots
WHERE ranking_id = :ranking_id
"""

# 榜单对比查询
RANKING_BOOKS_AT_TIME_QUERY = """
SELECT 
    rs.ranking_id,
    rs.book_id,
    b.title,
    rs.position,
    rs.score
FROM ranking_snapshots rs
JOIN books b ON rs.book_id = b.id
WHERE rs.ranking_id = :ranking_id
    AND DATE(rs.snapshot_time) = :target_date
ORDER BY rs.position ASC
"""

# 获取多个榜单的共同书籍
COMMON_BOOKS_IN_RANKINGS_QUERY = """
SELECT DISTINCT b.id, b.title
FROM books b
WHERE b.id IN (
    SELECT DISTINCT book_id 
    FROM ranking_snapshots 
    WHERE ranking_id IN :ranking_ids
        AND DATE(snapshot_time) = :target_date
)
"""

# 获取书籍每天最后一次榜单排名历史（高性能窗口函数查询）
BOOK_DAILY_LAST_RANKING_HISTORY_QUERY = """
SELECT 
    rs.novel_id,
    rs.position,
    rs.snapshot_time,
    r.page_id,
    r.channel_name,
    r.sub_channel_name
FROM (
    SELECT novel_id,
           ranking_id,
           position,
           snapshot_time,
           ROW_NUMBER() OVER (
               PARTITION BY DATE(snapshot_time), ranking_id 
               ORDER BY snapshot_time DESC
           ) as rn
    FROM ranking_snapshots 
    WHERE novel_id = :novel_id 
        AND snapshot_time >= :start_time
) rs
JOIN rankings r ON rs.ranking_id = r.id
WHERE rs.rn = 1
ORDER BY rs.snapshot_time DESC
"""
