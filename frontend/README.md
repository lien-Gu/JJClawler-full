# 晋江爬虫助手微信小程序

## 项目简介

晋江爬虫助手是基于uni-app框架（Vue 3）开发的微信小程序前端项目，为晋江文学城数据爬虫系统提供用户界面。用户可以通过小程序查看书籍排行榜、统计数据、书籍详情以及管理个人关注等功能。

## 核心功能

### 📊 首页 - 统计概览
- **统计报告展示**: 以轮播卡片形式展示各类数据统计报告
- **数据可视化**: 支持图表展示，点击查看详细报告
- **实时更新**: 根据后端爬虫数据实时更新统计信息

### 📈 榜单页面 - 排行榜管理  
- **榜单分类浏览**: 支持按频道分类查看不同类型榜单
- **搜索功能**: 支持书籍名称、作者、书籍ID等多维度搜索
- **榜单详情**: 点击榜单查看具体书籍排名和历史变化

### 📚 书籍详情 - 深度数据分析
- **书籍基础信息**: 书名、作者、分类、状态等基本信息
- **统计数据**: 收藏数、点击量、评论数、营养液等数据指标
- **排名历史**: 书籍在各个榜单中的历史排名变化趋势
- **数据图表**: 多维度数据可视化展示

### ❤️ 关注管理 - 个性化跟踪
- **书籍关注**: 关注感兴趣的书籍，跟踪其排名变化
- **榜单关注**: 关注特定榜单，及时了解榜单动态
- **数据提醒**: 关注的书籍或榜单有重要变化时提供提醒

### ⚙️ 设置中心 - 环境配置
- **环境切换**: 支持开发环境(dev)、测试环境(test)、生产环境(prod)切换
- **API配置**: 自定义后端API服务器地址
- **用户信息**: 用户头像、注册信息等个人资料管理
- **反馈建议**: 问题反馈和功能建议提交

## 技术架构

### 前端技术栈
- **框架**: uni-app (Vue 3) - 跨平台开发框架
- **样式**: SCSS - CSS预处理器
- **状态管理**: Vuex/本地状态 - 应用状态管理
- **网络请求**: uni.request - 封装HTTP请求
- **本地存储**: uni.storage - 数据持久化

### 架构特点
- **多环境支持**: dev/test/prod三环境自动切换
- **环境感知数据层**: 根据环境自动选择真实API或模拟数据
- **组件化开发**: 基础组件 + 业务组件分层设计
- **混入模式**: 通用功能通过Vue mixins复用
- **响应式设计**: 适配不同屏幕尺寸的移动设备

## 项目结构

```
frontend/
├── pages/                          # 应用页面
│   ├── index/index.vue             # 首页 - 统计报告展示
│   ├── ranking/                    # 榜单相关页面
│   │   ├── index.vue               # 榜单列表页
│   │   └── detail.vue              # 榜单详情页
│   ├── book/detail.vue             # 书籍详情页
│   ├── follow/index.vue            # 用户关注页
│   ├── report/detail.vue           # 统计报告详情页
│   ├── settings/                   # 设置相关页面
│   │   ├── index.vue               # 设置主页
│   │   └── api-config.vue          # API配置页
│   └── webview/index.vue           # 内置浏览器页
├── components/                     # 可复用组件
│   ├── Base*.vue                   # 基础UI组件
│   ├── Book*.vue                   # 书籍相关组件  
│   ├── Ranking*.vue                # 榜单相关组件
│   ├── Report*.vue                 # 报告相关组件
│   └── ...                        # 其他业务组件
├── utils/                          # 工具模块
│   ├── request.js                  # HTTP请求封装
│   ├── data-manager.js             # 数据管理器（环境感知）
│   ├── env-config.js               # 环境配置管理
│   ├── config.js                   # 应用配置管理
│   ├── storage.js                  # 本地存储工具
│   └── formatters.js               # 数据格式化工具
├── mixins/                         # Vue混入
│   ├── navigation.js               # 导航相关混入
│   └── formatter.js                # 格式化相关混入
├── styles/                         # 样式文件
│   ├── variables.scss              # SCSS变量定义
│   ├── mixins.scss                 # SCSS混入
│   ├── common.scss                 # 公共样式
│   └── ...                        # 其他样式文件
├── data/                           # 静态数据
│   ├── config.json                 # 环境配置数据
│   ├── openapi.json                # 后端API接口定义
│   └── fake_data.json              # 测试模拟数据
├── static/                         # 静态资源
│   └── icons/                      # 图标资源
└── docs/                           # 项目文档
    ├── UI-design.md                # UI设计文档
    └── project-restructure.md      # 项目重构方案
```

## 开发环境配置

### 环境要求
- **HBuilderX**: 推荐使用HBuilderX开发IDE
- **微信开发者工具**: 用于小程序预览和调试
- **Node.js**: 如使用CLI开发模式（可选）

### 开发命令

#### 使用HBuilderX开发（推荐）
```bash
# 1. 使用HBuilderX导入项目
# 2. 选择运行到微信开发者工具
# 3. 在微信开发者工具中预览和调试
```

#### 使用CLI开发（可选）
```bash
# 安装依赖
npm install

# 开发环境运行
npm run dev:mp-weixin

# 生产环境构建
npm run build:mp-weixin
```

### 环境配置
项目支持三种运行环境：

#### 开发环境 (dev)
```javascript
// 连接本地后端API
baseURL: 'http://localhost:8000/api/v1'
// 需要先启动后端服务
```

#### 测试环境 (test)  
```javascript
// 使用预制模拟数据
useLocalData: true
// 无需后端服务，便于离线开发
```

#### 生产环境 (prod)
```javascript
// 连接线上API服务器
baseURL: 'https://api.jjclawler.com/api/v1'
```

## API接口对接

### 后端API服务
项目与后端FastAPI服务进行数据交互，主要接口包括：

#### 书籍相关接口
- `GET /api/v1/books/` - 获取书籍列表（分页）
- `GET /api/v1/books/{novel_id}` - 获取书籍详情
- `GET /api/v1/books/{novel_id}/snapshots` - 获取书籍历史快照
- `GET /api/v1/books/{novel_id}/rankings` - 获取书籍排名历史

#### 榜单相关接口
- `GET /api/v1/rankings/` - 获取榜单列表
- `GET /api/v1/rankingsdetail/day/{ranking_id}` - 获取榜单详情（按天）
- `GET /api/v1/rankingsdetail/hour/{ranking_id}` - 获取榜单详情（按小时）
- `GET /api/v1/rankings/history/day/{ranking_id}` - 获取榜单历史（按天）
- `GET /api/v1/rankings/history/hour/{ranking_id}` - 获取榜单历史（按小时）

#### 调度相关接口
- `POST /api/v1/schedule/task/create` - 创建爬取任务
- `GET /api/v1/schedule/status` - 获取调度器状态

### 数据格式说明
所有API返回数据遵循统一格式：
```javascript
{
  "success": true,
  "code": 200,
  "message": "",
  "timestamp": "2025-08-29T10:00:00Z",
  "data": {
    // 具体业务数据
  }
}
```

## 开发指南

### 代码规范
- **组件命名**: 使用PascalCase，如`BookCard.vue`
- **文件命名**: 使用kebab-case，如`book-detail.vue`
- **变量命名**: 使用camelCase，如`bookDetail`
- **常量命名**: 使用SCREAMING_SNAKE_CASE，如`API_BASE_URL`

### 开发流程
1. **环境准备**: 配置开发环境和后端API连接
2. **功能开发**: 基于现有组件和服务开发新功能
3. **环境测试**: 在test环境使用模拟数据测试功能
4. **集成测试**: 在dev环境连接真实API测试
5. **生产发布**: 切换到prod环境进行生产发布

### 常用开发模式

#### 1. 添加新页面
```javascript
// 1. 在pages目录创建页面文件
// 2. 在pages.json中注册页面路由
// 3. 使用navigation mixin实现页面跳转
this.navigateTo('/pages/new-page/index')
```

#### 2. 添加API接口
```javascript
// 1. 在data-manager.js中添加新方法
async getNewData(params) {
  return this.getData('/api/new-endpoint', 'fakeDataMethod', params)
}

// 2. 在页面中调用
import dataManager from '@/utils/data-manager'
const data = await dataManager.getNewData(params)
```

#### 3. 添加新组件
```javascript
// 1. 在components目录创建组件
// 2. 导入并在页面中使用
import NewComponent from '@/components/NewComponent'

// 3. 注册组件
components: {
  NewComponent
}
```

## 部署说明

### 微信小程序发布
1. **项目构建**: 在HBuilderX中选择"发行" -> "小程序-微信"
2. **代码上传**: 使用微信开发者工具上传代码
3. **版本管理**: 在微信公众平台管理版本发布

### 其他平台部署
uni-app支持编译到多个平台：
- **H5网页版**: 可部署到Web服务器
- **APP应用**: 可打包成原生移动应用
- **其他小程序**: 支持支付宝、百度等小程序平台

## 常见问题

### Q: 如何切换开发环境？
A: 在设置页面可以切换环境，或者直接修改`data/config.json`中的`environment`字段。

### Q: 网络请求失败怎么办？
A: 检查当前环境配置，确认后端服务是否启动，或切换到test环境使用模拟数据。

### Q: 如何添加新的统计报告？
A: 在`fake-data-manager.js`中添加模拟数据，在后端API中添加对应接口，前端通过数据管理器调用。

### Q: 小程序预览时白屏怎么办？
A: 检查微信开发者工具的项目配置，确认appid设置正确，网络域名配置完整。

## 项目规划

### 已实现功能 ✅
- [x] 多环境配置管理
- [x] 书籍和榜单数据展示
- [x] 统计报告可视化
- [x] 基础用户界面

### 开发中功能 🚧
- [ ] 用户认证系统
- [ ] 数据推送提醒
- [ ] 离线数据缓存
- [ ] 高级搜索功能

### 计划功能 📋
- [ ] 社交分享功能
- [ ] 个性化推荐
- [ ] 数据导出功能
- [ ] 多主题支持

## 贡献指南

### 开发贡献
1. Fork项目仓库
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交变更: `git commit -m 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 创建Pull Request

### 问题反馈
- 通过GitHub Issues报告Bug
- 通过小程序设置页面提交反馈
- 发送邮件到项目维护者邮箱

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系我们

- **项目地址**: [GitHub Repository]
- **问题反馈**: [GitHub Issues]
- **技术交流**: [技术交流群/邮箱]

---

📱 **体验地址**: [小程序二维码]  
🔗 **在线文档**: [文档地址]  
⭐ **如果觉得项目有用，请给个Star支持一下！**