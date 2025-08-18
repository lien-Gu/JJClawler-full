# 错误记录文档

## 2025-08-18 数据库操作错误修复

### 错误1：ranking_data中必须包含rank_id

**时间**：2025-08-18 09:30

**错误信息**：
```
数据库操作失败: ranking_data中必须包含rank_id
```

**原因分析**：
- 位置：`app/database/service/ranking_service.py:32`
- 问题：`create_or_update_ranking` 方法要求 rank_id 必须存在，但某些解析器可能生成空的 rank_id
- 根本原因：过于严格的必填字段验证

**解决方法**：
- 修改 `create_or_update_ranking` 方法，当 rank_id 为空时直接创建新榜单
- 代码变更：将抛出异常改为直接调用 `create_ranking`

**修复后代码**：
```python
rank_id = ranking_data.get("rank_id")
if not rank_id:
    # rank_id为空时，直接创建新榜单
    return self.create_ranking(db, ranking_data)
```

### 错误2：UNIQUE constraint failed: books.novel_id

**时间**：2025-08-18 09:30

**错误信息**：
```
数据库操作失败: (sqlite3.IntegrityError) UNIQUE constraint failed: books.novel_id
[SQL: INSERT INTO books (novel_id, title, author_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)]
[parameters: ('3031082', '上线老婆变成邪神了', '1247508', '2025-08-18 09:30:01.799870', '2025-08-18 09:30:01.799875')]
```

**原因分析**：
- 位置：`app/database/service/book_service.py:72-87`
- 问题：`create_or_update_book` 方法在并发情况下可能出现竞态条件
- 具体场景：检查书籍不存在 → 尝试创建 → 其他线程已创建相同 novel_id → 唯一约束失败

**解决方法**：
1. 增强 novel_id 类型检查和转换
2. 在创建失败时增加重试机制，捕获唯一约束错误
3. 失败后回滚事务并重新尝试获取更新

**修复后代码**：
```python
# 确保novel_id是整数类型
try:
    novel_id = int(novel_id)
    book_data["novel_id"] = novel_id
except (ValueError, TypeError):
    raise ValueError(f"Invalid novel_id format: {novel_id}")

# 如果不存在，尝试创建新书籍
try:
    return self.create_book(db, book_data)
except Exception as e:
    # 如果创建失败（可能是并发导致的重复插入），再次尝试获取并更新
    error_str = str(e).lower()
    if "unique constraint failed" in error_str or "duplicate" in error_str:
        # 刷新会话，重新获取可能已经被其他事务创建的记录
        db.rollback()
        book = self.get_book_by_novel_id(db, novel_id)
        if book:
            return self.update_book(db, book, book_data)
    # 如果仍然失败，重新抛出异常
    raise e
```

**影响范围**：
- 提高了并发爬取的稳定性
- 避免了因数据竞争导致的爬取任务失败
- 保证了数据的一致性

**测试建议**：
- 进行并发爬取测试，验证修复效果
- 监控后续日志，确认错误不再出现