"""
页面配置接口

提供动态页面结构配置信息的API端点
使用PageService从配置文件获取页面信息
"""
from fastapi import APIRouter, HTTPException

from app.modules.service.crawl_service import get_crawl_service
from app.utils.response_utils import ApiResponse, success_response, error_response
from app.utils.error_codes import StatusCode

router = APIRouter(prefix="/pages", tags=["页面配置"])


@router.get("", response_model=ApiResponse[dict])
async def get_pages():
    """
    获取页面配置
    
    从配置文件动态获取页面结构配置，
    用于生成导航和页面布局
    """
    try:
        crawl_service = get_crawl_service()
        crawl_pages = crawl_service.get_pages_hierarchy()

        # 转换为API响应格式
        pages = {}
        total_rankings = 0
        for key in crawl_pages.keys():
            pages[key] = [i.id for i in crawl_pages[key]]
            total_rankings += len(pages[key]) + 1

        return success_response(
            data={
                "pages": pages,
                "total_pages": len(pages),
                "total_rankings": total_rankings
            },
            message="获取页面配置成功"
        )

    except Exception as e:
        error_resp = error_response(code=StatusCode.CONFIG_ERROR, message="获取页面配置失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )


@router.post("/ids", response_model=ApiResponse[dict])
async def refresh_page_config():
    """
    查看当前集成了哪些页面

    Returns:
        操作结果
    """
    try:
        from datetime import datetime
        crawl_service = get_crawl_service()
        all_tasks = crawl_service.get_all_task_configs()
        ids = [task.id for task in all_tasks]
        return success_response(
            data={ids},
            message="获取所有页面的id"
        )
    except Exception as e:
        error_resp = error_response(code=StatusCode.CONFIG_ERROR, message="刷新配置失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )


@router.post("/refresh", response_model=ApiResponse[dict])
async def refresh_page_config():
    """
    刷新页面配置缓存
    
    Returns:
        操作结果
    """
    try:
        from datetime import datetime
        crawl_service = get_crawl_service()
        crawl_service.refresh_config()
        return success_response(
            data={
                "config_reloaded": True
            },
            message="页面配置缓存已刷新"
        )
    except Exception as e:
        error_resp = error_response(code=StatusCode.CONFIG_ERROR, message="刷新配置失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )
