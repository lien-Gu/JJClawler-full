# 晋江文学城爬虫项目详细设计方案

## 1. 项目概述

### 1.1 项目背景
晋江文学城爬虫项目是一个基于Python的轻量级数据采集和API服务系统，专注于晋江文学城榜单数据的自动化采集、存储和查询服务。

### 1.2 设计目标
- **高效性**: 提供快速的数据采集和查询服务
- **可靠性**: 确保数据准确性和系统稳定性
- **可扩展性**: 支持新的数据源和功能扩展
- **易维护性**: 代码结构清晰，模块化设计
- **类型安全**: 全面使用类型注解和验证

### 1.3 技术选型原则
- **现代化**: 使用Python 3.12+的最新特性
- **类型安全**: FastAPI + Pydantic + SQLAlchemy提供完整的类型检查
- **轻量级**: SQLite数据库，无需额外部署成本
- **异步优先**: 支持高并发请求处理
- **测试覆盖**: 完整的单元测试和集成测试

## 2. 系统架构设计


### 2.1 核心模块依赖关系
```
API Layer
    ↓
Service Layer
    ↓
DAO Layer
    ↓
Model Layer
    ↓
Database Layer
```

### 2.2 数据流向
1. **爬虫数据流**: Scheduler → Crawler → Parser → Service → DAO → Database
2. **API查询流**: API → Service → DAO → Database → Service → API
3. **报告生成流**: Scheduler → Service → DAO → Database → Report Generator

## 3. 核心模块设计

### 3.1 配置模块 (config.py)
```python
# 使用Pydantic BaseSettings自动读取环境变量
class Settings(BaseSettings):
    # 数据库配置
    database_url: str = "sqlite:///./data/jjcrawler.db"
    database_echo: bool = False
    
    # API配置
    api_title: str = "JJCrawler API"
    api_version: str = "1.0.0"
    api_debug: bool = False
    
    # 爬虫配置
    crawl_user_agent: str = "Mozilla/5.0..."
    crawl_timeout: int = 30
    crawl_retry_times: int = 3
    crawl_delay: float = 1.0
    
    # 调度器配置
    scheduler_timezone: str = "Asia/Shanghai"
    scheduler_job_defaults: dict = {
        "coalesce": False,
        "max_instances": 1
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### 3.2 数据模型设计

#### 3.2.1 书籍模型 (Book)
```python
class Book(Base):
    __tablename__ = "books"
    
    # 主键和基本信息
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    novel_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    author: Mapped[str] = mapped_column(String(100), index=True)
    
    # 书籍状态
    status: Mapped[str] = mapped_column(String(20))  # 连载中/完结
    tag: Mapped[str] = mapped_column(String(50))     # 分类标签
    length: Mapped[int] = mapped_column(Integer)     # 字数
    intro: Mapped[str] = mapped_column(Text)         # 简介
    
    # 时间戳
    last_update: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    snapshots: Mapped[List["BookSnapshot"]] = relationship(back_populates="book")
```

#### 3.2.2 书籍快照模型 (BookSnapshot)
```python
class BookSnapshot(Base):
    __tablename__ = "book_snapshots"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    novel_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.novel_id"))
    
    # 统计数据
    favorites: Mapped[int] = mapped_column(Integer, default=0)
    total_clicks: Mapped[int] = mapped_column(Integer, default=0)
    monthly_clicks: Mapped[int] = mapped_column(Integer, default=0)
    weekly_clicks: Mapped[int] = mapped_column(Integer, default=0)
    daily_clicks: Mapped[int] = mapped_column(Integer, default=0)
    
    total_comments: Mapped[int] = mapped_column(Integer, default=0)
    monthly_comments: Mapped[int] = mapped_column(Integer, default=0)
    weekly_comments: Mapped[int] = mapped_column(Integer, default=0)
    daily_comments: Mapped[int] = mapped_column(Integer, default=0)
    
    total_recs: Mapped[int] = mapped_column(Integer, default=0)
    monthly_recs: Mapped[int] = mapped_column(Integer, default=0)
    weekly_recs: Mapped[int] = mapped_column(Integer, default=0)
    daily_recs: Mapped[int] = mapped_column(Integer, default=0)
    
    # 时间戳
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    
    # 关系
    book: Mapped["Book"] = relationship(back_populates="snapshots")
```

### 3.3 API层设计

#### 3.3.1 书籍API (books.py)
```python
@router.get("/", response_model=List[BookResponse])
async def get_books(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tag: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取书籍列表"""
    pass

@router.get("/{novel_id}", response_model=BookDetailResponse)
async def get_book_detail(
    novel_id: int,
    db: Session = Depends(get_db)
):
    """获取书籍详情"""
    pass

@router.get("/{novel_id}/trend", response_model=BookTrendResponse)
async def get_book_trend(
    novel_id: int,
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """获取书籍趋势数据"""
    pass

@router.get("/search", response_model=List[BookResponse])
async def search_books(
    keyword: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """搜索书籍"""
    pass
```

#### 3.3.2 榜单API (rankings.py)
```python
@router.get("/", response_model=List[RankingResponse])
async def get_rankings(
    type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """获取榜单列表"""
    pass

@router.get("/{ranking_id}", response_model=RankingDetailResponse)
async def get_ranking_detail(
    ranking_id: int,
    date: Optional[date] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取榜单详情"""
    pass

@router.get("/{ranking_id}/history", response_model=List[RankingHistoryResponse])
async def get_ranking_history(
    ranking_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """获取榜单历史数据"""
    pass
```

## 4. 错误处理与日志

### 4.1 异常处理策略
```python
# 自定义异常类
class JJCrawlerException(Exception):
    """基础异常类"""
    pass

class BookNotFoundError(JJCrawlerException):
    """书籍不存在异常"""
    pass

class CrawlerError(JJCrawlerException):
    """爬虫异常"""
    pass

class DatabaseError(JJCrawlerException):
    """数据库异常"""
    pass
```

### 4.2 日志配置
```python
# 日志配置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/jjcrawler.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
    },
    "loggers": {
        "jjcrawler": {
            "level": "DEBUG",
            "handlers": ["console", "file"]
        }
    }
}
```

## 5. 性能优化

### 5.1 数据库优化
- **索引策略**: 根据查询模式创建合适的索引
- **查询优化**: 使用SQLAlchemy的查询优化特性
- **连接池**: 配置合适的数据库连接池
- **批量操作**: 使用批量插入和更新减少数据库交互

### 5.2 缓存策略
```python
# Redis缓存配置
CACHE_CONFIG = {
    "backend": "redis",
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "expire": 3600  # 1小时过期
}

# 缓存装饰器
@cache.cached(timeout=3600)
async def get_book_detail(novel_id: int):
    """获取书籍详情（带缓存）"""
    pass
```

## 6. 部署架构

### 6.1 Docker Compose配置
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/jjcrawler.db
      - API_DEBUG=false
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - app
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

## 7. 测试策略

### 7.1 测试金字塔
```
┌─────────────────────┐
│    端到端测试 (E2E)  │  ← 少量，覆盖关键业务流程
├─────────────────────┤
│    集成测试          │  ← 适量，测试模块间交互
├─────────────────────┤
│    单元测试          │  ← 大量，测试个别函数/方法
└─────────────────────┘
```

### 7.2 测试覆盖率目标
- **单元测试**: 90%以上代码覆盖率
- **集成测试**: 80%以上接口覆盖率
- **端到端测试**: 100%关键业务流程覆盖

### 7.3 测试数据管理
```python
# 测试数据工厂
class BookFactory:
    @staticmethod
    def create_book(**kwargs):
        defaults = {
            "novel_id": 12345,
            "title": "测试小说",
            "author": "测试作者",
            "status": "连载中",
            "tag": "现代言情",
            "length": 100000,
            "intro": "测试小说简介",
            "last_update": datetime.now()
        }
        defaults.update(kwargs)
        return Book(**defaults)
```

## 8. 扩展规划

### 8.1 功能扩展
- **多数据源**: 支持更多文学网站
- **实时通知**: 书籍更新实时推送
- **数据分析**: 趋势分析和预测
- **用户系统**: 用户注册和个性化推荐

### 8.2 技术升级
- **微服务架构**: 拆分为多个微服务
- **容器化**: 完全容器化部署
- **消息队列**: 引入Redis/RabbitMQ
- **分布式**: 支持分布式部署

### 8.3 性能提升
- **缓存层**: 引入Redis缓存
- **CDN**: 静态资源CDN加速
- **负载均衡**: 多实例负载均衡
- **数据库优化**: 读写分离、分库分表

## 9. 总结

本设计方案基于现代化的Python技术栈，采用MVP架构原则，既保证了功能的完整性，又确保了系统的可维护性和可扩展性。通过分层设计、模块化开发、完善的测试策略和详细的文档，为项目的成功实施提供了坚实的基础。

项目的核心优势：
- **类型安全**: 全面使用类型注解和验证
- **高效性能**: 异步处理和数据库优化
- **易于维护**: 清晰的模块划分和代码结构
- **可扩展性**: 支持功能和技术的渐进式升级
- **完整测试**: 单元测试、集成测试、端到端测试全覆盖

这个设计方案将为JJCrawler项目提供一个稳定、高效、可维护的技术基础，支撑项目的长期发展。
