"""
书籍相关API测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime


class TestBooksAPI:
    """书籍API测试类"""
    
    def test_get_books_list(self, client: TestClient):
        """测试获取书籍列表API"""
        response = client.get("/api/v1/books")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data
        assert "message" in data
        assert isinstance(data["data"], list)
    
    def test_get_books_with_pagination(self, client: TestClient):
        """测试带分页的书籍列表API"""
        response = client.get("/api/v1/books?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)
    
    def test_get_book_detail(self, client: TestClient, sample_book_data):
        """测试获取书籍详情API"""
        # 先创建一本书
        book_id = 1  # 使用测试数据中存在的book_id
        response = client.get(f"/api/v1/books/{book_id}")
        
        # 如果书籍不存在，应该返回404
        if response.status_code == 404:
            assert response.json()["detail"] == "书籍不存在"
        else:
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            book_data = data["data"]
            assert "novel_id" in book_data
            assert "title" in book_data
    
    def test_get_book_detail_not_found(self, client: TestClient):
        """测试获取不存在的书籍详情"""
        response = client.get("/api/v1/books/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "书籍不存在"
    
    def test_get_book_snapshots(self, client: TestClient):
        """测试获取书籍快照数据API"""
        book_id = 12345
        response = client.get(f"/api/v1/books/{book_id}/snapshots")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "snapshots" in data
            assert isinstance(data["snapshots"], list)
    
    def test_get_book_snapshots_with_date_range(self, client: TestClient):
        """测试带日期范围的书籍快照API"""
        book_id = 12345
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        response = client.get(
            f"/api/v1/books/{book_id}/snapshots"
            f"?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code in [200, 404]
    
    def test_get_book_trends(self, client: TestClient):
        """测试获取书籍趋势数据API"""
        book_id = 12345
        response = client.get(f"/api/v1/books/{book_id}/trends")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "trends" in data
            assert isinstance(data["trends"], dict)
    
    def test_search_books(self, client: TestClient):
        """测试搜索书籍API"""
        response = client.get("/api/v1/books/search?keyword=测试")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)
    
    def test_search_books_with_filters(self, client: TestClient):
        """测试带过滤条件的搜索API"""
        response = client.get(
            "/api/v1/books/search"
            "?keyword=测试&page=1&size=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data
    
    def test_search_books_empty_query(self, client: TestClient):
        """测试空查询搜索"""
        response = client.get("/api/v1/books/search?keyword=")
        assert response.status_code == 422  # FastAPI validation error for min_length=1
    
    def test_get_book_ranking_history(self, client: TestClient):
        """测试获取书籍排名历史API"""
        book_id = 12345
        response = client.get(f"/api/v1/books/{book_id}/ranking-history")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "ranking_history" in data
            assert isinstance(data["ranking_history"], list)
    
    
    def test_api_response_format(self, client: TestClient):
        """测试API响应格式"""
        response = client.get("/api/v1/books")
        assert response.status_code == 200
        data = response.json()
        
        # 检查响应格式
        assert isinstance(data, dict)
        assert "data" in data
        assert "count" in data
        assert "message" in data
        
        # 检查书籍数据格式
        if data["data"]:
            book = data["data"][0]
            required_fields = ["novel_id", "title"]
            for field in required_fields:
                assert field in book
    
    def test_api_error_handling(self, client: TestClient):
        """测试API错误处理"""
        # 测试无效的书籍ID
        response = client.get("/api/v1/books/invalid_id")
        assert response.status_code == 422  # 验证错误
        
        # 测试无效的页码
        response = client.get("/api/v1/books?page=-1")
        assert response.status_code == 422  # 验证错误
        
        # 测试无效的每页大小
        response = client.get("/api/v1/books?size=0")
        assert response.status_code == 422  # 验证错误 