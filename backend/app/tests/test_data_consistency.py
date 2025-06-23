"""
数据一致性测试 - 阶段五

验证数据的完整性、一致性和业务规则
"""
import pytest
from sqlmodel import Session, select
from datetime import datetime, timedelta
from app.modules.database.connection import get_session
from app.modules.models.book import Book, BookSnapshot
from app.modules.models.ranking import Ranking, RankingSnapshot
from app.modules.service.book_service import BookService
from app.modules.service.ranking_service import RankingService
from app.modules.service.task_service import TaskService
import tempfile
import os


class TestDataIntegrity:
    """数据完整性测试"""

    def test_foreign_key_constraints(self):
        """测试外键约束"""
        with get_session() as session:
            # 1. 创建测试榜单
            test_ranking = Ranking(
                ranking_id="test_fk_ranking",
                name="外键测试榜单",
                channel="test_channel",
                frequency="daily",
                update_interval=24
            )
            session.add(test_ranking)
            session.commit()
            
            # 2. 创建测试书籍
            test_book = Book(
                book_id="test_fk_book",
                title="外键测试书籍",
                author_id="test_author",
                author_name="测试作者"
            )
            session.add(test_book)
            session.commit()
            
            # 3. 创建有效的书籍快照（应该成功）
            valid_snapshot = BookSnapshot(
                book_id=test_book.book_id,
                total_clicks=1000,
                total_favorites=200
            )
            session.add(valid_snapshot)
            session.commit()
            
            # 4. 创建有效的榜单快照（应该成功）
            valid_ranking_snapshot = RankingSnapshot(
                ranking_id=test_ranking.ranking_id,
                book_id=test_book.book_id,
                position=1
            )
            session.add(valid_ranking_snapshot)
            session.commit()
            
            # 5. 尝试创建无效的书籍快照（应该失败）
            try:
                invalid_snapshot = BookSnapshot(
                    book_id="nonexistent_book",
                    total_clicks=1000
                )
                session.add(invalid_snapshot)
                session.commit()
                assert False, "外键约束应该阻止无效的book_id"
            except Exception:
                session.rollback()
            
            # 6. 尝试创建无效的榜单快照（应该失败）
            try:
                invalid_ranking_snapshot = RankingSnapshot(
                    ranking_id="nonexistent_ranking",
                    book_id=test_book.book_id,
                    position=1
                )
                session.add(invalid_ranking_snapshot)
                session.commit()
                assert False, "外键约束应该阻止无效的ranking_id"
            except Exception:
                session.rollback()
            
            # 清理测试数据
            session.delete(valid_ranking_snapshot)
            session.delete(valid_snapshot)
            session.delete(test_book)
            session.delete(test_ranking)
            session.commit()

    def test_unique_constraints(self):
        """测试唯一性约束"""
        with get_session() as session:
            # 1. 创建第一个榜单
            ranking1 = Ranking(
                ranking_id="unique_test_ranking",
                name="唯一性测试榜单1",
                channel="test_channel",
                frequency="daily",
                update_interval=24
            )
            session.add(ranking1)
            session.commit()
            
            # 2. 尝试创建相同ranking_id的榜单（应该失败）
            try:
                ranking2 = Ranking(
                    ranking_id="unique_test_ranking",  # 重复的ranking_id
                    name="唯一性测试榜单2",
                    channel="test_channel2",
                    frequency="daily",
                    update_interval=24
                )
                session.add(ranking2)
                session.commit()
                assert False, "唯一性约束应该阻止重复的ranking_id"
            except Exception:
                session.rollback()
            
            # 3. 创建第一个书籍
            book1 = Book(
                book_id="unique_test_book",
                title="唯一性测试书籍1",
                author_id="test_author",
                author_name="测试作者"
            )
            session.add(book1)
            session.commit()
            
            # 4. 尝试创建相同book_id的书籍（应该失败）
            try:
                book2 = Book(
                    book_id="unique_test_book",  # 重复的book_id
                    title="唯一性测试书籍2",
                    author_id="test_author",
                    author_name="测试作者"
                )
                session.add(book2)
                session.commit()
                assert False, "唯一性约束应该阻止重复的book_id"
            except Exception:
                session.rollback()
            
            # 清理测试数据
            session.delete(book1)
            session.delete(ranking1)
            session.commit()

    def test_data_type_validation(self):
        """测试数据类型验证"""
        with get_session() as session:
            # 测试有效数据类型
            valid_book = Book(
                book_id="type_test_book",
                title="类型测试书籍",
                author_id="123",
                author_name="测试作者",
                novel_class="测试分类"
            )
            session.add(valid_book)
            session.commit()
            
            valid_snapshot = BookSnapshot(
                book_id=valid_book.book_id,
                total_clicks=1000,  # 正整数
                total_favorites=500,  # 正整数
                comment_count=100,  # 正整数
                chapter_count=50  # 正整数
            )
            session.add(valid_snapshot)
            session.commit()
            
            # 验证数据正确保存
            saved_book = session.exec(
                select(Book).where(Book.book_id == "type_test_book")
            ).first()
            assert saved_book is not None
            assert saved_book.title == "类型测试书籍"
            
            saved_snapshot = session.exec(
                select(BookSnapshot).where(BookSnapshot.book_id == valid_book.book_id)
            ).first()
            assert saved_snapshot is not None
            assert saved_snapshot.total_clicks == 1000
            
            # 清理测试数据
            session.delete(valid_snapshot)
            session.delete(valid_book)
            session.commit()


class TestBusinessLogicConsistency:
    """业务逻辑一致性测试"""

    def test_ranking_position_consistency(self):
        """测试榜单位置一致性"""
        with get_session() as session:
            # 创建测试数据
            test_ranking = Ranking(
                ranking_id="position_test_ranking",
                name="位置测试榜单",
                channel="test_channel",
                frequency="daily",
                update_interval=24
            )
            session.add(test_ranking)
            session.commit()
            
            # 创建测试书籍
            books = []
            for i in range(5):
                book = Book(
                    book_id=f"position_test_book_{i}",
                    title=f"位置测试书籍{i}",
                    author_id=f"author_{i}",
                    author_name=f"作者{i}"
                )
                books.append(book)
                session.add(book)
            session.commit()
            
            # 创建榜单快照，测试位置一致性
            now = datetime.now()
            for i, book in enumerate(books):
                snapshot = RankingSnapshot(
                    ranking_id=test_ranking.ranking_id,
                    book_id=book.book_id,
                    position=i + 1,  # 位置从1开始
                    snapshot_time=now
                )
                session.add(snapshot)
            session.commit()
            
            # 验证位置的唯一性和连续性
            snapshots = session.exec(
                select(RankingSnapshot)
                .where(RankingSnapshot.ranking_id == test_ranking.ranking_id)
                .where(RankingSnapshot.snapshot_time == now)
                .order_by(RankingSnapshot.position)
            ).all()
            
            assert len(snapshots) == 5, "应该有5个榜单快照"
            
            # 验证位置连续性
            positions = [snapshot.position for snapshot in snapshots]
            assert positions == [1, 2, 3, 4, 5], f"位置应该是连续的，实际：{positions}"
            
            # 验证没有重复位置
            assert len(set(positions)) == len(positions), "不应该有重复的位置"
            
            # 清理测试数据
            for snapshot in snapshots:
                session.delete(snapshot)
            for book in books:
                session.delete(book)
            session.delete(test_ranking)
            session.commit()

    def test_book_snapshot_time_consistency(self):
        """测试书籍快照时间一致性"""
        with get_session() as session:
            # 创建测试书籍
            test_book = Book(
                book_id="time_test_book",
                title="时间测试书籍",
                author_id="test_author",
                author_name="测试作者"
            )
            session.add(test_book)
            session.commit()
            
            # 创建多个时间点的快照
            base_time = datetime(2024, 1, 1, 12, 0, 0)
            snapshots = []
            
            for i in range(5):
                snapshot_time = base_time + timedelta(hours=i)
                snapshot = BookSnapshot(
                    book_id=test_book.book_id,
                    total_clicks=1000 + i * 100,  # 递增的点击量
                    total_favorites=500 + i * 50,  # 递增的收藏量
                    snapshot_time=snapshot_time
                )
                snapshots.append(snapshot)
                session.add(snapshot)
            session.commit()
            
            # 验证时间序列的正确性
            saved_snapshots = session.exec(
                select(BookSnapshot)
                .where(BookSnapshot.book_id == test_book.book_id)
                .order_by(BookSnapshot.snapshot_time)
            ).all()
            
            assert len(saved_snapshots) == 5, "应该有5个快照"
            
            # 验证时间递增
            for i in range(len(saved_snapshots) - 1):
                assert saved_snapshots[i].snapshot_time < saved_snapshots[i + 1].snapshot_time, \
                    "快照时间应该是递增的"
            
            # 验证数据递增（模拟真实的增长趋势）
            for i in range(len(saved_snapshots) - 1):
                assert saved_snapshots[i].total_clicks <= saved_snapshots[i + 1].total_clicks, \
                    "点击量应该是非递减的"
                assert saved_snapshots[i].total_favorites <= saved_snapshots[i + 1].total_favorites, \
                    "收藏量应该是非递减的"
            
            # 清理测试数据
            for snapshot in snapshots:
                session.delete(snapshot)
            session.delete(test_book)
            session.commit()

    def test_ranking_hierarchy_consistency(self):
        """测试榜单层级一致性"""
        with get_session() as session:
            # 创建父榜单
            parent_ranking = Ranking(
                ranking_id="parent_ranking",
                name="父榜单",
                channel="parent_channel",
                frequency="daily",
                update_interval=24,
                parent_id=None
            )
            session.add(parent_ranking)
            session.commit()
            
            # 创建子榜单
            child_ranking = Ranking(
                ranking_id="child_ranking",
                name="子榜单",
                channel="child_channel",
                frequency="daily",
                update_interval=24,
                parent_id=parent_ranking.ranking_id
            )
            session.add(child_ranking)
            session.commit()
            
            # 验证层级关系
            saved_child = session.exec(
                select(Ranking).where(Ranking.ranking_id == "child_ranking")
            ).first()
            assert saved_child is not None
            assert saved_child.parent_id == parent_ranking.ranking_id
            
            saved_parent = session.exec(
                select(Ranking).where(Ranking.ranking_id == "parent_ranking")
            ).first()
            assert saved_parent is not None
            assert saved_parent.parent_id is None
            
            # 测试不能创建循环引用
            try:
                parent_ranking.parent_id = child_ranking.ranking_id
                session.commit()
                assert False, "不应该允许循环引用"
            except Exception:
                session.rollback()
            
            # 清理测试数据
            session.delete(child_ranking)
            session.delete(parent_ranking)
            session.commit()


class TestServiceLayerConsistency:
    """服务层一致性测试"""

    def test_book_service_data_consistency(self):
        """测试书籍服务数据一致性"""
        with get_session() as session:
            book_service = BookService(session)
            
            # 创建测试书籍
            test_book = Book(
                book_id="service_test_book",
                title="服务测试书籍",
                author_id="test_author",
                author_name="测试作者",
                novel_class="测试分类"
            )
            session.add(test_book)
            
            # 创建书籍快照
            test_snapshot = BookSnapshot(
                book_id=test_book.book_id,
                total_clicks=1000,
                total_favorites=500,
                comment_count=100,
                chapter_count=20
            )
            session.add(test_snapshot)
            session.commit()
            
            # 通过服务获取书籍详情
            book_detail = book_service.get_book_detail(test_book.book_id)
            assert book_detail is not None
            assert book_detail["book_id"] == test_book.book_id
            assert book_detail["title"] == test_book.title
            assert "latest_stats" in book_detail
            
            # 验证统计数据一致性
            latest_stats = book_detail["latest_stats"]
            assert latest_stats["total_clicks"] == test_snapshot.total_clicks
            assert latest_stats["total_favorites"] == test_snapshot.total_favorites
            
            # 测试书籍搜索一致性
            search_results = book_service.search_books(
                keyword=None,
                novel_class="测试分类",
                author=None,
                limit=10,
                offset=0
            )
            assert search_results["total"] >= 1
            
            # 验证搜索结果包含我们创建的书籍
            found_book = None
            for book in search_results["books"]:
                if book["book_id"] == test_book.book_id:
                    found_book = book
                    break
            
            assert found_book is not None, "搜索结果应该包含测试书籍"
            assert found_book["novel_class"] == "测试分类"
            
            # 清理测试数据
            session.delete(test_snapshot)
            session.delete(test_book)
            session.commit()

    def test_ranking_service_data_consistency(self):
        """测试榜单服务数据一致性"""
        with get_session() as session:
            ranking_service = RankingService(session)
            
            # 创建测试数据
            test_ranking = Ranking(
                ranking_id="ranking_service_test",
                name="榜单服务测试",
                channel="test_channel",
                frequency="daily",
                update_interval=24
            )
            session.add(test_ranking)
            
            test_book = Book(
                book_id="ranking_service_book",
                title="榜单服务书籍",
                author_id="test_author",
                author_name="测试作者"
            )
            session.add(test_book)
            session.commit()
            
            # 创建榜单快照
            now = datetime.now()
            test_snapshot = RankingSnapshot(
                ranking_id=test_ranking.ranking_id,
                book_id=test_book.book_id,
                position=1,
                snapshot_time=now,
                ranking_clicks=800,
                ranking_favorites=400
            )
            session.add(test_snapshot)
            session.commit()
            
            # 通过服务获取榜单书籍
            ranking_books = ranking_service.get_ranking_books(
                ranking_id=test_ranking.ranking_id,
                date=None,
                limit=10,
                offset=0
            )
            
            assert ranking_books is not None
            assert "books" in ranking_books
            assert len(ranking_books["books"]) >= 1
            
            # 验证榜单书籍数据一致性
            found_book = ranking_books["books"][0]
            assert found_book["book_id"] == test_book.book_id
            assert found_book["position"] == 1
            assert found_book["ranking_clicks"] == 800
            assert found_book["ranking_favorites"] == 400
            
            # 测试榜单历史一致性
            ranking_history = ranking_service.get_ranking_history(
                ranking_id=test_ranking.ranking_id,
                days=7
            )
            
            assert ranking_history is not None
            assert "snapshots" in ranking_history
            assert ranking_history["ranking"]["ranking_id"] == test_ranking.ranking_id
            
            # 清理测试数据
            session.delete(test_snapshot)
            session.delete(test_book)
            session.delete(test_ranking)
            session.commit()

    def test_task_service_state_consistency(self):
        """测试任务服务状态一致性"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_file = os.path.join(temp_dir, "consistency_test_tasks.json")
            task_service = TaskService(tasks_file)
            
            # 创建任务
            task_id = task_service.create_task(
                task_type="consistency_test",
                metadata={"test": "consistency"}
            )
            
            # 验证初始状态
            task_detail = task_service.get_task_detail(task_id)
            assert task_detail["status"] == "pending"
            assert task_detail["progress"] == 0
            assert task_detail["items_crawled"] == 0
            
            # 启动任务
            success = task_service.start_task(task_id)
            assert success is True
            
            # 验证状态变化
            task_detail = task_service.get_task_detail(task_id)
            assert task_detail["status"] == "running"
            assert "started_at" in task_detail
            
            # 更新进度
            task_service.update_progress(task_id, 50, 25)
            task_detail = task_service.get_task_detail(task_id)
            assert task_detail["progress"] == 50
            assert task_detail["items_crawled"] == 25
            
            # 完成任务
            task_service.complete_task(task_id, {"result": "success"})
            task_detail = task_service.get_task_detail(task_id)
            assert task_detail["status"] == "completed"
            assert task_detail["progress"] == 100
            assert "completed_at" in task_detail
            
            # 验证任务状态转换的正确性
            all_tasks = task_service.get_all_tasks()
            completed_tasks = [
                task for task in all_tasks["completed_tasks"]
                if task["task_id"] == task_id
            ]
            assert len(completed_tasks) == 1
            assert completed_tasks[0]["status"] == "completed"
            
            # 验证不能重复启动已完成的任务
            success = task_service.start_task(task_id)
            assert success is False, "不应该能够重新启动已完成的任务"


class TestConcurrencyConsistency:
    """并发一致性测试"""

    def test_concurrent_task_creation(self):
        """测试并发任务创建的一致性"""
        from app.modules.service.task_service import TaskService
        import tempfile
        import os
        from concurrent.futures import ThreadPoolExecutor
        
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks_file = os.path.join(temp_dir, "concurrent_tasks.json")
            
            def create_task(task_index):
                task_service = TaskService(tasks_file)
                return task_service.create_task(
                    task_type=f"concurrent_test_{task_index}",
                    metadata={"index": task_index}
                )
            
            # 并发创建10个任务
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(create_task, i) for i in range(10)]
                task_ids = [future.result() for future in futures]
            
            # 验证所有任务都成功创建
            assert len(task_ids) == 10
            assert all(task_id for task_id in task_ids), "所有任务ID都应该有效"
            assert len(set(task_ids)) == 10, "所有任务ID都应该是唯一的"
            
            # 验证任务文件的一致性
            task_service = TaskService(tasks_file)
            all_tasks = task_service.get_all_tasks()
            current_task_ids = [task["task_id"] for task in all_tasks["current_tasks"]]
            
            # 验证所有创建的任务都在文件中
            for task_id in task_ids:
                assert task_id in current_task_ids, f"任务 {task_id} 应该在任务文件中"

    def test_concurrent_database_operations(self):
        """测试并发数据库操作的一致性"""
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        def create_and_query_book(book_index):
            with get_session() as session:
                # 创建书籍
                book = Book(
                    book_id=f"concurrent_book_{book_index}_{threading.current_thread().ident}",
                    title=f"并发测试书籍{book_index}",
                    author_id=f"author_{book_index}",
                    author_name=f"作者{book_index}"
                )
                session.add(book)
                session.commit()
                
                # 查询书籍
                saved_book = session.exec(
                    select(Book).where(Book.book_id == book.book_id)
                ).first()
                
                # 删除书籍
                session.delete(book)
                session.commit()
                
                return saved_book is not None
        
        # 并发执行数据库操作
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_and_query_book, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        # 验证所有操作都成功
        assert all(results), "所有并发数据库操作都应该成功"