"""
榜单API接口测试文件
测试app.api.rankings模块的所有接口
"""




class TestGetRankings:
    """测试获取榜单列表接口"""

    def test_get_rankings_success(self, client, mocker, mock_ranking_data):
        """测试成功获取榜单列表"""
        # 模拟RankingService
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        mock_service.get_all_rankings.return_value = {
            "rankings": [
                type("MockRanking", (), ranking)()
                for ranking in mock_ranking_data["ranking_list"]
            ],
            "total": 2,
        }

        # 发送请求
        response = client.get("/api/v1/rankings/?page=1&size=20")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "榜单列表获取成功"
        assert data["count"] == 2
        assert len(data["data"]) == 2

        # 验证service调用
        mock_service.get_all_rankings.assert_called_once()

    def test_get_rankings_with_filter(self, client, mocker, mock_ranking_data):
        """测试使用分组类型筛选获取榜单"""
        # 模拟service
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        mock_service.get_all_rankings.return_value = {
            "rankings": [
                type("MockRanking", (), mock_ranking_data["ranking_list"][0])()
            ],
            "total": 1,
        }

        # 发送请求
        response = client.get("/api/v1/rankings/?group_type=热门&page=1&size=20")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 1

        # 验证service调用
        mock_service.get_all_rankings.assert_called_once()

    def test_get_rankings_service_error(self, client, mocker):
        """测试服务层异常"""
        # 模拟service抛出异常
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        mock_service.get_all_rankings.side_effect = Exception("数据库连接失败")

        # 发送请求
        response = client.get("/api/v1/rankings/?page=1&size=20")

        # 验证响应
        assert response.status_code == 500
        data = response.json()
        assert "获取榜单列表失败" in data["detail"]


class TestGetRankingDetail:
    """测试获取榜单详情接口"""

    def test_get_ranking_detail_success(self, client, mocker, mock_ranking_data):
        """测试成功获取榜单详情"""
        # 模拟service
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        ranking_detail = mock_ranking_data["ranking_detail"]
        ranking_detail["ranking"] = type("MockRanking", (), ranking_detail["ranking"])()
        mock_service.get_ranking_detail_by_day.return_value = ranking_detail

        # 发送请求
        response = client.get("/api/v1/rankings/1?limit=50")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "榜单详情获取成功"
        assert data["data"]["ranking_id"] == 1
        assert data["data"]["name"] == "测试榜单"
        assert data["data"]["total_books"] == 2
        assert len(data["data"]["books"]) == 2

        # 验证service调用
        mock_service.get_ranking_detail_by_day.assert_called_once()

    def test_get_ranking_detail_with_date(self, client, mocker, mock_ranking_data):
        """测试指定日期获取榜单详情"""
        # 模拟service
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        ranking_detail = mock_ranking_data["ranking_detail"]
        ranking_detail["ranking"] = type("MockRanking", (), ranking_detail["ranking"])()
        mock_service.get_ranking_detail_by_day.return_value = ranking_detail

        # 发送请求
        response = client.get("/api/v1/rankings/1?date=2024-01-15&limit=50")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证service调用
        mock_service.get_ranking_detail_by_day.assert_called_once()

    def test_get_ranking_detail_not_found(self, client, mocker):
        """测试榜单不存在"""
        # 模拟service返回None
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        mock_service.get_ranking_detail_by_day.return_value = None

        # 发送请求
        response = client.get("/api/v1/rankings/999")

        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "榜单不存在"


class TestGetRankingHistory:
    """测试获取榜单历史接口"""

    def test_get_ranking_history_success(self, client, mocker):
        """测试成功获取榜单历史"""
        # 模拟service
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        from datetime import datetime

        mock_service.get_ranking_history.return_value = {
            "trend_data": [
                {"snapshot_time": datetime(2024, 1, 14)},
                {"snapshot_time": datetime(2024, 1, 15)},
            ]
        }

        # 发送请求
        response = client.get(
            "/api/v1/rankings/1/history?start_date=2024-01-01&end_date=2024-01-15"
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "榜单历史数据获取成功"
        assert data["data"]["ranking_id"] == 1
        assert len(data["data"]["history_data"]) == 2

        # 验证service调用
        mock_service.get_ranking_history.assert_called_once()

    def test_get_ranking_history_no_dates(self, client, mocker):
        """测试不指定日期获取榜单历史"""
        # 模拟service
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        mock_service.get_ranking_history.return_value = {"trend_data": []}

        # 发送请求
        response = client.get("/api/v1/rankings/1/history")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证service调用（start_date和end_date应该为None）
        mock_service.get_ranking_history.assert_called_once()


class TestGetRankingStats:
    """测试获取榜单统计接口"""

    def test_get_ranking_stats_success(
        self, client, mocker, mock_ranking_data, mock_ranking_stats
    ):
        """测试成功获取榜单统计"""
        # 模拟service
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        mock_service.get_ranking_by_id.return_value = type(
            "MockRanking", (), mock_ranking_data["ranking"]
        )()
        mock_service.get_ranking_statistics.return_value = mock_ranking_stats

        # 发送请求
        response = client.get("/api/v1/rankings/1/stats")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "榜单统计信息获取成功"
        assert data["data"]["ranking_id"] == 1
        assert data["data"]["ranking_name"] == "测试榜单"
        assert data["data"]["total_snapshots"] == 100
        assert data["data"]["unique_books"] == 50

        # 验证service调用
        mock_service.get_ranking_by_id.assert_called_once()
        mock_service.get_ranking_statistics.assert_called_once()

    def test_get_ranking_stats_not_found(self, client, mocker):
        """测试榜单不存在时获取统计"""
        # 模拟service返回None
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        mock_service.get_ranking_by_id.return_value = None

        # 发送请求
        response = client.get("/api/v1/rankings/999/stats")

        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "榜单不存在"


class TestCompareRankings:
    """测试榜单对比接口"""

    def test_compare_rankings_success(self, client, mocker, mock_comparison_data):
        """测试成功对比榜单"""
        # 模拟service
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        # 修改mock_comparison_data以匹配API期望的格式
        comparison_result = mock_comparison_data.copy()

        class MockRankingData:
            def __init__(self, data):
                self.data = data

            def get_by_id(self, ranking_id, default=[]):
                return self.data.get(ranking_id, default)

        comparison_result["ranking_data"] = MockRankingData(
            comparison_result["ranking_data"]
        )
        mock_service.compare_rankings.return_value = comparison_result

        # 发送请求
        request_data = {"ranking_ids": [1, 2], "date": "2024-01-15"}
        response = client.post("/api/v1/rankings/compare", json=request_data)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "榜单对比完成"
        assert len(data["data"]["rankings"]) == 2
        assert len(data["data"]["common_books"]) == 1
        assert "unique_books_count" in data["data"]

        # 验证service调用
        mock_service.compare_rankings.assert_called_once()

    def test_compare_rankings_insufficient_rankings(self, client):
        """测试榜单数量不足"""
        # 发送请求
        request_data = {"ranking_ids": [1], "date": "2024-01-15"}  # 只有一个榜单
        response = client.post("/api/v1/rankings/compare", json=request_data)

        # 验证响应
        assert response.status_code == 422  # Pydantic验证错误
        data = response.json()
        assert "detail" in data

    def test_compare_rankings_service_error(self, client, mocker):
        """测试对比服务异常"""
        # 模拟service抛出异常
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        mock_service.compare_rankings.side_effect = Exception("对比失败")

        # 发送请求
        request_data = {"ranking_ids": [1, 2], "date": "2024-01-15"}
        response = client.post("/api/v1/rankings/compare", json=request_data)

        # 验证响应
        assert response.status_code == 500
        data = response.json()
        assert "榜单对比失败" in data["detail"]


class TestRankingAPIValidation:
    """测试榜单API参数验证"""

    def test_invalid_page_parameter(self, client):
        """测试无效页码参数"""
        response = client.get("/api/v1/rankings/?page=0&size=20")
        assert response.status_code == 422  # 参数验证失败

    def test_invalid_size_parameter(self, client):
        """测试无效大小参数"""
        response = client.get("/api/v1/rankings/?page=1&size=0")
        assert response.status_code == 422  # 参数验证失败

    def test_invalid_limit_parameter(self, client):
        """测试无效限制参数"""
        response = client.get("/api/v1/rankings/1?limit=0")
        assert response.status_code == 422  # 参数验证失败

    def test_invalid_date_format(self, client):
        """测试无效日期格式"""
        response = client.get("/api/v1/rankings/1?date=invalid-date")
        assert response.status_code == 422  # 参数验证失败

    def test_invalid_json_body(self, client):
        """测试无效JSON请求体"""
        response = client.post("/api/v1/rankings/compare", json={})
        assert response.status_code == 422  # 缺少必需字段


class TestErrorHandling:
    """测试错误处理"""

    def test_unexpected_exception_handling(self, client, mocker):
        """测试未预期的异常处理"""
        # 模拟service抛出未预期异常
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        mock_service.get_all_rankings.side_effect = RuntimeError("未知错误")

        # 发送请求
        response = client.get("/api/v1/rankings/?page=1&size=20")

        # 验证响应
        assert response.status_code == 500
        data = response.json()
        assert "获取榜单列表失败" in data["detail"]
        assert "未知错误" in data["detail"]

    def test_http_exception_passthrough(self, client, mocker):
        """测试HTTPException直接传递"""
        # 模拟service返回None触发404
        mock_service = mocker.patch("app.api.rankings.ranking_service")
        mock_service.get_ranking_detail_by_day.return_value = None

        # 发送请求
        response = client.get("/api/v1/rankings/999")

        # 验证响应（HTTPException应该被直接传递）
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "榜单不存在"

    def test_database_connection_error(self, client, mocker):
        """测试数据库连接错误"""
        # 模拟get_db抛出异常
        mocker.patch("app.api.rankings.get_db", side_effect=Exception("数据库连接失败"))

        # 发送请求
        response = client.get("/api/v1/rankings/?page=1&size=20")

        # 验证响应
        assert response.status_code == 500
