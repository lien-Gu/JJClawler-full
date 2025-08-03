#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
# @Project: PyCharm
# @File    : error.py
# @Time: 2025/7/21 11:20
# @Author  : Lien Gu
'''
from httpx import Request
from pydantic import BaseModel

from .base import BaseResponse


class ErrorDetail(BaseModel):
    """详细的错误信息模型"""
    type: str
    detail: str
    path: str
    method: str


class ErrorResponse(BaseResponse):
    """统一的错误响应模型"""
    error: ErrorDetail

    @classmethod
    def generate_error_response(cls, request: Request, status_code: int, detail: str,
                                err_type: str = "HTTP_EXCEPTION") -> "ErrorResponse":
        # 添加HTTP异常处理器（路由未找到等）
        return cls(
            success=False,
            code=status_code,
            message=detail,
            error=ErrorDetail(
                type=err_type,
                detail=detail,
                path=str(request.url.path),
                method=request.method
            )
        )
