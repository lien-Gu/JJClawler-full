"""
页面配置相关的数据模型
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class RankingConfig(BaseModel):
    """榜单配置"""
    ranking_id: str = Field(..., description="榜单ID")
    name: str = Field(..., description="榜单中文名")
    channel: str = Field(..., description="API频道参数")
    frequency: str = Field(..., description="更新频率")
    update_interval: int = Field(..., description="更新间隔(小时)")


class SubPageConfig(BaseModel):
    """子页面配置"""
    short_name: str = Field(..., description="短名称")
    name: str = Field(..., description="中文名称")
    rankings: List[RankingConfig] = Field(default_factory=list, description="包含的榜单")


class PageConfig(BaseModel):
    """页面配置"""
    page_id: str = Field(..., description="页面ID")
    name: str = Field(..., description="页面中文名")
    rankings: List[RankingConfig] = Field(default_factory=list, description="直接包含的榜单")
    sub_pages: List[SubPageConfig] = Field(default_factory=list, description="子页面")


class PagesResponse(BaseModel):
    """页面配置响应"""
    pages: List[PageConfig] = Field(..., description="所有页面配置")
    total_pages: int = Field(..., description="总页面数")
    total_rankings: int = Field(..., description="总榜单数")