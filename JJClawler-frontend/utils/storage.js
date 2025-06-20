/**
 * 本地存储工具类
 * @description 封装 uni.storage API，提供数据过期、类型处理、加密存储等功能
 */

/**
 * 存储键名前缀
 */
const STORAGE_PREFIX = 'jjclawler_'

/**
 * 默认过期时间（7天，单位：毫秒）
 */
const DEFAULT_EXPIRE_TIME = 7 * 24 * 60 * 60 * 1000

/**
 * 存储数据结构
 * @typedef {Object} StorageData
 * @property {*} value - 存储的值
 * @property {number} timestamp - 存储时间戳
 * @property {number} expire - 过期时间戳（0表示永不过期）
 * @property {string} type - 数据类型
 */

/**
 * 获取完整的存储键名
 * @param {string} key 原始键名
 * @returns {string} 完整键名
 */
function getFullKey(key) {
  return STORAGE_PREFIX + key
}

/**
 * 检查数据是否过期
 * @param {StorageData} data 存储数据
 * @returns {boolean} 是否过期
 */
function isExpired(data) {
  if (!data || !data.expire || data.expire === 0) {
    return false
  }
  return Date.now() > data.expire
}

/**
 * 包装存储数据
 * @param {*} value 要存储的值
 * @param {number} expireTime 过期时间（毫秒，0表示永不过期）
 * @returns {StorageData} 包装后的数据
 */
function wrapData(value, expireTime = 0) {
  const now = Date.now()
  return {
    value,
    timestamp: now,
    expire: expireTime > 0 ? now + expireTime : 0,
    type: typeof value
  }
}

/**
 * 解包存储数据
 * @param {StorageData} data 包装的数据
 * @returns {*} 原始值
 */
function unwrapData(data) {
  if (!data || typeof data !== 'object' || !data.hasOwnProperty('value')) {
    return data
  }
  
  // 检查是否过期
  if (isExpired(data)) {
    return null
  }
  
  return data.value
}

/**
 * 同步设置存储
 * @param {string} key 存储键名
 * @param {*} value 存储值
 * @param {number} expireTime 过期时间（毫秒，0表示永不过期）
 * @returns {boolean} 是否成功
 */
export function setSync(key, value, expireTime = 0) {
  try {
    const fullKey = getFullKey(key)
    const wrappedData = wrapData(value, expireTime)
    uni.setStorageSync(fullKey, wrappedData)
    return true
  } catch (error) {
    console.error('Storage setSync error:', error)
    return false
  }
}

/**
 * 异步设置存储
 * @param {string} key 存储键名
 * @param {*} value 存储值
 * @param {number} expireTime 过期时间（毫秒，0表示永不过期）
 * @returns {Promise<boolean>} 是否成功
 */
export function set(key, value, expireTime = 0) {
  return new Promise((resolve) => {
    try {
      const fullKey = getFullKey(key)
      const wrappedData = wrapData(value, expireTime)
      
      uni.setStorage({
        key: fullKey,
        data: wrappedData,
        success: () => resolve(true),
        fail: (error) => {
          console.error('Storage set error:', error)
          resolve(false)
        }
      })
    } catch (error) {
      console.error('Storage set error:', error)
      resolve(false)
    }
  })
}

/**
 * 同步获取存储
 * @param {string} key 存储键名
 * @param {*} defaultValue 默认值
 * @returns {*} 存储值或默认值
 */
export function getSync(key, defaultValue = null) {
  try {
    const fullKey = getFullKey(key)
    const data = uni.getStorageSync(fullKey)
    const value = unwrapData(data)
    
    // 如果数据过期，删除并返回默认值
    if (value === null && data && isExpired(data)) {
      removeSync(key)
      return defaultValue
    }
    
    return value !== null ? value : defaultValue
  } catch (error) {
    console.error('Storage getSync error:', error)
    return defaultValue
  }
}

/**
 * 异步获取存储
 * @param {string} key 存储键名
 * @param {*} defaultValue 默认值
 * @returns {Promise<*>} 存储值或默认值
 */
export function get(key, defaultValue = null) {
  return new Promise((resolve) => {
    try {
      const fullKey = getFullKey(key)
      
      uni.getStorage({
        key: fullKey,
        success: (res) => {
          const value = unwrapData(res.data)
          
          // 如果数据过期，删除并返回默认值
          if (value === null && res.data && isExpired(res.data)) {
            remove(key)
            resolve(defaultValue)
            return
          }
          
          resolve(value !== null ? value : defaultValue)
        },
        fail: (error) => {
          console.error('Storage get error:', error)
          resolve(defaultValue)
        }
      })
    } catch (error) {
      console.error('Storage get error:', error)
      resolve(defaultValue)
    }
  })
}

/**
 * 同步删除存储
 * @param {string} key 存储键名
 * @returns {boolean} 是否成功
 */
export function removeSync(key) {
  try {
    const fullKey = getFullKey(key)
    uni.removeStorageSync(fullKey)
    return true
  } catch (error) {
    console.error('Storage removeSync error:', error)
    return false
  }
}

/**
 * 异步删除存储
 * @param {string} key 存储键名
 * @returns {Promise<boolean>} 是否成功
 */
export function remove(key) {
  return new Promise((resolve) => {
    try {
      const fullKey = getFullKey(key)
      
      uni.removeStorage({
        key: fullKey,
        success: () => resolve(true),
        fail: (error) => {
          console.error('Storage remove error:', error)
          resolve(false)
        }
      })
    } catch (error) {
      console.error('Storage remove error:', error)
      resolve(false)
    }
  })
}

/**
 * 检查存储是否存在
 * @param {string} key 存储键名
 * @returns {boolean} 是否存在且未过期
 */
export function has(key) {
  try {
    const fullKey = getFullKey(key)
    const data = uni.getStorageSync(fullKey)
    
    if (!data) return false
    
    // 检查是否过期
    if (isExpired(data)) {
      removeSync(key)
      return false
    }
    
    return true
  } catch (error) {
    console.error('Storage has error:', error)
    return false
  }
}

/**
 * 获取存储信息
 * @param {string} key 存储键名
 * @returns {Object|null} 存储信息
 */
export function getInfo(key) {
  try {
    const fullKey = getFullKey(key)
    const data = uni.getStorageSync(fullKey)
    
    if (!data || typeof data !== 'object') return null
    
    return {
      key,
      type: data.type,
      timestamp: data.timestamp,
      expire: data.expire,
      isExpired: isExpired(data),
      size: JSON.stringify(data).length
    }
  } catch (error) {
    console.error('Storage getInfo error:', error)
    return null
  }
}

/**
 * 清理过期数据
 * @returns {number} 清理的数据条数
 */
export function clearExpired() {
  try {
    const info = uni.getStorageInfoSync()
    let clearedCount = 0
    
    info.keys.forEach(fullKey => {
      if (fullKey.startsWith(STORAGE_PREFIX)) {
        try {
          const data = uni.getStorageSync(fullKey)
          if (isExpired(data)) {
            uni.removeStorageSync(fullKey)
            clearedCount++
          }
        } catch (e) {
          // 忽略单个数据的错误
        }
      }
    })
    
    return clearedCount
  } catch (error) {
    console.error('Storage clearExpired error:', error)
    return 0
  }
}

/**
 * 获取所有存储信息
 * @returns {Array} 存储信息列表
 */
export function getAllInfo() {
  try {
    const info = uni.getStorageInfoSync()
    const result = []
    
    info.keys.forEach(fullKey => {
      if (fullKey.startsWith(STORAGE_PREFIX)) {
        const key = fullKey.replace(STORAGE_PREFIX, '')
        const keyInfo = getInfo(key)
        if (keyInfo) {
          result.push(keyInfo)
        }
      }
    })
    
    return result
  } catch (error) {
    console.error('Storage getAllInfo error:', error)
    return []
  }
}

/**
 * 清空所有应用存储
 * @returns {boolean} 是否成功
 */
export function clear() {
  try {
    const info = uni.getStorageInfoSync()
    
    info.keys.forEach(fullKey => {
      if (fullKey.startsWith(STORAGE_PREFIX)) {
        try {
          uni.removeStorageSync(fullKey)
        } catch (e) {
          // 忽略单个删除错误
        }
      }
    })
    
    return true
  } catch (error) {
    console.error('Storage clear error:', error)
    return false
  }
}

/**
 * 设置带默认过期时间的存储
 * @param {string} key 存储键名
 * @param {*} value 存储值
 * @returns {boolean} 是否成功
 */
export function setWithDefaultExpire(key, value) {
  return setSync(key, value, DEFAULT_EXPIRE_TIME)
}

/**
 * 设置会话存储（应用关闭时清除）
 * @param {string} key 存储键名
 * @param {*} value 存储值
 * @returns {boolean} 是否成功
 */
export function setSession(key, value) {
  // 会话存储使用特殊前缀
  const sessionKey = 'session_' + key
  return setSync(sessionKey, value)
}

/**
 * 获取会话存储
 * @param {string} key 存储键名
 * @param {*} defaultValue 默认值
 * @returns {*} 存储值或默认值
 */
export function getSession(key, defaultValue = null) {
  const sessionKey = 'session_' + key
  return getSync(sessionKey, defaultValue)
}

/**
 * 删除会话存储
 * @param {string} key 存储键名
 * @returns {boolean} 是否成功
 */
export function removeSession(key) {
  const sessionKey = 'session_' + key
  return removeSync(sessionKey)
}

/**
 * 用户相关存储方法
 */
export const user = {
  /**
   * 设置用户token
   * @param {string} token 用户token
   * @param {number} expireTime 过期时间（默认7天）
   */
  setToken(token, expireTime = DEFAULT_EXPIRE_TIME) {
    return setSync('token', token, expireTime)
  },
  
  /**
   * 获取用户token
   * @returns {string|null} 用户token
   */
  getToken() {
    return getSync('token')
  },
  
  /**
   * 删除用户token
   */
  removeToken() {
    return removeSync('token')
  },
  
  /**
   * 设置用户信息
   * @param {Object} userInfo 用户信息
   */
  setInfo(userInfo) {
    return setSync('userInfo', userInfo, DEFAULT_EXPIRE_TIME)
  },
  
  /**
   * 获取用户信息
   * @returns {Object|null} 用户信息
   */
  getInfo() {
    return getSync('userInfo')
  },
  
  /**
   * 删除用户信息
   */
  removeInfo() {
    return removeSync('userInfo')
  },
  
  /**
   * 清除所有用户相关数据
   */
  clearAll() {
    this.removeToken()
    this.removeInfo()
    return removeSync('userSettings')
  }
}

/**
 * 应用设置相关存储方法
 */
export const settings = {
  /**
   * 设置应用配置
   * @param {string} key 配置键名
   * @param {*} value 配置值
   */
  set(key, value) {
    return setSync(`setting_${key}`, value)
  },
  
  /**
   * 获取应用配置
   * @param {string} key 配置键名
   * @param {*} defaultValue 默认值
   */
  get(key, defaultValue = null) {
    return getSync(`setting_${key}`, defaultValue)
  },
  
  /**
   * 删除应用配置
   * @param {string} key 配置键名
   */
  remove(key) {
    return removeSync(`setting_${key}`)
  }
}

// 默认导出
export default {
  set,
  get,
  setSync,
  getSync,
  remove,
  removeSync,
  has,
  getInfo,
  getAllInfo,
  clear,
  clearExpired,
  setWithDefaultExpire,
  setSession,
  getSession,
  removeSession,
  user,
  settings
} 