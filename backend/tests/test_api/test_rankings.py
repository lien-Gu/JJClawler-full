"""
榜单相关API测试
"""
from fastapi.testclient import TestClient


class TestRankingsAPI:
    """榜单API测试类"""

    def test_get_rankings_list(self, client: TestClient):
        """测试获取榜单列表API"""
        response = client.get("/api/v1/rankings")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data

        assert "message" in data
        assert isinstance(data["data"], list)

    def test_get_ranking_detail(self, client: TestClient):
        """测试获取榜单详情API"""
        ranking_id = 1
        response = client.get(f"/api/v1/rankings/{ranking_id}")

        if response.status_code == 404:
            assert response.json()["detail"] == "榜单不存在"
        else:
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            ranking_data = data["data"]
            assert "ranking_id" in ranking_data
            assert "name" in ranking_data
            assert "category" in ranking_data

    def test_get_ranking_history(self, client: TestClient):
        """测试获取榜单历史API"""
        ranking_id = 1
        response = client.get(f"/api/v1/rankings/{ranking_id}/history")
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            history_data = data["data"]
            assert "history_data" in history_data
            assert isinstance(history_data["history_data"], list)

    def test_get_ranking_statistics(self, client: TestClient):
        """测试获取榜单统计API"""
        ranking_id = 1
        response = client.get(f"/api/v1/rankings/{ranking_id}/stats")
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            stats_data = data["data"]
            assert "ranking_id" in stats_data
            assert "ranking_name" in stats_data

    def test_get_ranking_not_found(self, client: TestClient):
        """测试获取不存在的榜单"""
        response = client.get("/api/v1/rankings/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "榜单不存在"

    def test_ranking_response_format(self, client: TestClient):
        """测试榜单响应格式"""
        response = client.get("/api/v1/rankings")
        assert response.status_code == 200
        data = response.json()

        # 检查响应格式
        assert isinstance(data, dict)
        assert "data" in data
        assert "count" in data
        assert "message" in data

        # 检查榜单数据格式
        if data["data"]:
            ranking = data["data"][0]
            required_fields = ["ranking_id", "name", "category"]
            for field in required_fields:
                assert field in ranking

    def test_ranking_error_handling(self, client: TestClient):
        """测试榜单API错误处理"""
        # 测试无效的榜单ID
        response = client.get("/api/v1/rankings/invalid_id")
        assert response.status_code == 422  # 验证错误

        # 测试无效的页码
        response = client.get("/api/v1/rankings?page=-1")
        assert response.status_code == 422  # 验证错误

        # 测试无效的每页大小
        response = client.get("/api/v1/rankings?size=0")
        assert response.status_code == 422  # 验证错误
