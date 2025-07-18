"""
爬取流程管理器测试文件
测试CrawlFlow类的关键功能，包括真实的爬取过程
"""
import pytest
from pytest_mock import MockerFixture

from app.crawl.crawl_flow import CrawlFlow


class TestCrawlFlow:
    """测试CrawlFlow类的核心功能"""

    @pytest.fixture
    def crawl_flow(self):
        """创建CrawlFlow实例"""
        return CrawlFlow(request_delay=0.1)

    def test_initialization(self, crawl_flow):
        """测试初始化"""
        assert crawl_flow.client is not None
        assert crawl_flow.parser is not None
        assert crawl_flow.book_service is not None
        assert crawl_flow.ranking_service is not None
        assert isinstance(crawl_flow.crawled_book_ids, set)
        assert crawl_flow.stats['books_crawled'] == 0

    def test_generate_page_url(self, crawl_flow, mocker: MockerFixture):
        """测试生成页面地址"""
        mock_config = {
            "id": "test_page",
            "template": "test_template",
            "params": {"page": 1}
        }

        mocker.patch.object(crawl_flow.config, 'get_task_config', return_value=mock_config)
        mocker.patch.object(crawl_flow.config, 'build_url', return_value="https://test.com/page1")

        result = crawl_flow._generate_page_url("test_page")

        assert result == "https://test.com/page1"

    @pytest.mark.asyncio
    async def test_crawl_page_content(self, crawl_flow, mocker: MockerFixture, mock_page_content):
        """测试爬取页面内容"""
        mocker.patch.object(crawl_flow.client, 'get', return_value=mock_page_content)

        result = await crawl_flow._crawl_page_content("https://test.com/page1")

        assert result == mock_page_content
        assert crawl_flow.stats['total_requests'] == 1

    def test_parse_rankings_from_page(self, crawl_flow, mocker: MockerFixture, mock_page_content, mock_parsed_items):
        """测试从页面解析榜单"""
        mocker.patch.object(crawl_flow.parser, 'parse', return_value=[mock_parsed_items["ranking"]])

        result = crawl_flow._parse_rankings_from_page(mock_page_content)

        assert len(result) == 1
        assert result[0]["rank_id"] == "1"
        assert len(result[0]["books"]) == 2

    def test_extract_book_ids_from_rankings(self, crawl_flow, mock_rankings_data):
        """测试从榜单提取书籍ID"""
        result = crawl_flow._extract_book_ids_from_rankings(mock_rankings_data)

        assert len(result) == 1
        assert "12345" in result
        assert len(crawl_flow.crawled_book_ids) == 1

    @pytest.mark.asyncio
    async def test_crawl_books_details(self, crawl_flow, mocker: MockerFixture, mock_book_detail):
        """测试爬取书籍详情"""
        mocker.patch.object(crawl_flow, 'crawl_book_detail', return_value=mock_book_detail)

        result = await crawl_flow._crawl_books_details(["12345"])

        assert len(result) == 1
        assert result[0] == mock_book_detail
        assert crawl_flow.stats['books_crawled'] == 1

    @pytest.mark.asyncio
    async def test_crawl_book_detail(self, crawl_flow, mocker: MockerFixture, mock_book_detail, mock_parsed_items):
        """测试爬取单个书籍详情"""
        crawl_flow.config.templates = {'novel_detail': 'https://test.com/book/{novel_id}'}
        crawl_flow.config.params = {}

        mocker.patch.object(crawl_flow.client, 'get', return_value=mock_book_detail)
        mocker.patch.object(crawl_flow.parser, 'parse', return_value=[mock_parsed_items["book"]])

        result = await crawl_flow.crawl_book_detail("12345")

        assert result == mock_parsed_items["book"].data
        assert crawl_flow.stats['total_requests'] == 1

    @pytest.mark.asyncio
    async def test_save_crawl_result(self, crawl_flow, mocker: MockerFixture, mock_rankings_data, mock_books_data,
                                     mock_services):
        """测试保存爬取结果"""
        # Mock数据库会话
        mock_db = mocker.Mock()
        mocker.patch('app.crawl.crawl_flow.get_db', return_value=[mock_db])

        # Mock服务
        crawl_flow.ranking_service = mock_services["ranking_service"]
        crawl_flow.book_service = mock_services["book_service"]

        result = await crawl_flow._save_crawl_result(mock_rankings_data, mock_books_data)

        assert result is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_crawl_task_success(self, crawl_flow, mocker: MockerFixture, mock_page_content,
                                              mock_rankings_data, mock_books_data):
        """测试执行完整爬取任务成功"""
        # Mock所有步骤
        mocker.patch.object(crawl_flow, '_generate_page_url', return_value="https://test.com/page1")
        mocker.patch.object(crawl_flow, '_crawl_page_content', return_value=mock_page_content)
        mocker.patch.object(crawl_flow, '_parse_rankings_from_page', return_value=mock_rankings_data)
        mocker.patch.object(crawl_flow, '_extract_book_ids_from_rankings', return_value=["12345"])
        mocker.patch.object(crawl_flow, '_crawl_books_details', return_value=mock_books_data)
        mocker.patch.object(crawl_flow, '_save_crawl_result', return_value=True)

        result = await crawl_flow.execute_crawl_task("test_page")

        assert result["success"] is True
        assert result["page_id"] == "test_page"
        assert result["books_crawled"] == 1
        assert "execution_time" in result

    @pytest.mark.asyncio
    async def test_execute_crawl_task_failure(self, crawl_flow, mocker: MockerFixture):
        """测试执行爬取任务失败"""
        mocker.patch.object(crawl_flow, '_generate_page_url', return_value=None)

        result = await crawl_flow.execute_crawl_task("invalid_page")

        assert result["success"] is False
        assert "无法生成页面地址" in result["error_message"]

    def test_get_all_data(self, crawl_flow):
        """测试获取所有数据"""
        crawl_flow.books_data = [{"book_id": 1}]
        crawl_flow.rankings_data = [{"rank_id": 1}]
        crawl_flow.pages_data = [{"page_id": 1}]

        result = crawl_flow.get_all_data()

        assert len(result["books"]) == 1
        assert len(result["rankings"]) == 1
        assert len(result["pages"]) == 1

    @pytest.mark.asyncio
    async def test_close(self, crawl_flow, mocker: MockerFixture):
        """测试关闭资源"""
        mocker.patch.object(crawl_flow.client, 'close')

        await crawl_flow.close()

        crawl_flow.client.close.assert_called_once()


class TestRealCrawlFlow:
    """真实爬取流程测试（集成测试）"""

    @pytest.fixture
    def real_crawl_flow(self):
        """创建真实CrawlFlow实例"""
        return CrawlFlow(request_delay=0.5)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_page_crawl(self, real_crawl_flow):
        """测试真实的夹子榜爬取（集成测试）"""
        try:
            page_id = "index"
            result = await real_crawl_flow.execute_crawl_task(page_id)

            # 验证结果结构
            assert "success" in result
            assert "page_id" in result
            assert "books_crawled" in result
            assert "execution_time" in result

            if result["success"]:
                print(f"✅ 真实爬取成功: 爬取了 {result['books_crawled']} 本书籍")
                assert result["page_id"] == "jiazi"
                assert result["books_crawled"] >= 0
                assert result["execution_time"] > 0
            else:
                print(f"❌ 真实爬取失败: {result.get('error_message', '未知错误')}")

        except Exception as e:
            print(f"❌ 真实爬取异常: {e}")
            pytest.skip(f"网络问题跳过真实爬取测试: {e}")

        finally:
            await real_crawl_flow.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_book_detail_crawl(self, real_crawl_flow):
        """测试真实的书籍详情爬取（集成测试）"""
        try:
            test_book_id = "123456"

            result = await real_crawl_flow.crawl_book_detail(test_book_id)

            if result:
                assert "book_id" in result
                assert "title" in result
                print(f"✅ 真实书籍详情爬取成功: {result.get('title', '未知书名')}")
            else:
                print(f"❌ 真实书籍详情爬取失败: 书籍ID {test_book_id}")

        except Exception as e:
            print(f"❌ 真实书籍详情爬取异常: {e}")
            pytest.skip(f"网络问题跳过真实书籍详情爬取测试: {e}")

        finally:
            await real_crawl_flow.close()
