"""
统一异常处理中间件
"""
from typing import Callable

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import DatabaseError, IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware

from app.models.error import ErrorResponse
from app.logger import get_logger

logger = get_logger(__name__)


class ExceptionMiddleware(BaseHTTPMiddleware):
    """
    统一异常处理中间件

    处理所有未捕获的异常，返回标准化的错误响应
    """

    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response

        except HTTPException as e:
            return ErrorResponse.generate_error_response(
                request=request,
                status_code=e.status_code,
                detail=e.detail,
                err_type="HTTP_ERROR"
            ).to_json_obj()

        except DatabaseError as e:
            logger.error(f"数据库错误: {str(e)}", exc_info=True)
            return ErrorResponse.generate_error_response(
                request=request,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                err_type="DATABASE_ERROR",
                detail=f"数据库操作失败: {str(e)}"
            ).to_json_obj()

        except IntegrityError as e:
            logger.error(f"数据完整性错误: {str(e)}", exc_info=True)
            return ErrorResponse.generate_error_response(
                request=request,
                status_code=status.HTTP_400_BAD_REQUEST,
                err_type="INTEGRITY_ERROR",
                detail=f"数据完整性约束失败: {str(e)}"
            ).to_json_obj()

        except ValueError as e:
            logger.warning(f"值错误: {str(e)}", exc_info=True)
            return ErrorResponse.generate_error_response(
                request=request,
                status_code=status.HTTP_400_BAD_REQUEST,
                err_type="VALUE_ERROR",
                detail=str(e)
            ).to_json_obj()

        except FileNotFoundError as e:
            logger.error(f"文件未找到: {str(e)}", exc_info=True)
            return ErrorResponse.generate_error_response(
                request=request,
                status_code=status.HTTP_404_NOT_FOUND,
                err_type="FILE_NOT_FOUND",
                detail=f"请求的资源不存在: {str(e)}"
            ).to_json_obj()

        except PermissionError as e:
            logger.error(f"权限错误: {str(e)}", exc_info=True)
            return ErrorResponse.generate_error_response(
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                err_type="PERMISSION_ERROR",
                detail=f"权限不足: {str(e)}"
            ).to_json_obj()

        except Exception as e:
            logger.error(f"未捕获的异常: {str(e)}", exc_info=True)
            return ErrorResponse.generate_error_response(
                request=request,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                err_type="INTERNAL_ERROR",
                detail=f"服务器内部错误: {str(e)}"
            ).to_json_obj()
