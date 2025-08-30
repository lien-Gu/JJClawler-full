/**
 * 应用常量定义
 */

// 环境配置
export const ENVIRONMENTS = {
  DEV: 'dev',
  TEST: 'test', 
  PROD: 'prod'
}

// 本地存储键名
export const STORAGE_KEYS = {
  CURRENT_ENV: 'currentEnv',
  USER_FOLLOWS: 'userFollows',
  APP_CONFIG: 'app_config',
  USER_SETTINGS: 'userSettings',
  CACHE_PREFIX: 'cache_'
}

// API路径常量
export const API_PATHS = {
  BOOKS: '/api/v1/books',
  RANKINGS: '/api/v1/rankings',
  REPORTS: '/api/v1/reports',
  SCHEDULE: '/api/v1/schedule'
}

// 页面路径常量
export const PAGE_PATHS = {
  INDEX: '/pages/index/index',
  RANKING_LIST: '/pages/ranking/index',
  RANKING_DETAIL: '/pages/ranking/detail',
  BOOK_DETAIL: '/pages/book/detail',
  FOLLOW: '/pages/follow/index',
  SETTINGS: '/pages/settings/index',
  REPORT_DETAIL: '/pages/report/detail',
  WEBVIEW: '/pages/webview/index'
}

// 榜单类型
export const RANKING_TYPES = {
  JIAZI: 'jiazi',
  ROMANCE: 'romance',
  PURE_LOVE: 'pure_love',
  DERIVATIVE: 'derivative'
}

// 书籍状态
export const BOOK_STATUS = {
  ONGOING: 'ongoing',
  COMPLETED: 'completed',
  PAUSED: 'paused',
  DRAFT: 'draft'
}

// 请求状态
export const REQUEST_STATUS = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error'
}

// 时间间隔
export const TIME_INTERVALS = {
  HOUR: 'hour',
  DAY: 'day',
  WEEK: 'week',
  MONTH: 'month'
}

// 默认配置
export const DEFAULT_CONFIG = {
  PAGE_SIZE: 20,
  TIMEOUT: 10000,
  CACHE_DURATION: 30 * 60 * 1000, // 30分钟
  MAX_RETRY: 3
}

// 错误消息
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络连接失败，请检查网络设置',
  SERVER_ERROR: '服务器错误，请稍后重试',
  DATA_NOT_FOUND: '数据不存在',
  INVALID_PARAMS: '参数错误',
  UNAUTHORIZED: '未授权访问'
}