"""
数据库工具模块

提供统一的数据库事务管理和常用操作
"""

from contextlib import contextmanager
from typing import TypeVar, Callable, Any, Optional, List
from functools import wraps

from sqlmodel import Session, select
from app.modules.database import get_session_sync
from app.utils.log_utils import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


@contextmanager
def transaction_context():
    """
    数据库事务上下文管理器
    
    自动管理事务的提交和回滚
    """
    with get_session_sync() as session:
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库事务回滚: {e}", exc_info=True)
            raise


def transactional(func: Callable) -> Callable:
    """
    数据库事务装饰器
    
    自动为函数添加事务管理
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with transaction_context() as session:
            return func(session, *args, **kwargs)
    
    return wrapper


def safe_execute(
    session: Session, 
    operation: Callable, 
    *args, 
    **kwargs
) -> Optional[Any]:
    """
    安全执行数据库操作
    
    Args:
        session: 数据库会话
        operation: 要执行的操作
        *args: 操作参数
        **kwargs: 操作关键字参数
        
    Returns:
        操作结果，失败时返回None
    """
    try:
        return operation(session, *args, **kwargs)
    except Exception as e:
        logger.error(f"数据库操作失败: {e}", exc_info=True)
        return None


def batch_insert(
    session: Session, 
    model_class: type, 
    data_list: List[dict],
    batch_size: int = 100
) -> int:
    """
    批量插入数据
    
    Args:
        session: 数据库会话
        model_class: 模型类
        data_list: 数据列表
        batch_size: 批次大小
        
    Returns:
        成功插入的记录数
    """
    if not data_list:
        return 0
    
    inserted_count = 0
    
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i + batch_size]
        
        try:
            # 创建模型实例
            instances = [model_class(**data) for data in batch]
            
            # 批量添加
            session.add_all(instances)
            session.flush()  # 不提交，只刷新
            
            inserted_count += len(instances)
            logger.debug(f"批量插入 {len(instances)} 条记录")
            
        except Exception as e:
            logger.error(f"批量插入失败: {e}", exc_info=True)
            session.rollback()
            raise
    
    return inserted_count


def batch_upsert(
    session: Session,
    model_class: type,
    data_list: List[dict],
    unique_fields: List[str],
    batch_size: int = 100
) -> tuple[int, int]:
    """
    批量更新或插入数据
    
    Args:
        session: 数据库会话
        model_class: 模型类
        data_list: 数据列表
        unique_fields: 唯一字段列表
        batch_size: 批次大小
        
    Returns:
        (新增数量, 更新数量)
    """
    if not data_list:
        return 0, 0
    
    inserted_count = 0
    updated_count = 0
    
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i + batch_size]
        
        for data in batch:
            try:
                # 构建查询条件
                filters = []
                for field in unique_fields:
                    if field in data:
                        filters.append(getattr(model_class, field) == data[field])
                
                # 查找现有记录
                existing = session.exec(
                    select(model_class).where(*filters)
                ).first()
                
                if existing:
                    # 更新现有记录
                    for key, value in data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    updated_count += 1
                else:
                    # 创建新记录
                    instance = model_class(**data)
                    session.add(instance)
                    inserted_count += 1
                
            except Exception as e:
                logger.error(f"Upsert操作失败: {e}", exc_info=True)
                session.rollback()
                raise
    
    return inserted_count, updated_count


def get_or_create(
    session: Session,
    model_class: type,
    defaults: Optional[dict] = None,
    **kwargs
) -> tuple[Any, bool]:
    """
    获取或创建记录
    
    Args:
        session: 数据库会话
        model_class: 模型类
        defaults: 创建时的默认值
        **kwargs: 查询条件
        
    Returns:
        (实例, 是否为新创建)
    """
    # 构建查询条件
    filters = []
    for key, value in kwargs.items():
        filters.append(getattr(model_class, key) == value)
    
    # 查找现有记录
    instance = session.exec(
        select(model_class).where(*filters)
    ).first()
    
    if instance:
        return instance, False
    
    # 创建新记录
    create_data = kwargs.copy()
    if defaults:
        create_data.update(defaults)
    
    instance = model_class(**create_data)
    session.add(instance)
    session.flush()  # 获取ID但不提交
    
    return instance, True


def count_records(
    session: Session,
    model_class: type,
    **filters
) -> int:
    """
    统计记录数量
    
    Args:
        session: 数据库会话
        model_class: 模型类
        **filters: 过滤条件
        
    Returns:
        记录数量
    """
    query = select(model_class)
    
    # 添加过滤条件
    for key, value in filters.items():
        if hasattr(model_class, key):
            query = query.where(getattr(model_class, key) == value)
    
    result = session.exec(query)
    return len(list(result))