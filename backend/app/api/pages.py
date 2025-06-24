"""
页面配置接口

提供动态页面结构配置信息的API端点
使用PageService从配置文件获取页面信息
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.modules.models import PagesResponse, PageConfig, SubPageConfig, RankingConfig
from app.modules.service.page_service import get_page_service

router = APIRouter(prefix="/pages", tags=["页面配置"])


@router.get("", response_model=PagesResponse)
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
                    rankings.append(RankingConfig(
                        ranking_id=ranking['ranking_id'],
                        name=ranking['name'],
                        update_frequency=ranking['update_frequency']
                    ))
                
                # 构建子页面路径
                page_path = f"/rankings/{config_page['page_id']}"
                ranking_sub_pages.append(SubPageConfig(
                    name=config_page['name'],
                    path=page_path,
                    rankings=rankings
                ))
        
        # 主榜单页面
        pages.append(PageConfig(
            name="榜单页面",
            path="/rankings",
            sub_pages=ranking_sub_pages
        ))
        
        # 书籍页面
        pages.append(PageConfig(
            name="书籍页面",
            path="/books",
            sub_pages=[
                SubPageConfig(
                    name="书籍搜索",
                    path="/books/search",
                    rankings=[]
                ),
                SubPageConfig(
                    name="书籍详情",
                    path="/books/detail",
                    rankings=[]
                )
            ]
        ))
        
        # 爬虫管理页面
        pages.append(PageConfig(
            name="爬虫管理",
            path="/crawl",
            sub_pages=[
                SubPageConfig(
                    name="任务管理",
                    path="/crawl/tasks",
                    rankings=[]
                ),
                SubPageConfig(
                    name="任务监控",
                    path="/crawl/monitor",
                    rankings=[]
                )
            ]
        ))
        
        # 计算榜单总数
        total_rankings = sum(
            len(sub_page.rankings) 
            for page in pages 
            for sub_page in page.sub_pages
        )
        
        return PagesResponse(
            pages=pages,
            total_pages=len(pages),
            total_rankings=total_rankings
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取页面配置失败: {str(e)}")


@router.get("/statistics")
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
        
        return stats
    except Exception as e:
        # 如果获取失败，返回假数据
        from datetime import datetime
        return {
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


@router.post("/refresh")
async def refresh_page_config():
    """
    刷新页面配置缓存
    
    Returns:
        操作结果
    """
    try:
        page_service = get_page_service()
        page_service.refresh_config()
        return {"message": "页面配置缓存已刷新", "timestamp": ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新配置失败: {str(e)}")