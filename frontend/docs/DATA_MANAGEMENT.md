# 前端数据管理系统说明

## 概述

前端项目实现了一个统一的数据管理系统，支持三种环境下的不同数据获取方式：

- **dev环境**: 使用本地后端API获取真实数据
- **test环境**: 使用预制假数据，便于前端独立开发调试
- **prod环境**: 使用生产服务器API获取真实数据

## 核心文件

### 1. 配置文件
- `data/config.json`: 环境配置文件
- `data/fake_data.json`: 预制假数据文件

### 2. 工具类
- `utils/config.js`: 配置管理器
- `utils/data-manager.js`: 数据管理器
- `utils/request.js`: 网络请求工具

### 3. 页面设置
- `pages/settings/api-config.vue`: API配置页面

## 使用方法

### 在页面中使用数据管理器

```javascript
// 导入数据管理器
import dataManager from '@/utils/data-manager.js'

export default {
  async onLoad() {
    try {
      // 获取统计数据
      const stats = await dataManager.getOverviewStats()
      
      // 获取榜单列表
      const rankings = await dataManager.getRankingsList()
      
      // 获取热门榜单
      const hotRankings = await dataManager.getHotRankings({ limit: 6 })
      
      // 数据将根据当前环境自动选择数据源
    } catch (error) {
      console.error('数据加载失败:', error)
    }
  }
}
```

### 环境切换

用户可以通过以下方式切换环境：

1. **设置页面**: 设置 → API配置 → 选择环境
2. **编程方式**: 
   ```javascript
   import configManager from '@/utils/config.js'
   
   // 切换到测试环境（使用假数据）
   configManager.setEnvironment('test')
   
   // 切换到开发环境（使用本地API）
   configManager.setEnvironment('dev')
   
   // 切换到生产环境（使用服务器API）
   configManager.setEnvironment('prod')
   ```

## 环境说明

### dev环境
- **数据源**: 本地后端API (http://localhost:8000/api/v1)
- **用途**: 本地开发时连接真实后端服务
- **要求**: 需要启动后端服务

### test环境
- **数据源**: 预制假数据 (`data/fake_data.json`)
- **用途**: 前端独立开发调试，无需后端服务
- **特点**: 
  - 数据结构完整，覆盖所有业务场景
  - 响应速度快，无网络依赖
  - 连接测试总是显示成功

### prod环境
- **数据源**: 生产服务器API (https://api.jjclawler.com/api/v1)
- **用途**: 正式环境部署
- **要求**: 需要有可访问的生产服务器

## 假数据结构

`fake_data.json` 包含以下数据类型：

```json
{
  "stats": {
    "overview": { /* 首页统计数据 */ }
  },
  "rankings": {
    "list": [ /* 榜单列表 */ ],
    "hot": [ /* 热门榜单 */ ]
  },
  "books": {
    "jiazi_list": [ /* 夹子榜书籍 */ ],
    "detail": { /* 书籍详情 */ }
  },
  "pages": {
    "sites": [ /* 分站配置 */ ],
    "statistics": { /* 页面统计 */ }
  },
  "user": {
    "info": { /* 用户信息 */ },
    "stats": { /* 用户统计 */ }
  },
  "crawl": {
    "tasks": [ /* 爬虫任务 */ ],
    "status": { /* 调度器状态 */ }
  }
}
```

## API方法列表

数据管理器提供以下API方法：

### 统计数据
- `getOverviewStats()`: 获取首页统计概览
- `getPageStatistics()`: 获取页面统计

### 榜单数据
- `getRankingsList(params)`: 获取榜单列表
- `getHotRankings(params)`: 获取热门榜单
- `getRankingBooks(rankingId, params)`: 获取榜单书籍
- `searchRankings(params)`: 搜索榜单

### 书籍数据
- `getBookDetail(bookId)`: 获取书籍详情
- `getBookRankings(bookId)`: 获取书籍排名历史
- `getBookTrends(bookId)`: 获取书籍趋势数据
- `searchBooks(params)`: 搜索书籍

### 用户数据
- `getUserStats()`: 获取用户统计
- `getUserFollows()`: 获取用户关注列表

### 爬虫管理
- `triggerCrawl(target)`: 触发爬虫任务
- `getCrawlTasks()`: 获取爬虫任务列表
- `getSchedulerStatus()`: 获取调度器状态

## 调试模式

在调试模式下（`config.json` 中 `debug: true`），系统会：

1. 在控制台显示当前数据源信息
2. 记录详细的数据加载日志
3. 显示环境切换提示
4. 展示API调用详情

```javascript
// 检查调试模式
if (dataManager.getEnvironmentInfo().debug) {
  console.log('当前环境信息:', dataManager.getEnvironmentInfo())
}
```

## 缓存机制

系统支持数据缓存以提升用户体验：

- 统计数据缓存5分钟
- 榜单数据缓存15分钟
- 页面配置缓存30分钟
- test环境下缓存时间减半

## 错误处理

数据管理器具备完善的错误处理机制：

1. **网络错误**: 自动重试，降级到缓存数据
2. **数据解析错误**: 返回默认结构，避免页面崩溃
3. **接口不存在**: test环境返回模拟数据，其他环境显示错误提示

## 性能优化

1. **懒加载**: 按需加载数据，避免不必要的请求
2. **批量请求**: 支持并行请求多个接口
3. **请求去重**: 避免重复请求相同数据
4. **内存管理**: 及时清理过期缓存

## 扩展指南

### 添加新的假数据

1. 在 `fake_data.json` 中添加对应的数据结构
2. 在 `data-manager.js` 中添加对应的获取方法
3. 更新页面代码使用新的API方法

### 添加新的环境

1. 在 `config.json` 的 `environments` 中添加新环境配置
2. 在 `data-manager.js` 中添加特殊处理逻辑（如需要）
3. 更新API配置页面的环境选项

这个数据管理系统为前端开发提供了极大的灵活性，开发者可以在不依赖后端服务的情况下进行完整的功能开发和测试。