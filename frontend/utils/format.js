/**
 * 格式化工具函数集合
 * 整合原有的formatters.js功能
 */

/**
 * 格式化数字显示
 * @param {number} num 数字
 * @returns {string} 格式化后的数字字符串
 */
export const formatNumber = (num) => {
  if (num == null || isNaN(num)) return '0'
  
  const number = Number(num)
  if (number >= 100000000) {
    return (number / 100000000).toFixed(1).replace(/\.0$/, '') + '亿'
  }
  if (number >= 10000) {
    return (number / 10000).toFixed(1).replace(/\.0$/, '') + 'w'
  }
  return number.toString()
}

/**
 * 格式化时间显示（相对时间）
 * @param {string|Date} time 时间
 * @returns {string} 相对时间字符串
 */
export const formatTime = (time) => {
  if (!time) return ''
  
  const now = new Date()
  const target = new Date(time)
  const diff = now - target
  
  if (diff < 0) return '刚刚'
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 2592000000) return Math.floor(diff / 86400000) + '天前'
  return target.toLocaleDateString()
}

/**
 * 格式化日期显示（绝对日期）
 * @param {string|Date} date 日期
 * @param {Object} options 选项
 * @returns {string} 格式化日期
 */
export const formatDate = (date, options = {}) => {
  if (!date) return ''
  
  const target = new Date(date)
  const defaultOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    ...options
  }
  
  return target.toLocaleDateString('zh-CN', defaultOptions)
}

/**
 * 格式化字数显示
 * @param {number} count 字数
 * @returns {string} 格式化字数
 */
export const formatWordCount = (count) => {
  if (count == null || isNaN(count)) return '0字'
  
  const number = Number(count)
  if (number >= 10000) {
    return (number / 10000).toFixed(1).replace(/\.0$/, '') + '万字'
  }
  return number + '字'
}

/**
 * 格式化百分比
 * @param {number} value 值
 * @param {number} decimals 小数位数
 * @returns {string} 百分比字符串
 */
export const formatPercentage = (value, decimals = 1) => {
  if (value == null || isNaN(value)) return '0%'
  return (Number(value) * 100).toFixed(decimals) + '%'
}

/**
 * 格式化货币
 * @param {number} amount 金额
 * @param {string} currency 货币符号
 * @returns {string} 格式化货币
 */
export const formatCurrency = (amount, currency = '¥') => {
  if (amount == null || isNaN(amount)) return currency + '0'
  return currency + Number(amount).toLocaleString()
}

/**
 * 格式化文件大小
 * @param {number} bytes 字节数
 * @returns {string} 格式化文件大小
 */
export const formatFileSize = (bytes) => {
  if (bytes == null || isNaN(bytes)) return '0B'
  
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  if (bytes === 0) return '0B'
  
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(2) + sizes[i]
}

/**
 * 格式化书籍状态
 * @param {string} status 状态
 * @returns {string} 中文状态
 */
export const formatBookStatus = (status) => {
  const statusMap = {
    'ongoing': '连载中',
    'completed': '已完结',
    'paused': '暂停',
    'draft': '草稿'
  }
  return statusMap[status] || status
}

/**
 * 格式化排名变化
 * @param {number} change 排名变化
 * @returns {Object} 变化信息 {text, type}
 */
export const formatRankingChange = (change) => {
  if (change == null || change === 0) {
    return { text: '持平', type: 'stable' }
  }
  if (change > 0) {
    return { text: `上升${change}`, type: 'up' }
  }
  return { text: `下降${Math.abs(change)}`, type: 'down' }
}