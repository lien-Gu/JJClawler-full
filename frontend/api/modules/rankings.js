/**
 * 榜单相关API
 */

import request from '../request'

export const rankingsApi = {
  /**
   * 获取榜单列表
   * @param {Object} params 查询参数 {page_id, name, page, size}
   * @returns {Promise} 榜单列表
   */
  getList: (params = {}) => {
    const defaultParams = {
      page: 1,
      size: 20
    }
    return request.get('/api/v1/rankings/', { ...defaultParams, ...params })
  },

  /**
   * 获取榜单详情（按天）
   * @param {number} rankingId 榜单ID
   * @param {Object} params 查询参数 {target_date}
   * @returns {Promise} 榜单详情
   */
  getDetailByDay: (rankingId, params = {}) => {
    return request.get(`/api/v1/rankingsdetail/day/${rankingId}`, params)
  },

  /**
   * 获取夹子榜单详情（按小时）
   * @param {number} rankingId 榜单ID
   * @param {Object} params 查询参数 {target_date, hour}
   * @returns {Promise} 榜单详情
   */
  getDetailByHour: (rankingId, params = {}) => {
    return request.get(`/api/v1/rankingsdetail/hour/${rankingId}`, params)
  },

  /**
   * 获取榜单历史（按天）
   * @param {number} rankingId 榜单ID
   * @param {Object} params 查询参数 {start_date, end_date}
   * @returns {Promise} 榜单历史
   */
  getHistoryByDay: (rankingId, params = {}) => {
    if (!params.start_date) {
      // 默认查询最近30天
      const endDate = new Date()
      const startDate = new Date(endDate.getTime() - 30 * 24 * 60 * 60 * 1000)
      params = {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        ...params
      }
    }
    return request.get(`/api/v1/rankings/history/day/${rankingId}`, params)
  },

  /**
   * 获取榜单历史（按小时）
   * @param {number} rankingId 榜单ID
   * @param {Object} params 查询参数 {start_time, end_time}
   * @returns {Promise} 榜单历史
   */
  getHistoryByHour: (rankingId, params = {}) => {
    if (!params.start_time) {
      // 默认查询最近24小时
      const endTime = new Date()
      const startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000)
      params = {
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        ...params
      }
    }
    return request.get(`/api/v1/rankings/history/hour/${rankingId}`, params)
  }
}