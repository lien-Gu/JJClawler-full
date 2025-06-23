"""
API接口测试
"""
import pytest
from fastapi.testclient import TestClient


class TestPagesAPI:
    """页面配置API测试"""
    
    def test_get_pages(self, client: TestClient):
        """测试获取页面配置"""
        response = client.get("/api/v1/pages")
        assert response.status_code == 200
        
        data = response.json()
        assert "pages" in data
        assert "total_pages" in data
        assert "total_rankings" in data
        assert len(data["pages"]) > 0


class TestRankingsAPI:
    """榜单API测试"""
    
    def test_get_ranking_books(self, client: TestClient):
        """测试获取榜单书籍"""
        response = client.get("/api/v1/rankings/jiazi/books")
        assert response.status_code == 200
        
        data = response.json()
        assert "ranking" in data
        assert "books" in data
        assert data["ranking"]["ranking_id"] == "jiazi"
    
    def test_get_ranking_books_with_params(self, client: TestClient):
        """测试带参数的榜单书籍查询"""
        response = client.get("/api/v1/rankings/jiazi/books?limit=10&offset=5")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["books"]) <= 10
    
    def test_get_ranking_history(self, client: TestClient):
        """测试获取榜单历史"""
        response = client.get("/api/v1/rankings/jiazi/history?days=7")
        assert response.status_code == 200
        
        data = response.json()
        assert "ranking" in data
        assert "snapshots" in data
        assert data["days"] == 7
    
    def test_invalid_ranking_id(self, client: TestClient):
        """测试无效榜单ID"""
        response = client.get("/api/v1/rankings/invalid/books")
        assert response.status_code == 404


class TestBooksAPI:
    """书籍API测试"""
    
    def test_get_book_detail(self, client: TestClient):
        """测试获取书籍详情"""
        response = client.get("/api/v1/books/test_book_123")
        assert response.status_code == 200
        
        data = response.json()
        assert data["book_id"] == "test_book_123"
        assert "title" in data
        assert "author_name" in data
    
    def test_get_book_rankings(self, client: TestClient):
        """测试获取书籍榜单历史"""
        response = client.get("/api/v1/books/test_book_123/rankings")
        assert response.status_code == 200
        
        data = response.json()
        assert "book" in data
        assert "current_rankings" in data
        assert "history" in data
    
    def test_get_book_trends(self, client: TestClient):
        """测试获取书籍趋势"""
        response = client.get("/api/v1/books/test_book_123/trends?days=7")
        assert response.status_code == 200
        
        data = response.json()
        assert data["book_id"] == "test_book_123"
        assert "trends" in data
        assert len(data["trends"]) == 7
    
    def test_search_books(self, client: TestClient):
        """测试搜索书籍"""
        response = client.get("/api/v1/books?author=测试作者&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "total" in data
        assert "books" in data
        assert len(data["books"]) <= 5


class TestCrawlAPI:
    """爬虫管理API测试"""
    
    def test_trigger_jiazi_crawl(self, client: TestClient):
        """测试触发夹子爬取"""
        response = client.post("/api/v1/crawl/jiazi", json={"force": False})
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "message" in data
        assert data["status"] == "pending"
    
    def test_trigger_ranking_crawl(self, client: TestClient):
        """测试触发榜单爬取"""
        response = client.post("/api/v1/crawl/ranking/yq_gy", json={"force": True})
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "强制模式" in data["message"]
    
    def test_get_tasks(self, client: TestClient):
        """测试获取任务列表"""
        response = client.get("/api/v1/crawl/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert "current_tasks" in data
        assert "completed_tasks" in data
        assert "total_current" in data
    
    def test_get_task_detail(self, client: TestClient):
        """测试获取任务详情"""
        response = client.get("/api/v1/crawl/tasks/jiazi_test_task")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "jiazi_test_task"
        assert "status" in data
    
    def test_invalid_ranking_crawl(self, client: TestClient):
        """测试无效榜单爬取"""
        response = client.post("/api/v1/crawl/ranking/invalid", json={})
        assert response.status_code == 404