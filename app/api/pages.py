"""
页面配置接口

提供静态页面结构配置信息的API端点
"""
from fastapi import APIRouter
from app.modules.models import PagesResponse, PageConfig, SubPageConfig, RankingConfig

router = APIRouter(prefix="/pages", tags=["页面配置"])


@router.get("", response_model=PagesResponse)
async def get_pages():
    """
    获取页面配置
    
    返回前端需要的静态页面结构配置，
    用于生成导航和页面布局
    """
    # 静态页面配置（不依赖数据库）
    pages = [
        PageConfig(
            name="榜单页面",
            path="/rankings",
            sub_pages=[
                SubPageConfig(
                    name="夹子榜",
                    path="/rankings/jiazi",
                    rankings=[
                        RankingConfig(
                            ranking_id="jiazi",
                            name="夹子",
                            update_frequency="hourly"
                        )
                    ]
                ),
                SubPageConfig(
                    name="言情榜单",
                    path="/rankings/romance", 
                    rankings=[
                        RankingConfig(
                            ranking_id="yq_gy",
                            name="言情-古言",
                            update_frequency="hourly"
                        ),
                        RankingConfig(
                            ranking_id="yq_xy",
                            name="言情-现言",
                            update_frequency="daily"
                        )
                    ]
                ),
                SubPageConfig(
                    name="纯爱榜单",
                    path="/rankings/bl",
                    rankings=[
                        RankingConfig(
                            ranking_id="ca_ds",
                            name="纯爱-都市",
                            update_frequency="hourly"
                        ),
                        RankingConfig(
                            ranking_id="ca_gd",
                            name="纯爱-古代",
                            update_frequency="daily"
                        )
                    ]
                )
            ]
        ),
        PageConfig(
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
        ),
        PageConfig(
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
        )
    ]
    
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