# JJClawler 小程序 UI 设计文档

## 文档说明
此文档用于记录 JJClawler 微信小程序的 UI 设计信息。请填写相关设计信息，包括 Figma 链接、设计规范和页面结构，以便根据设计生成对应的前端代码。

## 项目概览

### 设计版本信息
- **设计版本**: v1.0
- **设计日期**: [2025.6.25]
- **设计师**: [Lien Gu]
- **最后更新**: [2025.6.25]

### Figma 链接
- **主设计文件**: https://www.figma.com/design/o8H03CPwlcSXHaG1wwT3Z8/version1?node-id=67-159

## 页面结构设计

### 1. 首页 (index)
**Figma Frame ID**: https://www.figma.com/design/o8H03CPwlcSXHaG1wwT3Z8/version1?node-id=70-896&t=Gb1o99hUfBrj2vF4-11

#### 功能描述
首页用于显示统计信息，在中间的位置显示生成的所有统计报告，支持向下滑动来查询更多的统计报告。

#### 布局结构
```
首页
├── 顶部招呼栏
│   ├── 显示欢迎话语“嗨～”
├── 主内容区 reports
│   ├── 包含许多个carousel，每个都代表一条报告。点击可以跳转到报告详情reports-detail页面
└── 底部标签栏 TabBar
    └── 所有页面都有tabBar，包含首页、榜单、关注和设置4个Tab，点击可以跳转到不同的页面
```

#### 组件列表
- [ ] [carousel] - 每个都由Item1和Item-Last组成，Item1中显示报告的简单描述。点击可以跳转到报告详情reports-detail页面
- [ ] [TabBar] - 所有页面都有tabBar，包含首页、榜单、关注和设置4个Tab，当处于对应的页面时候，图像下面的颜色会变深，字体颜色也变深

#### 交互说明
- 点击carousel跳转到reports-detail页面
- 点击TabBar可以跳转到不同的页面

---

### 2. 榜单页面 (ranking)
**Figma Frame ID**: https://www.figma.com/design/o8H03CPwlcSXHaG1wwT3Z8/version1?node-id=70-897&t=Gb1o99hUfBrj2vF4-11

#### 功能描述
显示爬取到的所有榜单

#### 布局结构
```
榜单页面
├── 搜索框search bar
└── 榜单分类tab
｜——具体榜单或者书籍列表
｜——导航栏TabBar
```

#### 组件列表
- [ ] [search bar] - 可以输入中文字符，或者书籍id，返回查询到的书籍和榜单。
- [ ] [ Frame 20] - 这是榜单列表的单条记录，Initial中显示榜单在这个页面中的序号，Header中显示榜单名称，subhead中显示榜单的层级从属，
                    点击右边的Media可以跳转到榜单详情页面。
#### 交互说明
- [描述交互行为]

---

### 3. 书籍详情页 (book-detail)https://www.figma.com/design/o8H03CPwlcSXHaG1wwT3Z8/version1?node-id=125-1230&t=Gb1o99hUfBrj2vF4-11

#### 功能描述
显示书籍的详细信息，header中显示书籍名称，subhead显示书籍的从属分类，右边的Icon button点击后可以添加关注或者取消关注。Item1中显示统计的图像，Tab group点击不同的tab
会在Item1中显示对应的统计图像。往下的ranking list显示书籍的上榜单历史，Initial显示是第几个榜单，overline显示榜单名称
headline显示榜单数据变化，supporting text显示上榜周期。显示trailing element说明正在榜上。

#### 布局结构
```
书籍详情页
├── [描述页面结构]
└── [描述其他元素]
```

#### 组件列表
- [ ] [组件名称] - [组件描述]

#### 交互说明
- [描述交互行为]

---

### 4. 设置页面 (settings)
**Figma Frame ID**: https://www.figma.com/design/o8H03CPwlcSXHaG1wwT3Z8/version1?node-id=70-899&t=Gb1o99hUfBrj2vF4-11

#### 功能描述
generic avatar是用户头像，支持用户自己自定义。frame39中是三个功能：自动更新、本地缓存和清理数据。

#### 布局结构
```
设置页面
├── [描述页面结构]
└── [描述其他元素]
```

#### 组件列表
- [ ] [组件名称] - [组件描述]

#### 交互说明
- [描述交互行为]


### 5. 关注页面 (follow)
**Figma Frame ID**:https://www.figma.com/design/o8H03CPwlcSXHaG1wwT3Z8/version1?node-id=70-898&t=Gb1o99hUfBrj2vF4-11 

#### 功能描述
component中的frame31显示用户关注了多少本书籍，多少本书籍正在上榜。frame31就是关注的书籍列表，其中每一个TabBar/component
都是一本关注的书籍。header中显示书籍名称，subhead显示书籍的本周的增长情况。右边的media可以显示书籍是否在榜单上，比如第一本就在榜单上
其他的不在，书籍还可以侧滑然后取消关注或者添加关注。

### 6. 榜单详情 (ranking-detail)
**Figma Frame ID**:https://www.figma.com/design/o8H03CPwlcSXHaG1wwT3Z8/version1?node-id=119-2617&t=Gb1o99hUfBrj2vF4-11


#### 功能描述
frame30中显示榜单名称，frame31中显示榜单层级，split button点击后frame32就会变味frame38，其中的变化在于
Trailing button的图像变了，component2也会滑出，并且其中显示榜单的统计信息，显示方法与书籍的统计信息类似。
再点击split button之后又会变回frame32的样子。frame13是书籍列表，显示榜单中的书籍。Icon button点击后可以
关注该书籍，并且点击后icon button的state属性也变从disabled状态变味pressed状态。

### 7. 榜单详情 (ranking-detail)
**Figma Frame ID**:https://www.figma.com/design/o8H03CPwlcSXHaG1wwT3Z8/version1?node-id=67-159&p=f&t=Gb1o99hUfBrj2vF4-11


#### 功能描述

目前这个功能还没有实现，暂定为将消息返回到response中。

---

## 组件设计

### 通用组件

#### 按钮组件 (Button)
**Figma Frame ID**: [请填写按钮组件的 node-id]

**变体类型**:
- [ ] Primary Button - 主要按钮
- [ ] Secondary Button - 次要按钮
- [ ] Text Button - 文字按钮
- [ ] Icon Button - 图标按钮

**状态**:
- [ ] Normal - 正常状态
- [ ] Hover - 悬停状态 (如适用)
- [ ] Active - 激活状态
- [ ] Disabled - 禁用状态

---

#### 卡片组件 (Card)
**Figma Frame ID**: [请填写卡片组件的 node-id]

**用途**: [描述卡片的使用场景]

**内容结构**:
- [ ] [描述卡片内容结构]

---

#### 列表项组件 (ListItem)
**Figma Frame ID**: [请填写列表项组件的 node-id]

**用途**: [描述列表项的使用场景]

**变体类型**:
- [ ] [描述不同类型的列表项]

---

### 业务组件

#### 书籍卡片 (BookCard)
**Figma Frame ID**: [请填写书籍卡片的 node-id]

**显示信息**:
- [ ] 书籍封面
- [ ] 书名
- [ ] 作者
- [ ] 分类标签
- [ ] 统计数据 (点击量、收藏数等)
- [ ] [其他信息]

---

#### 榜单项 (RankingItem)
**Figma Frame ID**: [请填写榜单项的 node-id]

**显示信息**:
- [ ] 排名序号
- [ ] 书籍信息
- [ ] 排名变化指示
- [ ] [其他信息]

---

## 响应式设计

### 屏幕尺寸适配
- **设计基准**: [如: iPhone 12 Pro - 390x844]
- **最小支持宽度**: [如: 320px]
- **最大支持宽度**: [如: 414px]

### 适配策略
- [ ] 等比缩放
- [ ] 弹性布局
- [ ] 响应式字体
- [ ] [其他适配方式]

## 动画和过渡

### 页面转场
- **进入动画**: [描述页面进入动画效果]
- **退出动画**: [描述页面退出动画效果]
- **持续时间**: [如: 300ms]
- **缓动函数**: [如: ease-in-out]

### 组件动画
- **按钮点击**: [描述按钮点击反馈动画]
- **列表加载**: [描述列表加载动画]
- **状态切换**: [描述状态切换动画]

## 图标和插图

### 图标系统
- **图标库**: [如: 自定义图标 / Feather Icons]
- **图标尺寸**: [如: 16px, 20px, 24px]
- **图标风格**: [如: 线性 / 面性]

### 插图
- **插图风格**: [描述插图风格]
- **使用场景**: [描述插图使用场景]

## 实现注意事项

### 技术约束
- [ ] 微信小程序原生组件限制
- [ ] 样式兼容性考虑
- [ ] 性能优化要求
- [ ] [其他技术限制]

### 特殊处理
- [ ] 长文本截断处理
- [ ] 图片懒加载
- [ ] 网络异常状态
- [ ] 加载状态显示
- [ ] [其他特殊情况]

### 无障碍设计
- [ ] 颜色对比度符合标准
- [ ] 文字大小适合阅读
- [ ] 触摸目标大小适当
- [ ] [其他无障碍考虑]

## 设计资源

### 设计文件
- **源文件格式**: [如: Figma]
- **导出格式**: [如: PNG, SVG]
- **导出规格**: [如: @1x, @2x, @3x]

### 字体资源
- **主要字体**: [如: PingFang SC]
- **备用字体**: [如: Helvetica, Arial]
- **特殊字体**: [如果有特殊字体需求]

### 图片资源
- **图片格式**: [如: WebP, PNG]
- **压缩要求**: [描述图片压缩要求]
- **命名规范**: [描述图片命名规范]

## 更新日志

### 版本 1.0 - [日期]
- [描述初始设计内容]

### 版本 1.1 - [日期]
- [描述更新内容]

---

## 使用说明

### 如何填写此文档
1. **Figma 链接**: 提供完整的 Figma 文件链接
2. **Frame ID**: 在 Figma 中右键点击 frame，选择 "Copy link"，从链接中提取 node-id 部分 (如：node-id=123%3A456 对应 123:456)
3. **设计规范**: 填写具体的颜色值、字体大小等数值
4. **组件描述**: 详细描述每个组件的功能、状态和变体

### Figma node-id 获取方法
1. 在 Figma 中选择要引用的 frame 或组件
2. 右键选择 "Copy link" 
3. 链接格式类似：`https://figma.com/design/file-key/file-name?node-id=123%3A456`
4. 提取 node-id 部分：`123:456` (将 %3A 替换为 :)

### 后续代码生成
填写完此文档后，可以结合 Figma 设计稿使用以下方式生成代码：
1. 提供具体的 Figma frame node-id
2. 说明需要生成的页面或组件
3. 指定使用的技术栈 (如：微信小程序、Vue.js 等)

---

**注意**: 请尽可能详细地填写设计信息，这将有助于生成更准确和高质量的前端代码。