/**
 * 简化的网络请求工具
 */

import envConfig from './env-config.js'

/**
 * 基础请求方法
 * @param {Object} options 请求选项
 * @returns {Promise} 请求结果
 */
function request(options) {
  return new Promise((resolve, reject) => {
    // 构建完整的URL
    let url = options.url
    if (!url.startsWith('http')) {
      url = envConfig.getBaseURL() + url
    }
    
    uni.request({
      url: url,
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
export function get(url, params = {}, options = {}) {
  // 将参数拼接到URL
  const queryString = Object.keys(params)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')
  
  if (queryString) {
    url += (url.includes('?') ? '&' : '?') + queryString
  }
  
  return request({
    url,
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
export function post(url, data = {}, options = {}) {
  return request({
    url,
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
export function put(url, data = {}, options = {}) {
  return request({
    url,
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
export function del(url, options = {}) {
  return request({
    url,
    method: 'DELETE',
    ...options
  })
}

export default {
  request,
  get,
  post,
  put,
  del
}