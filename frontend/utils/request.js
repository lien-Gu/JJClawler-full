/**
 * 网络请求工具类
 * @description 封装 uni.request，提供统一的请求配置、错误处理、拦截器等功能
 */

import configManager from './config.js'

// 基础配置（从配置文件动态获取）
let BASE_URL = configManager.getAPIBaseURL()
let TIMEOUT = configManager.getAPITimeout()

/**
 * HTTP状态码映射
 */
const HTTP_STATUS = {
  SUCCESS: 200,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500
}

/**
 * 错误信息映射
 */
const ERROR_MESSAGES = {
  [HTTP_STATUS.UNAUTHORIZED]: '未授权，请重新登录',
  [HTTP_STATUS.FORBIDDEN]: '拒绝访问',
  [HTTP_STATUS.NOT_FOUND]: '请求的资源不存在',
  [HTTP_STATUS.SERVER_ERROR]: '服务器内部错误',
  'NETWORK_ERROR': '网络连接异常',
  'TIMEOUT': '请求超时',
  'UNKNOWN': '未知错误'
}

/**
 * 请求拦截器
 * @param {Object} config 请求配置
 * @returns {Object} 处理后的配置
 */
function requestInterceptor(config) {
  // 添加基础URL
  if (!config.url.startsWith('http')) {
    config.url = BASE_URL + config.url
  }
  
  // 添加通用请求头
  config.header = {
    'Content-Type': 'application/json',
    ...config.header
  }
  
  // 添加认证token（如果存在）
  const token = uni.getStorageSync('token')
  if (token) {
    config.header.Authorization = `Bearer ${token}`
  }
  
  // 添加设备信息
  const systemInfo = uni.getSystemInfoSync()
  config.header['User-Agent'] = `JJClawler/${systemInfo.platform} ${systemInfo.version}`
  
  // 显示加载提示
  if (config.showLoading !== false) {
    uni.showLoading({
      title: config.loadingText || '加载中...',
      mask: true
    })
  }
  
  console.log('请求发送:', config)
  return config
}

/**
 * 响应拦截器
 * @param {Object} response 响应数据
 * @param {Object} config 请求配置
 * @returns {Promise} 处理后的响应
 */
function responseInterceptor(response, config) {
  // 隐藏加载提示
  if (config.showLoading !== false) {
    uni.hideLoading()
  }
  
  console.log('响应接收:', response)
  
  const { statusCode, data } = response
  
  // HTTP状态码检查
  if (statusCode === HTTP_STATUS.SUCCESS) {
    // 业务状态码检查
    if (data.code === 0 || data.success === true) {
      return Promise.resolve(data.data || data)
    } else {
      // 业务错误
      const errorMsg = data.message || data.msg || '请求失败'
      return Promise.reject({
        type: 'BUSINESS_ERROR',
        code: data.code,
        message: errorMsg,
        data: data
      })
    }
  } else {
    // HTTP错误
    const errorMsg = ERROR_MESSAGES[statusCode] || ERROR_MESSAGES.UNKNOWN
    return Promise.reject({
      type: 'HTTP_ERROR',
      code: statusCode,
      message: errorMsg,
      data: response
    })
  }
}

/**
 * 错误处理器
 * @param {Object} error 错误对象
 * @param {Object} config 请求配置
 */
function errorHandler(error, config) {
  // 隐藏加载提示
  if (config.showLoading !== false) {
    uni.hideLoading()
  }
  
  console.error('请求错误:', error)
  
  let errorMessage = ERROR_MESSAGES.UNKNOWN
  
  if (error.type === 'BUSINESS_ERROR' || error.type === 'HTTP_ERROR') {
    errorMessage = error.message
  } else if (error.errMsg) {
    if (error.errMsg.includes('timeout')) {
      errorMessage = ERROR_MESSAGES.TIMEOUT
    } else if (error.errMsg.includes('fail')) {
      errorMessage = ERROR_MESSAGES.NETWORK_ERROR
    }
  }
  
  // 显示错误提示（如果配置允许）
  if (config.showError !== false) {
    uni.showToast({
      title: errorMessage,
      icon: 'none',
      duration: 2000
    })
  }
  
  return Promise.reject({
    ...error,
    message: errorMessage
  })
}

/**
 * 核心请求方法
 * @param {Object} options 请求选项
 * @returns {Promise} 请求Promise
 */
function request(options = {}) {
  return new Promise((resolve, reject) => {
    // 合并默认配置
    const config = {
      method: 'GET',
      timeout: TIMEOUT,
      showLoading: true,
      showError: true,
      ...options
    }
    
    // 请求拦截
    const interceptedConfig = requestInterceptor(config)
    
    // 发送请求
    uni.request({
      ...interceptedConfig,
      success: (response) => {
        responseInterceptor(response, config)
          .then(resolve)
          .catch(reject)
      },
      fail: (error) => {
        errorHandler(error, config)
          .catch(reject)
      }
    })
  })
}

/**
 * GET请求
 * @param {String} url 请求地址
 * @param {Object} params 请求参数
 * @param {Object} options 其他选项
 * @returns {Promise} 请求Promise
 */
export function get(url, params = {}, options = {}) {
  return request({
    url,
    method: 'GET',
    data: params,
    ...options
  })
}

/**
 * POST请求
 * @param {String} url 请求地址
 * @param {Object} data 请求数据
 * @param {Object} options 其他选项
 * @returns {Promise} 请求Promise
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
 * @param {String} url 请求地址
 * @param {Object} data 请求数据
 * @param {Object} options 其他选项
 * @returns {Promise} 请求Promise
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
 * @param {String} url 请求地址
 * @param {Object} params 请求参数
 * @param {Object} options 其他选项
 * @returns {Promise} 请求Promise
 */
export function del(url, params = {}, options = {}) {
  return request({
    url,
    method: 'DELETE',
    data: params,
    ...options
  })
}

/**
 * 文件上传
 * @param {String} url 上传地址
 * @param {String} filePath 文件路径
 * @param {Object} formData 表单数据
 * @param {Object} options 其他选项
 * @returns {Promise} 上传Promise
 */
export function upload(url, filePath, formData = {}, options = {}) {
  return new Promise((resolve, reject) => {
    // 显示上传进度
    if (options.showProgress !== false) {
      uni.showLoading({
        title: '上传中...',
        mask: true
      })
    }
    
    // 添加认证token
    const header = { ...options.header }
    const token = uni.getStorageSync('token')
    if (token) {
      header.Authorization = `Bearer ${token}`
    }
    
    uni.uploadFile({
      url: url.startsWith('http') ? url : BASE_URL + url,
      filePath,
      name: options.name || 'file',
      formData,
      header,
      success: (response) => {
        if (options.showProgress !== false) {
          uni.hideLoading()
        }
        
        try {
          const data = JSON.parse(response.data)
          if (data.code === 0 || data.success === true) {
            resolve(data.data || data)
          } else {
            reject({
              type: 'BUSINESS_ERROR',
              message: data.message || '上传失败'
            })
          }
        } catch (e) {
          reject({
            type: 'PARSE_ERROR',
            message: '响应数据解析失败'
          })
        }
      },
      fail: (error) => {
        if (options.showProgress !== false) {
          uni.hideLoading()
        }
        
        let errorMessage = '上传失败'
        if (error.errMsg && error.errMsg.includes('fail')) {
          errorMessage = '网络连接异常'
        }
        
        if (options.showError !== false) {
          uni.showToast({
            title: errorMessage,
            icon: 'none'
          })
        }
        
        reject({
          type: 'UPLOAD_ERROR',
          message: errorMessage,
          error
        })
      }
    })
  })
}

/**
 * 设置基础URL
 * @param {String} baseUrl 基础URL
 */
export function setBaseURL(baseUrl) {
  BASE_URL = baseUrl
  configManager.updateConfig({ api: { baseURL: baseUrl } })
}

/**
 * 设置请求超时时间
 * @param {Number} timeout 超时时间（毫秒）
 */
export function setTimeout(timeout) {
  TIMEOUT = timeout
  configManager.updateConfig({ api: { timeout } })
}

/**
 * 刷新配置（重新加载配置文件中的设置）
 */
export function refreshConfig() {
  BASE_URL = configManager.getAPIBaseURL()
  TIMEOUT = configManager.getAPITimeout()
  console.log('请求配置已刷新:', { BASE_URL, TIMEOUT })
}

/**
 * 获取当前配置
 * @returns {Object} 当前配置
 */
export function getCurrentConfig() {
  return {
    BASE_URL,
    TIMEOUT,
    environment: configManager.getCurrentEnvironment()
  }
}

// 默认导出
export default {
  get,
  post,
  put,
  delete: del,
  upload,
  request,
  setBaseURL,
  setTimeout,
  refreshConfig,
  getCurrentConfig
} 