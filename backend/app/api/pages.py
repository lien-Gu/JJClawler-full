"""
页面配置接口

提供动态页面结构配置信息的API端点
使用PageService从配置文件获取页面信息
"""
from fastapi import APIRouter, HTTPException

from app.modules.service.page_service import get_page_service
from app.utils.response_utils import BaseResponse, success_response, error_response
from app.utils.error_codes import ErrorCodes

router = APIRouter(prefix="/pages", tags=["页面配置"])


@router.get("", response_model=BaseResponse[dict])
async def get_pages():
    """
    获取页面配置
    
    从配置文件动态获取页面结构配置，
    用于生成导航和页面布局
    """
    try:
        page_service = get_page_service()
        config_pages = page_service.get_all_pages()
        
        # 转换为API响应格式
        pages = []
        
        # 榜单页面
        ranking_sub_pages = []
        for config_page in config_pages:
            if config_page.get('parent_id') is None:  # 只处理根页面
                rankings = []
                for ranking in config_page.get('rankings', []):
                    rankings.append({
                        "ranking_id": ranking['ranking_id'],
                        "name": ranking['name'],
                        "update_frequency": ranking['update_frequency']
                    })
                
                # 构建子页面路径
                page_path = f"/rankings/{config_page['page_id']}"
                ranking_sub_pages.append({
                    "name": config_page['name'],
                    "path": page_path,
                    "rankings": rankings
                })
        
        # 主榜单页面
        pages.append({
            "name": "榜单页面",
            "path": "/rankings",
            "sub_pages": ranking_sub_pages
        })
        
        # 书籍页面
        pages.append({
            "name": "书籍页面",
            "path": "/books",
            "sub_pages": [
                {
                    "name": "书籍搜索",
                    "path": "/books/search",
                    "rankings": []
                },
                {
                    "name": "书籍详情",
                    "path": "/books/detail",
                    "rankings": []
                }
            ]
        })
        
        # 爬虫管理页面
        pages.append({
            "name": "爬虫管理",
            "path": "/crawl",
            "sub_pages": [
                {
                    "name": "任务管理",
                    "path": "/crawl/tasks",
                    "rankings": []
                },
                {
                    "name": "任务监控",
                    "path": "/crawl/monitor",
                    "rankings": []
                }
            ]
        })
        
        # 计算榜单总数
        total_rankings = sum(
            len(sub_page["rankings"]) 
            for page in pages 
            for sub_page in page["sub_pages"]
        )
        
        return success_response(
            data={
                "pages": pages,
                "total_pages": len(pages),
                "total_rankings": total_rankings
            },
            message="获取页面配置成功"
        )
        
    except Exception as e:
        error_resp = error_response(code=ErrorCodes.CONFIG_ERROR, message="获取页面配置失败")
        raise HTTPException(
            status_code=500, 
            detail=error_resp.model_dump()
        )


@router.get("/statistics", response_model=BaseResponse[dict])
async def get_page_statistics():
    """
    获取页面统计信息
    
    Returns:
        页面配置统计数据
    """
    try:
        page_service = get_page_service()
        stats = page_service.get_page_statistics()
        
        # 添加fake标识用于前端识别
        stats["meta"] = {
            "fake": False,
            "message": "Real page statistics from configuration",
            "timestamp": datetime.now().isoformat()
        }
        
        return success_response(
            data=stats,
            message="获取页面统计成功"
        )
    except Exception as e:
        # 如果获取失败，返回假数据
        from datetime import datetime
        fake_stats = {
            "total_pages": 7,
            "root_pages": 3,
            "sub_pages": 4,
            "total_rankings": 23,
            "config_path": "data/urls.json",
            "cache_valid": True,
            "last_updated": datetime.now().isoformat(),
            "meta": {
                "fake": True,
                "message": "Fake page statistics for development",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        }
        return success_response(
            data=fake_stats,
            message="获取页面统计成功（使用默认数据）"
        )


@router.post("/refresh", response_model=BaseResponse[dict])
async def refresh_page_config():
    """
    刷新页面配置缓存
    
    Returns:
        操作结果
    """
    try:
        from datetime import datetime
        page_service = get_page_service()
        page_service.refresh_config()
        return success_response(
            data={
                "timestamp": datetime.now().isoformat(),
                "config_reloaded": True
            },
            message="页面配置缓存已刷新"
        )
    except Exception as e:
        error_resp = error_response(code=ErrorCodes.CONFIG_ERROR, message="刷新配置失败")
        raise HTTPException(
            status_code=500, 
            detail=error_resp.model_dump()
        )