"""
API模块 - 定义HTTP接口端点
"""

from fastapi import APIRouter
from .books import router as books_router
from .rankings import router as rankings_router
from .crawl import router as crawl_router

# 创建主API路由器
api_router = APIRouter(prefix="/api/v1")

# 注册子路由
api_router.include_router(books_router, prefix="/books", tags=["books"])
api_router.include_router(rankings_router, prefix="/rankings", tags=["rankings"]) 
api_router.include_router(crawl_router, prefix="/crawl", tags=["crawl"])

__all__ = ["api_router"] 