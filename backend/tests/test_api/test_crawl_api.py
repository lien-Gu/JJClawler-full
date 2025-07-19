"""
爬虫API模块测试文件
测试api.crawl模块的关键功能
"""



class TestCrawlAllPages:
    """测试爬取所有页面接口"""

    def test_crawl_all_pages_success(self, client, mocker, mock_scheduler_response):
        """测试成功爬取所有页面"""
        # 设置模拟
        mock_scheduler = mocker.patch("app.api.crawl.get_scheduler")
        mock_scheduler.return_value.add_batch_jobs = mocker.AsyncMock(
            return_value=mock_scheduler_response["success"]
        )

        # 发送请求
        response = client.post("/api/v1/crawl/all?force=false")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "batch_id" in data["data"]
        assert "task_ids" in data["data"]

        # 验证调度器调用
        mock_scheduler.return_value.add_batch_jobs.assert_called_once()

    def test_crawl_all_pages_failure(self, client, mocker, mock_scheduler_response):
        """测试爬取所有页面失败"""
        # 设置模拟
        mock_scheduler = mocker.patch("app.api.crawl.get_scheduler")
        mock_scheduler.return_value.add_batch_jobs = mocker.AsyncMock(
            return_value=mock_scheduler_response["failure"]
        )

        # 发送请求
        response = client.post("/api/v1/crawl/all")

        # 验证响应
        assert response.status_code == 500


class TestCrawlSpecificPages:
    """测试爬取指定页面接口"""

    def test_crawl_specific_pages_success(self, client, mocker):
        """测试成功爬取指定页面"""
        # 设置模拟
        mock_scheduler = mocker.patch("app.api.crawl.get_scheduler")
        mock_scheduler.return_value.add_batch_jobs = mocker.AsyncMock(
            return_value={
                "success": True,
                "message": "批量任务创建成功",
                "batch_id": "batch_20240101_120000",
                "task_ids": [
                    "crawl_jiazi_batch_20240101_120000",
                    "crawl_index_batch_20240101_120000",
                ],
                "total_pages": 2,
                "successful_tasks": 2,
            }
        )

        # 发送请求
        response = client.post("/api/v1/crawl/pages", json=["jiazi", "index"])

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_pages"] == 2
        assert data["data"]["successful_tasks"] == 2

        # 验证调度器调用
        mock_scheduler.return_value.add_batch_jobs.assert_called_once()

    def test_crawl_specific_pages_empty_list(self, client):
        """测试空页面列表"""
        # 发送请求
        response = client.post("/api/v1/crawl/pages", json=[])

        # 验证响应
        assert response.status_code == 400


class TestCrawlSinglePage:
    """测试爬取单个页面接口"""

    def test_crawl_single_page_success(self, client, mocker, mock_scheduler_response):
        """测试成功爬取单个页面"""
        # 设置模拟
        mock_scheduler = mocker.patch("app.api.crawl.get_scheduler")
        mock_scheduler.return_value.add_batch_jobs = mocker.AsyncMock(
            return_value=mock_scheduler_response["success"]
        )

        # 发送请求
        response = client.post("/api/v1/crawl/page/jiazi?force=true")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["page_id"] == "jiazi"

        # 验证调度器调用
        mock_scheduler.return_value.add_batch_jobs.assert_called_once()


class TestSchedulerStatus:
    """测试调度器状态接口"""

    def test_get_scheduler_status_success(
        self, client, mocker, mock_scheduler_status, mock_jobs
    ):
        """测试成功获取调度器状态"""
        # 设置模拟
        mock_scheduler = mocker.patch("app.api.crawl.get_scheduler")
        mock_scheduler.return_value.get_status.return_value = mock_scheduler_status
        mock_scheduler.return_value.get_jobs.return_value = mock_jobs

        # 发送请求
        response = client.get("/api/v1/crawl/status")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["scheduler_status"]["status"] == "running"
        assert data["data"]["job_count"] == 1
        assert len(data["data"]["jobs"]) == 1

        # 验证调度器调用
        mock_scheduler.return_value.get_status.assert_called_once()
        mock_scheduler.return_value.get_jobs.assert_called_once()


class TestBatchStatus:
    """测试批量任务状态接口"""

    def test_get_batch_status_success(
        self, client, mocker, mock_batch_status, mock_batch_jobs
    ):
        """测试成功获取批量任务状态"""
        # 设置模拟
        mock_scheduler = mocker.patch("app.api.crawl.get_scheduler")
        mock_scheduler.return_value.get_batch_status.return_value = mock_batch_status[
            "found"
        ]
        mock_scheduler.return_value.get_batch_jobs.return_value = mock_batch_jobs

        # 发送请求
        response = client.get("/api/v1/crawl/batch/batch_20240101_120000/status")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["batch_id"] == "batch_20240101_120000"
        assert data["data"]["status"] == "running"
        assert data["data"]["total_jobs"] == 2
        assert len(data["data"]["jobs"]) == 2

        # 验证调度器调用
        mock_scheduler.return_value.get_batch_status.assert_called_once_with(
            "batch_20240101_120000"
        )
        mock_scheduler.return_value.get_batch_jobs.assert_called_once_with(
            "batch_20240101_120000"
        )

    def test_get_batch_status_not_found(self, client, mocker, mock_batch_status):
        """测试批量任务不存在"""
        # 设置模拟
        mock_scheduler = mocker.patch("app.api.crawl.get_scheduler")
        mock_scheduler.return_value.get_batch_status.return_value = mock_batch_status[
            "not_found"
        ]
        mock_scheduler.return_value.get_batch_jobs.return_value = []

        # 发送请求
        response = client.get("/api/v1/crawl/batch/nonexistent_batch/status")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "not_found"
        assert data["data"]["total_jobs"] == 0
        assert len(data["data"]["jobs"]) == 0


class TestErrorHandling:
    """测试错误处理"""

    def test_scheduler_exception_handling(self, client, mocker):
        """测试调度器异常处理"""
        # 设置模拟异常
        mock_scheduler = mocker.patch("app.api.crawl.get_scheduler")
        mock_scheduler.return_value.add_batch_jobs.side_effect = Exception("调度器异常")

        # 发送请求
        response = client.post("/api/v1/crawl/all")

        # 验证响应
        assert response.status_code == 500
        data = response.json()
        assert "触发爬取失败" in data["detail"]

    def test_status_exception_handling(self, client, mocker):
        """测试状态查询异常处理"""
        # 设置模拟异常
        mock_scheduler = mocker.patch("app.api.crawl.get_scheduler")
        mock_scheduler.return_value.get_status.side_effect = Exception("状态查询异常")

        # 发送请求
        response = client.get("/api/v1/crawl/status")

        # 验证响应
        assert response.status_code == 500
        data = response.json()
        assert "获取调度器状态失败" in data["detail"]
