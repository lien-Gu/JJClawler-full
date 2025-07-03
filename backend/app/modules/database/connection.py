"""
数据库连接管理

提供SQLite数据库的连接、会话管理和表创建
"""

from typing import Generator, Optional
from sqlmodel import SQLModel, create_engine, Session, select
from app.config import get_settings
from app.utils.log_utils import get_logger

logger = get_logger(__name__)

# 全局数据库引擎
_engine: Optional["Engine"] = None


def get_engine():
    """获取数据库引擎"""
    global _engine
    if _engine is None:
        settings = get_settings()

        # SQLite优化配置
        connect_args = {
            "check_same_thread": False,  # 允许多线程
        }

        _engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,  # 调试模式下打印SQL
            connect_args=connect_args,
        )

        # 设置SQLite PRAGMA优化
        _set_sqlite_pragma(_engine)

    return _engine


def _set_sqlite_pragma(engine):
    """设置SQLite优化参数"""
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # WAL模式提高并发性能
        cursor.execute("PRAGMA journal_mode=WAL")
        # 64MB缓存
        cursor.execute("PRAGMA cache_size=-64000")
        # 平衡性能和安全性
        cursor.execute("PRAGMA synchronous=NORMAL")
        # 启用外键约束
        cursor.execute("PRAGMA foreign_keys=ON")
        # 临时表存内存
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


def get_session() -> Generator[Session, None, None]:
    """获取数据库会话（依赖注入）"""
    with Session(get_engine()) as session:
        yield session


def get_session_sync() -> Session:
    """获取数据库会话（同步使用）"""
    return Session(get_engine())


def create_db_and_tables():
    """创建数据库表"""
    try:
        # 导入所有模型以确保表被注册
        from app.modules.models import (
            Ranking,
            Book,
            BookSnapshot,
            RankingSnapshot,
            TaskExecution,
        )

        engine = get_engine()
        SQLModel.metadata.create_all(engine)
        logger.info("数据库表创建成功")

        # 注意：榜单数据需要通过爬虫获取，不在此初始化

    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        raise


# 榜单数据将通过爬虫模块获取并存储，此处不再初始化mock数据


def check_database_health() -> bool:
    """检查数据库连接是否正常"""
    try:
        with Session(get_engine()) as session:
            # 简单查询测试连接（测试一个简单的SQL）
            session.exec(select(1))
            return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return False


def close_database_connections():
    """关闭数据库连接"""
    global _engine
    if _engine:
        _engine.dispose()
        _engine = None
        logger.info("数据库连接已关闭")
