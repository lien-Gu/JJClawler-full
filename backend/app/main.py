"""
FastAPI应用程序入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import api_router
from .middleware import ExceptionMiddleware
from .models.base import BaseResponse


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


@app.get("/")
async def root():
    """根路径"""
    return {"message": "JJCrawler API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    from datetime import datetime

    return {
        "status": "healthy",
        "message": "API is running",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
