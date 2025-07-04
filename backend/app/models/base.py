"""
基础数据模型 - 定义通用的响应结构
"""
from typing import Any, Dict, Generic, List, Optional, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar('T')


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("", description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = Field(False, description="请求是否成功")
    error_code: Optional[str] = Field(None, description="错误码")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


class PaginatedResponse(BaseResponse, Generic[T]):
    """分页响应模型"""
    data: List[T] = Field([], description="数据列表")
    total: int = Field(0, description="总数量")
    page: int = Field(1, description="当前页码")
    size: int = Field(20, description="每页大小")
    pages: int = Field(0, description="总页数")
    
    @classmethod
    def create(cls, data: List[T], total: int, page: int, size: int, **kwargs):
        """创建分页响应实例"""
        pages = (total + size - 1) // size  # 计算总页数
        return cls(data=data, total=total, page=page, size=size, pages=pages, **kwargs)


class DataResponse(BaseResponse, Generic[T]):
    """单个数据响应模型"""
    data: T = Field(..., description="响应数据")


class ListResponse(BaseResponse, Generic[T]):
    """列表响应模型"""
    data: List[T] = Field([], description="数据列表")
    count: int = Field(0, description="数据数量")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field("healthy", description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    version: str = Field("1.0.0", description="版本号")
    uptime: Optional[float] = Field(None, description="运行时间（秒）") 