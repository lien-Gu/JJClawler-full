/**
 * 微信小程序用户管理工具类
 * 处理用户登录、信息存储和关注列表管理
 */

class UserManager {
  constructor() {
    this.storageKeys = {
      USER_INFO: 'userInfo',
      FOLLOW_LIST: 'followList',
      LOGIN_STATUS: 'loginStatus'
    }
    
    // 开发阶段的测试关注数据
    this.testFollowData = [
      {
        id: '12345',
        type: 'book',
        name: '测试书籍1',
        author: '测试作者1',
        category: '现代言情',
        isOnList: true,
        followDate: new Date().toISOString()
      },
      {
        id: '67890',
        type: 'book', 
        name: '测试书籍2',
        author: '测试作者2',
        category: '古代言情',
        isOnList: false,
        followDate: new Date().toISOString()
      },
      {
        id: 'ranking_001',
        type: 'ranking',
        name: '测试榜单1',
        description: '热门榜单',
        category: '综合榜',
        followDate: new Date().toISOString()
      }
    ]
  }

  /**
   * 微信登录
   * @returns {Promise<Object>} 登录结果
   */
  async login() {
    try {
      // 先获取用户信息（必须在用户点击事件的同步调用中）
      const userProfileRes = await new Promise((resolve, reject) => {
        uni.getUserProfile({
          desc: '用于完善用户资料',
          success: resolve,
          fail: reject
        })
      })

      console.log('用户信息获取成功:', userProfileRes)

      // 再获取微信登录凭证
      const loginRes = await new Promise((resolve, reject) => {
        uni.login({
          provider: 'weixin',
          success: resolve,
          fail: reject
        })
      })

      console.log('微信登录凭证获取成功:', loginRes)

      // 构建用户信息对象
      const userInfo = {
        openid: loginRes.code, // 临时使用code作为标识，生产环境需要通过后端换取openid
        nickName: userProfileRes.userInfo.nickName,
        avatarUrl: userProfileRes.userInfo.avatarUrl,
        gender: userProfileRes.userInfo.gender,
        city: userProfileRes.userInfo.city,
        province: userProfileRes.userInfo.province,
        country: userProfileRes.userInfo.country,
        loginTime: new Date().toISOString()
      }

      // 保存用户信息和登录状态
      await this.saveUserInfo(userInfo)
      await this.setLoginStatus(true)
      
      // 首次登录时初始化测试关注数据
      if (!(await this.getFollowList()).length) {
        await this.initTestFollowData()
      }

      return {
        success: true,
        userInfo,
        message: '登录成功'
      }

    } catch (error) {
      console.error('登录失败:', error)
      return {
        success: false,
        error,
        message: '登录失败，请重试'
      }
    }
  }

  /**
   * 退出登录
   */
  async logout() {
    try {
      // 清除用户信息和登录状态
      uni.removeStorageSync(this.storageKeys.USER_INFO)
      uni.removeStorageSync(this.storageKeys.LOGIN_STATUS)
      // 保留关注列表数据
      
      return {
        success: true,
        message: '退出成功'
      }
    } catch (error) {
      console.error('退出失败:', error)
      return {
        success: false,
        message: '退出失败'
      }
    }
  }

  /**
   * 检查登录状态
   * @returns {boolean} 是否已登录
   */
  isLoggedIn() {
    try {
      // 添加安全检查，确保在应用完全初始化后再访问存储
      if (typeof uni === 'undefined') {
        console.warn('uni对象未准备就绪')
        return false
      }
      
      const loginStatus = uni.getStorageSync(this.storageKeys.LOGIN_STATUS)
      const userInfo = uni.getStorageSync(this.storageKeys.USER_INFO)
      return loginStatus && userInfo
    } catch (error) {
      console.error('检查登录状态失败:', error)
      return false
    }
  }

  /**
   * 获取用户信息
   * @returns {Object|null} 用户信息对象
   */
  getUserInfo() {
    try {
      return uni.getStorageSync(this.storageKeys.USER_INFO) || null
    } catch (error) {
      console.error('获取用户信息失败:', error)
      return null
    }
  }

  /**
   * 保存用户信息
   * @param {Object} userInfo 用户信息
   */
  async saveUserInfo(userInfo) {
    try {
      uni.setStorageSync(this.storageKeys.USER_INFO, userInfo)
    } catch (error) {
      console.error('保存用户信息失败:', error)
      throw error
    }
  }

  /**
   * 设置登录状态
   * @param {boolean} status 登录状态
   */
  async setLoginStatus(status) {
    try {
      uni.setStorageSync(this.storageKeys.LOGIN_STATUS, status)
    } catch (error) {
      console.error('设置登录状态失败:', error)
      throw error
    }
  }

  /**
   * 获取关注列表
   * @returns {Array} 关注列表
   */
  async getFollowList() {
    try {
      return uni.getStorageSync(this.storageKeys.FOLLOW_LIST) || []
    } catch (error) {
      console.error('获取关注列表失败:', error)
      return []
    }
  }

  /**
   * 保存关注列表
   * @param {Array} followList 关注列表
   */
  async saveFollowList(followList) {
    try {
      uni.setStorageSync(this.storageKeys.FOLLOW_LIST, followList)
    } catch (error) {
      console.error('保存关注列表失败:', error)
      throw error
    }
  }

  /**
   * 添加关注项
   * @param {Object} item 关注项
   */
  async addFollowItem(item) {
    try {
      const followList = await this.getFollowList()
      
      // 检查是否已关注
      const existingIndex = followList.findIndex(follow => follow.id === item.id && follow.type === item.type)
      
      if (existingIndex === -1) {
        const followItem = {
          ...item,
          followDate: new Date().toISOString()
        }
        followList.push(followItem)
        await this.saveFollowList(followList)
        
        return {
          success: true,
          message: '关注成功'
        }
      } else {
        return {
          success: false,
          message: '已经关注过了'
        }
      }
    } catch (error) {
      console.error('添加关注失败:', error)
      throw error
    }
  }

  /**
   * 取消关注
   * @param {string} id 项目ID
   * @param {string} type 项目类型
   */
  async removeFollowItem(id, type) {
    try {
      const followList = await this.getFollowList()
      const newList = followList.filter(item => !(item.id === id && item.type === type))
      
      await this.saveFollowList(newList)
      
      return {
        success: true,
        message: '取消关注成功'
      }
    } catch (error) {
      console.error('取消关注失败:', error)
      throw error
    }
  }

  /**
   * 检查是否已关注
   * @param {string} id 项目ID
   * @param {string} type 项目类型
   * @returns {boolean} 是否已关注
   */
  async isFollowing(id, type) {
    try {
      const followList = await this.getFollowList()
      return followList.some(item => item.id === id && item.type === type)
    } catch (error) {
      console.error('检查关注状态失败:', error)
      return false
    }
  }

  /**
   * 初始化测试关注数据
   */
  async initTestFollowData() {
    try {
      console.log('初始化测试关注数据')
      await this.saveFollowList(this.testFollowData)
    } catch (error) {
      console.error('初始化测试数据失败:', error)
    }
  }

  /**
   * 清除所有数据
   */
  async clearAllData() {
    try {
      uni.removeStorageSync(this.storageKeys.USER_INFO)
      uni.removeStorageSync(this.storageKeys.FOLLOW_LIST)
      uni.removeStorageSync(this.storageKeys.LOGIN_STATUS)
    } catch (error) {
      console.error('清除数据失败:', error)
      throw error
    }
  }
}

// 创建全局用户管理实例
const userManager = new UserManager()

export default userManager