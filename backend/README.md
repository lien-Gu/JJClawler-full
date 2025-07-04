# 晋江文学城爬虫后端项目

## 1. 项目概述

### 1.1 项目简介
JJCrawler 是一个轻量级的晋江文学城数据爬虫后端服务，采用现代化Python技术栈构建。项目专注于榜单数据采集和API服务，为前端应用提供稳定的数据接口。

### 1.2 核心特性
- **MVP架构设计**：每个模块专注于功能实现，职责明确
- **高效数据处理**：基于SQLite + APScheduler的轻量级解决方案
- **自动化爬取**：支持定时任务和手动触发
- **类型安全**：全面使用FastAPI + SQLAlchemy实现类型检查
- **模块化设计**：功能模块独立，易于维护和扩展

### 1.3 技术栈
- **后端框架**：FastAPI
- **数据库**：SQLite + SQLAlchemy ORM
- **任务调度**：APScheduler
- **HTTP客户端**：httpx
- **依赖管理**：Poetry

## 2. 快速开始

### 2.1 环境要求

**系统要求：**
- Python 3.12+
- Poetry (推荐) 或 pip
- Git
- 操作系统：macOS / Linux / Windows

**硬件要求：**
- CPU: 2核心+
- 内存: 4GB+
- 存储: 1GB+ 可用空间

### 2.2 安装部署

#### 2.2.1 克隆项目

```bash
# 克隆代码库
git clone https://github.com/lien-Gu/JJClawler-full.git
cd JJClawler-full/backend
```

#### 2.2.2 环境配置

**方式一：使用 Poetry（推荐）**

```bash
# 安装 Poetry (如果未安装)
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install

# 激活虚拟环境
poetry shell
```

**方式二：使用 pip**

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt  # 需要先生成requirements.txt
```

**生成requirements.txt（如需要）：**

```bash
# 使用Poetry生成
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

#### 2.2.3 环境变量配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（可选）
vim .env
```

默认配置已经可以直接运行，无需修改。

### 2.3 运行项目

#### 2.3.1 启动开发服务器

```bash
# 方式一：使用Poetry
poetry run uvicorn app.main:app --reload --port 8000

# 关闭
pkill -f uvicorn

# 方式二：如果已在虚拟环境中
uvicorn app.main:app --reload --port 8000

# 方式三：使用Python模块
python -m uvicorn app.main:app --reload --port 8000
```

#### 2.3.2 验证部署

**健康检查：**
```bash
curl http://localhost:8000/health
# 预期响应: {"status": "healthy", "timestamp": "..."}
```

**API文档：**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**测试API：**
```bash
# 触发爬取所有页面
curl -X POST http://localhost:8000/api/v1/crawl/all

# 触发爬取多个页面
curl -X POST http://localhost:8000/api/v1/crawl/pages \
  -H "Content-Type: application/json" \
  -d '{"page_ids": ["jiazi", "nvpin_wcxl"]}'

# 查看任务状态
curl http://localhost:8000/api/v1/crawl/tasks

# 查看爬虫系统状态
curl http://localhost:8000/api/v1/crawl/status

# 获取数据分析报告（未来功能）
curl http://localhost:8000/api/v1/reports/latest
```

### 2.4 开发环境

#### 2.4.1 代码格式化

```bash
# 格式化代码
poetry run black .
poetry run isort .
poetry run ruff check . --fix
```

#### 2.4.2 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定测试
poetry run pytest tests/test_api.py

# 生成覆盖率报告
poetry run pytest --cov=app tests/
```

### 2.5 生产部署

#### 2.5.1 Docker部署

```bash
# 构建镜像
docker build -t jjcrawler:latest .

# 运行容器
docker run -d \
  --name jjcrawler \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  jjcrawler:latest
```

#### 2.5.2 系统服务部署

**创建systemd服务文件：**

```bash
sudo vim /etc/systemd/system/jjcrawler.service
```

```ini
[Unit]
Description=JJ Crawler Backend Service
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/path/to/JJClawer3
Environment=PATH=/path/to/JJClawer3/venv/bin
ExecStart=/path/to/JJClawer3/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**启动服务：**

```bash
sudo systemctl daemon-reload
sudo systemctl enable jjcrawler
sudo systemctl start jjcrawler
sudo systemctl status jjcrawler
```

#### 2.5.3 Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2.6 常见问题

**Q: 启动时提示端口被占用？**
```bash
# 检查端口占用
lsof -i :8000
# 使用其他端口
uvicorn app.main:app --reload --port 8001
```

**Q: 依赖安装失败？**
```bash
# 清理缓存重新安装
poetry cache clear pypi --all
poetry install

# 或升级Poetry版本
poetry self update
```

**Q: 数据库文件权限问题？**
```bash
# 确保data目录有写权限
chmod 755 data/
chmod 644 data/*.db
```

**Q: 如何查看日志？**
```bash
# 开发环境直接查看控制台输出
# 生产环境查看systemd日志
sudo journalctl -u jjcrawler -f
```

## 3. 需求分析

### 3.1 功能需求

#### 3.1.1 数据爬取需求
| 功能模块 | 需求描述 | 优先级 |
|---------|---------|--------|
| 夹子榜单爬取 | 每小时更新一次夹子榜单数据 | P0 |
| 分类榜单爬取 | 按配置频率爬取各分类榜单（言情、纯爱、衍生等） | P0 |
| 小说详情爬取 | 爬取榜单中小说的详细信息 | P0 |
| 增量更新 | 仅爬取新增或变化的数据 | P2 |

#### 3.1.2 API接口需求
| 接口类型 | 功能描述 | 优先级 |
|---------|---------|--------|
| 榜单查询 | 查询历史榜单数据、最新榜单 | P0 |
| 小说查询 | 查询小说列表、小说详情 | P0 |
| 任务管理 | 查看爬取任务状态、手动触发爬取 | P1 |
| 统计信息 | 系统运行统计、数据统计 | P1 |

### 3.2 非功能需求

| 需求类型 | 具体要求 | 备注 |
|---------|---------|------|
| 性能要求 | 支持每小时处理1000+请求 | 2C4G服务器限制 |
| 可靠性 | 系统可用性>95%，支持断点续爬 | - |
| 安全性 | 遵守robots协议，控制请求频率 | 避免被封禁 |
| 可维护性 | 代码简洁易读，模块化设计 | 便于后续扩展 |
| 部署要求 | 支持Docker容器化部署 | Linux环境 |

### 3.3 数据需求

#### 3.3.1 爬取数据结构

参考data/example中的文件

## 4. 系统架构设计

### 4.1 技术选型

| 技术栈 | 选择 | 选择理由 |
|--------|------|----------|
| 编程语言 | Python 3.12+ | 爬虫生态成熟，开发效率高 |
| Web框架 | FastAPI | 高性能，自动生成API文档，类型安全 |
| HTTP库 | httpx | 异步支持，性能更好 |
| 数据库 | SQLite | 轻量级，无需额外部署，适合中小型项目 |
| ORM | SQLAlchemy | 成熟稳定，生态丰富，类型安全 |
| 任务调度 | APScheduler | 轻量级Python调度器，支持异步任务 |
| 时区支持 | pytz | 标准时区库，支持UTC和本地时区转换 |
| 依赖管理 | Poetry | 现代Python包管理工具 |

### 4.2 MVP架构设计

项目采用MVP（最小可行产品）原则，按功能模块组织，每个模块专注于实现其核心功能：

```
backend/
├── app/
│   ├── main.py                   # FastAPI应用入口
│   ├── config.py                 # 配置管理
│   ├── api/                      # API接口模块
│   │   ├── __init__.py
│   │   ├── books.py              # 书籍相关接口
│   │   ├── rankings.py           # 榜单相关接口
│   │   ├── crawl.py              # 爬虫管理接口（手动触发、任务监控）
│   │   └── reports.py            # 数据分析接口（未来功能）
│   ├── database/                 # 数据库模块
│   │   ├── __init__.py
│   │   ├── models/               # 数据模型定义
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # 基础模型
│   │   │   ├── book.py           # 书籍模型
│   │   │   └── ranking.py        # 榜单模型
│   │   ├── dao/                  # 数据访问层
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # 基础DAO
│   │   │   ├── book_dao.py       # 书籍数据访问
│   │   │   └── ranking_dao.py    # 榜单数据访问
│   │   ├── service/              # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── book_service.py   # 书籍业务逻辑
│   │   │   └── ranking_service.py # 榜单业务逻辑
│   │   └── connection.py         # 数据库连接管理
│   ├── crawler/                  # 爬虫模块
│   │   ├── __init__.py
│   │   ├── base.py               # 爬虫基础类（通用爬取逻辑）
│   │   ├── crawler.py            # 统一爬虫实现
│   │   └── parser.py              # 数据解析器目录
│   ├── scheduler/                # 调度模块
│   │   ├── __init__.py
│   │   ├── task_scheduler.py     # 任务调度器
│   │   └── jobs.py               # 定时任务定义
│   └── utils/                    # 工具模块
│       ├── __init__.py
│       ├── http_client.py        # HTTP客户端工具
│       ├── file_utils.py         # 文件操作工具
│       ├── time_utils.py         # 时间处理工具
│       ├── log_utils.py          # 日志工具
│       └── data_utils.py         # 数据处理工具
├── data/                         # 数据存储目录
│   ├── example/                  # 示例数据
│   ├── tasks/                    # 任务状态文件
│   └── logs/                     # 日志文件
├── tests/                        # 测试用例
│   ├── test_api/                 # API测试
│   ├── test_database/            # 数据库测试
│   ├── test_crawler/             # 爬虫测试
│   ├── test_scheduler/           # 调度器测试
│   └── test_reports/             # 报告生成测试（未来功能）
└── docs/                         # 文档说明
    ├── API.md                    # API文档
    └── DEPLOYMENT.md             # 部署文档
```

### 4.3 模块功能说明

#### 4.3.1 API模块 (app/api/)
**功能职责：**
- 定义HTTP接口端点
- 处理请求验证和响应格式化
- 调用业务逻辑服务
- 提供API文档支持

**核心文件：**
- `books.py`：书籍相关接口（详情、搜索、趋势）
- `rankings.py`：榜单相关接口（榜单查询、历史数据）
- `crawl.py`：爬虫管理接口（手动触发所有/单个/多个页面爬取、任务状态监控、系统状态查询）
- `reports.py`：数据分析接口（定时生成数据分析报告，未来功能）

#### 4.3.2 数据库模块 (app/database/)
**功能职责：**
- 数据模型定义和ORM映射
- 数据访问层实现
- 业务逻辑层封装
- 数据库连接管理

**核心组件：**
- `models/`：使用SQLAlchemy定义数据模型
- `dao/`：数据访问对象，封装CRUD操作
- `service/`：业务逻辑服务，组合DAO操作
- `connection.py`：数据库连接池管理

#### 4.3.3 爬虫模块 (app/crawler/)
**功能职责：**
- 实现通用网页数据爬取逻辑
- 支持多种页面类型的数据解析
- 数据清洗和标准化
- 错误处理和重试机制

**架构设计：**
- **通用爬取逻辑**：夹子榜和其他页面使用相同的爬取逻辑
- **差异化解析**：不同页面类型使用不同的解析器处理数据
- **模块化设计**：爬取逻辑与解析逻辑分离，易于扩展

**核心文件：**
- `base.py`：爬虫基础类和通用爬取逻辑
- `crawler.py`：统一爬虫实现（处理所有页面类型）
- `parsers/jiazi_parser.py`：夹子榜专用解析器
- `parsers/page_parser.py`：分类页面解析器

#### 4.3.4 调度模块 (app/scheduler/)
**功能职责：**
- 定时任务管理
- 爬取任务调度
- 数据分析报告生成调度
- 任务状态监控
- 异常处理和重试

**核心文件：**
- `task_scheduler.py`：任务调度器主类
- `jobs.py`：定时任务定义和配置（爬虫任务、报告生成任务）

#### 4.3.5 工具模块 (app/utils/)
**功能职责：**
- 提供通用工具函数
- 基础设施支持
- 横切关注点处理
- 代码复用

**核心文件：**
- `http_client.py`：HTTP客户端工具
- `file_utils.py`：文件操作工具
- `time_utils.py`：时间处理工具
- `log_utils.py`：日志工具
- `data_utils.py`：数据处理工具

### 4.4 数据库设计

数据库采用SQLAlchemy ORM，基于SQLite，设计了四个核心表：

**数据库表：**
- `books`：书籍基础信息表
- `book_snapshots`：书籍动态统计快照表
- `rankings`：榜单配置表
- `ranking_snapshots`：榜单排名快照表

**设计特点：**
- **数据分离**：静态信息与动态统计分表存储
- **时间序列**：支持历史数据查询和趋势分析
- **索引优化**：基于查询模式设计复合索引
- **轻量级**：SQLite适合中小型项目需求

### 4.5 MVP架构优势

**🎯 专注功能实现**
- 每个模块职责单一，专注于核心功能
- 减少层级复杂性，提高开发效率
- 便于快速迭代和功能验证

**🔧 易于维护**
- 模块边界清晰，修改影响范围可控
- 代码组织简洁，新人容易上手
- 功能模块独立，支持并行开发

**🚀 快速扩展**
- 新增功能只需添加相应模块
- 模块间依赖关系简单明确
- 支持渐进式架构演进

**💡 技术选型务实**
- SQLAlchemy成熟稳定，生态丰富
- 避免过度设计，满足当前需求
- 为未来升级预留空间

## 5. 详细设计

### 5.1 API接口设计

本项目提供完整的RESTful API接口，支持书籍查询、榜单管理、爬虫控制等功能。

**核心API分类：**
- 📊 **榜单数据接口**：`GET /api/v1/rankings/*` - 榜单查询和历史数据
- 📚 **书籍信息接口**：`GET /api/v1/books/*` - 书籍详情、趋势、排名历史
- 🕷️ **爬虫管理接口**：`POST /api/v1/crawl/*` - 手动触发爬取（所有/单个/多个页面）、任务状态监控、系统状态查询
- 📈 **数据分析接口**：`GET /api/v1/reports/*` - 数据分析报告（未来功能）
- 🔧 **系统状态接口**：`GET /health` - 健康检查

### 5.2 数据模型设计

使用SQLAlchemy定义数据模型，支持类型安全和ORM映射：

**核心模型：**
- `Book`：书籍基础信息模型
- `BookSnapshot`：书籍统计快照模型
- `Ranking`：榜单配置模型
- `RankingSnapshot`：榜单排名快照模型

### 5.3 爬虫策略设计

采用基于APScheduler的自动调度策略：

**调度策略：**
- 夹子榜：每小时更新一次
- 分类榜单：根据配置频率更新
- 数据分析报告：定期生成数据分析报告（未来功能）
- 智能重试：失败任务自动重试
- 并发控制：限制同时运行的爬虫数量

## 6. 监控方案

项目提供完整的监控体系：

**监控指标：**
- 系统健康状态检查
- 爬虫任务执行状态
- 数据库性能指标
- API响应时间统计

**日志管理：**
- 结构化日志输出
- 错误日志分级记录
- 定期日志轮转清理

## 7. 测试方案

### 7.1 测试策略

项目采用分层测试策略：

**测试类型：**
- **单元测试**：各模块功能测试
- **集成测试**：模块间交互测试
- **API测试**：接口功能和性能测试
- **端到端测试**：完整业务流程测试

**测试覆盖：**
- 核心业务逻辑100%覆盖
- API接口全面测试
- 数据库操作测试
- 爬虫功能测试
- 报告生成测试（未来功能）

## 8. 风险评估

| 风险类型 | 风险描述 | 应对措施 |
|---------|---------|----------|
| 技术风险 | 网站反爬虫机制 | 控制爬取频率，模拟正常用户行为 |
| 技术风险 | 数据结构变更 | 灵活的解析器设计，快速适配 |
| 性能风险 | 数据量增长 | 数据库优化，定期数据清理 |
| 运维风险 | 服务稳定性 | 健康检查，自动重启机制 |
| 合规风险 | 数据使用规范 | 遵守robots协议，仅用于学习研究 |

## 9. 后续优化建议

### 9.1 短期优化（1个月内）
- 实现数据增量更新
- 优化数据库查询性能
- 完善错误处理机制
- 增强监控告警功能

### 9.2 中期优化（3个月内）
- 引入缓存层提升性能
- 实现分布式爬虫架构
- 添加数据分析功能
- 开发管理后台界面

### 9.3 长期规划
- 支持多数据源扩展
- 机器学习预测分析
- 实时数据推送服务
- 用户个性化推荐

## 10. 附录

### 10.1 参考资料
- FastAPI官方文档: https://fastapi.tiangolo.com
- SQLAlchemy文档: https://www.sqlalchemy.org
- APScheduler文档: https://apscheduler.readthedocs.io

### 10.2 相关规范
- RESTful API设计规范
- Python PEP8编码规范
- Git提交信息规范

### 10.3 联系方式
- 项目负责人：[Lien Gu]
- 技术支持：[guliyu0216@163.com]
- 项目仓库：[https://github.com/lien-Gu/JJClawer3.git]