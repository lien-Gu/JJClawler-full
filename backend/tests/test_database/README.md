# 数据库测试模块

## 文件结构

```
tests/test_database/
├── conftest.py                 # 测试配置和数据fixture
├── test_models.py              # 数据库模型测试
├── test_dao.py                 # 数据访问层(DAO)测试
├── test_book_service.py        # 书籍服务层测试
├── test_ranking_service.py     # 榜单服务层测试
├── test_book_trend_dao.py      # 书籍趋势数据DAO测试
└── README.md                   # 本说明文档
```

## 测试分层架构

### 1. conftest.py
- 提供测试数据库配置
- 包含各种测试数据的fixture
- 支持内存SQLite数据库快速测试

**主要Fixture:**
- `test_db`: 测试数据库会话
- `sample_book`: 单个测试书籍
- `sample_books`: 多个测试书籍
- `sample_book_snapshots`: 书籍快照数据
- `sample_ranking`: 单个测试榜单
- `sample_rankings`: 多个测试榜单
- `sample_ranking_snapshots`: 榜单快照数据
- `sample_complete_data`: 完整的测试数据集

### 2. test_models.py
**测试范围:** 数据库模型层
- 模型创建和验证
- 字段约束测试
- 关系映射测试
- 唯一约束测试

**测试类:**
- `TestBookModel`: 书籍模型测试
- `TestBookSnapshotModel`: 书籍快照模型测试
- `TestRankingModel`: 榜单模型测试
- `TestRankingSnapshotModel`: 榜单快照模型测试
- `TestModelIntegration`: 模型集成测试

### 3. test_dao.py
**测试范围:** 数据访问层
- CRUD操作测试
- 查询方法测试
- 批量操作测试
- 数据统计测试

**测试类:**
- `TestBookDAO`: 书籍DAO测试
- `TestBookSnapshotDAO`: 书籍快照DAO测试
- `TestRankingDAO`: 榜单DAO测试
- `TestRankingSnapshotDAO`: 榜单快照DAO测试

### 4. test_book_service.py
**测试范围:** 书籍业务逻辑层
- 书籍服务基础功能
- 趋势数据服务（重构后的独立函数）

**测试类:**
- `TestBookService`: 书籍服务基础测试
- `TestBookTrendService`: 书籍趋势服务测试

**重点测试:**
- `get_book_trend_hourly()`: 按小时趋势
- `get_book_trend_daily()`: 按天趋势
- `get_book_trend_weekly()`: 按周趋势
- `get_book_trend_monthly()`: 按月趋势
- `get_book_trend_with_interval()`: 通用间隔趋势

### 5. test_ranking_service.py
**测试范围:** 榜单业务逻辑层
- 榜单查询和管理
- 榜单对比功能
- 榜单统计分析

**测试类:**
- `TestRankingService`: 榜单服务测试

### 6. test_book_trend_dao.py
**测试范围:** 书籍趋势数据DAO层（重构后的独立函数）
- 各种时间间隔的趋势数据查询
- 数据聚合准确性验证
- 边界条件测试

**测试类:**
- `TestBookSnapshotTrendDAO`: 趋势数据DAO测试

**重点测试:**
- `get_hourly_trend_by_book_id()`: 小时级聚合测试
- `get_daily_trend_by_book_id()`: 日级聚合测试
- `get_weekly_trend_by_book_id()`: 周级聚合测试
- `get_monthly_trend_by_book_id()`: 月级聚合测试
- 数据聚合准确性验证
- 时间排序和过滤测试

## 运行测试

### 运行所有数据库测试
```bash
pytest tests/test_database/
```

### 运行特定测试文件
```bash
# 模型测试
pytest tests/test_database/test_models.py

# DAO测试
pytest tests/test_database/test_dao.py

# 服务层测试
pytest tests/test_database/test_book_service.py
pytest tests/test_database/test_ranking_service.py

# 趋势功能测试
pytest tests/test_database/test_book_trend_dao.py
```

### 运行特定测试类
```bash
# 书籍模型测试
pytest tests/test_database/test_models.py::TestBookModel

# 趋势服务测试
pytest tests/test_database/test_book_service.py::TestBookTrendService
```

### 运行特定测试方法
```bash
# 测试按小时获取趋势数据
pytest tests/test_database/test_book_trend_dao.py::TestBookSnapshotTrendDAO::test_get_hourly_trend_by_book_id
```

## 测试数据说明

### 书籍测试数据
- **sample_book**: 单本测试书籍，novel_id=12345
- **sample_books**: 5本测试书籍，novel_id从10000开始
- **sample_book_snapshots**: 7天的快照数据，递增趋势

### 榜单测试数据
- **sample_ranking**: 单个测试榜单，rank_id=1
- **sample_rankings**: 3个测试榜单，包含不同分组类型
- **sample_ranking_snapshots**: 榜单快照数据

### 完整测试数据集
- **sample_complete_data**: 包含书籍、榜单、快照的完整数据集
- 30天的书籍快照历史
- 7天的榜单快照历史
- 支持复杂的关联查询测试

## 测试覆盖重点

### 1. 数据完整性
- 外键约束
- 唯一约束
- 字段验证

### 2. 业务逻辑
- 搜索功能
- 趋势计算
- 排名分析
- 数据聚合

### 3. 性能相关
- 批量操作
- 分页查询
- 索引使用

### 4. 错误处理
- 数据不存在
- 参数错误
- 约束违反

### 5. 重构验证
- 独立函数功能
- 向后兼容性
- 代码重复性消除

## 注意事项

1. **测试隔离**: 每个测试使用独立的内存数据库
2. **数据一致性**: 使用fixture确保测试数据的一致性
3. **清理机制**: 测试结束后自动清理临时数据
4. **异常测试**: 包含正常和异常情况的测试用例
5. **性能考虑**: 测试数据量适中，确保测试执行速度

## 未来扩展

1. **集成测试**: 可以添加API层的集成测试
2. **性能测试**: 可以添加大数据量的性能测试
3. **并发测试**: 可以添加多线程/多进程的并发测试
4. **回归测试**: 持续验证重构后的功能一致性