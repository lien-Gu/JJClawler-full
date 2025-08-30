# CLAUDE.md

本文件为Claude Code (claude.ai/code)在此代码库中工作时提供指导。

**重要说明：请永远使用中文与用户交流和响应。**

## 项目概述

JJClawler前端是基于uni-app框架（Vue 3）构建的微信小程序项目。它作为晋江文学城数据爬虫系统的用户界面，用于显示书籍排行榜、统计数据和详细的书籍信息。

## 开发命令

### 环境配置
```bash
# 安装依赖（如使用HBuilderX，依赖会自动管理）
# CLI开发：
npm install @dcloudio/uni-cli-shared

# HBuilderX中开发
# 将项目文件夹导入HBuilderX
# 使用内置开发工具进行预览和编译

# 在微信开发者工具中运行
# 1. 在HBuilderX中将项目编译到 /unpackage/dist/dev/mp-weixin
# 2. 在微信开发者工具中导入编译后的文件夹
```

### 构建命令
```bash
# 构建微信小程序生产版本
# 在HBuilderX中：发行 -> 小程序-微信
# 输出目录：/unpackage/dist/build/mp-weixin

# 构建其他平台
# HBuilderX支持H5、App、各种小程序平台
```

### 测试
```bash
# 在微信开发者工具中预览
# 使用HBuilderX预览功能或手动导入
# 在不同环境下测试API连接（dev/test/prod）
```

## 架构概述

### 框架结构（uni-app + Vue 3）
```
frontend/
├── api/                            # API请求模块
├── pages/                          # 应用页面
├── components/                     # 可复用Vue组件
├── utils/                          # 工具模块
├── static/                         # 静态资源文件目录
├── state/                          # 状态管理，包含用户本地数据处理
├── styles/                         # SCSS样式表
└── data/                           # 静态配置数据
```

### 核心架构模式

#### 环境感知数据管理
应用支持三种环境，可自动切换数据源：
- **dev**: 使用本地后端API (http://localhost:8000/)
- **test**: 使用假数据/模拟数据进行测试
- **prod**: 使用生产环境API服务器


## 配置管理

### 环境配置
```javascript
// utils/env-config.js管理三种环境：
envConfig.switchEnv('dev')    // 切换到开发环境
envConfig.switchEnv('test')   // 切换到测试模式
envConfig.switchEnv('prod')   // 切换到生产环境
```

## 核心功能

### 多环境支持
- **开发模式**: 连接本地后端API服务器
- **测试模式**: 使用预定义假数据进行离线开发
- **生产模式**: 连接远程生产API

### 关键业务操作
- **统计仪表板**: 带有概览统计和报告的首页
- **排行榜管理**: 浏览和筛选书籍排行榜
- **书籍详情**: 包含排名历史的详细书籍信息
- **用户关注**: 跟踪收藏的书籍和作者
- **搜索**: 跨数据源搜索书籍和排行榜

### 页面导航结构
```
TabBar页面:
├── index（首页）- 带有报告轮播的统计概览
├── ranking（榜单）- 带有搜索和筛选的排行榜列表
├── follow（关注）- 用户关注的书籍
└── settings（设置）- 环境切换和应用配置，用户信息

详情页面:
├── book/detail - 书籍信息和排名趋势
├── ranking/detail - 排行榜详情和书籍列表
└── report/detail - 统计报告可视化
```

## 开发工作流
UI组件设计参考： docs/UI-design.md
后端请求端口参考：data/openapi.json


## 后端集成

### 预期API端点
- `GET /reports` - 统计相关端点
- `GET /rankings`  排行榜相关端点
- `GET /books` - 书籍相关端点

当前已经实现的端点参考 data/openapi.json

### 身份认证
目前未实现身份认证系统。

## 平台特定注意事项

### 微信小程序约束
- 网络请求必须使用uni.request() API
- 文件系统访问限制为uni-app API
- 平台特定UI组件和导航
- 网络访问需要特定权限要求

## 重要提醒

**请在与用户的所有交流中使用中文。这包括代码注释、错误消息、日志输出和任何用户界面文本。**