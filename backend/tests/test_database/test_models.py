"""
数据库模型测试
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os


class TestDatabaseModels:
    """数据库模型测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """设置测试数据库"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # 创建数据库引擎
        self.engine = create_engine(
            f"sqlite:///{self.temp_db.name}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        
        # 创建表
        from app.database.models import Base
        Base.metadata.create_all(bind=self.engine)
        
        # 创建会话
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.SessionLocal()
        
        yield
        
        # 清理
        self.session.close()
        os.unlink(self.temp_db.name)
    
    def test_book_model_creation(self):
        """测试书籍模型创建"""
        from app.database.models.book import Book
        
        # 创建书籍实例
        book = Book(
            novel_id=12345,
            title="测试小说",
            author="测试作者",
            status="连载中",
            tag="现代言情",
            length=100000,
            favorites=1000,
            total_clicks=5000,
            intro="这是一本测试小说"
        )
        
        # 检查属性
        assert book.novel_id == 12345
        assert book.title == "测试小说"
        assert book.author == "测试作者"
        assert book.status == "连载中"
        assert book.tag == "现代言情"
        assert book.length == 100000
        assert book.favorites == 1000
        assert book.total_clicks == 5000
        assert book.intro == "这是一本测试小说"
        
        # 保存到数据库
        self.session.add(book)
        self.session.commit()
        
        # 验证保存成功
        saved_book = self.session.query(Book).filter_by(novel_id=12345).first()
        assert saved_book is not None
        assert saved_book.title == "测试小说"
    
    def test_book_model_validation(self):
        """测试书籍模型验证"""
        from app.database.models.book import Book
        
        # 测试必填字段
        with pytest.raises(ValueError):
            Book(title="", author="测试作者")  # 空标题
        
        with pytest.raises(ValueError):
            Book(title="测试小说", author="")  # 空作者
        
        with pytest.raises(ValueError):
            Book(title="测试小说", author="测试作者", novel_id=0)  # 无效ID
    
    def test_book_snapshot_model(self):
        """测试书籍快照模型"""
        from app.database.models.book import Book, BookSnapshot
        
        # 创建书籍
        book = Book(
            novel_id=12345,
            title="测试小说",
            author="测试作者"
        )
        self.session.add(book)
        self.session.commit()
        
        # 创建快照
        snapshot = BookSnapshot(
            book_id=book.id,
            favorites=1000,
            total_clicks=5000,
            monthly_clicks=500,
            weekly_clicks=100,
            daily_clicks=20,
            total_comments=200,
            monthly_comments=50,
            weekly_comments=10,
            daily_comments=2,
            total_recs=100,
            monthly_recs=25,
            weekly_recs=5,
            daily_recs=1,
            snapshot_time=datetime.now(timezone.utc)
        )
        
        # 保存快照
        self.session.add(snapshot)
        self.session.commit()
        
        # 验证快照保存成功
        saved_snapshot = self.session.query(BookSnapshot).filter_by(book_id=book.id).first()
        assert saved_snapshot is not None
        assert saved_snapshot.favorites == 1000
        assert saved_snapshot.total_clicks == 5000
    
    def test_ranking_model(self):
        """测试榜单模型"""
        from app.database.models.ranking import Ranking
        
        # 创建榜单
        ranking = Ranking(
            name="夹子榜",
            type="jiazi",
            url="https://www.jjwxc.net/topten.php?orderstr=4",
            description="夹子榜单",
            is_active=True,
            crawl_interval=3600
        )
        
        # 保存榜单
        self.session.add(ranking)
        self.session.commit()
        
        # 验证榜单保存成功
        saved_ranking = self.session.query(Ranking).filter_by(name="夹子榜").first()
        assert saved_ranking is not None
        assert saved_ranking.type == "jiazi"
        assert saved_ranking.is_active == True
        assert saved_ranking.crawl_interval == 3600
    
    def test_ranking_snapshot_model(self):
        """测试榜单快照模型"""
        from app.database.models.ranking import Ranking, RankingSnapshot
        from app.database.models.book import Book
        
        # 创建榜单
        ranking = Ranking(
            name="夹子榜",
            type="jiazi",
            url="https://www.jjwxc.net/topten.php?orderstr=4"
        )
        self.session.add(ranking)
        self.session.commit()
        
        # 创建书籍
        book = Book(
            novel_id=12345,
            title="测试小说",
            author="测试作者"
        )
        self.session.add(book)
        self.session.commit()
        
        # 创建榜单快照
        snapshot = RankingSnapshot(
            ranking_id=ranking.id,
            book_id=book.id,
            position=1,
            score=1000,
            snapshot_time=datetime.now(timezone.utc)
        )
        
        # 保存快照
        self.session.add(snapshot)
        self.session.commit()
        
        # 验证快照保存成功
        saved_snapshot = self.session.query(RankingSnapshot).filter_by(
            ranking_id=ranking.id,
            book_id=book.id
        ).first()
        assert saved_snapshot is not None
        assert saved_snapshot.position == 1
        assert saved_snapshot.score == 1000
    
    def test_model_relationships(self):
        """测试模型关系"""
        from app.database.models.book import Book, BookSnapshot
        from app.database.models.ranking import Ranking, RankingSnapshot
        
        # 创建书籍
        book = Book(
            novel_id=12345,
            title="测试小说",
            author="测试作者"
        )
        self.session.add(book)
        self.session.commit()
        
        # 创建书籍快照
        book_snapshot = BookSnapshot(
            book_id=book.id,
            favorites=1000,
            snapshot_time=datetime.now(timezone.utc)
        )
        self.session.add(book_snapshot)
        
        # 创建榜单
        ranking = Ranking(
            name="夹子榜",
            type="jiazi",
            url="https://www.jjwxc.net/topten.php?orderstr=4"
        )
        self.session.add(ranking)
        self.session.commit()
        
        # 创建榜单快照
        ranking_snapshot = RankingSnapshot(
            ranking_id=ranking.id,
            book_id=book.id,
            position=1,
            snapshot_time=datetime.now(timezone.utc)
        )
        self.session.add(ranking_snapshot)
        self.session.commit()
        
        # 测试关系
        assert book.snapshots is not None
        assert len(book.snapshots) == 1
        assert book.snapshots[0].favorites == 1000
        
        assert ranking.snapshots is not None
        assert len(ranking.snapshots) == 1
        assert ranking.snapshots[0].position == 1
    
    def test_model_timestamps(self):
        """测试模型时间戳"""
        from app.database.models.book import Book
        
        # 创建书籍
        book = Book(
            novel_id=12345,
            title="测试小说",
            author="测试作者"
        )
        self.session.add(book)
        self.session.commit()
        
        # 检查时间戳
        assert book.created_at is not None
        assert book.updated_at is not None
        assert book.created_at <= book.updated_at
        
        # 更新书籍
        original_updated_at = book.updated_at
        book.title = "更新后的小说"
        self.session.commit()
        
        # 检查更新时间
        assert book.updated_at > original_updated_at
    
    def test_model_indexes(self):
        """测试模型索引"""
        from app.database.models.book import Book
        from app.database.models.ranking import Ranking
        
        # 获取表结构信息
        book_table = Book.__table__
        ranking_table = Ranking.__table__
        
        # 检查索引存在
        book_indexes = [idx.name for idx in book_table.indexes]
        ranking_indexes = [idx.name for idx in ranking_table.indexes]
        
        # 验证关键索引存在
        assert any('novel_id' in idx for idx in book_indexes)
        assert any('title' in idx for idx in book_indexes)
        assert any('author' in idx for idx in book_indexes)
        assert any('type' in idx for idx in ranking_indexes)
    
    def test_model_constraints(self):
        """测试模型约束"""
        from app.database.models.book import Book
        from sqlalchemy.exc import IntegrityError
        
        # 创建书籍
        book1 = Book(
            novel_id=12345,
            title="测试小说",
            author="测试作者"
        )
        self.session.add(book1)
        self.session.commit()
        
        # 尝试创建相同novel_id的书籍（应该失败）
        book2 = Book(
            novel_id=12345,
            title="另一本小说",
            author="另一个作者"
        )
        self.session.add(book2)
        
        with pytest.raises(IntegrityError):
            self.session.commit()
    
    def test_model_serialization(self):
        """测试模型序列化"""
        from app.database.models.book import Book
        
        # 创建书籍
        book = Book(
            novel_id=12345,
            title="测试小说",
            author="测试作者",
            status="连载中",
            tag="现代言情",
            length=100000,
            favorites=1000,
            intro="这是一本测试小说"
        )
        
        # 序列化为字典
        book_dict = book.to_dict()
        
        # 验证序列化结果
        assert book_dict["novel_id"] == 12345
        assert book_dict["title"] == "测试小说"
        assert book_dict["author"] == "测试作者"
        assert book_dict["status"] == "连载中"
        assert book_dict["tag"] == "现代言情"
        assert book_dict["length"] == 100000
        assert book_dict["favorites"] == 1000
        assert book_dict["intro"] == "这是一本测试小说"
    
    def test_model_query_methods(self):
        """测试模型查询方法"""
        from app.database.models.book import Book
        
        # 创建多本书籍
        books = [
            Book(novel_id=1, title="小说1", author="作者1", tag="现代言情"),
            Book(novel_id=2, title="小说2", author="作者2", tag="古代言情"),
            Book(novel_id=3, title="小说3", author="作者1", tag="现代言情"),
        ]
        
        for book in books:
            self.session.add(book)
        self.session.commit()
        
        # 测试按作者查询
        author1_books = self.session.query(Book).filter_by(author="作者1").all()
        assert len(author1_books) == 2
        
        # 测试按标签查询
        modern_books = self.session.query(Book).filter_by(tag="现代言情").all()
        assert len(modern_books) == 2
        
        # 测试按标题搜索
        searched_books = self.session.query(Book).filter(
            Book.title.like("%小说%")
        ).all()
        assert len(searched_books) == 3 