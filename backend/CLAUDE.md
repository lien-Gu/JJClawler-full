# CLAUDE.md

always response in chinese

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

JJCrawler 是一个专为晋江文学城（Jinjiang Literature City）设计的 Python FastAPI 网络爬虫后端项目。
项目主要爬取小说排行榜数据和小说信息，为前端提供 RESTful API 数据访问服务。
项目采用**接口驱动开发**方法，优先定义 API 接口，然后将功能分解为独立模块。


## 项目技术栈

- 后端核心技术:FastAPI、SQLModel、SQLite、httpx、APScheduler、Uvicorn
- 开发工具链: uv、Python 3.12+、Black、isort、Ruff、pytest、pytest-mock
- 部署运维: Docker、Nginx、systemd

## 项目结构
项目源代码： @app

项目各个子模块路径：
    API目录：@app/api/
    爬虫模块：@app/crawl/
    数据库模块：@app/database/
    数据模型模块：@app/models/
    通用工具模块：@app/utils.py
    配置模块：@app/config.py

测试文件路径：@tests/，按 @tests/test_{module}/ 格式的子文件夹中存放各个模块的单元测试文件

脚本文件：@scripts/

文档目录：@docs/
    API文档：@docs/API.md，记录项目中暴露的 API 相关内容、API 地址、请求体格式
    错误记录文档：@docs/issues.md，开发过程中遇到的错误或问题需要简要记录到此文档中

## 开发流程

1. **代码参考**：检查或生成代码时，优先使用 context7 获取最新的参考代码
2. **思考过程**：根据内容复杂程度，在合适时机调用 mcp sequential-thinking 进行深度思考
3. **代码生成**：代码需要生成在相应功能模块下，并在对应测试文件夹中生成测试文件，确保测试通过
4. **错误记录**：代码发生错误并修复时，需要在 @docs/issues.md 中记录错误时间、原因和解决方法
5. **API文档同步**：修改或生成 @app/api/ 模块代码时，同步更新 @docs/API.md 文件内容


## 开发命令

### 环境设置
```bash
# Install dependencies
uv sync

# Activate virtual environment (optional, can use uv run directly)
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows
```

### 运行应用
```bash
# Start the FastAPI development server
uv run uvicorn main:app --reload --port 8000

# Or if in activated environment
uvicorn main:app --reload --port 8000
```

### 开发工具
```bash
# Add new dependencies
uv add package_name

# Add development dependencies
uv add --dev package_name

# Run tests (when implemented)
uv run pytest

# Format code (when configured)
uv run black .
uv run isort .
uv run ruff check . --fix
```

## 代码风格规范

### PEP 8 规范
- **命名规范**
  - 类名：使用 PascalCase（如 `BookService`）
  - 函数和变量名：使用 snake_case（如 `get_book_info`）
  - 常量：使用 UPPER_SNAKE_CASE（如 `MAX_RETRY_COUNT`）
  - 私有变量：以单下划线开头（如 `_private_var`）
  - 模块名：使用小写字母和下划线（如 `book_service.py`）

- **代码布局**
  - 行长度：不超过 88 字符（Black 默认设置）
  - 缩进：使用 4 个空格，不使用制表符
  - 空行：顶级函数和类定义前后用两个空行分隔
  - 导入：按标准库、第三方库、本地库顺序分组

- **注释和文档字符串**
  - 使用中文注释说明复杂逻辑
  - 函数使用 Google 风格的文档字符串
  - 类和模块需要有简洁的说明文档

### 代码质量原则

- **简单优先**：选择最简单可行的实现方案
- **代码复用**：如有相同或相似代码，必须抽取成公共函数
- **函数单一职责**：每个函数只做一件事情，功能清晰明确
- **避免重复代码**：遵循 DRY (Don't Repeat Yourself) 原则
- **易读性优先**：代码应该易于理解和维护
- **类型安全**：使用 SQLModel 进行数据库模型定义，使用 Pydantic 进行 API 模型验证

### 代码重构指导

1. **相似代码识别**
   - 相同的业务逻辑必须抽取为公共函数
   - 相似的数据处理逻辑抽取为工具函数
   - 重复的数据库操作抽取为 DAO 层方法

2. **函数抽取原则**
   - 超过 20 行的函数考虑拆分
   - 有重复逻辑的代码立即抽取
   - 复杂条件判断抽取为独立函数

3. **模块化设计**
   - 相关功能归类到同一模块
   - 保持模块间低耦合
   - 使用明确的接口定义

## 开发规范

- **接口优先**：总是先定义 API 接口，再实现后端逻辑
- **扁平架构**：最小化层次结构，模块间直接通信
- **混合存储**：复杂数据使用数据库，简单状态管理使用 JSON
- **任务隔离**：每个子任务有清晰的输入输出，避免跨模块耦合
- **渐进替换**：分阶段将 Mock 实现替换为真实功能
- **错误处理**：每个模块都要实现完善的错误处理和日志记录
- **限流控制**：尊重目标站点的访问限制（1秒间隔）
- **数据验证**：使用 Pydantic 模型进行请求响应验证
- **异步操作**：I/O 操作使用 async/await
- **测试策略**：优先实现 Mock API 以支持前端开发