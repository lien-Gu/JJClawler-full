"""
FastAPI应用程序入口
"""

import sys
import time
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from .models.error import ErrorResponse
from .api import api_router
from .config import get_settings
from .logger import get_logger, setup_logging
from .middleware import ExceptionMiddleware
from .models.base import BaseResponse, DataResponse

# 修复中文编码显示问题
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


# 初始化日志系统
setup_logging()
logger = get_logger(__name__)

# 应用启动时间
APP_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    # 启动时的初始化代码
    logger.info("应用程序启动")

    # 数据库初始化
    try:
        from .database.connection import ensure_db
        ensure_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise  # 数据库初始化失败应该阻止应用启动

    # 启动调度器
    try:
        from .schedule import start_scheduler
        await start_scheduler()
        logger.info("任务调度器启动成功")
    except Exception as e:
        logger.error(f"任务调度器启动失败: {e}")

    yield

    # 关闭时的清理代码
    try:
        from .schedule import stop_scheduler
        await stop_scheduler()
        logger.info("任务调度器已停止")
    except Exception as e:
        logger.error(f"任务调度器停止失败: {e}")

    logger.info("应用程序关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title="JJCrawler API",
    description="晋江文学城爬虫系统API",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加异常处理中间件（必须在CORS之前添加）
app.add_middleware(ExceptionMiddleware)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 添加HTTP异常处理器（FastAPI HTTPException）
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """FastAPI HTTP异常处理器 - 使用统一的响应格式"""
    return ErrorResponse.generate_error_response(request, exc.status_code, exc.detail).to_json_obj()


# 添加Starlette HTTP异常处理器（路由未找到等）
@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Starlette HTTP异常处理器 - 使用统一的响应格式"""
    detail = exc.detail if hasattr(exc, 'detail') else "页面未找到"
    return ErrorResponse.generate_error_response(request, exc.status_code, detail).to_json_obj()


# 注册路由
app.include_router(api_router)


@app.get("/", response_model=DataResponse[Dict])
async def root():
    """根路径 - 返回应用基本信息"""
    settings = get_settings()

    return DataResponse(
        success=True,
        code=200,
        message="API服务运行正常",
        data={
            "name": settings.project_name,
            "version": settings.project_version,
            "description": settings.api.description,
            "environment": settings.env
        }
    )


@app.get("/health", response_model=DataResponse[Dict])
async def health_check():
    """健康检查 - 简洁的系统状态检查"""
    settings = get_settings()
    
    # 检查各个组件状态（简化为布尔值）
    from .database.connection import check_db
    db_ok = check_db()
    from .schedule.scheduler import get_scheduler
    scheduler_ok = get_scheduler().is_running()
    
    # 计算运行时间
    uptime = time.time() - APP_START_TIME
    
    # 确定整体状态
    all_ok = db_ok and scheduler_ok
    health_status = "healthy" if all_ok else "unhealthy"
    
    health_data = {
        "status": health_status,
        "version": settings.project_version,
        "uptime": round(uptime, 2),
        "components": {
            "database": "ok" if db_ok else "error",
            "scheduler": "ok" if scheduler_ok else "error"
        }
    }
    
    return DataResponse(
        success=all_ok,
        code=200 if all_ok else 503,
        message=f"服务状态: {health_status}",
        data=health_data
    )




async def _check_scheduler() -> bool:
    """检查调度器状态 - 简化版本"""
    try:
        from .schedule.scheduler import scheduler
        return scheduler and scheduler.running
    except Exception:
        return False


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)