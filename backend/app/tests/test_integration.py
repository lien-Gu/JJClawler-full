"""
集成测试 - 阶段五

端到端集成测试，验证完整的数据流和业务逻辑
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.modules.database.connection import get_session
from app.modules.models.book import Book, BookSnapshot
from app.modules.models.ranking import Ranking, RankingSnapshot
from app.modules.service.task_service import TaskService
from app.utils.file_utils import read_json_file
import tempfile
import os


class TestEndToEndIntegration:
    """端到端集成测试"""

    def test_complete_crawl_to_api_flow(self, client: TestClient):
        """测试完整的爬取到API响应流程"""
        # 1. 触发夹子榜爬取
        crawl_response = client.post("/api/v1/crawl/jiazi", 
                                   json={"immediate": True})
        assert crawl_response.status_code == 200
        task_data = crawl_response.json()
        assert "task_id" in task_data
        
        # 2. 检查任务状态
        task_id = task_data["task_id"]
        task_response = client.get(f"/api/v1/crawl/tasks/{task_id}")
        assert task_response.status_code == 200
        
        # 3. 等待一段时间让爬取完成（实际环境中可能需要轮询）
        import time
        time.sleep(2)
        
        # 4. 验证榜单API返回数据
        ranking_response = client.get("/api/v1/rankings/jiazi/books")
        assert ranking_response.status_code == 200
        ranking_data = ranking_response.json()
        assert "books" in ranking_data
        assert "ranking" in ranking_data
        
        # 5. 如果有书籍数据，测试书籍详情API
        if ranking_data["books"]:
            book_id = ranking_data["books"][0]["book_id"]
            book_response = client.get(f"/api/v1/books/{book_id}")
            assert book_response.status_code == 200
            book_data = book_response.json()
            assert book_data["book_id"] == book_id

    def test_scheduler_integration(self, client: TestClient):
        """测试调度器集成"""
        # 1. 检查调度器状态
        scheduler_response = client.get("/api/v1/crawl/scheduler/status")
        assert scheduler_response.status_code == 200
        scheduler_data = scheduler_response.json()
        assert "running" in scheduler_data
        assert "total_jobs" in scheduler_data
        
        # 2. 获取定时任务列表
        jobs_response = client.get("/api/v1/crawl/scheduler/jobs")
        assert jobs_response.status_code == 200
        jobs_data = jobs_response.json()
        assert "jobs" in jobs_data
        assert len(jobs_data["jobs"]) > 0
        
        # 3. 验证夹子榜任务存在
        jiazi_job_exists = any(
            job["id"] == "jiazi_crawl" 
            for job in jobs_data["jobs"]
        )
        assert jiazi_job_exists, "夹子榜定时任务应该存在"

    def test_error_handling_integration(self, client: TestClient):
        """测试错误处理集成"""
        # 1. 测试无效榜单ID
        invalid_response = client.get("/api/v1/rankings/invalid_ranking/books")
        assert invalid_response.status_code == 404
        error_data = invalid_response.json()
        assert "error" in error_data
        
        # 2. 测试无效书籍ID
        invalid_book_response = client.get("/api/v1/books/invalid_book_123")
        assert invalid_book_response.status_code == 404
        
        # 3. 测试无效任务ID
        invalid_task_response = client.get("/api/v1/crawl/tasks/invalid_task_id")
        assert invalid_task_response.status_code == 404

    def test_pagination_and_filtering(self, client: TestClient):
        """测试分页和过滤功能"""
        # 1. 测试榜单分页
        page1_response = client.get("/api/v1/rankings/jiazi/books?limit=10&offset=0")
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        
        page2_response = client.get("/api/v1/rankings/jiazi/books?limit=10&offset=10")
        assert page2_response.status_code == 200
        page2_data = page2_response.json()
        
        # 验证分页数据不重复
        if page1_data["books"] and page2_data["books"]:
            page1_ids = {book["book_id"] for book in page1_data["books"]}
            page2_ids = {book["book_id"] for book in page2_data["books"]}
            assert page1_ids.isdisjoint(page2_ids), "分页数据不应重复"
        
        # 2. 测试书籍搜索过滤
        search_response = client.get("/api/v1/books?novel_class=言情&limit=5")
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert "books" in search_data
        assert len(search_data["books"]) <= 5


class TestDatabaseIntegration:
    """数据库集成测试"""

    def test_database_models_integration(self):
        """测试数据库模型集成"""
        with get_session() as session:
            # 1. 测试创建榜单
            test_ranking = Ranking(
                ranking_id="test_integration",
                name="集成测试榜单",
                channel="test_channel",
                frequency="daily",
                update_interval=24
            )
            session.add(test_ranking)
            session.commit()
            session.refresh(test_ranking)
            assert test_ranking.id is not None
            
            # 2. 测试创建书籍
            test_book = Book(
                book_id="test_book_integration",
                title="集成测试书籍",
                author_id="test_author_123",
                author_name="测试作者",
                novel_class="测试分类"
            )
            session.add(test_book)
            session.commit()
            session.refresh(test_book)
            assert test_book.id is not None
            
            # 3. 测试创建书籍快照
            test_snapshot = BookSnapshot(
                book_id=test_book.book_id,
                total_clicks=1000,
                total_favorites=200,
                comment_count=50,
                chapter_count=10
            )
            session.add(test_snapshot)
            session.commit()
            
            # 4. 测试创建榜单快照
            test_ranking_snapshot = RankingSnapshot(
                ranking_id=test_ranking.ranking_id,
                book_id=test_book.book_id,
                position=1
            )
            session.add(test_ranking_snapshot)
            session.commit()
            
            # 5. 验证关联查询
            book_snapshots = session.exec(
                select(BookSnapshot).where(BookSnapshot.book_id == test_book.book_id)
            ).all()
            assert len(book_snapshots) >= 1
            
            ranking_snapshots = session.exec(
                select(RankingSnapshot).where(
                    RankingSnapshot.ranking_id == test_ranking.ranking_id
                )
            ).all()
            assert len(ranking_snapshots) >= 1
            
            # 清理测试数据
            session.delete(test_ranking_snapshot)
            session.delete(test_snapshot)
            session.delete(test_book)
            session.delete(test_ranking)
            session.commit()

    def test_transaction_rollback(self):
        """测试事务回滚"""
        with get_session() as session:
            try:
                # 创建测试数据
                test_book = Book(
                    book_id="test_rollback_book",
                    title="回滚测试书籍",
                    author_id="test_author",
                    author_name="测试作者"
                )
                session.add(test_book)
                session.flush()  # 提交到数据库但不commit
                
                # 故意引发错误（违反唯一约束）
                duplicate_book = Book(
                    book_id="test_rollback_book",  # 重复的book_id
                    title="重复书籍",
                    author_id="test_author",
                    author_name="测试作者"
                )
                session.add(duplicate_book)
                session.commit()  # 这里应该会失败
                
                assert False, "应该抛出异常"
            except Exception:
                session.rollback()
                
                # 验证回滚成功，数据没有被保存
                existing_book = session.exec(
                    select(Book).where(Book.book_id == "test_rollback_book")
                ).first()
                assert existing_book is None, "回滚后数据不应存在"


class TestServiceIntegration:
    """服务层集成测试"""

    def test_task_service_integration(self):
        """测试任务服务集成"""
        # 使用临时文件进行测试
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_file = os.path.join(temp_dir, "test_tasks.json")
            
            # 创建任务服务实例
            task_service = TaskService(tasks_file)
            
            # 1. 创建任务
            task_id = task_service.create_task(
                task_type="test_integration",
                metadata={"test": "integration"}
            )
            assert task_id is not None
            
            # 2. 启动任务
            success = task_service.start_task(task_id)
            assert success is True
            
            # 3. 更新进度
            task_service.update_progress(task_id, 50, 25)
            
            # 4. 完成任务
            task_service.complete_task(task_id, {"result": "success"})
            
            # 5. 验证任务状态
            task_detail = task_service.get_task_detail(task_id)
            assert task_detail is not None
            assert task_detail["status"] == "completed"
            assert task_detail["progress"] == 100
            assert task_detail["items_crawled"] == 25
            
            # 6. 验证任务文件
            tasks_data = read_json_file(tasks_file)
            assert tasks_data is not None
            assert "completed_tasks" in tasks_data
            completed_tasks = [
                task for task in tasks_data["completed_tasks"]
                if task["task_id"] == task_id
            ]
            assert len(completed_tasks) == 1

    def test_page_service_integration(self, client: TestClient):
        """测试页面服务集成"""
        # 1. 测试页面配置获取
        response = client.get("/api/v1/pages")
        assert response.status_code == 200
        data = response.json()
        
        # 2. 验证页面结构
        assert "pages" in data
        assert "total_pages" in data
        assert "total_rankings" in data
        
        # 3. 验证至少有夹子榜
        page_ids = [page["page_id"] for page in data["pages"]]
        assert "jiazi" in page_ids
        
        # 4. 测试缓存刷新
        refresh_response = client.post("/api/v1/pages/refresh")
        assert refresh_response.status_code == 200
        
        # 5. 验证刷新后数据一致
        after_refresh_response = client.get("/api/v1/pages")
        assert after_refresh_response.status_code == 200
        after_refresh_data = after_refresh_response.json()
        assert len(after_refresh_data["pages"]) == len(data["pages"])


class TestPerformanceIntegration:
    """性能集成测试"""

    def test_concurrent_api_requests(self, client: TestClient):
        """测试并发API请求"""
        import concurrent.futures
        import threading
        
        def make_request():
            response = client.get("/api/v1/pages")
            return response.status_code == 200
        
        # 并发发送10个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # 验证所有请求都成功
        assert all(results), "所有并发请求都应该成功"

    def test_large_dataset_pagination(self, client: TestClient):
        """测试大数据集分页性能"""
        # 测试大偏移量的分页请求
        response = client.get("/api/v1/rankings/jiazi/books?limit=50&offset=1000")
        assert response.status_code == 200
        
        # 验证响应时间合理（实际项目中可能需要更严格的性能要求）
        import time
        start_time = time.time()
        client.get("/api/v1/rankings/jiazi/books?limit=100")
        end_time = time.time()
        
        # 响应时间应该在5秒内（可根据实际需求调整）
        assert (end_time - start_time) < 5.0, "API响应时间应该在可接受范围内"


class TestUtilsIntegration:
    """工具层集成测试"""

    def test_http_client_integration(self):
        """测试HTTP客户端集成"""
        from app.utils.http_client import HTTPClient
        
        # 创建HTTP客户端
        client = HTTPClient(timeout=10.0, rate_limit_delay=0.1)
        
        # 测试GET请求
        response = client.get("https://httpbin.org/get")
        assert response is not None
        assert response.status_code == 200
        
        # 测试POST请求
        test_data = {"test": "data"}
        response = client.post("https://httpbin.org/post", json=test_data)
        assert response is not None
        assert response.status_code == 200

    def test_file_utils_integration(self):
        """测试文件工具集成"""
        from app.utils.file_utils import read_json_file, write_json_file
        import tempfile
        import os
        
        # 测试JSON文件读写
        test_data = {
            "test": "integration",
            "numbers": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_integration.json")
            
            # 写入文件
            success = write_json_file(test_file, test_data)
            assert success is True
            
            # 读取文件
            read_data = read_json_file(test_file)
            assert read_data == test_data

    def test_data_utils_integration(self):
        """测试数据工具集成"""
        from app.utils.data_utils import parse_numeric_field, clean_text
        
        # 测试数字解析
        assert parse_numeric_field("1.5万") == 15000
        assert parse_numeric_field("3千") == 3000
        assert parse_numeric_field("123") == 123
        
        # 测试文本清洗
        dirty_text = "  <p>这是一个&nbsp;测试</p>  "
        clean = clean_text(dirty_text)
        assert clean == "这是一个 测试"