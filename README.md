# JJClawler 微信小程序 / JJClawler Mini-Program

## 1. 项目需求 / Project Requirements
>这是一个晋江app爬虫项目的前端部分，作用是使用restful方法为用户展示后端中爬取到的数据。
所有页面通用的结构是下方导航栏，导航栏可以通往四个页面：首页、榜单、关注、设置。
首页：用于展示一些关键的统计数据。
榜单：顶部展示一个搜索框，用户可以搜索自己想要查询的榜单或者书籍。
搜索栏下面是分站：夹子、书城、言情、纯爱、衍生、二次元、无CP+、百合，点击这些分站栏目后会出现这些页面中有的榜单
上面有的分站下面还有频道，比如言情下面还有古言、现言、幻言、古穿、未来等等，可以参考data/url.json中的层级分布，点击这些频道栏目后会出现这些频道页面中有的榜单。
点击榜单后会出现榜单的页面，上部分体现榜单的统计数据，下面体现榜单中有的书籍。
点击书籍后会出现书籍的页面，上部分提下书籍的统计数据，下面体现书籍的历史榜单信息。
关注：用户关注的榜单或者书籍，点击后就会进入对应的榜单和书籍页面。
设置：一些用户的信息和账号设置，还有反馈意见的页面

## 2. 项目结构 / Project Structure
```
JJClawler-frontend/
├── App.vue                    # 应用入口
├── main.js                   # 主入口文件
├── manifest.json             # 应用配置
├── pages.json               # 页面路由配置（页面创建并测试后再添加）
├── uni.scss                 # 全局SCSS变量和混入
├── pages/                   # 页面目录
│   ├── index/              # 首页
│   │   ├── index.vue
│   │   └── README.md
│   ├── ranking/            # 榜单相关页面
│   │   ├── index.vue       # 榜单多层级导航页
│   │   ├── detail.vue      # 榜单详情
│   │   └── README.md
│   ├── book/               # 书籍相关页面
│   │   ├── detail.vue      # 书籍详情
│   │   └── README.md
│   ├── follow/             # 关注页面
│   │   ├── index.vue
│   │   └── README.md
│   └── settings/           # 设置页面
│       ├── index.vue       # 设置主页
│       ├── feedback.vue    # 反馈页面
│       └── README.md
├── components/             # 组件目录
│   ├── TabBar.vue         # 自定义底部导航
│   ├── SearchBar.vue      # 搜索栏组件
│   ├── StatsCard.vue      # 统计卡片组件
│   ├── RankingCard.vue    # 榜单卡片组件
│   └── BookCard.vue       # 书籍卡片组件
├── styles/                # 样式文件目录
│   ├── common.scss        # 通用样式类
│   ├── variables.scss     # 额外样式变量
│   └── mixins.scss        # 额外SCSS混入
├── static/                # 静态资源目录
│   ├── logo.png          # 应用图标
│   ├── tab-home.png      # TabBar图标 - 首页
│   ├── tab-home-current.png    # TabBar选中图标 - 首页
│   ├── tab-ranking.png   # TabBar图标 - 榜单
│   ├── tab-ranking-current.png # TabBar选中图标 - 榜单
│   ├── tab-follow.png    # TabBar图标 - 关注
│   ├── tab-follow-current.png  # TabBar选中图标 - 关注
│   ├── tab-settings.png  # TabBar图标 - 设置
│   └── tab-settings-current.png # TabBar选中图标 - 设置
├── utils/                 # 工具类
│   ├── request.js         # 网络请求封装
│   └── storage.js         # 本地存储封装
└── data/                  # 数据文件
    └── url.json           # 分站频道配置数据
```

### CSS 组织规范 / CSS Organization
- **uni.scss**: 全局SCSS变量、混入、函数
- **styles/**: 模块化样式文件，通过 `@import` 引入
- **App.vue**: 全局基础样式和通用类
- **组件样式**: 各组件内部 `<style scoped>` 样式
- **static/**: 仅存放图片、字体等静态资源，不放CSS文件

## 3. 小程序页面 / Mini-Program Pages
### 主要页面路由 / Main Page Routes
- **首页** `/pages/index/index` - 统计数据展示
- **榜单页面** `/pages/ranking/index` - 多层级导航（分站→频道→榜单）
- **榜单详情** `/pages/ranking/detail` - 榜单统计 + 书籍列表
- **书籍详情** `/pages/book/detail` - 书籍统计 + 历史榜单
- **关注页面** `/pages/follow/index` - 用户关注的内容
- **设置页面** `/pages/settings/index` - 用户信息和设置
- **反馈页面** `/pages/settings/feedback` - 意见反馈

### 榜单页面交互设计 / Ranking Page Interaction
**单页面多层级导航结构：**
1. **层级1：分站选择** - 搜索框 + 分站标签栏（可滑动）
2. **层级2：频道选择** - 面包屑导航 + 频道标签栏（当分站有子频道时）
3. **层级3：榜单列表** - 面包屑导航 + 榜单卡片列表（可滑动浏览）

### 分站结构 / Site Structure
根据 `data/url.json` 配置：
- **夹子** - 夹子频道榜单
- **书城** - 书城频道榜单  
- **言情** - 古言、现言、幻言、古穿、未来等频道
- **纯爱** - 纯爱相关频道
- **衍生** - 衍生作品频道
- **二次元** - 二次元相关频道
- **无CP+** - 无CP频道
- **百合** - 百合频道

## 4. 小程序功能 / Features
### 核心功能 / Core Features
1. **数据展示功能**
   - 首页统计数据可视化
   - 榜单数据列表展示
   - 书籍详细信息展示

2. **搜索功能**
   - 榜单搜索
   - 书籍搜索
   - 搜索历史记录

3. **导航功能**
   - 分站分类导航
   - 频道分类导航
   - 底部Tab导航

4. **用户功能**
   - 关注榜单/书籍
   - 取消关注
   - 关注列表管理

5. **设置功能**
   - 用户信息设置
   - 应用设置
   - 意见反馈

### 技术特性 / Technical Features
- **响应式设计** - 适配不同屏幕尺寸
- **数据缓存** - 本地存储优化用户体验
- **下拉刷新** - 实时更新数据
- **上拉加载** - 分页加载更多内容

## 5. 接口设计 / API Specifications
### RESTful API 端点 / API Endpoints

#### 统计数据 / Statistics
- `GET /api/stats/overview` - 获取首页统计数据
- `GET /api/stats/ranking/{rankingId}` - 获取榜单统计数据
- `GET /api/stats/book/{bookId}` - 获取书籍统计数据

#### 分站与频道 / Sites & Channels
- `GET /api/sites` - 获取所有分站列表
- `GET /api/sites/{siteId}/channels` - 获取分站下的频道列表
- `GET /api/channels/{channelId}/rankings` - 获取频道下的榜单列表

#### 榜单 / Rankings
- `GET /api/rankings/search?q={keyword}` - 搜索榜单
- `GET /api/rankings/{rankingId}` - 获取榜单详情
- `GET /api/rankings/{rankingId}/books` - 获取榜单中的书籍列表

#### 书籍 / Books
- `GET /api/books/search?q={keyword}` - 搜索书籍
- `GET /api/books/{bookId}` - 获取书籍详情
- `GET /api/books/{bookId}/rankings` - 获取书籍历史榜单信息

#### 用户关注 / User Follow
- `GET /api/user/follows` - 获取用户关注列表
- `POST /api/user/follows` - 添加关注
- `DELETE /api/user/follows/{followId}` - 取消关注

#### 用户设置 / User Settings
- `GET /api/user/profile` - 获取用户信息
- `PUT /api/user/profile` - 更新用户信息
- `POST /api/feedback` - 提交反馈

## 6. 任务执行清单 / Task Execution Checklist

### 阶段一：项目基础搭建 / Phase 1: Project Setup
- [x] 创建项目README和需求分析
- [x] 创建数据配置文件 (data/url.json)
- [x] 设置样式组织结构 (uni.scss + styles目录)
- [x] 修复样式导入路径问题
- [ ] 创建基础目录结构
- [ ] 创建TabBar所需图标资源

### 阶段二：公共组件开发 / Phase 2: Common Components
- [ ] TabBar.vue - 底部导航组件
- [x] SearchBar.vue - 搜索栏组件  
- [x] StatsCard.vue - 统计卡片组件
- [x] RankingCard.vue - 榜单卡片组件
- [x] BookCard.vue - 书籍卡片组件

### 阶段三：工具类开发 / Phase 3: Utilities
- [x] request.js - 网络请求封装
- [x] storage.js - 本地存储封装

### 阶段四：页面开发 / Phase 4: Page Development
**开发流程**：创建页面 → 实现功能 → 测试访问 → 添加到pages.json

- [x] 首页 (index/index.vue) - 统计数据展示
- [x] 榜单页面 (ranking/index.vue) - 多层级导航
- [x] 榜单详情 (ranking/detail.vue) - 榜单统计和书籍
- [x] 书籍详情 (book/detail.vue) - 书籍信息和历史
- [x] 关注页面 (follow/index.vue) - 用户关注列表
- [x] 设置页面 (settings/index.vue) - 用户设置
- [ ] 反馈页面 (settings/feedback.vue) - 意见反馈（暂不开发）
- [x] 配置TabBar导航和页面路由

### 阶段五：接口集成 / Phase 5: API Integration
- [x] 创建API接口说明文档 (API.md)
- [x] 修复storage.js导出问题
- [ ] 集成统计数据API
- [ ] 集成分站频道API
- [ ] 集成榜单搜索API
- [ ] 集成书籍搜索API
- [ ] 集成用户关注API

### 阶段六：测试优化 / Phase 6: Testing & Optimization  
- [ ] 功能测试
- [ ] 性能优化
- [ ] 兼容性测试
- [ ] 用户体验优化

### 当前状态 / Current Status
✅ **已完成**: 项目架构设计、样式系统、公共组件、工具类、所有核心页面、TabBar导航配置、API文档
🔄 **进行中**: API接口集成、最终测试优化

### 最新更新 / Latest Updates
- **修复问题**: 解决settings页面中clearSync函数导出问题
- **API文档**: 创建完整的API.md说明文档，包含跨域配置指导
- **环境配置**: 详细说明开发环境(localhost:8000)和生产环境的配置

## 📱 所需图标资源详细规格 / Required Icon Resources

### TabBar 图标规格 / TabBar Icon Specifications
所有 TabBar 图标需要准备**普通状态**和**选中状态**两套：

#### 1. 首页图标 / Home Icons
- **文件名**: `tab-home.png` (普通) / `tab-home-current.png` (选中)
- **尺寸**: 40x40px (推荐使用矢量图标)
- **功能**: 代表首页/统计数据展示
- **设计**: 房屋/主页图标，简洁现代风格
- **背景**: 透明背景
- **颜色**: 普通状态 #7A7E83，选中状态 #3CC51F

#### 2. 榜单图标 / Ranking Icons  
- **文件名**: `tab-ranking.png` (普通) / `tab-ranking-current.png` (选中)
- **尺寸**: 40x40px (推荐使用矢量图标)
- **功能**: 代表榜单/排行功能
- **设计**: 排行榜/列表图标，可使用数字1-3或条形图样式
- **背景**: 透明背景
- **颜色**: 普通状态 #7A7E83，选中状态 #3CC51F

#### 3. 关注图标 / Follow Icons
- **文件名**: `tab-follow.png` (普通) / `tab-follow-current.png` (选中)  
- **尺寸**: 40x40px (推荐使用矢量图标)
- **功能**: 代表用户关注的内容
- **设计**: 心形/收藏/关注图标
- **背景**: 透明背景
- **颜色**: 普通状态 #7A7E83，选中状态 #3CC51F

#### 4. 设置图标 / Settings Icons
- **文件名**: `tab-settings.png` (普通) / `tab-settings-current.png` (选中)
- **尺寸**: 40x40px (推荐使用矢量图标)  
- **功能**: 代表设置/个人中心
- **设计**: 齿轮/设置图标
- **背景**: 透明背景
- **颜色**: 普通状态 #7A7E83，选中状态 #3CC51F

### 应用图标 / App Icon
- **文件名**: `logo.png`
- **尺寸**: 512x512px (高分辨率)
- **功能**: 应用主图标
- **设计**: 体现"晋江爬虫"主题，可结合书籍、数据、爬虫等元素
- **背景**: 可以有背景色或保持透明
- **格式**: PNG格式，支持透明度

### 图标设计建议 / Icon Design Guidelines
- **风格统一**: 所有图标保持一致的设计风格
- **简洁明了**: 在小尺寸下依然清晰可辨
- **符合规范**: 遵循微信小程序设计规范
- **适配性强**: 在不同背景下都有良好的可视性

## 7. 其他说明 / Additional Notes
*(待补充 / To be added)* 