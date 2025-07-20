"""
基础数据模型 - 定义通用的响应结构
"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar("T")


class BaseResponse(BaseModel):
    """基础响应模型"""

    success: bool = Field(True, description="请求是否成功")
    code: int = Field(200, description="响应码")
    message: str = Field("", description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class DataResponse(BaseResponse, Generic[T]):
    data: T = Field(..., description="响应数据")


class ListResponse(BaseResponse, Generic[T]):
    data: list[T] = Field(..., description="响应数据")


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field("healthy", description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    version: str = Field("1.0.0", description="版本号")
    uptime: float | None = Field(None, description="运行时间（秒）")
