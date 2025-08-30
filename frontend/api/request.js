/**
 * 统一请求管理器
 * 支持环境切换和模拟数据
 */

import configData from '@/data/config.json'
import mockData from '@/data/fake_data.json'

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
   * 获取排行榜列表
   */
  async getRankingsList(params = {}) {
    return await this.get('/rankings/', params)
  }

  /**
   * 获取排行榜详情（按天）
   */
  async getRankingDetail(rankingId, params = {}) {
    return await this.get(`/rankingsdetail/day/${rankingId}`, params)
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