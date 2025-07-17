"""
数据库基础模型定义
"""

from datetime import datetime
from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


class Base(DeclarativeBase):
    """SQLAlchemy基础模型类
    
    所有数据表的基础类，包含通用字段：
    - id: 主键，自增整数
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    
    # 主键ID - 所有表都有的自增主键
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        comment="主键ID，自增整数"
    )
    
    # 时间戳字段 - 所有表都有的创建和更新时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now,
        comment="记录创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now,
        comment="记录最后更新时间"
    )
