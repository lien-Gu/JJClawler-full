/**
 * 数据管理器 - 根据环境自动选择数据源
 * @description 统一管理三种环境下的数据获取：dev(后端API)、test(假数据)、pro(服务器API)
 */

import configManager from './config.js'
import request from './request.js'
import fakeData from '../data/fake_data.json'

class DataManager {
  constructor() {
    this.configManager = configManager
    this.fakeData = fakeData
  }

  /**
   * 获取当前环境
   * @returns {string} 环境名称
   */
  getCurrentEnvironment() {
    return this.configManager.getCurrentEnvironment()
  }

  /**
   * 是否使用假数据
   * @returns {boolean} 
   */
  shouldUseFakeData() {
    return this.getCurrentEnvironment() === 'test'
  }

  /**
   * 统一的数据获取方法
   * @param {string} apiPath API路径
   * @param {string} fakeDataPath 假数据路径（用.分隔）
   * @param {Object} params 请求参数
   * @param {Object} options 请求选项
   * @returns {Promise} 数据Promise
   */
  async getData(apiPath, fakeDataPath, params = {}, options = {}) {
    if (this.shouldUseFakeData()) {
      // 使用假数据
      return this.getFakeData(fakeDataPath, params)
    } else {
      // 使用真实API
      return await request.get(apiPath, params, options)
    }
  }

  /**
   * 统一的POST数据方法
   * @param {string} apiPath API路径
   * @param {Object} data 请求数据
   * @param {Object} options 请求选项
   * @returns {Promise} 响应Promise
   */
  async postData(apiPath, data = {}, options = {}) {
    if (this.shouldUseFakeData()) {
      // 假数据环境下模拟POST成功
      return Promise.resolve({ success: true, message: '操作成功(测试环境)' })
    } else {
      // 使用真实API
      return await request.post(apiPath, data, options)
    }
  }

  /**
   * 从假数据中获取指定路径的数据
   * @param {string} path 数据路径（用.分隔，如：'stats.overview'）
   * @param {Object} params 模拟查询参数
   * @returns {any} 数据
   */
  getFakeData(path, params = {}) {
    const pathParts = path.split('.')
    let data = this.fakeData
    
    // 按路径深入获取数据
    for (const part of pathParts) {
      if (data && typeof data === 'object' && part in data) {
        data = data[part]
      } else {
        console.warn(`假数据路径不存在: ${path}`)
        return null
      }
    }

    // 模拟一些查询参数的处理
    if (params.limit && Array.isArray(data)) {
      data = data.slice(0, params.limit)
    }

    // 深拷贝数据避免修改原始数据
    return JSON.parse(JSON.stringify(data))
  }

  // ================== 具体业务API方法 ==================

  /**
   * 获取首页统计概览
   */
  async getOverviewStats() {
    return this.getData('/stats/overview', 'stats.overview')
  }

  /**
   * 获取榜单列表
   */
  async getRankingsList(params = {}) {
    return this.getData('/rankings', 'rankings.list', params)
  }

  /**
   * 获取热门榜单
   */
  async getHotRankings(params = {}) {
    return this.getData('/rankings/hot', 'rankings.hot', params)
  }

  /**
   * 获取榜单中的书籍列表
   * @param {string} rankingId 榜单ID
   * @param {Object} params 查询参数
   */
  async getRankingBooks(rankingId, params = {}) {
    if (this.shouldUseFakeData()) {
      // 根据榜单ID返回对应的假数据
      const fakeDataKey = `books.${rankingId}_list`
      return this.getFakeData(fakeDataKey, params) || this.getFakeData('books.jiazi_list', params)
    } else {
      return await request.get(`/rankings/${rankingId}/books`, params)
    }
  }

  /**
   * 获取书籍详情
   * @param {string} bookId 书籍ID
   */
  async getBookDetail(bookId) {
    if (this.shouldUseFakeData()) {
      return this.getFakeData(`books.detail.${bookId}`) || this.getFakeData('books.detail.book_001')
    } else {
      return await request.get(`/books/${bookId}`)
    }
  }

  /**
   * 获取书籍排名历史
   * @param {string} bookId 书籍ID
   */
  async getBookRankings(bookId) {
    if (this.shouldUseFakeData()) {
      const bookDetail = this.getFakeData(`books.detail.${bookId}`) || this.getFakeData('books.detail.book_001')
      return bookDetail?.ranking_history || []
    } else {
      return await request.get(`/books/${bookId}/rankings`)
    }
  }

  /**
   * 获取书籍趋势数据
   * @param {string} bookId 书籍ID
   */
  async getBookTrends(bookId) {
    if (this.shouldUseFakeData()) {
      const bookDetail = this.getFakeData(`books.detail.${bookId}`) || this.getFakeData('books.detail.book_001')
      return bookDetail?.trends || {}
    } else {
      return await request.get(`/books/${bookId}/trends`)
    }
  }

  /**
   * 获取页面配置
   */
  async getPageConfig() {
    return this.getData('/pages', 'pages')
  }

  /**
   * 获取页面统计
   */
  async getPageStatistics() {
    return this.getData('/pages/statistics', 'pages.statistics')
  }

  /**
   * 搜索书籍
   * @param {Object} params 搜索参数
   */
  async searchBooks(params = {}) {
    if (this.shouldUseFakeData()) {
      // 模拟搜索，返回部分假数据
      const allBooks = this.getFakeData('books.jiazi_list')
      if (params.q) {
        return allBooks.filter(book => 
          book.title.includes(params.q) || 
          book.author.includes(params.q)
        )
      }
      return allBooks
    } else {
      return await request.get('/books', params)
    }
  }

  /**
   * 搜索榜单
   * @param {Object} params 搜索参数
   */
  async searchRankings(params = {}) {
    if (this.shouldUseFakeData()) {
      const allRankings = this.getFakeData('rankings.list')
      if (params.q) {
        return allRankings.filter(ranking => ranking.name.includes(params.q))
      }
      return allRankings
    } else {
      return await request.get('/rankings/search', params)
    }
  }

  /**
   * 获取用户统计
   */
  async getUserStats() {
    return this.getData('/user/stats', 'user.stats')
  }

  /**
   * 获取用户关注列表
   */
  async getUserFollows() {
    return this.getData('/user/follows', 'user.follows')
  }

  /**
   * 触发爬虫任务
   * @param {string} target 爬取目标
   */
  async triggerCrawl(target) {
    return this.postData(`/crawl/${target}`)
  }

  /**
   * 获取爬虫任务列表
   */
  async getCrawlTasks() {
    return this.getData('/crawl/tasks', 'crawl.tasks')
  }

  /**
   * 获取调度器状态
   */
  async getSchedulerStatus() {
    return this.getData('/crawl/scheduler/status', 'crawl.status')
  }

  /**
   * 获取调度器任务列表
   */
  async getSchedulerJobs() {
    return this.getData('/crawl/scheduler/jobs', 'crawl.jobs')
  }

  // ================== 环境提示方法 ==================

  /**
   * 显示当前数据源提示
   */
  showDataSourceTip() {
    const env = this.getCurrentEnvironment()
    const envDescriptions = {
      'dev': '开发环境 - 使用本地后端API',
      'test': '测试环境 - 使用预制假数据',
      'pro': '生产环境 - 使用服务器API'
    }
    
    if (configManager.isDebugMode()) {
      console.log(`当前数据源: ${envDescriptions[env] || env}`)
    }
  }

  /**
   * 获取环境状态信息
   */
  getEnvironmentInfo() {
    const env = this.getCurrentEnvironment()
    return {
      environment: env,
      useRealAPI: !this.shouldUseFakeData(),
      useFakeData: this.shouldUseFakeData(),
      baseURL: configManager.getAPIBaseURL(),
      debug: configManager.isDebugMode()
    }
  }
}

// 创建单例实例
const dataManager = new DataManager()

// 在调试模式下显示数据源提示
if (configManager.isDebugMode()) {
  dataManager.showDataSourceTip()
}

export default dataManager

// 导出便捷方法
export const getCurrentEnvironment = () => dataManager.getCurrentEnvironment()
export const shouldUseFakeData = () => dataManager.shouldUseFakeData()
export const getEnvironmentInfo = () => dataManager.getEnvironmentInfo()

// 导出主要API方法
export const {
  getOverviewStats,
  getRankingsList,
  getHotRankings,
  getRankingBooks,
  getBookDetail,
  getBookRankings,
  getBookTrends,
  getPageConfig,
  searchBooks,
  searchRankings,
  getUserStats,
  triggerCrawl,
  getCrawlTasks
} = dataManager