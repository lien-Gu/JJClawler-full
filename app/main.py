"""
FastAPI 应用入口

晋江文学城爬虫后端服务主应用
"""
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, ensure_directories

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在启动 JJCrawler3 应用...")
    
    # 确保必要目录存在
    ensure_directories()
    logger.info("目录结构检查完成")
    
    # TODO: 初始化数据库连接
    # TODO: 启动任务调度器
    
    logger.info("应用启动完成")
    
    yield
    
    # 关闭时执行
    logger.info("正在关闭应用...")
    # TODO: 关闭数据库连接
    # TODO: 停止任务调度器
    logger.info("应用已关闭")


# 创建FastAPI应用实例
def create_app() -> FastAPI:
    """创建FastAPI应用"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="晋江文学城爬虫后端服务 - 提供榜单数据采集和API接口",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    setup_routes(app)
    
    return app


def setup_routes(app: FastAPI):
    """设置路由"""
    
    @app.get("/", tags=["基础"])
    async def root():
        """根路径 - 项目信息"""
        settings = get_settings()
        return {
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "message": "晋江文学城爬虫后端服务运行中",
            "docs": "/docs",
            "api": settings.API_V1_STR
        }
    
    @app.get("/health", tags=["基础"])
    async def health_check():
        """健康检查"""
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "jjcrawler3",
            "version": get_settings().VERSION
        }
    
    # 注册API v1路由
    from app.api import pages, rankings, books, crawl
    
    settings = get_settings()
    app.include_router(pages.router, prefix=settings.API_V1_STR)
    app.include_router(rankings.router, prefix=settings.API_V1_STR)
    app.include_router(books.router, prefix=settings.API_V1_STR)
    app.include_router(crawl.router, prefix=settings.API_V1_STR)


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )