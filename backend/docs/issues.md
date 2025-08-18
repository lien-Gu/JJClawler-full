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

## 2025-08-18 日志和数据库问题修复

### 问题1：httpx日志冲刷有效信息

**时间**：2025-08-18 12:02

**现象**：
```
2025-08-18 12:02:00-httpx-INFO-HTTP Request: GET https://app-cdn.jjwxc.com/androidapi/novelbasicinfo?novelId=9195883 "HTTP/1.1 200 OK"
```
大量httpx请求日志在INFO级别输出，冲刷了业务日志

**解决方法**：
- 在 `app/logger.py` 中添加httpx日志级别控制
- 将httpx日志级别设置为WARNING，只记录错误和警告

**修复代码**：
```python
# 禁用httpx的INFO级别日志，只保留WARNING及以上
logging.getLogger("httpx").setLevel(logging.WARNING)
```

### 问题2：author_id NOT NULL约束错误

**时间**：2025-08-18 12:02

**错误信息**：
```
NOT NULL constraint failed: books.author_id
[parameters: (9615662, '选秀出道失败后', None, '2025-08-18 12:02:07.625259', '2025-08-18 12:02:07.625259')]
```

**原因分析**：
- 虽然数据库字段设置了 `nullable=True`，但解析器仍返回 `None` 值
- `_parse_book_basic_info` 方法中 `author_id` 处理不一致

**解决方法**：
- 修改 `parser.py` 中的 `_parse_book_basic_info` 方法
- 确保 `author_id` 为 `None` 时设置为 `0`

**修复代码**：
```python
"author_id": raw_basic_data.get("authorid") or 0,  # 修复：None值设为0
```

### 问题3：数据库事务回滚循环错误

**时间**：2025-08-18 12:02

**错误信息**：
```
This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback().
```

**原因分析**：
- 一旦数据库操作失败，事务被标记为回滚状态
- 后续操作继续使用相同session会失败
- 导致相同错误在不同书籍记录中重复出现

**解决方法**：
- 在异常处理中显式调用 `db.rollback()`
- 确保每次错误后重新开始新事务
- 在 `save_ranking_parsers` 和 `save_novel_parsers` 中都添加回滚处理

**修复代码**：
```python
except Exception as e:
    # 回滚当前事务，重新开始
    try:
        db.rollback()
    except Exception:
        pass  # 忽略回滚失败
    logger.error(f"书籍保存异常，跳过该记录: {book.get('novel_id', 'unknown')}, 错误: {e}")
    continue
```

**影响范围**：
- 消除了httpx日志干扰，提高日志可读性
- 解决了author_id约束问题，提高数据保存成功率
- 修复了事务回滚循环，确保单个失败不影响后续操作
- 提高了爬取系统的整体稳定性和容错性

### 问题4：数据库会话获取方式错误

**时间**：2025-08-18 12:02

**错误描述**：
在 `crawl_flow.py` 中使用 `get_db()` 直接调用，但 `get_db()` 是一个 yield 生成器函数，用于 FastAPI 依赖注入。

**错误代码**：
```python
db = get_db()  # 错误：返回的是生成器对象，不是 Session
```

**原因分析**：
- `get_db()` 是设计用于 FastAPI 依赖注入的生成器函数
- 直接调用返回的是生成器对象，不是数据库会话
- 导致 `db.commit()` 和 `db.rollback()` 调用失败

**解决方法**：
- 在爬虫模块中直接使用 `SessionLocal()` 创建数据库会话
- 修改导入语句和会话创建方式

**修复代码**：
```python
# 修改导入
from app.database.connection import SessionLocal

# 修改会话创建
db = SessionLocal()
```

**影响范围**：
- 修复了数据库事务操作的根本问题
- 确保 `commit()` 和 `rollback()` 调用正常工作
- 提高了数据库操作的可靠性

## 2025-08-18 重试机制失效问题修复

### 问题：503错误和其他异常不触发重试机制

**时间**：2025-08-18 16:32

**现象**：
```
2025-08-18 16:32:22-app.crawl.http_client-ERROR-HTTP请求失败: Server error '503 Service Temporarily Unavailable'
2025-08-18 16:32:22-app.crawl.crawl_flow-ERROR-书籍页面 8748356 内容获取异常: Server error '503 Service Temporarily Unavailable'
```
- HTTP 503错误没有触发重试机制
- 页面解析错误"该榜单中内容为空"也没有重试
- 没有看到重试装饰器的重试日志

**原因分析**：
- 位置：`app/crawl/crawl_flow.py:220-222` 和 `app/crawl/crawl_flow.py:281-283`
- 根本问题：**异常处理阻止了异常传播到重试装饰器**
- 具体机制：
  1. 函数内部捕获所有异常：`except Exception as e:`
  2. 记录错误日志后**返回异常对象**：`return e`
  3. 重试装饰器看到"成功返回"，不会触发重试
  4. `asyncio.gather(*tasks, return_exceptions=True)` 接收到异常对象，认为是正常结果

**错误的异常处理模式**：
```python
@create_retry_decorator()
async def _fetch_and_parse_book(self, novel_id: int) -> NovelPageParser | Exception:
    try:
        # HTTP请求和数据处理
        result = await self.client.run(book_url)
        return novel_parser
    except Exception as e:
        logger.error(f"书籍页面 {novel_id} 内容获取异常: {e}")
        return e  # ❌ 返回异常对象，装饰器看不到异常
```

**解决方法**：
- 移除函数内部的 `try-except` 块
- 让异常直接传播给重试装饰器
- 保持 `asyncio.gather(..., return_exceptions=True)` 处理最终失败的异常

**修复后代码**：
```python
@create_retry_decorator()
async def _fetch_and_parse_book(self, novel_id: int) -> NovelPageParser:
    async with self.request_semaphore:
        # 移除try-except，让异常直接传播给重试装饰器
        if not novel_id:
            raise ValueError(f"Invalid novel_id parameter: '{novel_id}'")
        
        book_url = crawl_task.build_novel_url(str(novel_id))
        result = await self.client.run(book_url)  # 503错误会直接抛出
        
        if not result.get("novelId"):
            raise KeyError(f"Invalid book data: missing novelId in response")
        
        novel_parser = NovelPageParser(result)
        return novel_parser
```

**修复效果**：
- ✅ HTTP 503错误会触发重试机制（配置了 `httpx.HTTPStatusError`）
- ✅ 页面解析错误会触发重试机制（配置了 `ValueError`）  
- ✅ 会看到重试装饰器的 `before_sleep_log` 日志
- ✅ 批量处理的容错性保持不变（`asyncio.gather` 处理最终异常）
- ✅ 临时性网络问题能够自动恢复

**影响范围**：
- 大幅提高了对临时性网络错误的容错能力
- 503服务不可用、网络超时等问题能够自动重试恢复
- 提高了整个爬取系统的稳定性和成功率
- 重试日志能够帮助监控网络状况