# JJClawler 爬虫任务操作指导

## 目录
1. [系统概览](#系统概览)
2. [可用爬虫任务](#可用爬虫任务)
3. [手动执行方法](#手动执行方法)
4. [任务监控](#任务监控)
5. [故障排除](#故障排除)
6. [最佳实践](#最佳实践)
7. [常见问题](#常见问题)

## 系统概览

JJClawler 是一个针对晋江文学城的爬虫系统，支持以下功能：
- **夹子榜爬虫**：爬取最高活跃度榜单，每小时更新
- **页面爬虫**：爬取各分类页面榜单，每日更新
- **任务管理**：自动化任务调度和状态监控
- **数据存储**：SQLite数据库 + JSON任务管理

## 可用爬虫任务

### 1. 夹子榜爬虫 (jiazi)
- **功能**：爬取夹子榜单数据
- **频率**：每小时执行
- **数据源**：`https://app-cdn.jjwxc.com/bookstore/favObservationByDate`
- **特点**：高频更新，活跃度最高的榜单

### 2. 页面爬虫 (page crawlers)
支持以下频道：

| 频道代码 | 中文名称 | 更新频率 | 子频道 |
|---------|----------|----------|--------|
| `index` | 首页 | 每日 | - |
| `yq` | 言情 | 每日 | 古言、现言、幻言、古穿、奇幻、未来、衍生言情、二次元 |
| `ca` | 纯爱 | 每日 | 都市、现代幻想、古代、未来幻想、衍生纯爱 |
| `ys` | 衍生 | 每日 | 无CP、纯爱、言情、二次元 |
| `nocp_plus` | 无CP+ | 每日 | 无CP、衍无、男主、女主、多元 |
| `bh` | 百合 | 每日 | - |

## 手动执行方法

### 方法1：API调用 (推荐)

#### 前置条件
确保后端服务运行在 `http://localhost:8000`

#### 夹子榜爬虫
```bash
# 立即执行
curl -X POST "http://localhost:8000/api/v1/crawl/jiazi" \
     -H "Content-Type: application/json" \
     -d '{"immediate": true}'

# 通过调度器触发
curl -X POST "http://localhost:8000/api/v1/crawl/scheduler/trigger/jiazi"
```

#### 页面爬虫
```bash
# 爬取特定频道
curl -X POST "http://localhost:8000/api/v1/crawl/page/yq" \
     -H "Content-Type: application/json" \
     -d '{"immediate": true}'

# 查看可用频道
curl -X GET "http://localhost:8000/api/v1/crawl/channels"
```

#### 批量执行所有频道
```bash
#!/bin/bash
# 执行所有主要频道爬虫
channels=("yq" "ca" "ys" "nocp_plus" "bh" "index")

for channel in "${channels[@]}"; do
  echo "触发频道: $channel"
  curl -X POST "http://localhost:8000/api/v1/crawl/scheduler/trigger/$channel"
  sleep 2  # 避免过于频繁的请求
done
```

### 方法2：Python脚本

#### 创建夹子榜爬虫脚本 (`manual_jiazi_crawl.py`)
```python
import asyncio
from app.modules.service.crawler_service import CrawlerService
from app.modules.service.task_service import get_task_manager, TaskType, execute_with_task

async def run_jiazi_crawl():
    """手动运行夹子榜爬虫"""
    print("开始执行夹子榜爬虫...")
    
    task_manager = get_task_manager()
    task_id = task_manager.create_task(
        TaskType.JIAZI, 
        {"trigger_source": "manual"}
    )
    
    async def crawl_func():
        crawler_service = CrawlerService()
        try:
            result = await crawler_service.crawl_and_save_jiazi()
            print(f"爬取完成: {result}")
            return result
        finally:
            crawler_service.close()
    
    success = await execute_with_task(task_id, crawl_func)
    
    if success:
        print(f"夹子榜爬虫执行成功，任务ID: {task_id}")
    else:
        print(f"夹子榜爬虫执行失败，任务ID: {task_id}")

if __name__ == "__main__":
    asyncio.run(run_jiazi_crawl())
```

#### 创建页面爬虫脚本 (`manual_page_crawl.py`)
```python
import asyncio
import sys
from app.modules.service.crawler_service import CrawlerService
from app.modules.service.task_service import get_task_manager, TaskType, execute_with_task
from app.modules.service.page_service import get_page_service

async def run_page_crawl(channel: str):
    """手动运行指定频道的页面爬虫"""
    print(f"开始执行频道 {channel} 的页面爬虫...")
    
    # 验证频道
    page_service = get_page_service()
    available_channels = page_service.get_ranking_channels()
    valid_channels = [c['channel'] for c in available_channels]
    
    if channel not in valid_channels:
        print(f"错误：无效频道 {channel}")
        print(f"可用频道：{valid_channels}")
        return
    
    # 创建并执行任务
    task_manager = get_task_manager()
    task_id = task_manager.create_task(
        TaskType.PAGE, 
        {"trigger_source": "manual", "channel": channel}
    )
    
    async def crawl_func():
        crawler_service = CrawlerService()
        try:
            result = await crawler_service.crawl_and_save_page(channel)
            print(f"频道 {channel} 爬取完成: {result}")
            return result
        finally:
            crawler_service.close()
    
    success = await execute_with_task(task_id, crawl_func)
    
    if success:
        print(f"频道 {channel} 爬虫执行成功，任务ID: {task_id}")
    else:
        print(f"频道 {channel} 爬虫执行失败，任务ID: {task_id}")

async def run_all_page_crawls():
    """运行所有页面爬虫"""
    print("开始执行所有页面爬虫...")
    
    page_service = get_page_service()
    channels = page_service.get_ranking_channels()
    
    for channel_info in channels:
        channel = channel_info['channel']
        if channel == 'jiazi':
            continue
        
        print(f"\n正在爬取频道：{channel} ({channel_info.get('zh_name', '未知')})")
        await run_page_crawl(channel)
        await asyncio.sleep(2)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        channel = sys.argv[1]
        asyncio.run(run_page_crawl(channel))
    else:
        asyncio.run(run_all_page_crawls())
```

#### 创建完整执行脚本 (`run_all_crawlers.py`)
```python
import asyncio
from manual_jiazi_crawl import run_jiazi_crawl
from manual_page_crawl import run_all_page_crawls

async def run_all_crawlers():
    """运行所有爬虫任务"""
    print("=" * 50)
    print("开始执行所有爬虫任务")
    print("=" * 50)
    
    # 1. 运行夹子榜爬虫
    print("\n1. 执行夹子榜爬虫")
    await run_jiazi_crawl()
    
    # 2. 运行所有页面爬虫
    print("\n2. 执行所有页面爬虫")
    await run_all_page_crawls()
    
    print("\n" + "=" * 50)
    print("所有爬虫任务执行完成")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_all_crawlers())
```

### 方法3：命令行执行

```bash
# 进入项目目录
cd backend
poetry shell

# 运行夹子榜爬虫
python manual_jiazi_crawl.py

# 运行特定频道页面爬虫
python manual_page_crawl.py yq

# 运行所有页面爬虫
python manual_page_crawl.py

# 运行所有爬虫
python run_all_crawlers.py
```

## 任务监控

### 查看任务状态

#### API查询
```bash
# 查看所有任务
curl -X GET "http://localhost:8000/api/v1/crawl/tasks"

# 查看特定任务
curl -X GET "http://localhost:8000/api/v1/crawl/tasks/{task_id}"

# 查看调度器状态
curl -X GET "http://localhost:8000/api/v1/crawl/scheduler/status"

# 查看监控状态
curl -X GET "http://localhost:8000/api/v1/crawl/monitor/status"
```

#### 任务状态说明
- **pending**: 任务已创建，等待执行
- **running**: 任务正在执行
- **completed**: 任务执行成功
- **failed**: 任务执行失败

### 监控脚本

创建 `monitor_tasks.py`：
```python
import asyncio
import time
from app.modules.service.task_service import get_task_manager

async def monitor_tasks():
    """监控任务状态"""
    task_manager = get_task_manager()
    
    while True:
        try:
            summary = task_manager.get_task_summary()
            print(f"\n任务状态 [{time.strftime('%Y-%m-%d %H:%M:%S')}]:")
            print(f"  当前任务: {summary['current_count']}")
            print(f"  已完成: {summary['completed_count']}")
            print(f"  失败任务: {summary['failed_count']}")
            
            # 显示当前运行的任务
            if summary['current_tasks']:
                print("  正在运行的任务:")
                for task in summary['current_tasks']:
                    print(f"    - {task['task_id']} ({task['task_type']}) - {task['status']}")
            
            await asyncio.sleep(30)  # 每30秒检查一次
            
        except KeyboardInterrupt:
            print("\n监控已停止")
            break
        except Exception as e:
            print(f"监控错误: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(monitor_tasks())
```

## 故障排除

### 常见错误及解决方案

#### 1. 连接错误
**错误**: `Connection refused` 或 `ConnectionError`
**解决方案**:
- 检查后端服务是否运行: `curl http://localhost:8000/health`
- 检查网络连接
- 验证目标网站是否可访问

#### 2. 任务失败
**错误**: 任务状态为 `failed`
**排查步骤**:
```bash
# 查看失败任务详情
curl -X GET "http://localhost:8000/api/v1/crawl/tasks?status=failed"

# 检查系统日志
tail -f logs/app.log  # 如果有日志文件

# 手动检查缺失任务
curl -X POST "http://localhost:8000/api/v1/crawl/monitor/check"
```

#### 3. 数据库锁定
**错误**: `database is locked`
**解决方案**:
- 重启后端服务
- 检查是否有多个进程同时访问数据库
- 确保SQLite WAL模式已启用

#### 4. 爬虫被阻止
**错误**: HTTP 403 或 429 状态码
**解决方案**:
- 检查请求频率，确保间隔至少1秒
- 验证User-Agent和请求头
- 等待一段时间后重试

### 调试技巧

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 检查爬虫配置
```bash
# 查看URLs配置
cat data/urls.json

# 检查任务文件
cat data/tasks/tasks.json
```

## 最佳实践

### 1. 执行时机
- **夹子榜**: 每小时整点执行，避免高峰期
- **页面爬虫**: 错开执行时间，避免同时进行
- **批量执行**: 建议在低峰期（凌晨1-6点）进行

### 2. 频率控制
- 请求间隔至少1秒
- 批量任务之间间隔2-5秒
- 避免在短时间内重复执行相同任务

### 3. 错误处理
- 监控任务状态，及时处理失败任务
- 保留错误日志，便于问题诊断
- 设置重试机制，避免临时性错误

### 4. 数据管理
- 定期清理历史任务数据
- 备份重要数据库文件
- 监控磁盘使用情况

### 5. 性能优化
- 使用异步操作，提高并发性能
- 合理设置数据库连接池
- 避免在高负载时执行大批量任务

## 常见问题

### Q1: 如何查看某个任务的执行结果？
A: 使用API查询任务详情：
```bash
curl -X GET "http://localhost:8000/api/v1/crawl/tasks/{task_id}"
```

### Q2: 任务长时间处于running状态怎么办？
A: 可能是任务卡死，建议：
1. 检查任务日志
2. 重启后端服务
3. 手动重新触发任务

### Q3: 如何停止正在运行的任务？
A: 目前系统不支持主动停止任务，可以：
1. 重启后端服务（会终止所有运行中的任务）
2. 等待任务自然超时

### Q4: 数据爬取不完整怎么办？
A: 
1. 检查任务执行结果中的`items_crawled`字段
2. 查看是否有网络错误或API变更
3. 手动重新执行相关任务

### Q5: 如何设置定时执行？
A: 系统已内置定时任务：
- 夹子榜：每小时自动执行
- 页面爬虫：每日自动执行
- 可通过调度器API查看和管理定时任务

### Q6: 如何备份爬取的数据？
A: 
```bash
# 备份数据库
cp data/*.db backup/

# 备份任务文件
cp -r data/tasks/ backup/tasks/
```

---

## 联系信息

如有问题或需要技术支持，请查看：
- 项目文档: `docs/`
- API文档: `http://localhost:8000/docs`
- 测试文件: `test_main.http`

**注意**: 使用爬虫时请遵守目标网站的robots.txt和使用条款，合理控制爬取频率，避免对目标服务器造成过大负担。