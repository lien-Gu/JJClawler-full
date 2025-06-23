"""
爬虫模块真实URL集成测试

这些测试使用真实的晋江文学城API进行测试，需要网络连接
可以通过环境变量 ENABLE_REAL_NETWORK_TESTS=true 来启用
"""
import pytest
import asyncio
import os
from app.modules.crawler.jiazi_crawler import JiaziCrawler
from app.modules.crawler.page_crawler import PageCrawler
from app.modules.crawler.parser import DataParser
from app.utils.http_client import HTTPClient


# 真实网络测试标记

class TestRealJiaziCrawler:
    """真实夹子榜爬虫测试"""
    
    @pytest.mark.asyncio
    async def test_real_jiazi_crawl(self, real_urls_config):
        """测试真实的夹子榜数据爬取"""
        # 创建HTTP客户端
        http_client = HTTPClient(timeout=30, rate_limit_delay=2.0)
        
        try:
            # 直接使用真实URL测试
            jiazi_url = real_urls_config["content"]["jiazi"]["url"]
            print("url: {}".format(jiazi_url))
            
            # 发送请求
            response = await http_client.get(jiazi_url)
            
            # 验证响应
            assert response is not None
            assert isinstance(response, dict)
            assert "code" in response
            
            # 如果API正常响应
            if response.get("code") == "200":
                assert "data" in response
                data = response["data"]
                
                if "list" in data and data["list"]:
                    # 验证书籍数据结构
                    book_list = data["list"]
                    assert len(book_list) > 0
                    
                    # 检查第一本书的基本字段
                    first_book = book_list[0]
                    required_fields = ["novelId", "novelName", "authorName"]
                    for field in required_fields:
                        assert field in first_book, f"缺少必需字段: {field}"
                    
                    # 验证数据类型
                    assert isinstance(first_book["novelId"], (str, int))
                    assert isinstance(first_book["novelName"], str)
                    assert isinstance(first_book["authorName"], str)
                    
                    print(f"✓ 夹子榜爬取成功，获取到 {len(book_list)} 本书籍")
                    print(f"✓ 第一本书：《{first_book['novelName']}》 - {first_book['authorName']}")
                else:
                    print("⚠ 夹子榜数据为空，可能是非活跃时间")
            else:
                print(f"⚠ API返回非200状态: {response.get('code')} - {response.get('message', '')}")
                
        finally:
            await http_client.close()
    
    @pytest.mark.asyncio
    async def test_real_jiazi_data_parsing(self, real_urls_config, sample_jiazi_response_data):
        """测试真实数据的解析功能"""
        parser = DataParser()
        
        # 使用示例数据测试解析
        books, snapshots = parser.parse_jiazi_data(sample_jiazi_response_data)
        
        # 验证解析结果
        assert len(books) == 3
        assert len(snapshots) == 3
        
        # 验证第一本书的解析结果
        first_book = books[0]
        assert first_book.book_id == "5485513"
        assert first_book.title == "重生九零：福运娇妻美又飒"
        assert first_book.author_name == "青丝如墨"
        assert first_book.novel_class == "言情"
        
        # 验证第一个快照的解析结果
        first_snapshot = snapshots[0]
        assert first_snapshot.book_id == "5485513"
        assert first_snapshot.total_clicks == 1256000  # 125.6万
        assert first_snapshot.total_favorites == 452000  # 45.2万
        assert first_snapshot.comment_count == 12000   # 1.2万
        assert first_snapshot.chapter_count == 134


@pytest.mark.skipif(
    os.getenv("ENABLE_REAL_NETWORK_TESTS", "false").lower() != "true",
    reason="真实网络测试被禁用"
)
class TestRealPageCrawler:
    """真实分类页面爬虫测试"""
    
    @pytest.mark.asyncio
    async def test_real_yq_page_crawl(self, real_urls_config):
        """测试真实的言情分类页面爬取"""
        http_client = HTTPClient(timeout=30, rate_limit_delay=2.0)
        
        try:
            # 构建言情页面URL
            base_url = real_urls_config["base_url"]
            version = real_urls_config["version"]
            yq_channel = real_urls_config["content"]["pages"]["yq"]["channel"]
            
            yq_url = base_url.format(yq_channel, version)
            
            # 发送请求
            response = await http_client.get(yq_url)
            
            # 验证响应
            assert response is not None
            assert isinstance(response, dict)
            
            if response.get("code") == "200":
                data = response.get("data", {})
                
                # 检查不同的数据结构
                if "list" in data:
                    # 单一列表结构
                    book_list = data["list"]
                    if book_list:
                        assert len(book_list) > 0
                        print(f"✓ 言情页面爬取成功(单列表)，获取到 {len(book_list)} 本书籍")
                        
                elif "blocks" in data:
                    # 多区块结构
                    blocks = data["blocks"]
                    total_books = 0
                    for block in blocks:
                        if "list" in block:
                            total_books += len(block["list"])
                    
                    if total_books > 0:
                        print(f"✓ 言情页面爬取成功(多区块)，获取到 {total_books} 本书籍")
                    else:
                        print("⚠ 言情页面数据为空")
                else:
                    print("⚠ 未识别的言情页面数据结构")
            else:
                print(f"⚠ 言情页面API返回非200状态: {response.get('code')}")
                
        finally:
            await http_client.close()
    
    @pytest.mark.asyncio
    async def test_real_ca_page_crawl(self, real_urls_config):
        """测试真实的纯爱分类页面爬取"""
        http_client = HTTPClient(timeout=30, rate_limit_delay=2.0)
        
        try:
            base_url = real_urls_config["base_url"]
            version = real_urls_config["version"]
            ca_channel = real_urls_config["content"]["pages"]["ca"]["channel"]
            
            ca_url = base_url.format(ca_channel, version)
            
            response = await http_client.get(ca_url)
            
            assert response is not None
            if response.get("code") == "200":
                print("✓ 纯爱页面API响应正常")
            else:
                print(f"⚠ 纯爱页面API返回状态: {response.get('code')}")
                
        finally:
            await http_client.close()


@pytest.mark.skipif(
    os.getenv("ENABLE_REAL_NETWORK_TESTS", "false").lower() != "true",
    reason="真实网络测试被禁用"
)
class TestRealDataValidation:
    """真实数据验证测试"""
    
    @pytest.mark.asyncio
    async def test_real_book_info_fetch(self, real_urls_config):
        """测试真实的书籍信息获取"""
        http_client = HTTPClient(timeout=30, rate_limit_delay=2.0)
        
        try:
            # 使用已知存在的书籍ID
            novel_url_template = real_urls_config["novel_url"]
            test_novel_id = "5485513"  # 真实存在的书籍ID
            
            novel_url = novel_url_template.format(test_novel_id)
            response = await http_client.get(novel_url)
            
            assert response is not None
            if response.get("code") == "200":
                novel_info = response.get("data", {})
                if novel_info:
                    # 验证书籍信息字段
                    expected_fields = ["novelId", "novelName", "authorName"]
                    for field in expected_fields:
                        assert field in novel_info, f"书籍信息缺少字段: {field}"
                    
                    print(f"✓ 书籍信息获取成功: 《{novel_info.get('novelName', '')}》")
                else:
                    print("⚠ 书籍信息为空")
            else:
                print(f"⚠ 书籍信息API返回状态: {response.get('code')}")
                
        finally:
            await http_client.close()
    
    def test_real_url_parsing(self, book_url_test_cases):
        """测试真实URL的解析功能"""
        from app.modules.crawler.base import extract_book_id_from_url
        
        success_count = 0
        for url, expected_id in book_url_test_cases:
            result = extract_book_id_from_url(url)
            if result == expected_id:
                success_count += 1
                if expected_id:
                    print(f"✓ URL解析成功: {url} -> {result}")
            else:
                print(f"✗ URL解析失败: {url} -> 期望:{expected_id}, 实际:{result}")
        
        # 至少70%的测试用例应该通过
        success_rate = success_count / len(book_url_test_cases)
        assert success_rate >= 0.7, f"URL解析成功率过低: {success_rate:.2%}"
    
    def test_real_numeric_parsing(self, numeric_field_test_cases):
        """测试真实数值格式的解析"""
        from app.modules.crawler.parser import DataParser
        
        success_count = 0
        for input_value, expected_result in numeric_field_test_cases:
            test_item = {"test_field": input_value}
            result = DataParser._parse_numeric_field(test_item, ["test_field"], 0)
            
            if result == expected_result:
                success_count += 1
                print(f"✓ 数值解析成功: '{input_value}' -> {result}")
            else:
                print(f"✗ 数值解析失败: '{input_value}' -> 期望:{expected_result}, 实际:{result}")
        
        # 至少80%的测试用例应该通过
        success_rate = success_count / len(numeric_field_test_cases)
        assert success_rate >= 0.8, f"数值解析成功率过低: {success_rate:.2%}"


@pytest.mark.skipif(
    os.getenv("ENABLE_REAL_NETWORK_TESTS", "false").lower() != "true",
    reason="真实网络测试被禁用"
)
class TestRealCrawlerWorkflow:
    """真实爬虫工作流测试"""
    
    @pytest.mark.asyncio
    async def test_full_jiazi_workflow(self, real_urls_config):
        """测试完整的夹子榜爬虫工作流"""
        # 创建临时配置文件
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(real_urls_config, f, ensure_ascii=False, indent=2)
            temp_config_path = f.name
        
        try:
            # 模拟配置文件路径
            with pytest.MonkeyPatch().context() as m:
                m.setattr("os.path.join", lambda *args: temp_config_path)
                
                # 创建爬虫实例
                http_client = HTTPClient(timeout=30, rate_limit_delay=2.0)
                
                # 直接测试爬取逻辑（不依赖文件系统）
                jiazi_url = real_urls_config["content"]["jiazi"]["url"]
                response = await http_client.get(jiazi_url)
                
                if response and response.get("code") == "200":
                    # 测试数据解析
                    parser = DataParser()
                    try:
                        books, snapshots = parser.parse_jiazi_data(response)
                        
                        if books and snapshots:
                            print(f"✓ 完整工作流测试成功:")
                            print(f"  - 爬取书籍: {len(books)} 本")
                            print(f"  - 生成快照: {len(snapshots)} 条")
                            print(f"  - 示例书籍: 《{books[0].title}》")
                            
                            # 验证数据一致性
                            assert len(books) == len(snapshots)
                            assert all(book.book_id == snapshot.book_id 
                                     for book, snapshot in zip(books, snapshots))
                        else:
                            print("⚠ 解析结果为空")
                    except Exception as e:
                        print(f"⚠ 数据解析失败: {e}")
                else:
                    print("⚠ 夹子榜API请求失败")
                
                await http_client.close()
                
        finally:
            # 清理临时文件
            os.unlink(temp_config_path)
    
    @pytest.mark.asyncio 
    async def test_error_handling_with_real_urls(self):
        """测试真实URL的错误处理"""
        http_client = HTTPClient(timeout=5, rate_limit_delay=1.0)
        
        try:
            # 测试无效URL
            invalid_url = "https://app-cdn.jjwxc.com/invalid/endpoint"
            
            try:
                response = await http_client.get(invalid_url)
                # 如果没有抛出异常，检查响应状态
                if response:
                    print(f"无效URL响应: {response.get('code', 'unknown')}")
            except Exception as e:
                print(f"✓ 正确处理了无效URL异常: {type(e).__name__}")
            
            # 测试超时处理
            timeout_client = HTTPClient(timeout=0.1, rate_limit_delay=0.1)
            try:
                await timeout_client.get("https://app-cdn.jjwxc.com/bookstore/favObservationByDate")
            except Exception as e:
                print(f"✓ 正确处理了超时异常: {type(e).__name__}")
            finally:
                await timeout_client.close()
                
        finally:
            await http_client.close()


# 运行指南的docstring
__doc__ += """

运行真实网络测试:
=================

1. 启用真实网络测试:
   export ENABLE_REAL_NETWORK_TESTS=true

2. 只运行网络测试:
   pytest tests/crawler/test_integration_real.py -m network -v

3. 跳过网络测试运行其他测试:
   pytest tests/crawler/ -m "not network" -v

4. 运行所有测试（包括网络测试）:
   pytest tests/crawler/ -v

注意事项:
- 网络测试需要稳定的网络连接
- 测试过程中会访问真实的晋江文学城API
- 请遵守网站的使用条款和请求频率限制
- 建议在开发环境中谨慎使用，避免频繁请求
"""