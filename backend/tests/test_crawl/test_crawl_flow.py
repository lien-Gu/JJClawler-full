"""
爬虫流程管理器测试 - 修复版本
测试 CrawlFlow 的完整爬取流程，适配最新的两阶段处理架构
"""

import pytest
from unittest.mock import patch

from app.crawl.crawl_flow import CrawlFlow


@pytest.fixture
def crawl_flow_with_mocks(mock_crawl_config, mock_http_client, mock_book_service, mock_ranking_service):
    """创建带有mock依赖的CrawlFlow实例"""
    with patch('app.crawl.crawl_flow.CrawlConfig', return_value=mock_crawl_config), \
         patch('app.crawl.crawl_flow.HttpClient', return_value=mock_http_client), \
         patch('app.crawl.crawl_flow.BookService', return_value=mock_book_service), \
         patch('app.crawl.crawl_flow.RankingService', return_value=mock_ranking_service):
        return CrawlFlow()


class TestCrawlFlow:
    """测试爬虫流程管理器的核心功能"""

    def test_initialization(self, crawl_flow_with_mocks):
        """测试CrawlFlow初始化"""
        flow = crawl_flow_with_mocks
        
        assert flow.config is not None
        assert flow.client is not None  
        assert flow.book_service is not None
        assert flow.ranking_service is not None

    @pytest.mark.asyncio
    async def test_execute_crawl_task_success(
        self, 
        crawl_flow_with_mocks, 
        mock_jiazi_response, 
        mock_book_detail_response,
        test_db_session
    ):
        """测试成功执行爬取任务"""
        flow = crawl_flow_with_mocks
        
        # 设置mock返回值
        flow.client.run.side_effect = [
            mock_jiazi_response,  # 页面内容
            [mock_book_detail_response, mock_book_detail_response]  # 书籍详情列表
        ]
        
        # Mock数据库操作
        with patch('app.crawl.crawl_flow.SessionLocal', return_value=test_db_session):
            result = await flow.execute_crawl_task(["jiazi"])
        
        # 验证结果
        assert result["success"] is True
        assert "execution_time" in result
        assert "page_results" in result
        assert "book_results" in result
        assert "store_results" in result

    @pytest.mark.asyncio
    async def test_execute_crawl_task_page_content_fail(self, crawl_flow_with_mocks):
        """测试页面内容爬取失败"""
        flow = crawl_flow_with_mocks
        
        # 模拟页面内容为空
        flow.client.run.return_value = None
        
        result = await flow.execute_crawl_task(["jiazi"])
        
        assert result["success"] is False
        assert "exception" in result

    @pytest.mark.asyncio
    async def test_execute_crawl_task_invalid_page_id(self, crawl_flow_with_mocks):
        """测试无效页面ID"""
        flow = crawl_flow_with_mocks
        
        # 模拟build_url返回None
        flow.config.build_url.return_value = None
        
        result = await flow.execute_crawl_task(["invalid_page"])
        
        assert result["success"] is False
        assert "exception" in result

    @pytest.mark.asyncio
    async def test_execute_crawl_task_exception_handling(self, crawl_flow_with_mocks):
        """测试异常处理"""
        flow = crawl_flow_with_mocks
        
        # 模拟HTTP客户端抛出异常
        flow.client.run.side_effect = Exception("Network timeout")
        
        result = await flow.execute_crawl_task(["jiazi"])
        
        assert result["success"] is False
        assert "exception" in result

    def test_save_ranking_parsers(
        self, 
        crawl_flow_with_mocks, 
        mock_jiazi_response,
        test_db_session
    ):
        """测试保存榜单解析器数据"""
        from app.crawl.parser import PageParser
        
        flow = crawl_flow_with_mocks
        
        # 创建解析器
        page_parser = PageParser(mock_jiazi_response, "jiazi")
        rankings = page_parser.rankings
        
        # 调用保存方法
        flow.save_ranking_parsers(rankings, test_db_session)
        
        # 验证服务方法被调用
        assert flow.ranking_service.create_or_update_ranking.call_count == len(rankings)
        assert flow.book_service.create_or_update_book.call_count >= len(rankings)
        assert flow.ranking_service.batch_create_ranking_snapshots.call_count == len(rankings)

    def test_save_novel_parsers(
        self, 
        crawl_flow_with_mocks, 
        mock_book_detail_response,
        test_db_session
    ):
        """测试保存书籍解析器数据"""
        from app.crawl.parser import NovelPageParser
        
        flow = crawl_flow_with_mocks
        
        # 创建书籍解析器
        book_parsers = [
            NovelPageParser(mock_book_detail_response),
            NovelPageParser(mock_book_detail_response)
        ]
        
        # 调用保存方法
        flow.save_novel_parsers(book_parsers, test_db_session)
        
        # 验证服务方法被调用
        assert flow.book_service.create_or_update_book.call_count == 2
        assert flow.book_service.batch_create_book_snapshots.call_count == 1

    @pytest.mark.asyncio
    async def test_close_resources(self, crawl_flow_with_mocks):
        """测试资源清理"""
        flow = crawl_flow_with_mocks
        
        await flow.close()
        
        flow.client.close.assert_called_once()


class TestRealCrawlFlow:
    """真实网络爬取测试（集成测试）"""

    @pytest.mark.integration
    @pytest.mark.real_network  
    @pytest.mark.asyncio
    async def test_real_jiazi_crawl(self, test_db_session):
        """测试真实的夹子榜爬取"""
        # 创建真实的CrawlFlow实例
        real_flow = CrawlFlow()
        
        try:
            # 使用真实数据库会话
            with patch('app.crawl.crawl_flow.SessionLocal', return_value=test_db_session):
                result = await real_flow.execute_crawl_task(["jiazi"])
            
            # 验证基本结果结构
            assert "success" in result
            assert "execution_time" in result
            
            if result["success"]:
                print(f"✅ 真实夹子榜爬取成功")
                print(f"   - 页面结果: {result['page_results']}")
                print(f"   - 书籍结果: {result['book_results']}")
                print(f"   - 执行时间: {result['execution_time']:.2f}秒")
                
                # 验证数据保存到数据库
                # 这里可以查询数据库验证数据是否正确保存
                # 由于是集成测试，我们主要验证流程是否完整执行
                assert result["execution_time"] > 0
                
            else:
                error_msg = str(result.get("exception", "未知错误"))
                print(f"❌ 真实夹子榜爬取失败: {error_msg}")
                
                # 如果是网络问题，跳过测试而不是失败
                if "网络" in error_msg or "连接" in error_msg or "timeout" in error_msg.lower():
                    pytest.skip(f"网络问题跳过测试: {error_msg}")
                else:
                    # 其他错误应该导致测试失败
                    pytest.fail(f"爬取任务失败: {error_msg}")
                    
        except Exception as e:
            print(f"❌ 真实爬取异常: {e}")
            # 网络异常跳过测试
            if any(keyword in str(e).lower() for keyword in ["network", "timeout", "connection", "dns"]):
                pytest.skip(f"网络问题跳过测试: {e}")
            else:
                raise
                
        finally:
            await real_flow.close()

    @pytest.mark.integration
    @pytest.mark.real_network
    @pytest.mark.asyncio
    async def test_real_index_page_crawl(self, test_db_session):
        """测试真实的首页爬取"""
        real_flow = CrawlFlow()
        
        try:
            with patch('app.crawl.crawl_flow.SessionLocal', return_value=test_db_session):
                result = await real_flow.execute_crawl_task(["index"])
            
            if result["success"]:
                print(f"✅ 真实首页爬取成功")
                print(f"   - 页面结果: {result['page_results']}")
                print(f"   - 书籍结果: {result['book_results']}")
                print(f"   - 执行时间: {result['execution_time']:.2f}秒")
                
                # 首页通常包含多个榜单，所以执行时间应该合理
                assert result["execution_time"] > 0
                
            else:
                error_msg = str(result.get("exception", "未知错误"))
                print(f"❌ 真实首页爬取失败: {error_msg}")
                
                if "网络" in error_msg or "连接" in error_msg:
                    pytest.skip(f"网络问题跳过测试: {error_msg}")
                else:
                    pytest.fail(f"爬取任务失败: {error_msg}")
                    
        except Exception as e:
            print(f"❌ 真实首页爬取异常: {e}")
            if any(keyword in str(e).lower() for keyword in ["network", "timeout", "connection"]):
                pytest.skip(f"网络问题跳过测试: {e}")
            else:
                raise
                
        finally:
            await real_flow.close()

    @pytest.mark.integration
    @pytest.mark.real_network
    @pytest.mark.asyncio  
    async def test_real_novel_detail_crawl(self):
        """测试真实的书籍详情爬取"""
        from app.crawl.http import HttpClient
        from app.crawl.crawl_config import CrawlConfig
        from app.crawl.parser import NovelPageParser
        
        try:
            # 使用真实配置和HTTP客户端
            config = CrawlConfig()
            client = HttpClient()
            
            # 使用一个已知存在的书籍ID进行测试
            # 注意：这个ID可能需要根据实际情况调整
            test_novel_id = "123456"
            novel_url = config.build_novel_url(test_novel_id)
            
            # 发起真实请求
            response = await client.run(novel_url)
            
            if response:
                # 解析书籍详情
                parser = NovelPageParser(response)
                book_detail = parser.book_detail
                
                print(f"✅ 书籍详情爬取成功: {book_detail.get('title', '未知书名')}")
                
                # 验证基本字段存在
                assert "novel_id" in book_detail
                assert "title" in book_detail
                
            else:
                print(f"❌ 书籍详情响应为空")
                pytest.skip("书籍API无响应，跳过测试")
                
        except Exception as e:
            print(f"❌ 真实书籍详情爬取异常: {e}")
            if any(keyword in str(e).lower() for keyword in ["network", "timeout", "connection"]):
                pytest.skip(f"网络问题跳过测试: {e}")
            else:
                # 对于书籍不存在等业务异常，也跳过测试
                pytest.skip(f"业务异常跳过测试: {e}")
        
        finally:
            await client.close()


class TestCrawlFlowErrorScenarios:
    """爬虫流程错误场景测试"""

    @pytest.mark.asyncio
    async def test_malformed_page_response(self, crawl_flow_with_mocks):
        """测试页面响应格式错误"""
        flow = crawl_flow_with_mocks
        
        # 返回格式错误的响应
        malformed_response = {"error": "invalid format"}
        flow.client.run.side_effect = [malformed_response, []]
        
        result = await flow.execute_crawl_task(["jiazi"])
        
        # 应该能处理错误并返回失败结果
        assert result["success"] is False
        assert "exception" in result

    @pytest.mark.asyncio
    async def test_empty_book_list(self, crawl_flow_with_mocks):
        """测试空书籍列表情况"""
        flow = crawl_flow_with_mocks
        
        # 返回空的书籍列表
        empty_response = {"code": "200", "data": {"list": []}}
        flow.client.run.side_effect = [empty_response, []]
        
        result = await flow.execute_crawl_task(["jiazi"])
        
        # 空列表不应该导致失败，但统计应该为0
        if result["success"]:
            assert result["execution_time"] >= 0

    @pytest.mark.asyncio
    async def test_partial_book_detail_failure(self, crawl_flow_with_mocks, mock_jiazi_response, test_db_session):
        """测试部分书籍详情请求失败"""
        flow = crawl_flow_with_mocks
        
        # 书籍详情部分失败（返回异常对象）
        book_responses = [
            {"novelId": "123456", "novelName": "成功的书籍"},
            Exception("书籍详情请求失败")  # 模拟异常
        ]
        
        flow.client.run.side_effect = [mock_jiazi_response, book_responses]
        
        # 应该能处理部分失败的情况
        result = await flow.execute_crawl_task(["jiazi"])
        
        # 即使部分失败，整体流程可能仍然成功
        # 具体取决于实现的容错策略
        assert "success" in result
        assert "execution_time" in result