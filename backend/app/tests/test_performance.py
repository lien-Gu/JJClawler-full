"""
性能测试 - 阶段五

测试系统在各种负载下的性能表现
"""
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.modules.database.connection import get_session
from app.modules.models.book import Book, BookSnapshot
from app.modules.models.ranking import RankingSnapshot
import threading
import queue
import statistics


class TestAPIPerformance:
    """API性能测试"""

    def test_health_check_response_time(self, client: TestClient):
        """测试健康检查响应时间"""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 0.1, f"健康检查响应时间应该小于100ms，实际：{response_time:.3f}s"

    def test_pages_api_response_time(self, client: TestClient):
        """测试页面配置API响应时间"""
        response_times = []
        
        # 连续10次请求测试
        for _ in range(10):
            start_time = time.time()
            response = client.get("/api/v1/pages")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 0.5, f"平均响应时间应该小于500ms，实际：{avg_response_time:.3f}s"
        assert max_response_time < 1.0, f"最大响应时间应该小于1s，实际：{max_response_time:.3f}s"

    def test_ranking_api_response_time(self, client: TestClient):
        """测试榜单API响应时间"""
        start_time = time.time()
        response = client.get("/api/v1/rankings/jiazi/books?limit=50")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 2.0, f"榜单API响应时间应该小于2s，实际：{response_time:.3f}s"

    def test_concurrent_requests_performance(self, client: TestClient):
        """测试并发请求性能"""
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/pages")
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time
            }
        
        # 并发20个请求
        concurrent_count = 20
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(concurrent_count)]
            results = [future.result() for future in as_completed(futures)]
            total_time = time.time() - start_time
        
        # 验证所有请求都成功
        success_count = sum(1 for r in results if r['status_code'] == 200)
        assert success_count == concurrent_count, f"并发请求成功率：{success_count}/{concurrent_count}"
        
        # 验证平均响应时间
        avg_response_time = statistics.mean([r['response_time'] for r in results])
        assert avg_response_time < 1.0, f"并发请求平均响应时间：{avg_response_time:.3f}s"
        
        # 验证总处理时间（应该明显少于串行执行时间）
        serial_time_estimate = concurrent_count * 0.1  # 假设串行执行每个请求需要100ms
        assert total_time < serial_time_estimate, f"并发处理应该比串行快，并发：{total_time:.3f}s，估算串行：{serial_time_estimate:.3f}s"

    def test_pagination_performance(self, client: TestClient):
        """测试分页性能"""
        page_sizes = [10, 50, 100]
        offsets = [0, 100, 500, 1000]
        
        for page_size in page_sizes:
            for offset in offsets:
                start_time = time.time()
                response = client.get(f"/api/v1/rankings/jiazi/books?limit={page_size}&offset={offset}")
                end_time = time.time()
                
                response_time = end_time - start_time
                assert response.status_code == 200
                assert response_time < 3.0, f"分页查询响应时间过长：limit={page_size}, offset={offset}, time={response_time:.3f}s"

    def test_search_performance(self, client: TestClient):
        """测试搜索性能"""
        search_params = [
            "?keyword=测试",
            "?novel_class=言情",
            "?author=作者",
            "?keyword=小说&novel_class=言情&limit=20"
        ]
        
        for params in search_params:
            start_time = time.time()
            response = client.get(f"/api/v1/books{params}")
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response.status_code == 200
            assert response_time < 2.0, f"搜索性能测试失败：{params}, 响应时间：{response_time:.3f}s"


class TestDatabasePerformance:
    """数据库性能测试"""

    def test_database_connection_pool(self):
        """测试数据库连接池性能"""
        def query_database():
            with get_session() as session:
                # 简单查询测试
                result = session.exec("SELECT 1").first()
                return result is not None
        
        # 并发执行数据库操作
        with ThreadPoolExecutor(max_workers=5) as executor:
            start_time = time.time()
            futures = [executor.submit(query_database) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
            total_time = time.time() - start_time
        
        assert all(results), "所有数据库查询都应该成功"
        assert total_time < 2.0, f"数据库连接池性能测试失败，总时间：{total_time:.3f}s"

    def test_bulk_insert_performance(self):
        """测试批量插入性能"""
        test_books = []
        batch_size = 100
        
        # 准备测试数据
        for i in range(batch_size):
            book = Book(
                book_id=f"perf_test_book_{i}",
                title=f"性能测试书籍{i}",
                author_id=f"author_{i}",
                author_name=f"测试作者{i}",
                novel_class="测试分类"
            )
            test_books.append(book)
        
        # 测试批量插入
        with get_session() as session:
            start_time = time.time()
            for book in test_books:
                session.add(book)
            session.commit()
            insert_time = time.time() - start_time
            
            # 清理测试数据
            for book in test_books:
                session.delete(book)
            session.commit()
        
        # 验证性能（100条记录应该在1秒内完成）
        assert insert_time < 1.0, f"批量插入性能测试失败，插入{batch_size}条记录耗时：{insert_time:.3f}s"

    def test_complex_query_performance(self):
        """测试复杂查询性能"""
        with get_session() as session:
            # 测试复杂的连接查询
            start_time = time.time()
            
            # 模拟一个复杂查询：获取榜单快照和书籍信息
            query = """
            SELECT rs.ranking_id, rs.book_id, rs.position, b.title, b.author_name
            FROM ranking_snapshots rs
            JOIN books b ON rs.book_id = b.book_id
            WHERE rs.ranking_id = 'jiazi'
            ORDER BY rs.snapshot_time DESC, rs.position
            LIMIT 50
            """
            
            result = session.exec(query).all()
            query_time = time.time() - start_time
        
        assert query_time < 1.0, f"复杂查询性能测试失败，查询耗时：{query_time:.3f}s"


class TestCrawlerPerformance:
    """爬虫性能测试"""

    def test_http_client_performance(self):
        """测试HTTP客户端性能"""
        from app.utils.http_client import HTTPClient
        
        client = HTTPClient(timeout=5.0, rate_limit_delay=0.1)
        
        # 测试多个请求的性能
        urls = [
            "https://httpbin.org/get",
            "https://httpbin.org/json",
            "https://httpbin.org/uuid"
        ]
        
        start_time = time.time()
        responses = []
        
        for url in urls:
            response = client.get(url)
            responses.append(response)
        
        total_time = time.time() - start_time
        
        # 验证所有请求都成功
        assert all(r and r.status_code == 200 for r in responses), "所有HTTP请求都应该成功"
        
        # 验证性能（3个请求应该在10秒内完成，考虑网络延迟）
        assert total_time < 10.0, f"HTTP客户端性能测试失败，3个请求耗时：{total_time:.3f}s"

    def test_data_parsing_performance(self):
        """测试数据解析性能"""
        from app.utils.data_utils import parse_numeric_field, clean_text
        
        # 准备测试数据
        test_numbers = ["1.5万", "3千", "123", "5.6万", "2千"] * 100  # 500个数字
        test_texts = ["  <p>这是测试&nbsp;文本</p>  "] * 200  # 200个文本
        
        # 测试数字解析性能
        start_time = time.time()
        parsed_numbers = [parse_numeric_field(num) for num in test_numbers]
        number_parse_time = time.time() - start_time
        
        # 测试文本清洗性能
        start_time = time.time()
        cleaned_texts = [clean_text(text) for text in test_texts]
        text_clean_time = time.time() - start_time
        
        assert len(parsed_numbers) == len(test_numbers)
        assert len(cleaned_texts) == len(test_texts)
        assert number_parse_time < 1.0, f"数字解析性能测试失败，解析500个数字耗时：{number_parse_time:.3f}s"
        assert text_clean_time < 1.0, f"文本清洗性能测试失败，清洗200个文本耗时：{text_clean_time:.3f}s"


class TestTaskServicePerformance:
    """任务服务性能测试"""

    def test_task_file_operations_performance(self):
        """测试任务文件操作性能"""
        from app.modules.service.task_service import TaskService
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_file = os.path.join(temp_dir, "perf_test_tasks.json")
            task_service = TaskService(tasks_file)
            
            # 测试大量任务创建和操作的性能
            task_ids = []
            
            # 创建100个任务
            start_time = time.time()
            for i in range(100):
                task_id = task_service.create_task(
                    task_type=f"perf_test_{i}",
                    metadata={"test": f"performance_{i}"}
                )
                task_ids.append(task_id)
            create_time = time.time() - start_time
            
            # 批量操作任务
            start_time = time.time()
            for task_id in task_ids[:50]:  # 操作前50个任务
                task_service.start_task(task_id)
                task_service.update_progress(task_id, 50, 25)
                task_service.complete_task(task_id, {"result": "success"})
            operate_time = time.time() - start_time
            
            # 查询所有任务
            start_time = time.time()
            all_tasks = task_service.get_all_tasks()
            query_time = time.time() - start_time
            
            assert create_time < 2.0, f"创建100个任务耗时过长：{create_time:.3f}s"
            assert operate_time < 3.0, f"操作50个任务耗时过长：{operate_time:.3f}s"
            assert query_time < 0.5, f"查询所有任务耗时过长：{query_time:.3f}s"
            assert len(all_tasks["current_tasks"]) + len(all_tasks["completed_tasks"]) >= 100

    def test_concurrent_task_operations(self):
        """测试并发任务操作性能"""
        from app.modules.service.task_service import TaskService
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_file = os.path.join(temp_dir, "concurrent_test_tasks.json")
            task_service = TaskService(tasks_file)
            
            def create_and_operate_task(task_index):
                """创建并操作一个任务"""
                task_id = task_service.create_task(
                    task_type=f"concurrent_test_{task_index}",
                    metadata={"index": task_index}
                )
                task_service.start_task(task_id)
                task_service.update_progress(task_id, 100, 50)
                task_service.complete_task(task_id, {"result": f"success_{task_index}"})
                return task_id
            
            # 并发创建和操作10个任务
            with ThreadPoolExecutor(max_workers=5) as executor:
                start_time = time.time()
                futures = [
                    executor.submit(create_and_operate_task, i) 
                    for i in range(10)
                ]
                task_ids = [future.result() for future in as_completed(futures)]
                total_time = time.time() - start_time
            
            assert len(task_ids) == 10, "应该成功创建10个任务"
            assert all(task_id for task_id in task_ids), "所有任务ID都应该有效"
            assert total_time < 5.0, f"并发任务操作耗时过长：{total_time:.3f}s"
            
            # 验证任务状态
            all_tasks = task_service.get_all_tasks()
            completed_count = len(all_tasks["completed_tasks"])
            assert completed_count >= 10, f"应该有至少10个完成的任务，实际：{completed_count}"


class TestMemoryPerformance:
    """内存性能测试"""

    def test_memory_usage_under_load(self, client: TestClient):
        """测试负载下的内存使用"""
        import psutil
        import os
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行大量请求
        request_count = 100
        for i in range(request_count):
            response = client.get("/api/v1/pages")
            assert response.status_code == 200
            
            # 每20个请求检查一次内存
            if i % 20 == 19:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                
                # 内存增长不应该超过50MB
                assert memory_increase < 50, f"内存使用增长过多：{memory_increase:.1f}MB"
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        # 总内存增长应该控制在合理范围内
        assert total_increase < 100, f"总内存增长过多：{total_increase:.1f}MB"


if __name__ == "__main__":
    # 可以直接运行这个文件进行性能测试
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))