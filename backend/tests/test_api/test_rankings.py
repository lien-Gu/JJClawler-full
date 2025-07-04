"""
榜单相关API测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime


class TestRankingsAPI:
    """榜单API测试类"""
    
    def test_get_rankings_list(self, client: TestClient):
        """测试获取榜单列表API"""
        response = client.get("/api/v1/rankings")
        assert response.status_code == 200
        data = response.json()
        assert "rankings" in data
        assert isinstance(data["rankings"], list)
    
    def test_get_ranking_detail(self, client: TestClient):
        """测试获取榜单详情API"""
        ranking_id = 1
        response = client.get(f"/api/v1/rankings/{ranking_id}")
        
        if response.status_code == 404:
            assert response.json()["detail"] == "Ranking not found"
        else:
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "name" in data
            assert "type" in data
            assert "url" in data
    
    def test_get_ranking_snapshots(self, client: TestClient):
        """测试获取榜单快照数据API"""
        ranking_id = 1
        response = client.get(f"/api/v1/rankings/{ranking_id}/snapshots")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "snapshots" in data
            assert isinstance(data["snapshots"], list)
    
    def test_get_ranking_snapshots_with_date_range(self, client: TestClient):
        """测试带日期范围的榜单快照API"""
        ranking_id = 1
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        response = client.get(
            f"/api/v1/rankings/{ranking_id}/snapshots"
            f"?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code in [200, 404]
    
    def test_get_jiazi_ranking(self, client: TestClient):
        """测试获取夹子榜API"""
        response = client.get("/api/v1/rankings/jiazi")
        assert response.status_code == 200
        data = response.json()
        assert "ranking" in data
        assert "books" in data
        assert isinstance(data["books"], list)
    
    def test_get_jiazi_ranking_with_limit(self, client: TestClient):
        """测试获取限定数量的夹子榜API"""
        response = client.get("/api/v1/rankings/jiazi?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert len(data["books"]) <= 10
    
    def test_get_category_rankings(self, client: TestClient):
        """测试获取分类榜单API"""
        response = client.get("/api/v1/rankings/category/现代言情")
        assert response.status_code == 200
        data = response.json()
        assert "ranking" in data
        assert "books" in data
        assert isinstance(data["books"], list)
    
    def test_get_latest_rankings(self, client: TestClient):
        """测试获取最新榜单API"""
        response = client.get("/api/v1/rankings/latest")
        assert response.status_code == 200
        data = response.json()
        assert "rankings" in data
        assert isinstance(data["rankings"], list)
    
    def test_get_ranking_history(self, client: TestClient):
        """测试获取榜单历史API"""
        ranking_id = 1
        response = client.get(f"/api/v1/rankings/{ranking_id}/history")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "history" in data
            assert isinstance(data["history"], list)
    
    def test_get_ranking_trends(self, client: TestClient):
        """测试获取榜单趋势API"""
        ranking_id = 1
        response = client.get(f"/api/v1/rankings/{ranking_id}/trends")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "trends" in data
            assert isinstance(data["trends"], dict)
    
    def test_get_ranking_statistics(self, client: TestClient):
        """测试获取榜单统计API"""
        ranking_id = 1
        response = client.get(f"/api/v1/rankings/{ranking_id}/statistics")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "statistics" in data
            assert isinstance(data["statistics"], dict)
    
    def test_get_active_rankings(self, client: TestClient):
        """测试获取活跃榜单API"""
        response = client.get("/api/v1/rankings/active")
        assert response.status_code == 200
        data = response.json()
        assert "rankings" in data
        assert isinstance(data["rankings"], list)
    
    def test_get_ranking_by_type(self, client: TestClient):
        """测试按类型获取榜单API"""
        response = client.get("/api/v1/rankings/by-type/jiazi")
        assert response.status_code == 200
        data = response.json()
        assert "rankings" in data
        assert isinstance(data["rankings"], list)
    
    def test_get_ranking_not_found(self, client: TestClient):
        """测试获取不存在的榜单"""
        response = client.get("/api/v1/rankings/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Ranking not found"
    
    def test_ranking_response_format(self, client: TestClient):
        """测试榜单响应格式"""
        response = client.get("/api/v1/rankings")
        assert response.status_code == 200
        data = response.json()
        
        # 检查响应格式
        assert isinstance(data, dict)
        assert "rankings" in data
        
        # 检查榜单数据格式
        if data["rankings"]:
            ranking = data["rankings"][0]
            required_fields = ["id", "name", "type", "url"]
            for field in required_fields:
                assert field in ranking
    
    def test_ranking_error_handling(self, client: TestClient):
        """测试榜单API错误处理"""
        # 测试无效的榜单ID
        response = client.get("/api/v1/rankings/invalid_id")
        assert response.status_code == 422  # 验证错误
        
        # 测试无效的限制数量
        response = client.get("/api/v1/rankings/jiazi?limit=-1")
        assert response.status_code == 422  # 验证错误
        
        # 测试无效的日期格式
        response = client.get("/api/v1/rankings/1/snapshots?start_date=invalid")
        assert response.status_code == 422  # 验证错误 