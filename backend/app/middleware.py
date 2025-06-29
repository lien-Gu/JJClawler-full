"""
中间件模块

提供通用的中间件功能
"""
import traceback
from typing import Callable
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.log_utils import get_logger

logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """统一错误处理中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            # 让FastAPI处理HTTP异常
            raise
        except Exception as e:
            # 处理未捕获的异常
            logger.error(
                f"未处理的异常 - {request.method} {request.url}: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "内部服务器错误",
                    "error_type": type(e).__name__
                }
            )


def create_api_error_response(message: str, status_code: int = 500) -> HTTPException:
    """创建标准化的API错误响应"""
    return HTTPException(
        status_code=status_code,
        detail=message
    )


async def handle_service_cleanup(service_obj):
    """统一的服务清理处理"""
    try:
        if hasattr(service_obj, 'close'):
            service_obj.close()
    except Exception as e:
        logger.warning(f"服务清理时发生警告: {e}")
