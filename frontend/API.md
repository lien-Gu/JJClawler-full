# API 接口说明文档

## 概述

本文档描述了晋江爬虫前端项目所需的所有API接口，包括开发环境和生产环境的配置说明。

## 环境配置

### 开发环境
- 后端地址：`http://localhost:8000`
- 跨域：需要后端配置CORS

### 生产环境
- 后端地址：`https://your-domain.com` （需要替换为实际域名）
- 跨域：通过HTTPS + 域名配置

## 跨域配置说明

### 开发环境跨域配置

#### 1. 后端CORS配置（推荐）
后端需要在响应头中添加：
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

#### 2. UniApp代理配置（备选）
在 `manifest.json` 中配置：
```json
{
  "h5": {
    "devServer": {
      "proxy": {
        "/api": {
          "target": "http://localhost:8000",
          "changeOrigin": true,
          "secure": false
        }
      }
    }
  }
}
```

### 生产环境配置
1. 确保前后端使用相同协议（HTTPS）
2. 配置正确的域名和端口
3. 后端配置生产环境的CORS策略

## API 接口列表

### 1. 统计数据接口

#### 1.1 获取首页统计数据
```
GET /api/stats/overview
```

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "totalBooks": 12580,
    "totalRankings": 156,
    "totalSites": 8,
    "todayUpdates": 245,
    "siteStats": [
      {
        "site": "夹子",
        "books": 2580,
        "rankings": 25,
        "todayUpdates": 45
      }
    ],
    "hotRankings": [
      {
        "id": 1,
        "name": "月榜",
        "site": "夹子",
        "channel": "现代言情",
        "bookCount": 50,
        "updateTime": "2024-01-15T10:30:00Z"
      }
    ],
    "recentUpdates": [
      {
        "id": 1,
        "name": "周榜",
        "site": "书城",
        "updateTime": "2024-01-15T09:45:00Z"
      }
    ]
  }
}
```

### 2. 榜单相关接口

#### 2.1 获取榜单列表
```
GET /api/rankings?site={site}&channel={channel}&page={page}&limit={limit}
```

**参数说明：**
- `site`: 分站名称（可选）
- `channel`: 频道名称（可选）
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 156,
    "page": 1,
    "limit": 20,
    "list": [
      {
        "id": 1,
        "name": "月榜",
        "site": "夹子",
        "channel": "现代言情",
        "bookCount": 50,
        "updateTime": "2024-01-15T10:30:00Z",
        "isFollowed": false
      }
    ]
  }
}
```

#### 2.2 获取榜单详情
```
GET /api/rankings/{id}
```

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "月榜",
    "site": "夹子",
    "channel": "现代言情",
    "description": "晋江夹子现代言情月榜",
    "bookCount": 50,
    "updateTime": "2024-01-15T10:30:00Z",
    "createTime": "2024-01-01T00:00:00Z",
    "isFollowed": false,
    "stats": {
      "totalViews": 125680,
      "totalCollections": 8520,
      "avgScore": 8.5
    }
  }
}
```

#### 2.3 获取榜单书籍列表
```
GET /api/rankings/{id}/books?page={page}&limit={limit}&sort={sort}&order={order}
```

**参数说明：**
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）
- `sort`: 排序字段（rank, views, collections, score）
- `order`: 排序方向（asc, desc）

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 50,
    "page": 1,
    "limit": 20,
    "list": [
      {
        "id": 1,
        "title": "书名示例",
        "author": "作者名",
        "rank": 1,
        "views": 125680,
        "collections": 8520,
        "score": 8.5,
        "tags": ["现代", "甜文"],
        "status": "连载中",
        "updateTime": "2024-01-15T10:30:00Z",
        "isFollowed": false
      }
    ]
  }
}
```

### 3. 书籍相关接口

#### 3.1 获取书籍详情
```
GET /api/books/{id}
```

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "书名示例",
    "author": "作者名",
    "description": "书籍简介...",
    "cover": "https://example.com/cover.jpg",
    "tags": ["现代", "甜文"],
    "status": "连载中",
    "wordCount": 125000,
    "chapterCount": 45,
    "views": 125680,
    "collections": 8520,
    "score": 8.5,
    "publishTime": "2024-01-01T00:00:00Z",
    "updateTime": "2024-01-15T10:30:00Z",
    "isFollowed": false,
    "stats": {
      "dailyViews": 1250,
      "weeklyViews": 8520,
      "monthlyViews": 25680
    }
  }
}
```

#### 3.2 获取书籍榜单历史
```
GET /api/books/{id}/rankings?page={page}&limit={limit}
```

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 15,
    "page": 1,
    "limit": 10,
    "list": [
      {
        "rankingId": 1,
        "rankingName": "月榜",
        "site": "夹子",
        "channel": "现代言情",
        "rank": 1,
        "enterTime": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

#### 3.3 获取相关推荐书籍
```
GET /api/books/{id}/recommendations?limit={limit}
```

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 2,
      "title": "推荐书籍",
      "author": "作者名",
      "score": 8.3,
      "reason": "同类型高分作品"
    }
  ]
}
```

### 4. 搜索接口

#### 4.1 搜索书籍
```
GET /api/search/books?q={keyword}&page={page}&limit={limit}
```

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 25,
    "page": 1,
    "limit": 20,
    "list": [
      {
        "id": 1,
        "title": "书名示例",
        "author": "作者名",
        "score": 8.5,
        "highlight": "匹配的关键词片段"
      }
    ]
  }
}
```

#### 4.2 搜索榜单
```
GET /api/search/rankings?q={keyword}&page={page}&limit={limit}
```

### 5. 关注相关接口

#### 5.1 获取关注的榜单
```
GET /api/follows/rankings?page={page}&limit={limit}&sort={sort}
```

**参数说明：**
- `sort`: 排序方式（time, name, update）

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 12,
    "page": 1,
    "limit": 20,
    "list": [
      {
        "id": 1,
        "name": "月榜",
        "site": "夹子",
        "channel": "现代言情",
        "followTime": "2024-01-15T10:30:00Z",
        "updateTime": "2024-01-15T10:30:00Z",
        "newBooks": 5
      }
    ]
  }
}
```

#### 5.2 获取关注的书籍
```
GET /api/follows/books?page={page}&limit={limit}&sort={sort}
```

#### 5.3 关注榜单
```
POST /api/follows/rankings/{id}
```

**响应示例：**
```json
{
  "code": 200,
  "message": "关注成功",
  "data": {
    "isFollowed": true
  }
}
```

#### 5.4 取消关注榜单
```
DELETE /api/follows/rankings/{id}
```

#### 5.5 关注书籍
```
POST /api/follows/books/{id}
```

#### 5.6 取消关注书籍
```
DELETE /api/follows/books/{id}
```

#### 5.7 批量取消关注
```
DELETE /api/follows/batch
```

**请求体：**
```json
{
  "type": "rankings", // 或 "books"
  "ids": [1, 2, 3]
}
```

### 6. 用户相关接口

#### 6.1 获取用户信息
```
GET /api/user/profile
```

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "nickname": "用户昵称",
    "avatar": "https://example.com/avatar.jpg",
    "followRankings": 12,
    "followBooks": 25,
    "joinTime": "2024-01-01T00:00:00Z"
  }
}
```

#### 6.2 更新用户信息
```
PUT /api/user/profile
```

**请求体：**
```json
{
  "nickname": "新昵称",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

### 7. 反馈接口

#### 7.1 提交反馈
```
POST /api/feedback
```

**请求体：**
```json
{
  "type": "bug", // bug, feature, other
  "title": "反馈标题",
  "content": "反馈内容",
  "contact": "联系方式（可选）"
}
```

### 8. 系统接口

#### 8.1 获取应用配置
```
GET /api/system/config
```

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "version": "1.0.0",
    "updateTime": "2024-01-15T10:30:00Z",
    "announcement": "系统公告内容",
    "maintenance": false
  }
}
```

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 需要替换的API路径

在 `utils/request.js` 中，需要将以下配置：

```javascript
// 开发环境
const baseURL = 'http://localhost:8000'

// 生产环境（需要替换为实际域名）
const baseURL = 'https://your-domain.com'
```

## 注意事项

1. **跨域问题**：
   - 开发环境建议后端配置CORS
   - 生产环境确保前后端协议一致

2. **请求头配置**：
   - 所有请求需要包含 `Content-Type: application/json`
   - 如有认证需求，添加 `Authorization: Bearer {token}`

3. **错误处理**：
   - 统一错误响应格式
   - 前端需要处理网络异常和业务异常

4. **分页参数**：
   - 默认页码从1开始
   - 默认每页20条数据

5. **时间格式**：
   - 统一使用ISO 8601格式：`YYYY-MM-DDTHH:mm:ssZ`

6. **图片资源**：
   - 确保图片URL可访问
   - 建议使用CDN加速 