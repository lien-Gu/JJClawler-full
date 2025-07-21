"""
FastAPI应用程序入口
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import api_router
from .config import get_settings
from .middleware import ExceptionMiddleware
from .models.base import BaseResponse, DataResponse, HealthData, ComponentHealth, SystemInfo

# 应用启动时间
APP_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    # 启动时的初始化代码
    print("应用程序启动")

    # 启动调度器
    try:
        from .schedule import start_scheduler

        await start_scheduler()
        print("任务调度器启动成功")
    except Exception as e:
        print(f"任务调度器启动失败: {e}")

    yield

    # 关闭时的清理代码
    try:
        from .schedule import stop_scheduler

        await stop_scheduler()
        print("任务调度器已停止")
    except Exception as e:
        print(f"任务调度器停止失败: {e}")

    print("应用程序关闭")


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
    return await _create_unified_error_response(request, exc.status_code, exc.detail)


# 添加Starlette HTTP异常处理器（路由未找到等）
@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Starlette HTTP异常处理器 - 使用统一的响应格式"""
    detail = exc.detail if hasattr(exc, 'detail') else "页面未找到"
    return await _create_unified_error_response(request, exc.status_code, detail)


async def _create_unified_error_response(request: Request, status_code: int, detail: str):
    """创建统一的错误响应格式"""
    error_response = BaseResponse(
        success=False,
        code=status_code,
        message=detail,
    )

    # 转换为字典并添加错误详情（使用mode='json'确保datetime正确序列化）
    error_data = error_response.model_dump(mode='json')
    error_data["error"] = {
        "type": "HTTP_ERROR",
        "detail": detail,
        "path": str(request.url.path),
        "method": request.method,
    }

    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


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
    """健康检查 - 检查数据库、调度器、系统资源等"""
    settings = get_settings()
    components = {}
    overall_status = "healthy"

    # 检查数据库连接
    from database.connection import check_db
    db_component = await check_db()
    components["database"] = db_component

    # 检查调度器状态
    scheduler_component = await _check_scheduler()
    components.append(scheduler_component)

    # 检查网络连接（可选）
    network_component = await _check_network()
    components.append(network_component)

    # 获取系统信息
    system_info = await _get_system_info()

    # 计算运行时间
    uptime = time.time() - APP_START_TIME

    # 确定整体状态
    if any(comp.status == "unhealthy" for comp in components):
        overall_status = "unhealthy"
    elif any(comp.status == "degraded" for comp in components):
        overall_status = "degraded"

    health_data = {

    }


    return DataResponse(
        success=overall_status != "unhealthy",
        code=200 if overall_status != "unhealthy" else 503,
        message=f"服务状态: {overall_status}",
        data=health_data
    )





async def _check_scheduler() -> ComponentHealth:
    """检查调度器状态"""
    try:
        from .schedule.scheduler import scheduler

        if scheduler and scheduler.running:
            jobs = scheduler.get_jobs()
            return ComponentHealth(
                name="scheduler",
                status="healthy",
                message="调度器运行正常",
                details={
                    "running": True,
                    "jobs_count": len(jobs),
                    "next_run": str(min([job.next_run_time for job in jobs], default="N/A"))
                }
            )
        else:
            return ComponentHealth(
                name="scheduler",
                status="degraded",
                message="调度器未运行",
                details={"running": False}
            )
    except Exception as e:
        return ComponentHealth(
            name="scheduler",
            status="unhealthy",
            message=f"调度器检查失败: {str(e)[:100]}",
            details={"error": str(e)}
        )


async def _check_network() -> ComponentHealth:
    """检查网络连接状态（测试外部网络）"""
    try:
        import httpx

        timeout = httpx.Timeout(5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get("https://httpbin.org/status/200")
            if response.status_code == 200:
                return ComponentHealth(
                    name="network",
                    status="healthy",
                    message="网络连接正常",
                    details={"external_access": True, "test_url": "httpbin.org"}
                )
            else:
                return ComponentHealth(
                    name="network",
                    status="degraded",
                    message=f"网络连接异常: {response.status_code}",
                    details={"external_access": False, "status_code": response.status_code}
                )
    except Exception as e:
        return ComponentHealth(
            name="network",
            status="degraded",
            message=f"网络检查失败: {str(e)[:100]}",
            details={"error": str(e), "external_access": False}
        )


async def _get_system_info() -> SystemInfo:
    """获取系统资源信息"""
    try:
        import psutil

        # 获取系统资源信息
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu = psutil.cpu_percent(interval=0.1)

        return SystemInfo(
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            cpu_usage=cpu
        )
    except ImportError:
        # psutil未安装，返回空信息
        return SystemInfo()
    except Exception:
        # 其他错误，返回空信息
        return SystemInfo()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
