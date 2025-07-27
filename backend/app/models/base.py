"""
基础数据模型 - 定义通用的响应结构
"""

from datetime import datetime
from typing import Generic, TypeVar, Optional, List

from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar("T")


class BaseResponse(BaseModel):
    """基础响应模型"""

    success: bool = Field(True, description="请求是否成功")
    code: int = Field(200, description="响应码")
    message: str = Field("", description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class PaginationData(BaseModel, Generic[T]):
    data_list: List[T] = Field([], description="内容列表")
    page: int = Field(0, description="第几页")
    size: int = Field(20, description="一页的数量")
    total_pages: int = Field(0, description="总页数")


class DataResponse(BaseResponse, Generic[T]):
    data: Optional[T] = None


class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
