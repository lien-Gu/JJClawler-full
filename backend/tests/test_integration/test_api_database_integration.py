"""
API与数据库集成测试 - 测试API层到数据库层的完整数据流
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json

# 假设的导入（根据项目实际结构调整）
from app.main import app
from app.database.models.book import Book, BookSnapshot
from app.database.models.ranking import Ranking, RankingSnapshot
from app.database.connection import get_db, Base


class TestAPIDBIntegration:
    """API与数据库集成测试类"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 使用测试数据库会话
        pass
    
    def test_books_api_with_real_database(self, client, test_db, sample_book_data):
        """测试书籍API与真实数据库的集成"""
        # 创建测试数据
        db = test_db()
        
        # 创建书籍记录
        test_book = Book(
            novel_id=sample_book_data["novel_id"],
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            status=sample_book_data["status"],
            tag=sample_book_data["tag"],
            length=sample_book_data["length"],
            intro=sample_book_data["intro"],
            last_update=datetime.fromisoformat(sample_book_data["last_update"])
        )
        db.add(test_book)
        
        # 创建书籍快照记录
        test_snapshot = BookSnapshot(
            novel_id=sample_book_data["novel_id"],
            favorites=sample_book_data["favorites"],
            total_clicks=sample_book_data["total_clicks"],
            monthly_clicks=sample_book_data["monthly_clicks"],
            weekly_clicks=sample_book_data["weekly_clicks"],
            daily_clicks=sample_book_data["daily_clicks"],
            total_comments=sample_book_data["total_comments"],
            monthly_comments=sample_book_data["monthly_comments"],
            weekly_comments=sample_book_data["weekly_comments"],
            daily_comments=sample_book_data["daily_comments"],
            total_recs=sample_book_data["total_recs"],
            monthly_recs=sample_book_data["monthly_recs"],
            weekly_recs=sample_book_data["weekly_recs"],
            daily_recs=sample_book_data["daily_recs"],
            snapshot_time=datetime.now()
        )
        db.add(test_snapshot)
        db.commit()
        
        # 测试API调用
        response = client.get("/api/v1/books")
        assert response.status_code == 200
        
        books_data = response.json()
        assert isinstance(books_data, list)
        assert len(books_data) > 0
        
        # 验证返回的数据
        found_book = None
        for book in books_data:
            if book["novel_id"] == sample_book_data["novel_id"]:
                found_book = book
                break
        
        assert found_book is not None
        assert found_book["title"] == sample_book_data["title"]
        assert found_book["author"] == sample_book_data["author"]
        
        db.close()
    
    def test_book_detail_api_with_database(self, client, test_db, sample_book_data):
        """测试书籍详情API与数据库的集成"""
        db = test_db()
        
        # 创建测试数据
        test_book = Book(
            novel_id=sample_book_data["novel_id"],
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            status=sample_book_data["status"],
            tag=sample_book_data["tag"],
            length=sample_book_data["length"],
            intro=sample_book_data["intro"],
            last_update=datetime.fromisoformat(sample_book_data["last_update"])
        )
        db.add(test_book)
        db.commit()
        
        # 测试API调用
        response = client.get(f"/api/v1/books/{sample_book_data['novel_id']}")
        assert response.status_code == 200
        
        book_detail = response.json()
        assert book_detail["novel_id"] == sample_book_data["novel_id"]
        assert book_detail["title"] == sample_book_data["title"]
        assert book_detail["author"] == sample_book_data["author"]
        assert book_detail["intro"] == sample_book_data["intro"]
        
        db.close()
    
    def test_book_search_api_with_database(self, client, test_db, sample_book_data):
        """测试书籍搜索API与数据库的集成"""
        db = test_db()
        
        # 创建多个测试书籍
        for i in range(3):
            test_book = Book(
                novel_id=sample_book_data["novel_id"] + i,
                title=f"测试小说{i}",
                author=f"测试作者{i}",
                status="连载中",
                tag="现代言情",
                length=100000 + i * 10000,
                intro=f"这是第{i}本测试小说",
                last_update=datetime.now()
            )
            db.add(test_book)
        db.commit()
        
        # 测试搜索功能
        response = client.get("/api/v1/books/search?keyword=测试小说")
        assert response.status_code == 200
        
        search_results = response.json()
        assert isinstance(search_results, list)
        assert len(search_results) >= 3
        
        # 验证搜索结果
        for book in search_results:
            assert "测试小说" in book["title"]
        
        db.close()
    
    def test_rankings_api_with_database(self, client, test_db, sample_ranking_data):
        """测试榜单API与数据库的集成"""
        db = test_db()
        
        # 创建榜单配置
        test_ranking = Ranking(
            name=sample_ranking_data["name"],
            type=sample_ranking_data["type"],
            url=sample_ranking_data["url"],
            description=sample_ranking_data["description"],
            is_active=sample_ranking_data["is_active"],
            crawl_interval=sample_ranking_data["crawl_interval"]
        )
        db.add(test_ranking)
        db.commit()
        
        # 创建榜单快照
        test_snapshot = RankingSnapshot(
            ranking_id=test_ranking.id,
            novel_id=12345,
            rank_position=1,
            rank_score=95.5,
            snapshot_time=datetime.now()
        )
        db.add(test_snapshot)
        db.commit()
        
        # 测试API调用
        response = client.get("/api/v1/rankings")
        assert response.status_code == 200
        
        rankings_data = response.json()
        assert isinstance(rankings_data, list)
        assert len(rankings_data) > 0
        
        # 验证返回的数据
        found_ranking = None
        for ranking in rankings_data:
            if ranking["name"] == sample_ranking_data["name"]:
                found_ranking = ranking
                break
        
        assert found_ranking is not None
        assert found_ranking["type"] == sample_ranking_data["type"]
        assert found_ranking["description"] == sample_ranking_data["description"]
        
        db.close()
    
    def test_ranking_detail_api_with_database(self, client, test_db, sample_ranking_data, sample_book_data):
        """测试榜单详情API与数据库的集成"""
        db = test_db()
        
        # 创建测试数据
        test_ranking = Ranking(
            name=sample_ranking_data["name"],
            type=sample_ranking_data["type"],
            url=sample_ranking_data["url"],
            description=sample_ranking_data["description"],
            is_active=sample_ranking_data["is_active"],
            crawl_interval=sample_ranking_data["crawl_interval"]
        )
        db.add(test_ranking)
        
        test_book = Book(
            novel_id=sample_book_data["novel_id"],
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            status=sample_book_data["status"],
            tag=sample_book_data["tag"],
            length=sample_book_data["length"],
            intro=sample_book_data["intro"],
            last_update=datetime.fromisoformat(sample_book_data["last_update"])
        )
        db.add(test_book)
        db.commit()
        
        # 创建榜单快照
        test_snapshot = RankingSnapshot(
            ranking_id=test_ranking.id,
            novel_id=sample_book_data["novel_id"],
            rank_position=1,
            rank_score=95.5,
            snapshot_time=datetime.now()
        )
        db.add(test_snapshot)
        db.commit()
        
        # 测试API调用
        response = client.get(f"/api/v1/rankings/{test_ranking.id}")
        assert response.status_code == 200
        
        ranking_detail = response.json()
        assert ranking_detail["id"] == test_ranking.id
        assert ranking_detail["name"] == sample_ranking_data["name"]
        assert "books" in ranking_detail
        assert len(ranking_detail["books"]) > 0
        
        # 验证榜单中的书籍信息
        ranked_book = ranking_detail["books"][0]
        assert ranked_book["novel_id"] == sample_book_data["novel_id"]
        assert ranked_book["rank_position"] == 1
        assert ranked_book["title"] == sample_book_data["title"]
        
        db.close()
    
    def test_book_trend_api_with_database(self, client, test_db, sample_book_data):
        """测试书籍趋势API与数据库的集成"""
        db = test_db()
        
        # 创建书籍
        test_book = Book(
            novel_id=sample_book_data["novel_id"],
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            status=sample_book_data["status"],
            tag=sample_book_data["tag"],
            length=sample_book_data["length"],
            intro=sample_book_data["intro"],
            last_update=datetime.fromisoformat(sample_book_data["last_update"])
        )
        db.add(test_book)
        
        # 创建多个时间点的快照数据
        base_time = datetime.now() - timedelta(days=7)
        for i in range(7):
            snapshot = BookSnapshot(
                novel_id=sample_book_data["novel_id"],
                favorites=1000 + i * 10,
                total_clicks=5000 + i * 50,
                monthly_clicks=500 + i * 5,
                weekly_clicks=100 + i * 2,
                daily_clicks=20 + i,
                total_comments=200 + i * 2,
                monthly_comments=50 + i,
                weekly_comments=10,
                daily_comments=2,
                total_recs=100 + i,
                monthly_recs=25,
                weekly_recs=5,
                daily_recs=1,
                snapshot_time=base_time + timedelta(days=i)
            )
            db.add(snapshot)
        db.commit()
        
        # 测试趋势API
        response = client.get(f"/api/v1/books/{sample_book_data['novel_id']}/trend?days=7")
        assert response.status_code == 200
        
        trend_data = response.json()
        assert "novel_id" in trend_data
        assert "trend_data" in trend_data
        assert len(trend_data["trend_data"]) == 7
        
        # 验证趋势数据
        for i, data_point in enumerate(trend_data["trend_data"]):
            assert data_point["favorites"] == 1000 + i * 10
            assert data_point["total_clicks"] == 5000 + i * 50
            
        db.close()
    
    def test_pagination_api_with_database(self, client, test_db):
        """测试分页API与数据库的集成"""
        db = test_db()
        
        # 创建多个测试书籍用于分页测试
        for i in range(25):
            test_book = Book(
                novel_id=10000 + i,
                title=f"分页测试小说{i:02d}",
                author=f"作者{i:02d}",
                status="连载中",
                tag="现代言情",
                length=100000 + i * 1000,
                intro=f"这是第{i}本用于分页测试的小说",
                last_update=datetime.now()
            )
            db.add(test_book)
        db.commit()
        
        # 测试第一页
        response = client.get("/api/v1/books?page=1&size=10")
        assert response.status_code == 200
        
        page_data = response.json()
        assert "items" in page_data
        assert "total" in page_data
        assert "page" in page_data
        assert "size" in page_data
        assert "pages" in page_data
        
        assert len(page_data["items"]) == 10
        assert page_data["total"] == 25
        assert page_data["page"] == 1
        assert page_data["size"] == 10
        assert page_data["pages"] == 3
        
        # 测试第二页
        response = client.get("/api/v1/books?page=2&size=10")
        assert response.status_code == 200
        
        page_data = response.json()
        assert len(page_data["items"]) == 10
        assert page_data["page"] == 2
        
        # 测试最后一页
        response = client.get("/api/v1/books?page=3&size=10")
        assert response.status_code == 200
        
        page_data = response.json()
        assert len(page_data["items"]) == 5  # 最后一页只有5条记录
        assert page_data["page"] == 3
        
        db.close()
    
    def test_api_error_handling_with_database(self, client, test_db):
        """测试API错误处理与数据库的集成"""
        # 测试获取不存在的书籍
        response = client.get("/api/v1/books/999999")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "detail" in error_data
        assert "not found" in error_data["detail"].lower()
        
        # 测试获取不存在的榜单
        response = client.get("/api/v1/rankings/999999")
        assert response.status_code == 404
        
        # 测试无效的搜索参数
        response = client.get("/api/v1/books/search?keyword=")
        assert response.status_code == 422  # 或者其他适当的错误码
    
    def test_concurrent_api_calls_with_database(self, client, test_db, sample_book_data):
        """测试并发API调用与数据库的集成"""
        import threading
        import time
        
        db = test_db()
        
        # 创建测试数据
        test_book = Book(
            novel_id=sample_book_data["novel_id"],
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            status=sample_book_data["status"],
            tag=sample_book_data["tag"],
            length=sample_book_data["length"],
            intro=sample_book_data["intro"],
            last_update=datetime.fromisoformat(sample_book_data["last_update"])
        )
        db.add(test_book)
        db.commit()
        db.close()
        
        # 并发调用API
        results = []
        errors = []
        
        def make_api_call():
            try:
                response = client.get(f"/api/v1/books/{sample_book_data['novel_id']}")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # 创建多个线程并发调用
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_api_call)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        assert len(errors) == 0  # 应该没有错误
        assert len(results) == 10  # 应该有10个响应
        assert all(status == 200 for status in results)  # 所有响应都应该成功
    
    def test_data_consistency_across_apis(self, client, test_db, sample_book_data, sample_ranking_data):
        """测试跨API的数据一致性"""
        db = test_db()
        
        # 创建测试数据
        test_book = Book(
            novel_id=sample_book_data["novel_id"],
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            status=sample_book_data["status"],
            tag=sample_book_data["tag"],
            length=sample_book_data["length"],
            intro=sample_book_data["intro"],
            last_update=datetime.fromisoformat(sample_book_data["last_update"])
        )
        db.add(test_book)
        
        test_ranking = Ranking(
            name=sample_ranking_data["name"],
            type=sample_ranking_data["type"],
            url=sample_ranking_data["url"],
            description=sample_ranking_data["description"],
            is_active=sample_ranking_data["is_active"],
            crawl_interval=sample_ranking_data["crawl_interval"]
        )
        db.add(test_ranking)
        db.commit()
        
        test_snapshot = RankingSnapshot(
            ranking_id=test_ranking.id,
            novel_id=sample_book_data["novel_id"],
            rank_position=1,
            rank_score=95.5,
            snapshot_time=datetime.now()
        )
        db.add(test_snapshot)
        db.commit()
        
        # 从不同API获取同一书籍信息
        book_response = client.get(f"/api/v1/books/{sample_book_data['novel_id']}")
        ranking_response = client.get(f"/api/v1/rankings/{test_ranking.id}")
        
        assert book_response.status_code == 200
        assert ranking_response.status_code == 200
        
        book_data = book_response.json()
        ranking_data = ranking_response.json()
        
        # 验证数据一致性
        ranked_book = ranking_data["books"][0]
        assert book_data["novel_id"] == ranked_book["novel_id"]
        assert book_data["title"] == ranked_book["title"]
        assert book_data["author"] == ranked_book["author"]
        
        db.close() 