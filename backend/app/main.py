"""
FastAPI应用程序入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api import api_router
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    # 启动时的初始化代码
    print("应用程序启动")
    yield
    # 关闭时的清理代码
    print("应用程序关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title="JJCrawler API",
    description="晋江文学城爬虫系统API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)