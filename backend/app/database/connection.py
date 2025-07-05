"""
数据库连接管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

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