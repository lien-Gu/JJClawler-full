"""
页面配置接口

提供页面和榜单配置信息的API端点
"""
from fastapi import APIRouter, Depends
from app.modules.service import RankingService
from app.modules.models import PagesResponse, PageConfig, SubPageConfig, RankingConfig

router = APIRouter(prefix="/pages", tags=["页面配置"])


def get_ranking_service() -> RankingService:
    """获取Ranking服务实例"""
    return RankingService()


@router.get("", response_model=PagesResponse)
async def get_pages(ranking_service: RankingService = Depends(get_ranking_service)):
    """
    获取页面配置
    
    返回前端需要的页面结构和榜单配置信息，
    用于动态生成导航和页面
    """
    try:
        # 获取所有榜单配置
        rankings = ranking_service.get_all_rankings()
        
        # 构建页面配置
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
                                ranking_id=r.ranking_id,
                                name=r.name,
                                update_frequency=r.frequency.value
                            )
                            for r in rankings if "yq_" in r.ranking_id
                        ]
                    ),
                    SubPageConfig(
                        name="纯爱榜单",
                        path="/rankings/bl",
                        rankings=[
                            RankingConfig(
                                ranking_id=r.ranking_id,
                                name=r.name,
                                update_frequency=r.frequency.value
                            )
                            for r in rankings if "ca_" in r.ranking_id
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
            )
        ]
        
        total_rankings = len(rankings)
        
        return PagesResponse(
            pages=pages,
            total_pages=len(pages),
            total_rankings=total_rankings
        )
    finally:
        ranking_service.close()