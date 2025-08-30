/**
 * 书籍相关API
 */

import request from '../request'

export const booksApi = {
  /**
   * 获取书籍列表
   * @param {Object} params 查询参数
   * @returns {Promise} 书籍列表
   */
  getList: (params = {}) => {
    return request.get('/api/v1/books/', params)
  },

  /**
   * 获取书籍详情
   * @param {number} novelId 书籍ID
   * @returns {Promise} 书籍详情
   */
  getDetail: (novelId) => {
    return request.get(`/api/v1/books/${novelId}`)
  },

  /**
   * 获取书籍历史快照
   * @param {number} novelId 书籍ID
   * @param {Object} params 查询参数 {interval, count}
   * @returns {Promise} 书籍快照列表
   */
  getSnapshots: (novelId, params = {}) => {
    const defaultParams = {
      interval: 'day',
      count: 7
    }
    return request.get(`/api/v1/books/${novelId}/snapshots`, { ...defaultParams, ...params })
  },

  /**
   * 获取书籍排名历史
   * @param {number} novelId 书籍ID
   * @param {Object} params 查询参数 {days}
   * @returns {Promise} 书籍排名历史
   */
  getRankings: (novelId, params = {}) => {
    const defaultParams = {
      days: 30
    }
    return request.get(`/api/v1/books/${novelId}/rankings`, { ...defaultParams, ...params })
  }
}