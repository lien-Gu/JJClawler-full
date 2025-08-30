/**
 * 统计报告相关API
 */

import request from '../request'

export const reportsApi = {
  /**
   * 获取统计概览
   * @returns {Promise} 统计概览数据
   */
  getOverview: () => {
    return request.get('/api/v1/stats/overview')
  },

  /**
   * 获取报告列表
   * @param {Object} params 查询参数 {page, size, type}
   * @returns {Promise} 报告列表
   */
  getReportsList: (params = {}) => {
    const defaultParams = {
      page: 1,
      size: 10
    }
    return request.get('/api/v1/reports/', { ...defaultParams, ...params })
  },

  /**
   * 获取报告详情
   * @param {string} reportId 报告ID
   * @returns {Promise} 报告详情
   */
  getReportDetail: (reportId) => {
    return request.get(`/api/v1/reports/${reportId}`)
  }
}