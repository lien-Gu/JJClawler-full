/**
 * 通用辅助函数
 */

/**
 * 防抖函数
 * @param {Function} func 要防抖的函数
 * @param {number} delay 延迟时间
 * @returns {Function} 防抖后的函数
 */
export const debounce = (func, delay) => {
  let timeoutId
  return function (...args) {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func.apply(this, args), delay)
  }
}

/**
 * 节流函数
 * @param {Function} func 要节流的函数
 * @param {number} delay 节流时间
 * @returns {Function} 节流后的函数
 */
export const throttle = (func, delay) => {
  let lastCall = 0
  return function (...args) {
    const now = new Date().getTime()
    if (now - lastCall < delay) return
    lastCall = now
    return func.apply(this, args)
  }
}

/**
 * 深拷贝对象
 * @param {*} obj 要拷贝的对象
 * @returns {*} 拷贝后的对象
 */
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime())
  if (obj instanceof Array) return obj.map(item => deepClone(item))
  
  const cloned = {}
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloned[key] = deepClone(obj[key])
    }
  }
  return cloned
}

/**
 * 生成唯一ID
 * @returns {string} 唯一ID
 */
export const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

/**
 * 检查是否为空值
 * @param {*} value 要检查的值
 * @returns {boolean} 是否为空
 */
export const isEmpty = (value) => {
  if (value == null) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') return Object.keys(value).length === 0
  return false
}

/**
 * 安全的JSON解析
 * @param {string} str JSON字符串
 * @param {*} defaultValue 默认值
 * @returns {*} 解析结果或默认值
 */
export const safeJsonParse = (str, defaultValue = null) => {
  try {
    return JSON.parse(str)
  } catch (error) {
    console.warn('JSON解析失败:', error)
    return defaultValue
  }
}

/**
 * 创建延迟Promise
 * @param {number} ms 延迟毫秒数
 * @returns {Promise} 延迟Promise
 */
export const sleep = (ms) => {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 重试函数
 * @param {Function} fn 要重试的函数
 * @param {number} times 重试次数
 * @param {number} delay 重试间隔
 * @returns {Promise} 重试结果
 */
export const retry = async (fn, times = 3, delay = 1000) => {
  try {
    return await fn()
  } catch (error) {
    if (times > 1) {
      await sleep(delay)
      return retry(fn, times - 1, delay)
    }
    throw error
  }
}

/**
 * 获取URL参数
 * @param {string} url URL字符串
 * @returns {Object} 参数对象
 */
export const getUrlParams = (url) => {
  const params = {}
  const urlSearchParams = new URLSearchParams(url.split('?')[1] || '')
  for (const [key, value] of urlSearchParams.entries()) {
    params[key] = value
  }
  return params
}

/**
 * 构建URL参数字符串
 * @param {Object} params 参数对象
 * @returns {string} 参数字符串
 */
export const buildUrlParams = (params) => {
  return Object.keys(params)
    .filter(key => params[key] !== undefined && params[key] !== null)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')
}

/**
 * 数组去重
 * @param {Array} arr 要去重的数组
 * @param {string} key 对象数组去重的键名
 * @returns {Array} 去重后的数组
 */
export const uniqueArray = (arr, key = null) => {
  if (!Array.isArray(arr)) return []
  
  if (key) {
    const seen = new Set()
    return arr.filter(item => {
      const val = item[key]
      if (seen.has(val)) return false
      seen.add(val)
      return true
    })
  }
  
  return [...new Set(arr)]
}

/**
 * 简单的模板字符串替换
 * @param {string} template 模板字符串
 * @param {Object} data 数据对象
 * @returns {string} 替换后的字符串
 */
export const templateReplace = (template, data) => {
  return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    return data[key] !== undefined ? data[key] : match
  })
}

/**
 * 获取文件扩展名
 * @param {string} filename 文件名
 * @returns {string} 扩展名
 */
export const getFileExtension = (filename) => {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2)
}

/**
 * 检查是否为有效的URL
 * @param {string} url URL字符串
 * @returns {boolean} 是否为有效URL
 */
export const isValidUrl = (url) => {
  try {
    new URL(url)
    return true
  } catch (error) {
    return false
  }
}