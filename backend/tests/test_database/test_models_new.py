"""
数据库模型测试
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from app.database.models import Book, BookSnapshot, Ranking, RankingSnapshot


class TestBookModel:
    """书籍模型测试"""
    
    def test_create_book(self, test_db):
        """测试创建书籍"""
        book = Book(
            novel_id=12345,
            title="测试小说",
            author="测试作者"
        )
        test_db.add(book)
        test_db.commit()
        
        assert book.id is not None
        assert book.novel_id == 12345
        assert book.title == "测试小说"
        assert book.author == "测试作者"
        assert book.created_at is not None
        assert book.updated_at is not None
    
    def test_book_novel_id_unique(self, test_db):
        """测试novel_id唯一约束"""
        book1 = Book(novel_id=12345, title="小说1", author="作者1")
        book2 = Book(novel_id=12345, title="小说2", author="作者2")
        
        test_db.add(book1)
        test_db.commit()
        
        test_db.add(book2)
        with pytest.raises(IntegrityError):
            test_db.commit()
    
    def test_book_relationships(self, test_db, sample_book):
        """测试书籍关系"""
        # 创建快照
        snapshot = BookSnapshot(
            book_id=sample_book.id,
            favorites=100,
            clicks=500
        )
        test_db.add(snapshot)
        test_db.commit()
        
        # 测试关系
        test_db.refresh(sample_book)
        assert len(sample_book.snapshots) == 1
        assert sample_book.snapshots[0].favorites == 100


class TestBookSnapshotModel:
    """书籍快照模型测试"""
    
    def test_create_book_snapshot(self, test_db, sample_book):
        """测试创建书籍快照"""
        snapshot = BookSnapshot(
            book_id=sample_book.id,
            favorites=1000,
            clicks=5000,
            comments=100,
            recommendations=50,
            word_count=100000,
            status="连载中"
        )
        test_db.add(snapshot)
        test_db.commit()
        
        assert snapshot.id is not None
        assert snapshot.book_id == sample_book.id
        assert snapshot.favorites == 1000
        assert snapshot.clicks == 5000
        assert snapshot.snapshot_time is not None
    
    def test_book_snapshot_defaults(self, test_db, sample_book):
        """测试快照默认值"""
        snapshot = BookSnapshot(book_id=sample_book.id)
        test_db.add(snapshot)
        test_db.commit()
        
        assert snapshot.favorites == 0
        assert snapshot.clicks == 0
        assert snapshot.comments == 0
        assert snapshot.recommendations == 0
    
    def test_book_snapshot_relationship(self, test_db, sample_book):
        """测试快照与书籍的关系"""
        snapshot = BookSnapshot(
            book_id=sample_book.id,
            favorites=100
        )
        test_db.add(snapshot)
        test_db.commit()
        test_db.refresh(snapshot)
        
        assert snapshot.book is not None
        assert snapshot.book.id == sample_book.id


class TestRankingModel:
    """榜单模型测试"""
    
    def test_create_ranking(self, test_db):
        """测试创建榜单"""
        ranking = Ranking(
            rank_id=1,
            name="测试榜单",
            page_id="test_page",
            rank_group_type="romance"
        )
        test_db.add(ranking)
        test_db.commit()
        
        assert ranking.id is not None
        assert ranking.rank_id == 1
        assert ranking.name == "测试榜单"
        assert ranking.page_id == "test_page"
        assert ranking.rank_group_type == "romance"
    
    def test_ranking_rank_id_unique(self, test_db):
        """测试rank_id唯一约束"""
        ranking1 = Ranking(rank_id=1, name="榜单1", page_id="page1")
        ranking2 = Ranking(rank_id=1, name="榜单2", page_id="page2")
        
        test_db.add(ranking1)
        test_db.commit()
        
        test_db.add(ranking2)
        with pytest.raises(IntegrityError):
            test_db.commit()


class TestRankingSnapshotModel:
    """榜单快照模型测试"""
    
    def test_create_ranking_snapshot(self, test_db, sample_ranking, sample_book):
        """测试创建榜单快照"""
        snapshot = RankingSnapshot(
            ranking_id=sample_ranking.id,
            book_id=sample_book.id,
            position=1,
            score=95.5
        )
        test_db.add(snapshot)
        test_db.commit()
        
        assert snapshot.id is not None
        assert snapshot.ranking_id == sample_ranking.id
        assert snapshot.book_id == sample_book.id
        assert snapshot.position == 1
        assert snapshot.score == 95.5
    
    def test_ranking_snapshot_unique_constraint(self, test_db, sample_ranking, sample_book):
        """测试榜单快照唯一约束"""
        snapshot_time = datetime.now()
        
        snapshot1 = RankingSnapshot(
            ranking_id=sample_ranking.id,
            book_id=sample_book.id,
            position=1,
            snapshot_time=snapshot_time
        )
        snapshot2 = RankingSnapshot(
            ranking_id=sample_ranking.id,
            book_id=sample_book.id,
            position=2,
            snapshot_time=snapshot_time
        )
        
        test_db.add(snapshot1)
        test_db.commit()
        
        test_db.add(snapshot2)
        with pytest.raises(IntegrityError):
            test_db.commit()
    
    def test_ranking_snapshot_relationships(self, test_db, sample_ranking, sample_book):
        """测试榜单快照关系"""
        snapshot = RankingSnapshot(
            ranking_id=sample_ranking.id,
            book_id=sample_book.id,
            position=1
        )
        test_db.add(snapshot)
        test_db.commit()
        test_db.refresh(snapshot)
        
        assert snapshot.ranking is not None
        assert snapshot.ranking.id == sample_ranking.id
        assert snapshot.book is not None
        assert snapshot.book.id == sample_book.id


class TestModelIntegration:
    """模型集成测试"""
    
    def test_complete_data_flow(self, test_db):
        """测试完整的数据流"""
        # 创建书籍
        book = Book(novel_id=12345, title="测试小说", author="测试作者")
        test_db.add(book)
        test_db.commit()
        test_db.refresh(book)
        
        # 创建榜单
        ranking = Ranking(rank_id=1, name="测试榜单", page_id="test")
        test_db.add(ranking)
        test_db.commit()
        test_db.refresh(ranking)
        
        # 创建书籍快照
        book_snapshot = BookSnapshot(
            book_id=book.id,
            favorites=1000,
            clicks=5000
        )
        test_db.add(book_snapshot)
        test_db.commit()
        
        # 创建榜单快照
        ranking_snapshot = RankingSnapshot(
            ranking_id=ranking.id,
            book_id=book.id,
            position=1,
            score=95.0
        )
        test_db.add(ranking_snapshot)
        test_db.commit()
        
        # 验证所有关系
        test_db.refresh(book)
        test_db.refresh(ranking)
        
        assert len(book.snapshots) == 1
        assert len(book.ranking_snapshots) == 1
        assert len(ranking.ranking_snapshots) == 1
        
        assert book.snapshots[0].favorites == 1000
        assert book.ranking_snapshots[0].position == 1
        assert ranking.ranking_snapshots[0].book_id == book.id