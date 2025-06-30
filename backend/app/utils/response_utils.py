"""
API响应工具

提供标准化的响应格式，使用枚举状态码确保类型安全
"""
from typing import TypeVar, Generic, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from .error_codes import StatusCode

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """标准API响应模型"""
    success: bool = Field(description="操作是否成功")
    code: StatusCode = Field(description="状态码枚举值")
    message: str = Field(description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


def success_response(
    data: Any = None, 
    message: str = "操作成功"
) -> ApiResponse:
    """构建成功响应"""
    return ApiResponse(
        success=True,
        code=StatusCode.SUCCESS,
        message=message,
        data=data
    )


def error_response(
    code: StatusCode,
    message: str
) -> ApiResponse:
    """构建错误响应"""
    return ApiResponse(
        success=False,
        code=code,
        message=message,
        data=None
    )


def paginated_response(
    data: list,
    page: int,
    page_size: int, 
    total_count: int,
    message: str = "查询成功"
) -> ApiResponse:
    """构建分页响应 - 分页信息嵌套在data中"""
    total_pages = (total_count + page_size - 1) // page_size
    
    return ApiResponse(
        success=True,
        code=StatusCode.SUCCESS,
        message=message,
        data={
            "items": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    )


