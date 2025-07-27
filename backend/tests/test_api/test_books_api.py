"""
书籍API接口测试文件
测试app.api.books模块的所有接口
"""




class TestGetBooksList:
    """测试获取书籍列表接口"""

    def test_get_books_list_success(self, client, mocker, mock_pagination_data):
        """测试成功获取书籍列表"""
        # 模拟BookService
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.get_books_with_pagination.return_value = mock_pagination_data

        # 发送请求
        response = client.get("/api/v1/books/?page=1&size=20")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取书籍列表成功"
        assert data["count"] == 2
        assert len(data["data"]) == 2

        # 验证数据格式
        assert data["data"][0]["id"] == 1
        assert data["data"][0]["novel_id"] == 12345
        assert data["data"][0]["title"] == "测试小说1"
        assert data["data"][1]["id"] == 2
        assert data["data"][1]["novel_id"] == 12346
        assert data["data"][1]["title"] == "测试小说2"

        # 验证service被调用
        mock_service.get_books_with_pagination.assert_called_once()

    def test_get_books_list_invalid_page(self, client):
        """测试无效页码参数"""
        response = client.get("/api/v1/books/?page=0&size=20")
        assert response.status_code == 422  # 参数验证失败

    def test_get_books_list_service_error(self, client, mocker):
        """测试服务层异常"""
        # 模拟service抛出异常
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.get_books_with_pagination.side_effect = Exception("数据库连接失败")

        # 发送请求
        response = client.get("/api/v1/books/?page=1&size=20")

        # 验证响应
        assert response.status_code == 500
        data = response.json()
        assert "获取书籍列表失败" in data["detail"]


class TestSearchBooks:
    """测试搜索书籍接口"""

    def test_search_books_success(self, client, mocker, mock_search_results):
        """测试成功搜索书籍"""
        # 模拟BookService
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.search_books.return_value = mock_search_results

        # 发送请求
        response = client.get("/api/v1/books/search?keyword=测试&page=1&size=20")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "搜索成功"
        assert data["count"] == 2

        # 验证数据内容
        assert data["data"][0]["id"] == 1
        assert data["data"][0]["title"] == "搜索结果1"
        assert data["data"][1]["id"] == 2
        assert data["data"][1]["title"] == "搜索结果2"

        # 验证service被调用
        mock_service.search_books.assert_called_once()

    def test_search_books_empty_keyword(self, client):
        """测试空搜索关键词"""
        response = client.get("/api/v1/books/search?keyword=&page=1&size=20")
        assert response.status_code == 422  # 参数验证失败

    def test_search_books_no_results(self, client, mocker):
        """测试搜索无结果"""
        # 模拟service返回空结果
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.search_books.return_value = []

        # 发送请求
        response = client.get("/api/v1/books/search?keyword=不存在的书&page=1&size=20")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0
        assert len(data["data"]) == 0


class TestGetBookDetail:
    """测试获取书籍详情接口"""

    def test_get_book_detail_success(
        self, client, mocker, mock_book_data, mock_book_snapshot_data
    ):
        """测试成功获取书籍详情"""
        # 模拟service返回数据
        mock_service = mocker.patch("app.api.books.book_service")
        mock_book_obj = type("MockBook", (), mock_book_data["book"])()
        mock_service.get_book_by_novel_id.return_value = mock_book_obj
        mock_service.get_book_detail_by_novel_id.return_value = (
            mock_book_obj,
            type("MockSnapshot", (), mock_book_snapshot_data["latest_snapshot"])(),
        )

        # 发送请求（使用novel_id）
        response = client.get("/api/v1/books/12345")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "获取书籍详情成功"
        assert data["data"]["id"] == 1
        assert data["data"]["title"] == "测试小说"
        assert data["data"]["clicks"] == 50000

        # 验证service被调用
        mock_service.get_book_by_novel_id.assert_called_once_with(mocker.ANY, "12345")
        mock_service.get_book_detail_by_novel_id.assert_called_once()

    def test_get_book_detail_not_found(self, client, mocker):
        """测试书籍不存在"""
        # 模拟service抛出404异常
        from fastapi import HTTPException
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.get_book_by_novel_id.side_effect = HTTPException(
            status_code=404, detail="书籍不存在: 99999"
        )

        # 发送请求（使用novel_id）
        response = client.get("/api/v1/books/99999")

        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert "书籍不存在" in data["detail"]


class TestGetBookTrend:
    """测试获取书籍趋势接口"""

    def test_get_book_trend_success(
        self, client, mocker, mock_book_data, mock_book_snapshot_data
    ):
        """测试成功获取书籍趋势"""
        # 模拟service
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.get_book_by_id.return_value = type(
            "MockBook", (), mock_book_data["book"]
        )()
        mock_service.get_book_trend.return_value = [
            type("MockSnapshot", (), snapshot)()
            for snapshot in mock_book_snapshot_data["trend_snapshots"]
        ]

        # 发送请求
        response = client.get("/api/v1/books/1/trend?duration=day")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "获取24小时内每小时趋势数据成功" in data["message"]
        assert data["count"] == 2
        assert len(data["data"]) == 2

        # 验证service被调用
        mock_service.get_book_by_id.assert_called_once()
        mock_service.get_book_trend.assert_called_once()

    def test_get_book_trend_book_not_found(self, client, mocker):
        """测试书籍不存在时获取趋势"""
        # 模拟service返回None
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.get_book_by_id.return_value = None

        # 发送请求
        response = client.get("/api/v1/books/999/trend?duration=day")

        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "书籍不存在"

    def test_get_book_trend_different_durations(
        self, client, mocker, mock_book_data, mock_book_snapshot_data
    ):
        """测试不同的duration参数"""
        # 模拟service
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.get_book_by_id.return_value = type(
            "MockBook", (), mock_book_data["book"]
        )()
        mock_service.get_book_trend.return_value = [
            type("MockSnapshot", (), snapshot)()
            for snapshot in mock_book_snapshot_data["trend_snapshots"]
        ]

        duration_tests = [
            ("day", "获取24小时内每小时趋势数据成功"),
            ("week", "获取一周内每小时趋势数据成功"),
            ("month", "获取一个月内每天1点趋势数据成功"),
            ("half-year", "获取半年内每天1点趋势数据成功"),
        ]

        for duration, expected_message in duration_tests:
            # 发送请求
            response = client.get(f"/api/v1/books/1/trend?duration={duration}")

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert expected_message in data["message"]

    def test_get_book_trend_invalid_duration(self, client, mocker):
        """测试无效的duration参数"""
        # 发送请求
        response = client.get("/api/v1/books/1/trend?duration=invalid")

        # 验证响应
        assert response.status_code == 422  # FastAPI validation error


class TestGetBookTrendAggregated:
    """测试聚合趋势数据接口"""

    def test_get_book_trend_hourly_success(
        self, client, mocker, mock_book_data, mock_book_snapshot_data
    ):
        """测试成功获取小时级趋势"""
        # 模拟service
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.get_book_by_id.return_value = type(
            "MockBook", (), mock_book_data["book"]
        )()
        mock_service.get_book_trend_hourly.return_value = mock_book_snapshot_data[
            "aggregated_data"
        ]

        # 发送请求
        response = client.get("/api/v1/books/1/trend/hourly?hours=24")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "获取24小时的趋势数据成功" in data["message"]
        assert data["count"] == 1

    def test_get_book_trend_aggregated_success(
        self, client, mocker, mock_book_data, mock_book_snapshot_data
    ):
        """测试通用聚合趋势接口"""
        # 模拟service
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.get_book_by_id.return_value = type(
            "MockBook", (), mock_book_data["book"]
        )()
        mock_service.get_book_trend_with_interval.return_value = (
            mock_book_snapshot_data["aggregated_data"]
        )

        # 发送请求
        response = client.get(
            "/api/v1/books/1/trend/aggregated?period_count=7&interval=day"
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "获取7个天的聚合趋势数据成功" in data["message"]
        assert data["count"] == 1

        # 验证service被调用
        mock_service.get_book_by_id.assert_called_once()
        mock_service.get_book_trend_with_interval.assert_called_once()

    def test_get_book_trend_aggregated_invalid_interval(self, client):
        """测试无效的时间间隔参数"""
        response = client.get(
            "/api/v1/books/1/trend/aggregated?period_count=7&interval=invalid"
        )
        assert response.status_code == 422  # 参数验证失败


class TestGetBookRankingHistory:
    """测试获取书籍排名历史接口"""

    def test_get_book_ranking_history_success(
        self, client, mocker, mock_book_data
    ):
        """测试成功获取排名历史"""
        # 模拟book service
        mock_book_service = mocker.patch("app.api.books.book_service")
        mock_book_data_obj = type("MockBook", (), mock_book_data["book"])()
        mock_book_service.get_book_by_novel_id.return_value = mock_book_data_obj

        # 模拟ranking service返回详细历史数据
        mock_ranking_service = mocker.patch("app.api.books.ranking_service")
        mock_ranking_history_with_details = [
            {
                "ranking_id": 1,
                "ranking_name": "总点击榜",
                "position": 15,
                "score": 95000,
                "snapshot_time": "2023-10-15T12:00:00"
            },
            {
                "ranking_id": 2,
                "ranking_name": "收藏榜",
                "position": 8,
                "score": 75000,
                "snapshot_time": "2023-10-15T11:00:00"
            }
        ]
        mock_ranking_service.get_book_ranking_history_with_details.return_value = mock_ranking_history_with_details

        # 发送请求（使用novel_id而不是book_id）
        response = client.get("/api/v1/books/12345/rankings?ranking_id=1&days=30")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "获取2条排名历史成功" in data["message"]
        assert data["count"] == 2
        assert len(data["data"]) == 2
        
        # 验证数据结构 - 现在返回的是列表，不是包装对象
        first_item = data["data"][0]
        assert first_item["book_id"] == mock_book_data["book"]["id"]
        assert first_item["ranking_id"] == 1
        assert first_item["ranking_name"] == "总点击榜"
        assert first_item["position"] == 15

        # 验证service调用
        mock_book_service.get_book_by_novel_id.assert_called_once_with(mocker.ANY, "12345")
        mock_ranking_service.get_book_ranking_history_with_details.assert_called_once()

    def test_get_book_ranking_history_no_ranking_id(
        self, client, mocker, mock_book_data
    ):
        """测试不指定榜单ID获取排名历史"""
        # 模拟book service
        mock_book_service = mocker.patch("app.api.books.book_service")
        mock_book_data_obj = type("MockBook", (), mock_book_data["book"])()
        mock_book_service.get_book_by_novel_id.return_value = mock_book_data_obj

        # 模拟ranking service
        mock_ranking_service = mocker.patch("app.api.books.ranking_service")
        mock_ranking_service.get_book_ranking_history_with_details.return_value = []

        # 发送请求（不指定ranking_id）
        response = client.get("/api/v1/books/12345/rankings?days=30")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0

        # 验证service调用（ranking_id应该为None）
        mock_ranking_service.get_book_ranking_history_with_details.assert_called_once_with(
            mocker.ANY, mock_book_data_obj.id, None, 30
        )

    def test_get_book_ranking_history_book_not_found(self, client, mocker):
        """测试书籍不存在的情况"""
        # 模拟book service抛出404异常
        from fastapi import HTTPException
        mock_book_service = mocker.patch("app.api.books.book_service")
        mock_book_service.get_book_by_novel_id.side_effect = HTTPException(
            status_code=404, detail="书籍不存在: 99999"
        )

        # 发送请求
        response = client.get("/api/v1/books/99999/rankings?days=30")

        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert "书籍不存在" in data["detail"]


class TestErrorHandling:
    """测试错误处理"""

    def test_unexpected_exception_handling(self, client, mocker):
        """测试未预期的异常处理"""
        # 模拟service抛出未预期异常
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.get_books_with_pagination.side_effect = RuntimeError("未知错误")

        # 发送请求
        response = client.get("/api/v1/books/?page=1&size=20")

        # 验证响应
        assert response.status_code == 500
        data = response.json()
        assert "获取书籍列表失败" in data["detail"]
        assert "未知错误" in data["detail"]

    def test_http_exception_passthrough(self, client, mocker):
        """测试HTTPException直接传递"""
        # 模拟service返回None触发404
        mock_service = mocker.patch("app.api.books.book_service")
        mock_service.get_book_detail_by_novel_id.return_value = None

        # 发送请求
        response = client.get("/api/v1/books/999")

        # 验证响应（HTTPException应该被直接传递）
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "书籍不存在"
