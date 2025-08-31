/**
 * 统一请求管理器
 * 支持环境切换和模拟数据
 */

import configData from '@/data/config.json'
import mockData from '@/data/fake_data.json'
import mockingManager from './mocking.js'

class RequestManager {
  constructor() {
    this.currentEnv = uni.getStorageSync('currentEnv') || 'dev'
    this.config = configData.environments[this.currentEnv]
  }

  /**
   * 获取模拟数据
   */
  async getMockData(url) {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 700))
    
    // 根据URL路径返回对应的模拟数据
    if (url.includes('/books/')) {
      if (url.includes('/snapshots')) {
        return { success: true, data: mockData.books?.snapshots || [] }
      }
      if (url.includes('/rankings')) {
        return { success: true, data: mockData.books?.rankings || [] }
      }
      if (url.match(/\/books\/\d+$/)) {
        return { success: true, data: mockData.books?.detail || {} }
      }
      return { success: true, data: mockData.books?.list || [] }
    }
    
    if (url.includes('/rankings')) {
      if (url.includes('/history')) {
        return { success: true, data: mockData.rankings?.history || {} }
      }
      if (url.includes('detail')) {
        return { success: true, data: mockData.rankings?.detail || {} }
      }
      return { success: true, data: mockData.rankings?.list || [] }
    }
    
    if (url.includes('/stats') || url.includes('reports')) {
      return { success: true, data: mockData.stats?.overview || {} }
    }
    
    // 默认返回空数据
    return { success: true, data: null }
  }

  /**
   * 统一GET请求方法
   */
  async get(url, params = {}) {
    // 更新当前环境配置
    this.currentEnv = uni.getStorageSync('currentEnv') || 'dev'
      console.log(`当前环境：${this.currentEnv}`)
    this.config = configData.environments[this.currentEnv]
    
    // 如果是测试环境，使用模拟数据
    if (this.config.useLocalData) {
      return await this.getMockData(url)
    }
    
    // 构建查询参数
    const queryString = Object.keys(params)
      .filter(key => params[key] !== undefined && params[key] !== null)
      .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
      .join('&')
    
    const fullUrl = queryString ? `${url}${url.includes('?') ? '&' : '?'}${queryString}` : url
    
    // 真实API请求
    return new Promise((resolve, reject) => {
      uni.request({
        url: this.config.baseURL + fullUrl,
        method: 'GET',
        header: {
          'Content-Type': 'application/json'
        },
        timeout: 10000,
        success: (response) => {
          if (response.statusCode === 200) {
            resolve(response.data)
          } else {
            reject(new Error(`HTTP ${response.statusCode}`))
          }
        },
        fail: (error) => {
          console.error('请求失败:', error)
          reject(error)
        }
      })
    })
  }

  // ========== 业务API方法 ==========

  /**
   * 获取概览统计数据
   */
  async getOverviewStats() {
    try {
      return await this.get('/stats/overview')
    } catch (error) {
      // 如果API失败，返回模拟数据
      console.warn('概览统计API失败，使用模拟数据:', error.message)
      return {
        success: true,
        data: {
          total_books: 12450,
          total_rankings: 48,
          total_authors: 8900,
          recent_updates: 234
        }
      }
    }
  }

  /**
   * 获取书籍详情
   */
  async getBookDetail(bookId) {
    return await this.get(`/books/${bookId}`)
  }

  /**
   * 获取书籍排名历史
   */
  async getBookRankings(bookId, params = {}) {
    return await this.get(`/books/${bookId}/rankings`, params)
  }

  /**
   * 获取书籍快照
   */
  async getBookSnapshots(bookId, params = {}) {
    return await this.get(`/books/${bookId}/snapshots`, params)
  }

  /**
   * 格式化榜单名称
   */
  formatRankingName(channelName, subChannelName) {
    if (channelName && subChannelName) {
      return `${channelName} - ${subChannelName}`;
    } else if (channelName) {
      return channelName;
    } else if (subChannelName) {
      return subChannelName;
    } else {
      return '未知榜单';
    }
  }

  /**
   * 获取排行榜列表
   * 包含完整的数据处理逻辑
   */
  async getRankingsList(params = {}) {
    try {
      const response = await this.get('/rankings/', params);
      console.log('榜单列表API响应:', response);
      
      if (response && response.success && response.data) {
        const responseData = response.data;
        console.log('responseData结构:', JSON.stringify(responseData, null, 2));
        
        // 获取榜单列表数据
        if (responseData.data_list && Array.isArray(responseData.data_list)) {
          console.log(`找到data_list数组，长度: ${responseData.data_list.length}`);
          
          if (responseData.data_list.length > 0) {
            const rankingsData = responseData.data_list.map(item => ({
              id: item.id,
              name: this.formatRankingName(item.channel_name, item.sub_channel_name),
              channel_name: item.channel_name || '',
              sub_channel_name: item.sub_channel_name || '',
              page_id: item.page_id,
              rank_group_type: item.rank_group_type || '其他',
              description: `${item.rank_group_type || '其他'} - ${item.page_id}`,
              isBook: false
            }));
            
            console.log(`成功转换 ${rankingsData.length} 个榜单项目`);
            return {
              success: true,
              data: rankingsData,
              totalPages: responseData.total_pages || 1
            };
          } else {
            console.warn('data_list数组为空，使用模拟数据');
            return await this.getMockRankingsListFallback(params);
          }
        } else {
          console.warn('responseData中没有找到data_list数组，使用模拟数据');
          return await this.getMockRankingsListFallback(params);
        }
      } else {
        console.warn('API响应格式不正确，使用模拟数据:', {
          hasResponse: !!response,
          hasSuccess: response?.success,
          hasData: !!response?.data
        });
        return await this.getMockRankingsListFallback(params);
      }
    } catch (error) {
      console.error('加载榜单列表失败，使用模拟数据:', error);
      return await this.getMockRankingsListFallback(params);
    }
  }

  /**
   * 榜单列表的模拟数据回退方案
   */
  async getMockRankingsListFallback(params = {}) {
    const mockResponse = await mockingManager.getMockDataByPath('/rankings/', params);
    if (mockResponse.success && mockResponse.data.data_list) {
      const rankingsData = mockResponse.data.data_list.map(item => ({
        id: item.id,
        name: this.formatRankingName(item.channel_name, item.sub_channel_name),
        channel_name: item.channel_name || '',
        sub_channel_name: item.sub_channel_name || '',
        page_id: item.page_id,
        rank_group_type: item.rank_group_type || '模拟',
        description: `${item.rank_group_type || '模拟'} - ${item.page_id}`,
        isBook: false
      }));
      
      return {
        success: true,
        data: rankingsData,
        totalPages: mockResponse.data.total_pages || 1
      };
    }
    
    return { success: false, data: [], totalPages: 0 };
  }

  /**
   * 获取排行榜详情（按天）
   * 包含夹子榜单的特殊处理逻辑
   */
  async getRankingDetail(rankingId, params = {}) {
    try {
      const response = await this.get(`/rankingsdetail/day/${rankingId}`, params);
      console.log('夹子书籍API响应:', response);
      
      if (response && response.success && response.data) {
        const responseData = response.data;
        const booksData = responseData.books || [];
        
        if (booksData.length > 0) {
          // 将书籍数据转换为统一格式
          const { page = 1, size = 20 } = params;
          const rankingsData = booksData.map((book, index) => ({
            id: `book_${book.id}`,
            name: book.title || book.name || `书籍${index + 1}`,
            description: `作者: ${book.author || '未知'} | 收藏: ${book.collectCount || 0}`,
            channel_name: '夹子榜单',
            sub_channel_name: `排名第${((page - 1) * size) + index + 1}位`,
            page_id: 'jiazi',
            rank_group_type: 'jiazi',
            bookData: book,
            isBook: true
          }));
          
          return {
            success: true,
            data: rankingsData,
            totalPages: Math.ceil((responseData.total || booksData.length) / size)
          };
        } else {
          console.warn('夹子榜单书籍数据为空，使用模拟数据');
          return await this.getMockJiaziFallback(params);
        }
      } else {
        console.warn('夹子榜单API响应格式不正确，使用模拟数据');
        return await this.getMockJiaziFallback(params);
      }
    } catch (error) {
      console.error('加载夹子书籍失败，使用模拟数据:', error);
      return await this.getMockJiaziFallback(params);
    }
  }

  /**
   * 夹子榜单的模拟数据回退方案
   */
  async getMockJiaziFallback(params = {}) {
    const mockResponse = await mockingManager.getMockDataByPath('/rankingsdetail/day/1', params);
    if (mockResponse.success && mockResponse.data.books) {
      const { page = 1, size = 20 } = params;
      const rankingsData = mockResponse.data.books.map((book, index) => ({
        id: `book_${book.id}`,
        name: book.title || book.name || `书籍${index + 1}`,
        description: `作者: ${book.author || '未知'} | 收藏: ${book.collectCount || 0}`,
        channel_name: '夹子榜单',
        sub_channel_name: `排名第${((page - 1) * size) + index + 1}位`,
        page_id: 'jiazi',
        rank_group_type: 'jiazi',
        bookData: book,
        isBook: true
      }));
      
      return {
        success: true,
        data: rankingsData,
        totalPages: Math.ceil((mockResponse.data.total || rankingsData.length) / size)
      };
    }
    
    return { success: false, data: [], totalPages: 0 };
  }

  /**
   * 获取排行榜书籍列表（从排行榜详情中提取）
   */
  async getRankingBooks(rankingId, params = {}) {
    const response = await this.getRankingDetail(rankingId, params)
    if (response.success && response.data) {
      return {
        success: true,
        data: {
          books: response.data.books || [],
          total: response.data.books?.length || 0
        }
      }
    }
    return response
  }

  /**
   * 获取排行榜历史（按天）
   */
  async getRankingHistory(rankingId, params = {}) {
    return await this.get(`/rankings/history/day/${rankingId}`, params)
  }

  /**
   * 获取热门榜单
   */
  async getHotRankings(params = {}) {
    const defaultParams = { size: 10, ...params }
    return await this.getRankingsList(defaultParams)
  }

  /**
   * 获取用户关注数据（本地存储）
   */
  async getUserFollows() {
    try {
      const followList = uni.getStorageSync('followList') || []
      return {
        success: true,
        data: followList
      }
    } catch (error) {
      return {
        success: false,
        data: [],
        error: error.message
      }
    }
  }
}

// 创建单例实例
const requestManager = new RequestManager()
export default requestManager