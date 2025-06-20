"""
数据库连接管理

提供SQLite数据库的连接、会话管理和表创建
"""
import logging
from typing import Generator, Optional
from sqlmodel import SQLModel, create_engine, Session, select
from app.config import get_settings

logger = logging.getLogger(__name__)

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
            connect_args=connect_args
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
        from app.modules.models import Ranking, Book, BookSnapshot, RankingSnapshot
        
        engine = get_engine()
        SQLModel.metadata.create_all(engine)
        logger.info("数据库表创建成功")
        
        # 初始化基础数据
        _init_base_data()
        
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        raise


def _init_base_data():
    """初始化基础榜单配置数据"""
    from app.modules.models import Ranking, UpdateFrequency
    
    with Session(get_engine()) as session:
        # 检查是否已有数据
        existing_rankings = session.exec(select(Ranking)).first()
        if existing_rankings:
            logger.info("榜单配置数据已存在，跳过初始化")
            return
        
        # 基础榜单配置
        base_rankings = [
            Ranking(
                ranking_id="jiazi",
                name="夹子",
                channel="favObservation",
                frequency=UpdateFrequency.HOURLY,
                update_interval=1
            ),
            Ranking(
                ranking_id="yq_gy",
                name="言情-古言",
                channel="gywx", 
                frequency=UpdateFrequency.HOURLY,
                update_interval=2
            ),
            Ranking(
                ranking_id="yq_xy",
                name="言情-现言",
                channel="dsyq",
                frequency=UpdateFrequency.DAILY,
                update_interval=24
            ),
            Ranking(
                ranking_id="ca_ds",
                name="纯爱-都市",
                channel="xddm",
                frequency=UpdateFrequency.HOURLY,
                update_interval=2
            ),
            Ranking(
                ranking_id="ca_gd",
                name="纯爱-古代",
                channel="gddm",
                frequency=UpdateFrequency.DAILY,
                update_interval=24
            )
        ]
        
        for ranking in base_rankings:
            session.add(ranking)
        
        try:
            session.commit()
            logger.info(f"初始化了 {len(base_rankings)} 个榜单配置")
        except Exception as e:
            session.rollback()
            logger.error(f"初始化基础数据失败: {e}")
            raise


def check_database_health() -> bool:
    """检查数据库连接是否正常"""
    try:
        from app.modules.models import Ranking
        with Session(get_engine()) as session:
            # 简单查询测试连接
            result = session.exec(select(Ranking)).first()
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