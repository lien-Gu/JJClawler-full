"""
数据库连接管理
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ..config import get_settings
from ..logger import get_logger
from ..utils import get_model_fields

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


async def check_db() -> bool:
    """检查数据库连接状态"""
    try:
        with SessionLocal() as db:
            result = db.execute(text("SELECT 1"))
            result.fetchone()
        return True
    except Exception:
        return False


def ensure_db():
    """
    确保数据库存在且结构正确
    简化版本：创建数据库表或建立连接
    """
    logger = get_logger(__name__)
    logger.info("初始化数据库连接...")
    
    try:
        # 检查数据库连接
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        logger.info("数据库连接正常")
        
        # 创建表结构（如果不存在）
        create_tables()
        logger.info("数据库表结构确认完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise RuntimeError(f"数据库初始化失败: {e}")
