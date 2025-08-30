/**
 * API统一导出入口
 */

export { booksApi } from './modules/books'
export { rankingsApi } from './modules/rankings'
export { reportsApi } from './modules/reports'  
export { scheduleApi } from './modules/schedule'

// 导出请求管理器实例，便于环境切换等操作
export { requestManager } from './request'