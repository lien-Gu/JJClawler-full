"""
页面配置接口

提供页面和榜单配置信息的API端点
"""
from fastapi import APIRouter, Depends
from app.schemas.pages import PagesResponse, PageConfig, SubPageConfig, RankingConfig

router = APIRouter(prefix="/pages", tags=["页面配置"])


@router.get("", response_model=PagesResponse)
async def get_pages():
    """
    获取所有页面配置
    
    返回系统中所有页面和榜单的配置信息，
    基于urls.json文件生成结构化数据
    """
    # Mock数据 - 基于实际urls.json结构设计
    mock_pages = [
        PageConfig(
            page_id="index",
            name="首页",
            rankings=[
                RankingConfig(
                    ranking_id="jiazi",
                    name="夹子",
                    channel="favObservation",
                    frequency="hourly",
                    update_interval=1
                )
            ],
            sub_pages=[]
        ),
        PageConfig(
            page_id="yq",
            name="言情",
            rankings=[],
            sub_pages=[
                SubPageConfig(
                    short_name="gy",
                    name="古言",
                    rankings=[
                        RankingConfig(
                            ranking_id="yq_gy",
                            name="言情-古言",
                            channel="gywx",
                            frequency="hourly",
                            update_interval=2
                        )
                    ]
                ),
                SubPageConfig(
                    short_name="xy",
                    name="现言", 
                    rankings=[
                        RankingConfig(
                            ranking_id="yq_xy",
                            name="言情-现言",
                            channel="dsyq",
                            frequency="daily",
                            update_interval=24
                        )
                    ]
                )
            ]
        ),
        PageConfig(
            page_id="ca",
            name="纯爱",
            rankings=[],
            sub_pages=[
                SubPageConfig(
                    short_name="ds",
                    name="都市",
                    rankings=[
                        RankingConfig(
                            ranking_id="ca_ds",
                            name="纯爱-都市",
                            channel="xddm",
                            frequency="hourly",
                            update_interval=2
                        )
                    ]
                ),
                SubPageConfig(
                    short_name="gd",
                    name="古代",
                    rankings=[
                        RankingConfig(
                            ranking_id="ca_gd",
                            name="纯爱-古代",
                            channel="gddm",
                            frequency="daily",
                            update_interval=24
                        )
                    ]
                )
            ]
        )
    ]
    
    # 计算统计信息
    total_rankings = 0
    for page in mock_pages:
        total_rankings += len(page.rankings)
        for sub_page in page.sub_pages:
            total_rankings += len(sub_page.rankings)
    
    return PagesResponse(
        pages=mock_pages,
        total_pages=len(mock_pages),
        total_rankings=total_rankings
    )