/**
 * 格式化混入
 * 提供通用的格式化方法
 */

import { 
  formatNumber, 
  formatWordCount, 
  formatTime, 
  formatDate, 
  formatPercentage, 
  formatCurrency,
  formatFileSize 
} from '@/utils/formatters.js';

export default {
  methods: {
    /**
     * 格式化数字显示
     */
    formatNumber(num) {
      return formatNumber(num);
    },
    
    /**
     * 格式化字数显示
     */
    formatWordCount(count) {
      return formatWordCount(count);
    },
    
    /**
     * 格式化时间显示 (相对时间)
     */
    formatTime(time) {
      return formatTime(time);
    },
    
    /**
     * 格式化日期显示 (绝对日期)
     */
    formatDate(date, options = {}) {
      return formatDate(date, options);
    },
    
    /**
     * 格式化百分比
     */
    formatPercentage(value, decimals = 1) {
      return formatPercentage(value, decimals);
    },
    
    /**
     * 格式化货币
     */
    formatCurrency(amount, currency = '¥') {
      return formatCurrency(amount, currency);
    },
    
    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
      return formatFileSize(bytes);
    }
  }
};