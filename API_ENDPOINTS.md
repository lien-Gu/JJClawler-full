# JJClawler 前后端API接口对照表

## 📋 概述

本文档整理了前端需要调用的所有API接口以及后端提供的API接口，标明了实现状态和缺失接口。

## 🔍 前端API调用需求分析

### 前端调用位置说明

| 调用位置 | 文件路径 | 功能说明 |
|----------|----------|----------|
| data-manager.js | `/frontend/utils/data-manager.js` | 统一数据管理层，所有API调用入口 |
| request.js | `/frontend/utils/request.js` | HTTP请求基础工具，处理请求配置 |
| 页面组件 | `/frontend/pages/**/*.vue` | 页面级组件，通过data-manager调用API |
| api-config.vue | `/frontend/pages/settings/api-config.vue` | API配置页面，直接调用健康检查接口 |

### 后端API处理位置说明

| API模块 | 文件路径 | 功能说明 |
|---------|----------|----------|
| main.py | `/backend/app/main.py` | 主应用入口，注册路由和基础接口 |
| books.py | `/backend/app/api/books.py` | 书籍相关API接口 |
| rankings.py | `/backend/app/api/rankings.py` | 榜单相关API接口 |
| crawl.py | `/backend/app/api/crawl.py` | 爬虫管理API接口 |
| stats.py | `/backend/app/api/stats.py` | 统计数据API接口 |
| pages.py | `/backend/app/api/pages.py` | 页面配置API接口 |

## 📊 API接口对照表

### ✅ 已实现的接口

| 前端需求API | 后端提供API | 状态 | 调用位置 | 处理位置 |
|-------------|-------------|------|----------|----------|
| `GET /stats/overview` | `GET /api/v1/stats/overview` | ✅ 已实现 | data-manager.js:102 | stats.py:16 |
| `GET /rankings` | `GET /api/v1/rankings` | ✅ 已实现 | data-manager.js:109 | rankings.py:30 |
| `GET /rankings/hot` | `GET /api/v1/rankings/hot` | ✅ 已实现 | data-manager.js:116 | rankings.py:89 |
| `GET /rankings/{rankingId}/books` | `GET /api/v1/rankings/{ranking_id}/books` | ✅ 已实现 | data-manager.js:130 | rankings.py:212 |
| `GET /books/{bookId}` | `GET /api/v1/books/{book_id}` | ✅ 已实现 | data-manager.js:142 | books.py:21 |
| `GET /books/{bookId}/rankings` | `GET /api/v1/books/{book_id}/rankings` | ✅ 已实现 | data-manager.js:155 | books.py:42 |
| `GET /books/{bookId}/trends` | `GET /api/v1/books/{book_id}/trends` | ✅ 已实现 | data-manager.js:168 | books.py:72 |
| `GET /pages` | `GET /api/v1/pages` | ✅ 已实现 | data-manager.js:176 | pages.py:14 |
| `GET /books` | `GET /api/v1/books` | ✅ 已实现 | data-manager.js:202 | books.py:105 |
| `GET /rankings/search` | `GET /api/v1/rankings/search` | ✅ 已实现 | data-manager.js:218 | rankings.py:161 |
| `POST /crawl/{target}` | `POST /api/v1/crawl/jiazi` & `POST /api/v1/crawl/page/{channel}` | ✅ 已实现 | data-manager.js:241 | crawl.py:36,67 |
| `GET /crawl/tasks` | `GET /api/v1/crawl/tasks` | ✅ 已实现 | data-manager.js:248 | crawl.py:109 |
| `GET /crawl/scheduler/status` | `GET /api/v1/crawl/scheduler/status` | ✅ 已实现 | data-manager.js:255 | crawl.py:248 |
| `GET /crawl/scheduler/jobs` | `GET /api/v1/crawl/scheduler/jobs` | ✅ 已实现 | data-manager.js:262 | crawl.py:270 |
| `GET /health` | `GET /health` | ✅ 已实现 | api-config.vue:213 | main.py:125 |

### ✅ 新实现的接口

| 前端需求API | 后端提供API | 状态 | 调用位置 | 处理位置 |
|-------------|-------------|------|----------|----------|
| `GET /pages/statistics` | `GET /api/v1/pages/statistics` | ✅ 已实现 | data-manager.js:183 | pages.py:109 |
| `GET /user/stats` | `GET /api/v1/user/stats` | ✅ 已实现 | data-manager.js:226 | users.py:15 |
| `GET /user/follows` | `GET /api/v1/user/follows` | ✅ 已实现 | data-manager.js:233 | users.py:51 |

### 📝 路径差异说明

1. **API版本前缀**: 
   - 前端期望: 直接路径 (如 `/stats/overview`)
   - 后端提供: 带版本前缀 (如 `/api/v1/stats/overview`)
   - **解决方案**: 前端通过配置基础URL自动添加 `/api/v1` 前缀

2. **参数命名**:
   - 前端使用: `rankingId`, `bookId`
   - 后端使用: `ranking_id`, `book_id`
   - **解决方案**: 后端API已按RESTful规范使用下划线命名

3. **爬虫接口差异**:
   - 前端期望: `POST /crawl/{target}`
   - 后端提供: `POST /crawl/jiazi` 和 `POST /crawl/page/{channel}`
   - **解决方案**: 前端根据target参数调用不同接口

## ✅ 已完成实现的接口

### 1. 页面统计接口
```
GET /api/v1/pages/statistics
响应: 页面访问统计数据 (包含fake标识)
状态: ✅ 已实现
```

### 2. 用户统计接口
```
GET /api/v1/user/stats
响应: 用户相关统计信息 (包含fake标识)
状态: ✅ 已实现
```

### 3. 用户关注列表接口
```
GET /api/v1/user/follows
响应: 用户关注的榜单/书籍列表 (包含fake标识)
状态: ✅ 已实现
```

### 4. 用户关注管理接口
```
POST /api/v1/user/follows - 添加关注 (包含fake标识)
DELETE /api/v1/user/follows/{follow_id} - 取消关注 (包含fake标识)
GET /api/v1/user/profile - 获取用户档案 (包含fake标识)
状态: ✅ 已实现
```

## 💾 Fake数据标识规范

对于未实现的功能，后端需要返回包含fake标识的预制数据：

```json
{
  "data": { /* 实际数据 */ },
  "meta": {
    "fake": true,
    "message": "This is fake data for development",
    "timestamp": "2024-06-24T23:50:00Z"
  }
}
```

## 🔧 配置说明

### 前端API配置 (data/config.json)
```json
{
  "api": {
    "baseURL": "http://localhost:8000/api/v1",
    "timeout": 10000,
    "environment": "dev"
  }
}
```

### 前端设计配置 (styles/design-tokens.scss)
```scss
// Brand Colors
$brand-primary: #4A4459;
$surface-dark: #E8DEF8;
$surface-white: #F3EDF7;
$surface-default: #FFFFFF;

// Typography
$font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
$heading1-font-size-rpx: 48rpx; // 24px
$body-font-size-rpx: 28rpx; // 14px

// Spacing
$spacing-xs: 8rpx;
$spacing-sm: 16rpx;
$spacing-md: 24rpx;
$spacing-lg: 32rpx;
```

### 环境切换
- **dev**: 使用真实后端API (`http://localhost:8000/api/v1`)
- **test**: 使用假数据 (fake_data.json)
- **prod**: 使用生产API (`https://api.jjclawler.com/api/v1`)

### 组件引用配置
```javascript
// 统一引用基础组件
import BaseCard from '@/components/BaseCard.vue'
import BaseButton from '@/components/BaseButton.vue'

// 统一引用Mixins
import formatterMixin from '@/mixins/formatter.js'
import navigationMixin from '@/mixins/navigation.js'
```

## 📈 接口实现状态

### ✅ 已完成实现 (2024-06-25)
1. **高优先级** (影响核心功能):
   - ✅ `GET /pages/statistics` - 页面统计展示 
   - ✅ `GET /user/follows` - 关注功能

2. **中优先级** (完善用户体验):
   - ✅ `GET /user/stats` - 用户个人统计

3. **扩展功能**:
   - ✅ `POST /user/follows` - 添加关注
   - ✅ `DELETE /user/follows/{follow_id}` - 取消关注
   - ✅ `GET /user/profile` - 用户档案信息

## 🚀 前端架构优化状态

### ✅ 组件化重构完成 (2024-06-25)
1. **基础组件库**:
   - ✅ BaseCard - 统一卡片容器
   - ✅ BaseButton - 标准化按钮
   - ✅ TabBar - 底部导航
   - ✅ ReportCarousel - 报告展示
   - ✅ SearchBar - 搜索组件
   - ✅ CategoryTabs - 分类标签
   - ✅ RankingListItem - 榜单项

2. **代码复用优化**:
   - ✅ Formatter Mixin - 统一格式化逻辑
   - ✅ Navigation Mixin - 统一导航逻辑
   - ✅ Design Tokens - Material Design系统
   - ✅ Utility Functions - 纯函数工具

3. **重构组件**:
   - ✅ RankingCard - 使用新架构
   - ✅ BookCard - 使用新架构
   - ✅ StatsCard - 使用新架构
   - ✅ BookList - 使用新架构

## 🧪 测试说明

### API接口测试
1. **健康检查**: `GET /health` - 用于前端测试API连接
2. **统计接口**: `GET /stats/overview` - 首页数据展示
3. **榜单接口**: `GET /rankings/hot` - 热门榜单展示
4. **书籍接口**: `GET /books/{book_id}` - 书籍详情展示

### 前端组件测试
1. **基础组件**: 测试BaseCard、BaseButton的各种变体和状态
2. **组合组件**: 测试使用基础组件的复合组件功能
3. **Mixins功能**: 验证formatter和navigation混入的正确性
4. **设计一致性**: 确保所有组件遵循Material Design规范
5. **响应式**: 测试组件在不同屏幕尺寸下的表现

## 🎨 前端UI组件重构 (2024-06-25)

### 新增组件架构

| 组件类型 | 组件名称 | 文件路径 | 功能说明 |
|----------|----------|----------|----------|
| **基础组件** | BaseCard | `/frontend/components/BaseCard.vue` | 可复用卡片容器，支持多种变体和插槽 |
| **基础组件** | BaseButton | `/frontend/components/BaseButton.vue` | 标准化按钮组件，支持多种类型和状态 |
| **导航组件** | TabBar | `/frontend/components/TabBar.vue` | 底部导航栏，基于Figma设计 |
| **展示组件** | ReportCarousel | `/frontend/components/ReportCarousel.vue` | 报告展示卡片 |
| **搜索组件** | SearchBar | `/frontend/components/SearchBar.vue` | 统一搜索输入框 |
| **分类组件** | CategoryTabs | `/frontend/components/CategoryTabs.vue` | 水平滚动分类标签 |
| **列表组件** | RankingListItem | `/frontend/components/RankingListItem.vue` | 榜单列表项 |

### 重构后的组件

| 原组件名称 | 重构状态 | 主要改进 |
|------------|----------|----------|
| RankingCard.vue | ✅ 已重构 | 使用BaseCard和BaseButton，集成formatter和navigation mixins |
| BookCard.vue | ✅ 已重构 | 使用BaseCard和BaseButton，统一样式和交互 |
| StatsCard.vue | ✅ 已重构 | 使用BaseCard，支持多种主题色彩 |
| BookList.vue | ✅ 已重构 | 使用design tokens，集成formatter mixins |

### Mixins 系统

| Mixin名称 | 文件路径 | 功能说明 |
|-----------|----------|----------|
| formatter.js | `/frontend/mixins/formatter.js` | 统一格式化方法（数字、时间、日期等） |
| navigation.js | `/frontend/mixins/navigation.js` | 统一导航方法（页面跳转、返回等） |

### 设计系统

| 资源类型 | 文件路径 | 功能说明 |
|----------|----------|----------|
| Design Tokens | `/frontend/styles/design-tokens.scss` | Material Design色彩系统、字体、间距等 |
| Utility Functions | `/frontend/utils/formatters.js` | 纯函数格式化工具 |

### Figma集成

- **设计源**: 基于Figma设计规范创建Material Design色彩系统
- **组件对应**: 每个UI组件都对应Figma中的设计元素
- **一致性**: 确保设计和开发的一致性

## 🔄 更新日志

- **2024-06-24**: 初始版本，分析前后端API接口差异，识别3个缺失接口
- **2024-06-25 (上午)**: ✅ 完成所有缺失接口实现：
  - 实现 `/pages/statistics` 接口，返回页面统计信息
  - 实现 `/user/stats` 接口，返回用户统计数据
  - 实现 `/user/follows` 接口，返回用户关注列表
  - 扩展实现用户关注管理功能 (POST/DELETE)
  - 实现用户档案信息接口
  - 所有新接口均包含fake标识，便于前端识别开发数据
  - 后端服务器测试通过，所有API端点响应正常
- **2024-06-25 (下午)**: 🎨 完成前端UI重构：
  - 基于Figma设计创建新UI组件系统
  - 实现BaseCard、BaseButton等可复用基础组件
  - 创建formatter和navigation mixins消除代码重复
  - 重构RankingCard、BookCard、StatsCard、BookList组件
  - 建立Material Design设计令牌系统
  - 提升代码可维护性和组件复用率
  - 统一组件接口规范（props、emits、slots）