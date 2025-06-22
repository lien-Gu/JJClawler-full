# 爬虫模块测试说明

这个目录包含了晋江文学城爬虫模块的完整测试套件。

## 📁 文件结构

```
tests/crawler/
├── __init__.py
├── conftest.py                    # 测试配置和数据fixtures
├── pytest.ini                    # pytest配置文件
├── README.md                      # 本说明文件
├── test_crawler_base.py          # 爬虫基础模块测试
├── test_jiazi_crawler.py         # 夹子榜爬虫测试
├── test_page_crawler.py          # 分类页面爬虫测试
├── test_parser.py                # 数据解析器测试
└── test_integration_real.py      # 真实URL集成测试
```

## 🧪 测试类型

### 单元测试 (unit)
- **test_crawler_base.py**: 测试基础工具函数
- **test_parser.py**: 测试数据解析逻辑
- **test_jiazi_crawler.py**: 测试夹子榜爬虫（mock网络）
- **test_page_crawler.py**: 测试分类页面爬虫（mock网络）

### 集成测试 (integration)
- **test_integration_real.py**: 使用真实API的集成测试

### 网络测试 (network)
- 需要真实网络连接的测试
- 默认被跳过，可通过环境变量启用

## 🚀 运行测试

### 基本用法

```bash
# 运行所有爬虫测试
pytest tests/crawler/ -v

# 只运行单元测试（不需要网络）
pytest tests/crawler/ -m "unit" -v

# 跳过网络测试
pytest tests/crawler/ -m "not network" -v

# 运行特定文件的测试
pytest tests/crawler/test_parser.py -v

# 运行特定测试方法
pytest tests/crawler/test_parser.py::TestJiaziDataParsing::test_parse_jiazi_data_success -v
```

### 启用真实网络测试

```bash
# 设置环境变量启用网络测试
export ENABLE_REAL_NETWORK_TESTS=true

# 只运行网络测试
pytest tests/crawler/test_integration_real.py -m network -v

# 运行所有测试（包括网络测试）
pytest tests/crawler/ -v
```

### 测试报告

```bash
# 生成覆盖率报告
pytest tests/crawler/ --cov=app.modules.crawler --cov-report=html

# 生成JUnit XML报告
pytest tests/crawler/ --junitxml=test-results.xml

# 详细输出
pytest tests/crawler/ -vv --tb=long
```

## 📊 测试数据

### conftest.py 提供的 Fixtures

- **real_urls_config**: 真实的URL配置数据
- **mock_urls_config**: 模拟的URL配置数据
- **sample_jiazi_response_data**: 夹子榜API响应示例
- **sample_page_response_data**: 分类页面API响应示例
- **book_url_test_cases**: URL解析测试用例
- **numeric_field_test_cases**: 数值字段解析测试用例
- **mock_http_client**: 模拟的HTTP客户端
- **mock_data_parser**: 模拟的数据解析器

### 测试标记

- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.network`: 网络测试
- `@pytest.mark.slow`: 慢速测试

## 🔧 测试配置

### 环境变量

- `ENABLE_REAL_NETWORK_TESTS`: 启用真实网络测试 (true/false)

### pytest 配置

pytest.ini 文件包含了：
- 测试标记定义
- 输出格式配置
- 日志配置
- 警告过滤

## 📋 测试覆盖

### 爬虫基础模块 (base.py)
- ✅ 配置管理
- ✅ 数据验证
- ✅ URL工具函数
- ✅ 爬虫统计

### 夹子榜爬虫 (jiazi_crawler.py)
- ✅ 初始化和配置
- ✅ 数据爬取逻辑
- ✅ 错误处理
- ✅ 资源管理

### 分类页面爬虫 (page_crawler.py)
- ✅ URL构建
- ✅ 多频道支持
- ✅ 页面结构处理
- ✅ 频道配置管理

### 数据解析器 (parser.py)
- ✅ 夹子榜数据解析
- ✅ 分类页面数据解析
- ✅ 数值字段处理
- ✅ 异常数据处理

## ⚠️ 注意事项

1. **网络测试**: 真实网络测试会访问晋江文学城的实际API，请：
   - 遵守网站的使用条款
   - 控制请求频率，避免过于频繁
   - 在开发环境中谨慎使用

2. **测试数据**: 示例数据基于真实API响应结构，但包含模拟内容

3. **Mock使用**: 单元测试使用mock避免网络依赖，确保测试稳定性

4. **CI/CD**: 在持续集成中建议跳过网络测试，只在必要时手动运行

## 🐛 故障排除

### 常见问题

1. **ImportError**: 确保Python路径正确，在项目根目录运行测试
2. **网络超时**: 检查网络连接，或禁用网络测试
3. **配置文件缺失**: 确保 `data/urls.json` 文件存在且格式正确

### 调试技巧

```bash
# 启用详细日志
pytest tests/crawler/ -v -s --log-cli-level=DEBUG

# 在第一个失败处停止
pytest tests/crawler/ -x

# 重新运行失败的测试
pytest tests/crawler/ --lf
```

## 📈 性能测试

部分测试包含性能验证：
- HTTP客户端响应时间
- 数据解析效率
- 并发请求处理

## 🔄 持续改进

测试套件会随着爬虫模块的发展持续更新：
- 新增API支持时添加相应测试
- 优化测试数据和用例
- 改进测试覆盖率和质量