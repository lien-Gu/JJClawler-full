"""
统一API响应工具

提供标准化的响应格式和构建工具，简化API开发
"""
from typing import TypeVar, Generic, Optional, Any, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """统一的API响应基础类"""
    success: bool = Field(default=True, description="操作是否成功")
    message: str = Field(default="操作成功", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    code: int = Field(default=200, description="业务状态码")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应类"""
    success: bool = Field(default=True, description="操作是否成功") 
    message: str = Field(default="查询成功", description="响应消息")
    data: List[T] = Field(description="数据列表")
    pagination: Dict[str, Any] = Field(description="分页信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class ErrorResponse(BaseModel):
    """错误响应类"""
    success: bool = Field(default=False, description="操作是否成功")
    message: str = Field(description="错误消息")
    error_code: str = Field(description="错误代码") 
    details: Optional[Any] = Field(default=None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


# 响应构建工具函数
def success_response(
    data: Any = None, 
    message: str = "操作成功",
    code: int = 200
) -> BaseResponse:
    """构建成功响应"""
    return BaseResponse(
        success=True,
        message=message,
        data=data,
        code=code
    )


def error_response(
    message: str,
    error_code: str = "INTERNAL_ERROR", 
    details: Any = None
) -> ErrorResponse:
    """构建错误响应"""
    return ErrorResponse(
        message=message,
        error_code=error_code,
        details=details
    )


def paginated_response(
    data: List[Any],
    page: int,
    page_size: int, 
    total_count: int,
    message: str = "查询成功"
) -> PaginatedResponse:
    """构建分页响应"""
    total_pages = (total_count + page_size - 1) // page_size
    
    return PaginatedResponse(
        message=message,
        data=data,
        pagination={
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    )