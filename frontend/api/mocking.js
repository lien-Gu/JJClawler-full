/**
 * 模拟数据管理器
 * 集中管理所有模拟数据和模拟数据生成逻辑
 */

// 榜单名称模拟数据
const MOCK_RANKING_NAMES = [
  '完结榜', '收藏榜', '点击榜', '推荐榜', '评分榜', 
  '新书榜', '月度榜', '季度榜', '年度榜', '热门榜',
  '原创榜', '同人榜', '现代榜', '古代榜', '幻想榜',
  '都市榜', '校园榜', '职场榜', '军事榜', '历史榜'
];

// 分类对应的榜单类型
const CATEGORY_RANKING_TYPES = {
  'index': '书城',
  'yq': '言情',
  'ca': '纯爱', 
  'ys': '衍生',
  'nocp_plus': '无CP+',
  'bh': '百合',
  'jiazi': '夹子'
};

class MockingManager {
  /**
   * 模拟网络延迟
   */
  async simulateNetworkDelay() {
    const delay = 300 + Math.random() * 700;
    await new Promise(resolve => setTimeout(resolve, delay));
  }

  /**
   * 生成模拟榜单列表数据
   */
  generateMockRankings(pageId, page = 1, size = 20) {
    const categoryName = CATEGORY_RANKING_TYPES[pageId] || pageId;
    const startIndex = (page - 1) * size;
    
    const mockRankings = Array.from({ length: size }, (_, index) => {
      const globalIndex = startIndex + index;
      const rankingName = MOCK_RANKING_NAMES[globalIndex % MOCK_RANKING_NAMES.length];
      
      return {
        id: `ranking_${pageId}_${page}_${index + 1}`,
        channel_name: categoryName,
        sub_channel_name: rankingName,
        page_id: pageId,
        rank_group_type: '模拟数据',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
    });
    
    return {
      success: true,
      data: {
        data_list: mockRankings,
        page: page,
        size: size,
        total_pages: 3, // 模拟3页数据
        total_count: size * 3
      }
    };
  }

  /**
   * 生成模拟书籍数据（用于夹子榜单）
   */
  generateMockBooks(page = 1, size = 20) {
    const startIndex = (page - 1) * size;
    
    const mockBooks = Array.from({ length: size }, (_, index) => {
      const globalIndex = startIndex + index;
      
      return {
        id: `book_${globalIndex + 1}`,
        title: `测试书籍${globalIndex + 1}`,
        author: `作者${globalIndex + 1}`,
        collectCount: Math.floor(Math.random() * 10000) + 100,
        wordCount: Math.floor(Math.random() * 500000) + 50000,
        status: Math.random() > 0.5 ? '连载中' : '已完结',
        updateTime: new Date().toISOString()
      };
    });
    
    return {
      success: true,
      data: {
        books: mockBooks,
        total: size * 3,
        page: page,
        size: size
      }
    };
  }

  /**
   * 生成模拟概览统计数据
   */
  generateMockOverviewStats() {
    return {
      success: true,
      data: {
        total_books: Math.floor(Math.random() * 10000) + 10000,
        total_rankings: Math.floor(Math.random() * 50) + 40,
        total_authors: Math.floor(Math.random() * 5000) + 5000,
        recent_updates: Math.floor(Math.random() * 500) + 100,
        hot_rankings: this.generateMockRankings('index', 1, 5).data.data_list
      }
    };
  }

  /**
   * 生成模拟书籍详情数据
   */
  generateMockBookDetail(bookId) {
    return {
      success: true,
      data: {
        id: bookId,
        title: `测试书籍${bookId}`,
        author: `作者${bookId}`,
        description: '这是一本测试书籍的详细描述...',
        collectCount: Math.floor(Math.random() * 10000) + 100,
        wordCount: Math.floor(Math.random() * 500000) + 50000,
        status: Math.random() > 0.5 ? '连载中' : '已完结',
        tags: ['测试', '模拟数据'],
        updateTime: new Date().toISOString()
      }
    };
  }

  /**
   * 根据API路径返回对应的模拟数据
   */
  async getMockDataByPath(path, params = {}) {
    await this.simulateNetworkDelay();
    
    // 榜单列表
    if (path === '/rankings/') {
      const { page_id = 'index', page = 1, size = 20 } = params;
      return this.generateMockRankings(page_id, parseInt(page), parseInt(size));
    }
    
    // 夹子榜单详情
    if (path.startsWith('/rankingsdetail/day/')) {
      const { page = 1, size = 20 } = params;
      return this.generateMockBooks(parseInt(page), parseInt(size));
    }
    
    // 概览统计
    if (path === '/stats/overview') {
      return this.generateMockOverviewStats();
    }
    
    // 书籍详情
    if (path.startsWith('/books/') && !path.includes('rankings')) {
      const bookId = path.replace('/books/', '');
      return this.generateMockBookDetail(bookId);
    }
    
    // 书籍排名历史
    if (path.includes('/books/') && path.includes('/rankings')) {
      return {
        success: true,
        data: {
          rankings: [],
          total: 0
        }
      };
    }
    
    // 默认返回空数据
    return {
      success: true,
      data: null,
      message: '暂无数据'
    };
  }
}

// 创建单例实例
const mockingManager = new MockingManager();
export default mockingManager;