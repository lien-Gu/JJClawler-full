"""
数据库连接管理
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from typing import Tuple

from ..config import get_settings

# 获取配置
settings = get_settings()

# 创建数据库引擎
engine = create_engine(
    settings.database.url,
    echo=settings.database.echo,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    pool_recycle=settings.database.pool_recycle,
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """创建数据库表"""
    from .db.base import Base

    Base.metadata.create_all(bind=engine)


def drop_tables():
    """删除数据库表"""
    from .db.base import Base

    Base.metadata.drop_all(bind=engine)


def migrate_database():
    """
    数据库迁移功能
    检查数据库结构是否发生变化，如果有变化则重建数据库
    """
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        # 尝试检查现有表结构
        with engine.connect() as conn:
            # 检查是否能正常连接数据库
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            existing_tables = [row[0] for row in result.fetchall()]
            logger.info(f"发现现有表: {existing_tables}")
            
        # 检查表结构是否匹配当前模型
        from .db.base import Base
        expected_tables = list(Base.metadata.tables.keys())
        logger.info(f"期望的表: {expected_tables}")
        
        # 如果表结构不匹配，重建数据库
        if set(existing_tables) != set(expected_tables):
            logger.warning("数据库表结构不匹配，开始重建数据库...")
            drop_tables()
            create_tables()
            logger.info("数据库重建完成")
        else:
            logger.info("数据库表结构匹配，无需迁移")
            
    except Exception as e:
        logger.warning(f"数据库检查失败，重建数据库: {e}")
        # 如果检查失败，直接重建
        try:
            drop_tables()
        except:
            pass  # 忽略删除表失败的错误
        create_tables()
        logger.info("数据库重建完成")


def ensure_database():
    """
    确保数据库存在且结构正确
    在应用启动时调用
    """
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("检查数据库状态...")
    
    try:
        migrate_database()
        logger.info("数据库准备就绪")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def check_db() -> bool:
    """检查数据库连接状态"""
    try:
        async with get_db() as db:
            result = await db.execute(text("SELECT 1"))
            await result.fetchone()
        return True
    except Exception as e:
        return False
