/**
 * 应用初始化工具
 * 处理应用启动时的初始化逻辑
 */
import userStore from '@/store/userStore.js'

/**
 * 应用启动初始化
 */
export const initializeApp = async () => {
  try {
    console.log('开始初始化应用...')
    
    // 等待一个微任务，确保应用实例完全就绪
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // 1. 初始化用户状态管理
    await userStore.initUserState()
    
    // 2. 检查并初始化测试数据（仅在开发阶段）
    initTestDataIfNeeded()
    
    console.log('应用初始化完成')
    
    return {
      success: true,
      message: '应用初始化成功'
    }
  } catch (error) {
    console.error('应用初始化失败:', error)
    return {
      success: false,
      message: '应用初始化失败',
      error
    }
  }
}

/**
 * 检查并初始化测试数据
 */
const initTestDataIfNeeded = () => {
  try {
    // 如果用户已登录但关注列表为空，添加测试数据
    if (userStore.state.isLoggedIn && userStore.state.followList.length === 0) {
      console.log('用户已登录但关注列表为空，初始化测试数据')
      // userManager会在登录时自动初始化测试数据，这里不需要重复操作
      return
    }
    
    // 如果是第一次使用应用，可以设置一些默认配置
    const isFirstTime = !uni.getStorageSync('appInitialized')
    if (isFirstTime) {
      console.log('首次启动应用，设置默认配置')
      
      // 设置默认应用设置
      const defaultSettings = {
        autoUpdate: true,
        localCache: true
      }
      uni.setStorageSync('appSettings', defaultSettings)
      
      // 标记已初始化
      uni.setStorageSync('appInitialized', true)
      
      console.log('默认配置已设置')
    }
  } catch (error) {
    console.error('初始化测试数据失败:', error)
  }
}

/**
 * 用户登录成功后的初始化
 */
export const initializeUserData = (userInfo) => {
  try {
    console.log('初始化用户数据:', userInfo.nickName)
    
    // 1. 检查是否需要迁移本地数据
    migrateLocalDataIfNeeded()
    
    // 2. 同步用户状态
    userStore.refreshFollowList()
    
    console.log('用户数据初始化完成')
    
    return {
      success: true,
      message: '用户数据初始化成功'
    }
  } catch (error) {
    console.error('用户数据初始化失败:', error)
    return {
      success: false,
      message: '用户数据初始化失败',
      error
    }
  }
}

/**
 * 迁移本地数据（如果需要）
 */
const migrateLocalDataIfNeeded = () => {
  try {
    // 检查是否有旧版本的关注数据需要迁移
    const oldFollowList = uni.getStorageSync('followList')
    const migrationVersion = uni.getStorageSync('migrationVersion') || '1.0.0'
    
    if (oldFollowList && Array.isArray(oldFollowList) && migrationVersion === '1.0.0') {
      console.log('发现旧版本关注数据，开始迁移...')
      
      // 确保数据格式正确
      const migratedData = oldFollowList.map(item => ({
        id: item.id,
        type: item.type || 'book',
        name: item.name || item.title,
        author: item.author || '未知作者',
        category: item.category || '未分类',
        isOnList: item.isOnList !== undefined ? item.isOnList : true,
        followDate: item.followDate || new Date().toISOString()
      }))
      
      // 保存迁移后的数据
      uni.setStorageSync('followList', migratedData)
      uni.setStorageSync('migrationVersion', '1.1.0')
      
      console.log('数据迁移完成，共迁移', migratedData.length, '项数据')
    }
  } catch (error) {
    console.error('数据迁移失败:', error)
  }
}

/**
 * 清理应用数据
 */
export const clearAppData = () => {
  try {
    console.log('开始清理应用数据...')
    
    // 清理用户相关数据
    userStore.clearError()
    
    // 清理本地存储
    const keysToKeep = ['appSettings'] // 保留应用设置
    const allKeys = uni.getStorageInfoSync().keys
    
    for (const key of allKeys) {
      if (!keysToKeep.includes(key)) {
        uni.removeStorageSync(key)
      }
    }
    
    console.log('应用数据清理完成')
    
    return {
      success: true,
      message: '数据清理成功'
    }
  } catch (error) {
    console.error('清理应用数据失败:', error)
    return {
      success: false,
      message: '数据清理失败',
      error
    }
  }
}

/**
 * 获取应用状态信息
 */
export const getAppStatus = () => {
  try {
    const storageInfo = uni.getStorageInfoSync()
    const userInfo = userStore.state.userInfo
    const followList = userStore.state.followList
    
    return {
      storage: {
        keys: storageInfo.keys.length,
        size: storageInfo.currentSize
      },
      user: {
        isLoggedIn: userStore.state.isLoggedIn,
        nickName: userInfo?.nickName || 'N/A',
        followCount: followList.length
      },
      app: {
        initialized: !!uni.getStorageSync('appInitialized'),
        migrationVersion: uni.getStorageSync('migrationVersion') || '1.0.0'
      }
    }
  } catch (error) {
    console.error('获取应用状态失败:', error)
    return null
  }
}

export default {
  initializeApp,
  initializeUserData,
  clearAppData,
  getAppStatus
}