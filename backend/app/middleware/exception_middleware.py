"""
统一异常处理中间件
"""

import logging
import traceback
from datetime import datetime
from typing import Any, Callable

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DatabaseError, IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


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
            # 已知的HTTP异常直接抛出，不需要额外处理
            return await self._create_error_response(
                status_code=e.status_code,
                error_type="HTTP_ERROR",
                detail=e.detail,
                request=request
            )
            
        except DatabaseError as e:
            # 数据库相关异常
            logger.error(f"数据库错误: {str(e)}", exc_info=True)
            return await self._create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type="DATABASE_ERROR", 
                detail="数据库操作失败",
                request=request,
                original_error=str(e)
            )
            
        except IntegrityError as e:
            # 数据完整性约束异常
            logger.error(f"数据完整性错误: {str(e)}", exc_info=True)
            return await self._create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type="INTEGRITY_ERROR",
                detail="数据完整性约束失败",
                request=request,
                original_error=str(e)
            )
            
        except ValueError as e:
            # 值错误（通常是业务逻辑错误）
            logger.warning(f"值错误: {str(e)}", exc_info=True)
            return await self._create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type="VALUE_ERROR",
                detail=str(e),
                request=request
            )
            
        except FileNotFoundError as e:
            # 文件未找到异常
            logger.error(f"文件未找到: {str(e)}", exc_info=True)
            return await self._create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                error_type="FILE_NOT_FOUND",
                detail="请求的资源不存在",
                request=request,
                original_error=str(e)
            )
            
        except PermissionError as e:
            # 权限错误
            logger.error(f"权限错误: {str(e)}", exc_info=True)
            return await self._create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                error_type="PERMISSION_ERROR",
                detail="权限不足",
                request=request,
                original_error=str(e)
            )
            
        except Exception as e:
            # 所有其他未预期的异常
            logger.error(f"未捕获的异常: {str(e)}", exc_info=True)
            return await self._create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type="INTERNAL_ERROR",
                detail="服务器内部错误",
                request=request,
                original_error=str(e)
            )

    async def _create_error_response(
        self, 
        status_code: int, 
        error_type: str,
        detail: str, 
        request: Request,
        original_error: str = None
    ) -> JSONResponse:
        """
        创建标准化的错误响应
        
        Args:
            status_code: HTTP状态码
            error_type: 错误类型
            detail: 错误详情
            request: 请求对象
            original_error: 原始错误信息（仅在调试模式下返回）
        
        Returns:
            JSONResponse: 标准化的错误响应
        """
        # 直接构建响应数据字典
        error_data = {
            "success": False,
            "code": status_code,
            "message": detail,
            "timestamp": datetime.now().isoformat(),
            "error": {
                "type": error_type,
                "detail": detail,
                "path": str(request.url.path),
                "method": request.method,
            }
        }
        
        # 在开发环境下添加更多调试信息
        if self._is_debug_mode():
            error_data["error"]["original_error"] = original_error
            error_data["error"]["traceback"] = traceback.format_exc()
            
        return JSONResponse(
            status_code=status_code,
            content=error_data
        )

    def _is_debug_mode(self) -> bool:
        """检查是否为调试模式"""
        try:
            from ..config import get_settings
            settings = get_settings()
            return settings.debug or settings.env == "dev"
        except Exception:
            return False