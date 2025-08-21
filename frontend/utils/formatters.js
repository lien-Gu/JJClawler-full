/**
 * 通用格式化工具函数
 */

/**
 * 格式化数字显示
 * @param {number} num 数字
 * @returns {string} 格式化后的字符串
 */
export function formatNumber(num) {
  if (typeof num !== 'number') return num || '0';
  
  if (num >= 100000000) {
    return (num / 100000000).toFixed(1) + '亿';
  } else if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k';
  }
  
  return num.toString();
}

/**
 * 格式化字数显示
 * @param {number} count 字数
 * @returns {string} 格式化后的字符串
 */
export function formatWordCount(count) {
  if (typeof count !== 'number') return count || '未知';
  
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + '万字';
  } else if (count >= 1000) {
    return (count / 1000).toFixed(1) + '千字';
  }
  
  return count + '字';
}

/**
 * 格式化时间显示 (相对时间)
 * @param {string|Date} time 时间
 * @returns {string} 格式化后的字符串
 */
export function formatTime(time) {
  if (!time) return '未知';
  
  const now = new Date();
  const targetTime = new Date(time);
  const diff = now - targetTime;
  
  const minutes = Math.floor(diff / (1000 * 60));
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const months = Math.floor(diff / (1000 * 60 * 60 * 24 * 30));
  
  if (minutes < 1) {
    return '刚刚';
  } else if (minutes < 60) {
    return `${minutes}分钟前`;
  } else if (hours < 24) {
    return `${hours}小时前`;
  } else if (days < 30) {
    return `${days}天前`;
  } else if (months < 12) {
    return `${months}个月前`;
  } else {
    return targetTime.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
}

/**
 * 格式化日期显示 (绝对日期)
 * @param {string|Date} date 日期
 * @param {object} options 格式化选项
 * @returns {string} 格式化后的字符串
 */
export function formatDate(date, options = {}) {
  if (!date) return '未知';
  
  const defaultOptions = {
    year: 'numeric',
    month: 'short', 
    day: 'numeric',
    ...options
  };
  
  const targetDate = new Date(date);
  return targetDate.toLocaleDateString('zh-CN', defaultOptions);
}

/**
 * 格式化百分比
 * @param {number} value 数值 (0-1)
 * @param {number} decimals 小数位数
 * @returns {string} 格式化后的字符串
 */
export function formatPercentage(value, decimals = 1) {
  if (typeof value !== 'number') return '0%';
  
  return (value * 100).toFixed(decimals) + '%';
}

/**
 * 格式化货币
 * @param {number} amount 金额
 * @param {string} currency 货币符号
 * @returns {string} 格式化后的字符串
 */
export function formatCurrency(amount, currency = '¥') {
  if (typeof amount !== 'number') return currency + '0';
  
  return currency + amount.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

/**
 * 格式化文件大小
 * @param {number} bytes 字节数
 * @returns {string} 格式化后的字符串
 */
export function formatFileSize(bytes) {
  if (typeof bytes !== 'number') return '0 B';
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return size.toFixed(1) + ' ' + units[unitIndex];
}