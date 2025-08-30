/**
 * 调度任务相关API
 */

import request from '../request'

export const scheduleApi = {
  /**
   * 创建爬取任务
   * @param {Object} params 任务参数 {page_ids, run_time}
   * @returns {Promise} 任务创建结果
   */
  createCrawlJob: (params = {}) => {
    const defaultParams = {
      page_ids: ['jiazi']
    }
    return request.post('/api/v1/schedule/task/create', { ...defaultParams, ...params })
  },

  /**
   * 获取调度器状态
   * @returns {Promise} 调度器状态信息
   */
  getSchedulerStatus: () => {
    return request.get('/api/v1/schedule/status')
  }
}