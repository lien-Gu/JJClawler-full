/**
 * 假数据管理器
 * 用于 test 环境下提供模拟数据
 */

import fakeData from '@/data/fake_data.json'

class FakeDataManager {
  constructor() {
    this.data = fakeData
  }

  /**
   * 模拟API响应延迟
   */
  async delay(ms = 300) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * 获取统计概览
   */
  async getOverviewStats() {
    await this.delay()
    return this.data.stats.overview
  }

  /**
   * 获取热门榜单
   */
  async getHotRankings(params = {}) {
    await this.delay()
    const { limit = 10 } = params
    return this.data.rankings.hot.slice(0, limit)
  }

  /**
   * 获取榜单列表
   */
  async getRankingsList(params = {}) {
    await this.delay()
    const { page = 1, pageSize = 20, category, subCategory } = params
    let rankings = [...this.data.rankings.list]
    
    // 分类过滤
    if (category) {
      rankings = rankings.filter(r => r.channel === category)
    }
    
    // 分页
    const start = (page - 1) * pageSize
    const end = start + pageSize
    
    return rankings.slice(start, end)
  }

  /**
   * 获取榜单详情
   */
  async getRankingDetail(rankingId) {
    await this.delay()
    const ranking = this.data.rankings.list.find(r => r.id === rankingId)
    if (!ranking) {
      throw new Error('Ranking not found')
    }
    return ranking
  }

  /**
   * 获取榜单书籍列表
   */
  async getRankingBooks(rankingId, params = {}) {
    await this.delay()
    const { page = 1, limit = 20 } = params
    
    // 根据榜单ID返回对应的书籍列表
    let books = []
    if (rankingId === 'jiazi') {
      books = this.data.books.jiazi_list
    } else {
      // 其他榜单返回模拟数据
      books = this.generateMockBooks(limit)
    }
    
    // 分页
    const start = (page - 1) * limit
    const end = start + limit
    
    return {
      books: books.slice(start, end),
      total: books.length,
      page,
      limit
    }
  }

  /**
   * 获取书籍详情
   */
  async getBookDetail(bookId) {
    await this.delay()
    const bookDetail = this.data.books.detail[bookId]
    if (!bookDetail) {
      // 返回模拟的书籍详情
      return this.generateMockBookDetail(bookId)
    }
    return bookDetail
  }

  /**
   * 获取书籍排名历史
   */
  async getBookRankings(bookId) {
    await this.delay()
    const bookDetail = this.data.books.detail[bookId]
    if (bookDetail && bookDetail.ranking_history) {
      return bookDetail.ranking_history.map(item => ({
        ...item,
        id: item.ranking_id,
        name: item.ranking_name,
        rankChange: Math.floor(Math.random() * 10) - 5,
        startDate: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
        endDate: Math.random() > 0.5 ? new Date().toISOString() : null,
        isActive: Math.random() > 0.3
      }))
    }
    return []
  }

  /**
   * 获取用户关注列表
   */
  async getUserFollows() {
    await this.delay()
    return this.data.user.follows.books.map(book => ({
      ...book,
      type: 'book',
      name: book.title,
      isOnList: Math.random() > 0.5,
      weeklyGrowth: Math.floor(Math.random() * 40) - 20
    }))
  }

  /**
   * 获取页面配置
   */
  async getPages() {
    await this.delay()
    return this.data.pages
  }

  /**
   * 获取爬虫任务状态
   */
  async getCrawlTasks() {
    await this.delay()
    return this.data.crawl.tasks
  }

  /**
   * 获取调度器状态
   */
  async getSchedulerStatus() {
    await this.delay()
    return this.data.crawl.status
  }

  /**
   * 生成模拟书籍列表
   */
  generateMockBooks(count = 20) {
    const categories = ['言情', '纯爱', '衍生', '百合']
    const statuses = ['连载中', '已完结', '暂停']
    
    return Array.from({ length: count }, (_, index) => ({
      id: `mock_book_${index + 1}`,
      title: `模拟书籍标题${index + 1}`,
      author: `作者${index + 1}`,
      author_id: `author_${index + 1}`,
      rank: index + 1,
      category: categories[Math.floor(Math.random() * categories.length)],
      total_clicks: Math.floor(Math.random() * 1000000) + 10000,
      total_favorites: Math.floor(Math.random() * 100000) + 1000,
      comment_count: Math.floor(Math.random() * 10000) + 100,
      chapter_count: Math.floor(Math.random() * 200) + 10,
      last_updated: new Date().toISOString(),
      status: statuses[Math.floor(Math.random() * statuses.length)],
      rank_change: Math.floor(Math.random() * 10) - 5
    }))
  }

  /**
   * 生成模拟书籍详情
   */
  generateMockBookDetail(bookId) {
    return {
      id: bookId,
      title: `书籍标题 ${bookId}`,
      author: '模拟作者',
      author_id: 'mock_author',
      category: '言情',
      tags: ['模拟', '测试', '数据'],
      description: '这是一个模拟的书籍详情描述...',
      total_clicks: Math.floor(Math.random() * 1000000),
      total_favorites: Math.floor(Math.random() * 100000),
      comment_count: Math.floor(Math.random() * 10000),
      chapter_count: Math.floor(Math.random() * 200),
      word_count: Math.floor(Math.random() * 500000),
      first_published: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
      last_updated: new Date().toISOString(),
      status: '连载中',
      cover_url: ''
    }
  }
}

export default new FakeDataManager()