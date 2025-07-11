"""
异步数据库连接管理
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator

from ..config import get_settings

# 获取配置
settings = get_settings()

# 创建异步数据库引擎
# 将 sqlite:/// 转换为 sqlite+aiosqlite:///
database_url = settings.database.url
if database_url.startswith("sqlite:///"):
    database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

async_engine = create_async_engine(
    database_url,
    echo=settings.database.echo,
    pool_size=settings.database.pool_size if not database_url.startswith("sqlite") else None,
    max_overflow=settings.database.max_overflow if not database_url.startswith("sqlite") else None,
    pool_timeout=settings.database.pool_timeout if not database_url.startswith("sqlite") else None,
    pool_recycle=settings.database.pool_recycle if not database_url.startswith("sqlite") else None,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_engine():
    """获取异步数据库引擎"""
    return async_engine


async def create_tables():
    """创建数据库表"""
    from .db.base import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """删除数据库表"""
    from .db.base import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)