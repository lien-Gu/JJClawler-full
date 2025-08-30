/**
 * 本地存储工具集合
 * 支持简单值和复杂对象的存储
 */

/**
 * 同步设置存储
 * @param {string} key 键名
 * @param {*} value 值
 */
export function setSync(key, value) {
  try {
    uni.setStorageSync(key, value)
  } catch (error) {
    console.error('存储失败:', error)
  }
}

/**
 * 同步获取存储
 * @param {string} key 键名
 * @param {*} defaultValue 默认值
 * @returns {*} 存储的值或默认值
 */
export function getSync(key, defaultValue = null) {
  try {
    const value = uni.getStorageSync(key)
    return value !== '' ? value : defaultValue
  } catch (error) {
    console.error('读取存储失败:', error)
    return defaultValue
  }
}

/**
 * 存储对象（自动JSON序列化）
 * @param {string} key 键名
 * @param {Object} obj 对象
 * @returns {boolean} 是否存储成功
 */
export function setObject(key, obj) {
  try {
    uni.setStorageSync(key, JSON.stringify(obj))
    return true
  } catch (error) {
    console.error('存储对象失败:', error)
    return false
  }
}

/**
 * 获取对象（自动JSON解析）
 * @param {string} key 键名
 * @param {Object} defaultValue 默认值
 * @returns {Object} 解析后的对象或默认值
 */
export function getObject(key, defaultValue = null) {
  try {
    const value = uni.getStorageSync(key)
    return value ? JSON.parse(value) : defaultValue
  } catch (error) {
    console.error('获取对象失败:', error)
    return defaultValue
  }
}

/**
 * 同步删除存储
 * @param {string} key 键名
 */
export function removeSync(key) {
  try {
    uni.removeStorageSync(key)
  } catch (error) {
    console.error('删除存储失败:', error)
  }
}

/**
 * 同步清除所有存储
 */
export function clearSync() {
  try {
    uni.clearStorageSync()
  } catch (error) {
    console.error('清除存储失败:', error)
  }
}

/**
 * 获取存储信息
 * @returns {Object} 存储信息
 */
export function getInfoSync() {
  try {
    return uni.getStorageInfoSync()
  } catch (error) {
    console.error('获取存储信息失败:', error)
    return { keys: [], currentSize: 0, limitSize: 0 }
  }
}

// 导出存储对象，提供统一接口
export const storage = {
  set: setSync,
  get: getSync,
  setObject,
  getObject,
  remove: removeSync,
  clear: clearSync,
  getInfo: getInfoSync
}

export default {
  setSync,
  getSync,
  setObject,
  getObject,
  removeSync,
  clearSync,
  getInfoSync,
  storage
}