"""
服务工具模块

提供统一的服务管理、错误处理和响应格式化功能
"""

from contextlib import contextmanager
from typing import Type, TypeVar, Dict, Any, List, Optional, Callable
from fastapi import HTTPException

from app.utils.log_utils import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@contextmanager
def service_context(service_class: Type[T]) -> T:
    """
    服务上下文管理器

    自动管理服务的创建和清理，确保资源正确释放

    Args:
        service_class: 服务类

    Yields:
        服务实例
    """
    service = service_class()
    try:
        yield service
    finally:
        if hasattr(service, "close"):
            service.close()


def handle_api_error(
    error: Exception, context: str = "操作", status_code: int = 500
) -> None:
    """
    统一的API错误处理

    Args:
        error: 异常对象
        context: 操作上下文描述
        status_code: HTTP状态码

    Raises:
        HTTPException: 格式化后的HTTP异常
    """
    error_msg = f"{context}失败: {str(error)}"
    logger.error(error_msg, exc_info=True)
    raise HTTPException(status_code=status_code, detail=error_msg)


def to_api_response(
    data: Any, transformer: Optional[Callable] = None, default_empty: Any = None
) -> Any:
    """
    统一的API响应格式化

    Args:
        data: 原始数据
        transformer: 数据转换函数
        default_empty: 数据为空时的默认值

    Returns:
        格式化后的响应数据
    """
    if not data:
        return default_empty or []

    if transformer:
        if isinstance(data, list):
            return [transformer(item) for item in data]
        else:
            return transformer(data)

    if isinstance(data, list):
        return [
            item.model_dump() if hasattr(item, "model_dump") else item for item in data
        ]

    return data.model_dump() if hasattr(data, "model_dump") else data


def paginate_response(
    data: List[Any], page: int, page_size: int, total_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    统一的分页响应格式

    Args:
        data: 数据列表
        page: 页码
        page_size: 每页大小
        total_count: 总数量（如果已知）

    Returns:
        分页响应字典
    """
    if total_count is None:
        total_count = len(data)

    total_pages = (total_count + page_size - 1) // page_size

    return {
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


def execute_with_error_handling(
    operation: Callable, context: str, *args, **kwargs
) -> Any:
    """
    执行操作并统一处理错误

    Args:
        operation: 要执行的操作函数
        context: 操作上下文描述
        *args: 操作参数
        **kwargs: 操作关键字参数

    Returns:
        操作结果

    Raises:
        HTTPException: 如果操作失败
    """
    try:
        return operation(*args, **kwargs)
    except Exception as e:
        handle_api_error(e, context)
