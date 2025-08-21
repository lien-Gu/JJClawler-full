"""
SQL查询模块

此模块包含所有数据库查询语句，按业务模块组织：
- book_queries: 书籍相关的SQL查询
- ranking_queries: 榜单相关的SQL查询

使用示例:
    from app.database.sql.book_queries import BOOK_HOURLY_SNAPSHOTS_QUERY
    from app.database.sql.ranking_queries import RANKING_HISTORY_QUERY
"""

__all__ = ["book_queries", "ranking_queries"]
