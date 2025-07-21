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


class ComponentHealth(BaseModel):
    """组件健康状态"""
    name: str = Field(..., description="组件名称")
    status: str = Field(..., description="组件状态: healthy/degraded/unhealthy")
    message: str = Field("", description="状态消息")
    details: dict = Field(default_factory=dict, description="详细信息")


class SystemInfo(BaseModel):
    """系统信息"""
    memory_usage: float | None = Field(None, description="内存使用率(%)")
    disk_usage: float | None = Field(None, description="磁盘使用率(%)")
    cpu_usage: float | None = Field(None, description="CPU使用率(%)")


class HealthData(BaseModel):
    """健康检查数据"""
    status: str = Field("healthy", description="整体服务状态")
    version: str = Field(..., description="版本号")
    uptime: float = Field(..., description="运行时间（秒）")
    components: list[ComponentHealth] = Field(..., description="组件状态列表")
    system: SystemInfo = Field(..., description="系统信息")


class AppInfo(BaseModel):
    """应用基本信息"""
    name: str = Field(..., description="应用名称")
    version: str = Field(..., description="应用版本")
    description: str = Field(..., description="应用描述")
    environment: str = Field(..., description="运行环境")
