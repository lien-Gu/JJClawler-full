/**
 * 用户状态管理Store
 * 提供全局用户状态和关注状态的实时同步
 */
import { reactive, computed } from 'vue'
import userManager from '@/utils/user.js'

// 用户状态响应式对象
const userState = reactive({
  // 登录状态
  isLoggedIn: false,
  
  // 用户信息
  userInfo: null,
  
  // 关注列表
  followList: [],
  
  // 加载状态
  loading: false,
  
  // 错误状态
  error: null
})

// 创建用户Store
export const useUserStore = () => {
  // 计算属性
  const followedBookIds = computed(() => {
    return userState.followList
      .filter(item => item.type === 'book')
      .map(item => item.id)
  })
  
  const followedRankingIds = computed(() => {
    return userState.followList
      .filter(item => item.type === 'ranking')
      .map(item => item.id)
  })
  
  const followStats = computed(() => {
    const books = userState.followList.filter(item => item.type === 'book')
    const rankings = userState.followList.filter(item => item.type === 'ranking')
    
    return {
      totalItems: userState.followList.length,
      booksCount: books.length,
      rankingsCount: rankings.length,
      onListBooksCount: books.filter(book => book.isOnList).length
    }
  })

  // 初始化用户状态
  const initUserState = async () => {
    try {
      userState.loading = true
      userState.error = null
      
      // 检查登录状态
      const isLoggedIn = userManager.isLoggedIn()
      userState.isLoggedIn = isLoggedIn
      
      if (isLoggedIn) {
        // 获取用户信息
        const userInfo = userManager.getUserInfo()
        userState.userInfo = userInfo
        
        // 获取关注列表
        const followList = await userManager.getFollowList()
        userState.followList = followList
        
        console.log('用户状态初始化成功:', {
          isLoggedIn,
          userInfo: userInfo?.nickName,
          followCount: followList.length
        })
      }
    } catch (error) {
      console.error('用户状态初始化失败:', error)
      userState.error = error.message
    } finally {
      userState.loading = false
    }
  }

  // 用户登录
  const login = async () => {
    try {
      userState.loading = true
      userState.error = null
      
      const result = await userManager.login()
      
      if (result.success) {
        userState.isLoggedIn = true
        userState.userInfo = result.userInfo
        
        // 重新加载关注列表
        await refreshFollowList()
        
        console.log('用户登录成功:', result.userInfo.nickName)
        return result
      } else {
        userState.error = result.message
        return result
      }
    } catch (error) {
      console.error('登录失败:', error)
      userState.error = error.message
      return {
        success: false,
        message: error.message
      }
    } finally {
      userState.loading = false
    }
  }

  // 用户退出
  const logout = async () => {
    try {
      const result = await userManager.logout()
      
      if (result.success) {
        userState.isLoggedIn = false
        userState.userInfo = null
        // 保留关注列表数据，但不在UI中显示
        
        console.log('用户退出成功')
      }
      
      return result
    } catch (error) {
      console.error('退出失败:', error)
      return {
        success: false,
        message: error.message
      }
    }
  }

  // 刷新关注列表
  const refreshFollowList = async () => {
    try {
      const followList = await userManager.getFollowList()
      userState.followList = followList
      console.log('关注列表已刷新:', followList.length, '项')
    } catch (error) {
      console.error('刷新关注列表失败:', error)
      userState.error = error.message
    }
  }

  // 添加关注
  const addFollow = async (item) => {
    if (!userState.isLoggedIn) {
      throw new Error('请先登录')
    }
    
    try {
      const result = await userManager.addFollowItem(item)
      
      if (result.success) {
        // 实时更新状态
        await refreshFollowList()
        console.log('关注添加成功:', item.name || item.title)
      }
      
      return result
    } catch (error) {
      console.error('添加关注失败:', error)
      throw error
    }
  }

  // 取消关注
  const removeFollow = async (id, type) => {
    if (!userState.isLoggedIn) {
      throw new Error('请先登录')
    }
    
    try {
      const result = await userManager.removeFollowItem(id, type)
      
      if (result.success) {
        // 实时更新状态
        await refreshFollowList()
        console.log('关注取消成功:', id)
      }
      
      return result
    } catch (error) {
      console.error('取消关注失败:', error)
      throw error
    }
  }

  // 检查是否已关注
  const isFollowing = (id, type) => {
    if (!userState.isLoggedIn) {
      return false
    }
    
    return userState.followList.some(item => item.id === id && item.type === type)
  }

  // 切换关注状态
  const toggleFollow = async (item) => {
    if (!userState.isLoggedIn) {
      throw new Error('请先登录')
    }
    
    const { id, type } = item
    const isCurrentlyFollowing = isFollowing(id, type)
    
    try {
      if (isCurrentlyFollowing) {
        return await removeFollow(id, type)
      } else {
        return await addFollow(item)
      }
    } catch (error) {
      console.error('切换关注状态失败:', error)
      throw error
    }
  }

  // 清除错误状态
  const clearError = () => {
    userState.error = null
  }

  return {
    // 状态
    state: userState,
    
    // 计算属性
    followedBookIds,
    followedRankingIds,
    followStats,
    
    // 方法
    initUserState,
    login,
    logout,
    refreshFollowList,
    addFollow,
    removeFollow,
    isFollowing,
    toggleFollow,
    clearError
  }
}

// 创建全局store实例
const userStore = useUserStore()

export default userStore