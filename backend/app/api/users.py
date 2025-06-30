"""
用户相关接口

提供用户统计和关注功能的API端点
"""
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter

from app.utils.service_utils import handle_api_error
from app.utils.response_utils import ApiResponse, success_response, error_response

router = APIRouter(prefix="/user", tags=["用户信息"])


@router.get("/stats", response_model=ApiResponse[dict])
async def get_user_stats():
    """
    获取用户统计信息
    
    返回用户相关的统计数据，包括关注数量、浏览历史等
    """
    try:
        # 生成假数据用于前端测试
        fake_user_stats = {
            "user_id": "fake_user_001",
            "total_follows": 12,
            "total_bookmarks": 28,
            "total_views": 156,
            "recent_activities": 8,
            "favorite_genres": [
                {"genre": "言情", "count": 15},
                {"genre": "悬疑", "count": 8},
                {"genre": "科幻", "count": 5}
            ],
            "reading_time_minutes": 2340,
            "last_active": datetime.now().isoformat(),
            "join_date": "2024-01-15T10:30:00Z",
            "meta": {
                "fake": True,
                "message": "This is fake data for development",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return success_response(
            data=fake_user_stats,
            message="获取用户统计成功"
        )
        
    except Exception as e:
        handle_api_error(e, "获取用户统计")


@router.get("/follows", response_model=ApiResponse[dict])
async def get_user_follows():
    """
    获取用户关注列表
    
    返回用户关注的榜单和书籍列表
    """
    try:
        # 生成假数据用于前端测试
        fake_follows = [
            {
                "id": "follow_001",
                "type": "ranking",
                "name": "夹子榜",
                "description": "最受欢迎的作品榜单",
                "followed_at": "2024-06-20T14:30:00Z",
                "last_updated": "2024-06-24T12:00:00Z",
                "total_books": 100,
                "update_frequency": "每小时"
            },
            {
                "id": "follow_002", 
                "type": "ranking",
                "name": "言情周榜",
                "description": "言情类作品周排行",
                "followed_at": "2024-06-18T09:15:00Z",
                "last_updated": "2024-06-24T08:00:00Z",
                "total_books": 50,
                "update_frequency": "每天"
            },
            {
                "id": "follow_003",
                "type": "book", 
                "name": "重生之农女当家",
                "description": "古代言情小说",
                "author": "梦笔生花",
                "followed_at": "2024-06-22T16:45:00Z",
                "last_updated": "2024-06-24T20:30:00Z",
                "total_clicks": 123456,
                "total_favorites": 8901,
                "chapter_count": 156
            },
            {
                "id": "follow_004",
                "type": "book",
                "name": "星际战争编年史", 
                "description": "科幻军事小说",
                "author": "银河之光",
                "followed_at": "2024-06-19T11:20:00Z",
                "last_updated": "2024-06-24T18:15:00Z",
                "total_clicks": 98765,
                "total_favorites": 5432,
                "chapter_count": 203
            },
            {
                "id": "follow_005",
                "type": "ranking",
                "name": "纯爱月榜",
                "description": "纯爱类作品月排行", 
                "followed_at": "2024-06-21T13:10:00Z",
                "last_updated": "2024-06-24T06:00:00Z",
                "total_books": 30,
                "update_frequency": "每天"
            }
        ]
        
        follow_data = {
            "follows": fake_follows,
            "total_count": len(fake_follows),
            "rankings_count": len([f for f in fake_follows if f["type"] == "ranking"]),
            "books_count": len([f for f in fake_follows if f["type"] == "book"]),
            "meta": {
                "fake": True,
                "message": "This is fake data for development",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return success_response(
            data=follow_data,
            message="获取用户关注列表成功"
        )
        
    except Exception as e:
        handle_api_error(e, "获取用户关注列表")


@router.post("/follows", response_model=ApiResponse[dict])
async def add_user_follow():
    """
    添加用户关注
    
    添加榜单或书籍到用户关注列表
    """
    try:
        # 模拟添加关注操作
        follow_result = {
            "follow_id": f"follow_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "operation": "add_follow",
            "meta": {
                "fake": True,
                "message": "This is fake operation for development",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return success_response(
            data=follow_result,
            message="添加关注成功"
        )
        
    except Exception as e:
        handle_api_error(e, "添加用户关注")


@router.delete("/follows/{follow_id}", response_model=ApiResponse[dict])
async def remove_user_follow(follow_id: str):
    """
    取消用户关注
    
    从用户关注列表中移除指定项目
    """
    try:
        # 模拟取消关注操作
        remove_result = {
            "removed_id": follow_id,
            "operation": "remove_follow",
            "meta": {
                "fake": True,
                "message": "This is fake operation for development", 
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return success_response(
            data=remove_result,
            message=f"已取消关注 {follow_id}"
        )
        
    except Exception as e:
        handle_api_error(e, "取消用户关注")


@router.get("/profile", response_model=ApiResponse[dict])
async def get_user_profile():
    """
    获取用户基本信息
    
    返回用户的基本档案信息
    """
    try:
        # 生成假的用户档案数据
        fake_profile = {
            "user_id": "fake_user_001",
            "username": "游客用户",
            "email": None,
            "avatar": None,
            "status": "未登录",
            "preferences": {
                "theme": "light",
                "language": "zh-CN",
                "notifications": True,
                "auto_refresh": True
            },
            "statistics": {
                "total_follows": 12,
                "total_views": 156,
                "days_active": 25,
                "favorite_genre": "言情"
            },
            "created_at": "2024-01-15T10:30:00Z",
            "last_login": datetime.now().isoformat(),
            "meta": {
                "fake": True,
                "message": "This is fake user profile for development",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return success_response(
            data=fake_profile,
            message="获取用户档案成功"
        )
        
    except Exception as e:
        handle_api_error(e, "获取用户档案")