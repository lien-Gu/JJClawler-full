# JJClawler 全栈项目

## 项目概述
JJClawler 是一个「晋江文学城」数据爬虫与可视化小程序的全栈解决方案。整体分为两部分：

1. **后端 (FastAPI + SQLModel)** —— 负责数据爬取、存储与 RESTful API 服务。
2. **前端 (Uni-app 小程序)** —— 负责在微信小程序端展示榜单、书籍等可视化数据。

> 后端与前端目录均已独立维护完整的 README，本文档聚合关键信息并说明如何在 Cursor 中完成端到端联调。

---

## 目录结构
```
JJClawler-full/
├── backend/   # FastAPI 服务与爬虫实现
└── frontend/  # Uni-app 微信小程序
```

### backend 关键子目录
- `app/`      FastAPI 应用入口及五层架构实现
- `data/`     爬虫配置与示例数据
- `tests/`    Pytest 测试集

### frontend 关键子目录
- `pages/`    小程序页面（首页、榜单、书籍、关注、设置）
- `components/` 公共组件（搜索框、卡片等）
- `utils/`    请求/缓存封装

---

## 环境要求
| 模块 | 语言/运行时 | 依赖管理 |
| ---- | ---------- | -------- |
| 后端 | Python ≥ 3.10 | Poetry (推荐) 或 pip |
| 前端 | Node ≥ 14    | pnpm / npm / yarn 均可 |

> Windows / macOS / Linux 均验证通过。

---

## 快速开始

### 1. 克隆仓库
```bash
$ git clone https://github.com/your-name/JJClawler-full.git
$ cd JJClawler-full
```

### 2. 启动后端
```bash
# 进入后端目录
$ cd backend
# 安装依赖
$ poetry install              # 或 pip install -r requirements.txt
# 运行开发服务器 (默认 8000)
$ poetry run uvicorn app.main:app --reload
```
接口文档：`http://localhost:8000/docs`

### 3. 启动前端
```bash
# 另开终端，进入前端目录
$ cd frontend
# 安装依赖
$ npm i  # 或 pnpm i / yarn
# 本地开发：使用 HBuilderX → 运行到微信开发者工具
```
在微信开发者工具中将后台地址设置为 `http://localhost:8000` 即可联调。

---

## 在 Cursor 中的前后端联调流程
> 假设你已经在 Cursor 的内置终端中打开 **根目录**。

1. **并行启动服务**  
   - 在终端 **面板 1** 运行后端：
     ```bash
     cd backend && poetry run uvicorn app.main:app --reload
     ```
   - 在终端 **面板 2** 运行前端：
     ```bash
     cd frontend && npm run dev   # 或对应的 uni-app 命令
     ```
2. **配置环境变量**  
   - backend 默认监听 `localhost:8000`，如有冲突可修改端口并在 frontend `utils/request.js` 中同步修改 `baseURL`。
3. **断点调试**  
   - Cursor 支持 VSCode 风格断点。后端可在 `app/` 目录下设置断点；前端可在 Chrome DevTools (微信开发者工具) 中调试。
4. **快速热更新**  
   - FastAPI `--reload` 和 uni-app 的热重载可实现秒级刷新，提高开发效率。

---

## 常见问题
| 问题 | 解决方案 |
| ---- | -------- |
| 端口被占用 | 修改 `uvicorn` 启动端口或本地 nginx 代理 |
| 小程序跨域 | 微信开发者工具 → 详情 → 本地设置 → 勾选"不校验合法域名" |
| 数据为空 | 检查 `data/urls.json` 是否配置正确，或手动触发 `POST /api/v1/crawl/jiazi` |

---

## 参考文档
- backend/README.md —— 详细后端架构、数据库设计、部署方案
- frontend/README.md —— 小程序页面结构、组件说明、接口定义

欢迎 Issue / PR 😊
