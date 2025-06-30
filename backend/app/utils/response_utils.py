"""
统一API响应工具

提供完全标准化的响应格式，所有响应都使用相同的结构
"""
from typing import TypeVar, Generic, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

T = TypeVar('T')

class UnifiedResponse(BaseModel, Generic[T]):
    """统一响应模型 - 成功和失败都使用相同结构"""
    success: bool = Field(description="操作是否成功")
    code: int = Field(description="状态码 - 200为成功，其他为错误码")
    message: str = Field(description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


# 响应构建工具函数
def success_response(
    data: Any = None, 
    message: str = "操作成功"
) -> UnifiedResponse:
    """构建成功响应"""
    return UnifiedResponse(
        success=True,
        code=200,
        message=message,
        data=data
    )


def error_response(
    code: int,
    message: str
) -> UnifiedResponse:
    """构建错误响应"""
    return UnifiedResponse(
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
) -> UnifiedResponse:
    """构建分页响应 - 分页信息放在data中"""
    total_pages = (total_count + page_size - 1) // page_size
    
    return UnifiedResponse(
        success=True,
        code=200,
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


# 为了兼容性，保留旧的类型别名
BaseResponse = UnifiedResponse
PaginatedResponse = UnifiedResponse