/**
 * 统一请求管理器
 * 整合原有的request.js和data-manager.js功能
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
   * @param {string} url API路径
   * @param {Object} options 请求选项
   * @returns {Promise} 模拟数据
   */
  async getMockData(url, options = {}) {
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
    
    if (url.includes('/schedule')) {
      return { success: true, data: mockData.schedule || {} }
    }
    
    // 默认返回空数据
    return { success: true, data: null }
  }

  /**
   * 统一请求方法，自动处理环境切换和模拟数据
   * @param {string} url 请求URL
   * @param {Object} options 请求选项
   * @returns {Promise} 请求结果
   */
  async request(url, options = {}) {
    // 更新当前环境配置
    this.currentEnv = uni.getStorageSync('currentEnv') || 'dev'
    this.config = configData.environments[this.currentEnv]
    
    // 如果是测试环境，使用模拟数据
    if (this.config.useLocalData) {
      return await this.getMockData(url, options)
    }
    
    // 真实API请求
    return new Promise((resolve, reject) => {
      uni.request({
        url: this.config.baseURL + url,
        method: options.method || 'GET',
        data: options.data || {},
        header: {
          'Content-Type': 'application/json',
          ...options.header
        },
        timeout: options.timeout || 10000,
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

  /**
   * GET请求
   * @param {string} url 请求地址
   * @param {Object} params 查询参数
   * @param {Object} options 其他选项
   * @returns {Promise} 请求结果
   */
  get(url, params = {}, options = {}) {
    // 将参数拼接到URL
    const queryString = Object.keys(params)
      .filter(key => params[key] !== undefined && params[key] !== null)
      .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
      .join('&')
    
    const fullUrl = queryString ? `${url}${url.includes('?') ? '&' : '?'}${queryString}` : url
    
    return this.request(fullUrl, {
      method: 'GET',
      ...options
    })
  }

  /**
   * POST请求
   * @param {string} url 请求地址
   * @param {Object} data 请求数据
   * @param {Object} options 其他选项
   * @returns {Promise} 请求结果
   */
  post(url, data = {}, options = {}) {
    return this.request(url, {
      method: 'POST',
      data,
      ...options
    })
  }

  /**
   * PUT请求
   * @param {string} url 请求地址
   * @param {Object} data 请求数据
   * @param {Object} options 其他选项
   * @returns {Promise} 请求结果
   */
  put(url, data = {}, options = {}) {
    return this.request(url, {
      method: 'PUT',
      data,
      ...options
    })
  }

  /**
   * DELETE请求
   * @param {string} url 请求地址
   * @param {Object} options 其他选项
   * @returns {Promise} 请求结果
   */
  delete(url, options = {}) {
    return this.request(url, {
      method: 'DELETE',
      ...options
    })
  }

  /**
   * 切换环境
   * @param {string} env 环境名称
   */
  switchEnvironment(env) {
    if (configData.environments[env]) {
      this.currentEnv = env
      this.config = configData.environments[env]
      uni.setStorageSync('currentEnv', env)
      console.log(`环境已切换到: ${env}`)
    } else {
      console.error(`无效的环境: ${env}`)
    }
  }

  /**
   * 获取当前环境信息
   * @returns {Object} 环境信息
   */
  getEnvironmentInfo() {
    return {
      environment: this.currentEnv,
      config: this.config,
      useLocalData: this.config.useLocalData || false,
      baseURL: this.config.baseURL
    }
  }
}

// 创建单例实例
const requestManager = new RequestManager()

export default requestManager