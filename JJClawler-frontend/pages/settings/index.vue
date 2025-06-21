<template>
  <view class="settings-page">
    <!-- 用户信息区域 -->
    <view class="user-section">
      <view class="user-avatar"></view>
      <view class="login-btn" @tap="handleLogin">
        <text class="login-text">login</text>
      </view>
    </view>
    
    <!-- 分隔线 -->
    <view class="section-divider"></view>
    
    <!-- 设置选项 -->
    <view class="settings-section">
      <!-- 自动刷新 -->
      <view class="setting-item">
        <text class="setting-label">自动刷新</text>
        <view class="setting-switch" :class="{ active: autoRefresh }" @tap="toggleAutoRefresh">
          <view class="switch-handle"></view>
        </view>
      </view>
      
      <!-- 数据缓存 -->
      <view class="setting-item">
        <text class="setting-label">数据缓存</text>
        <view class="setting-switch" :class="{ active: dataCache }" @tap="toggleDataCache">
          <view class="switch-handle"></view>
        </view>
      </view>
      
      <!-- 自动订阅 -->
      <view class="setting-item">
        <text class="setting-label">自动订阅</text>
        <view class="setting-switch" :class="{ active: autoSubscribe }" @tap="toggleAutoSubscribe">
          <view class="switch-handle"></view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 设置页面
 * @description 用户设置和应用配置，按照Figma设计样式
 */
export default {
  name: 'SettingsPage',
  
  data() {
    return {
      // 用户登录状态
      isLoggedIn: false,
      userInfo: null,
      
      // 设置选项
      autoRefresh: true,
      dataCache: true,
      autoSubscribe: false
    }
  },
  
  onLoad() {
    this.loadSettings()
  },
  
  methods: {
    /**
     * 加载设置
     */
    loadSettings() {
      try {
        // 从本地存储加载设置
        this.autoRefresh = uni.getStorageSync('autoRefresh') !== false
        this.dataCache = uni.getStorageSync('dataCache') !== false
        this.autoSubscribe = uni.getStorageSync('autoSubscribe') === true
        
        // 检查登录状态
        const userInfo = uni.getStorageSync('userInfo')
        if (userInfo) {
          this.isLoggedIn = true
          this.userInfo = userInfo
        }
      } catch (error) {
        console.error('加载设置失败:', error)
      }
    },
    
    /**
     * 处理登录
     */
    handleLogin() {
      if (this.isLoggedIn) {
        // 已登录，显示用户菜单或退出登录
        this.showUserMenu()
      } else {
        // 未登录，跳转到登录页面
        this.goToLogin()
      }
    },
    
    /**
     * 跳转到登录页面
     */
    goToLogin() {
      // 这里可以跳转到登录页面或者调用登录接口
      uni.showModal({
        title: '登录',
        content: '是否要进行登录？',
        confirmText: '登录',
        success: (res) => {
          if (res.confirm) {
            // 模拟登录成功
            this.mockLogin()
          }
        }
      })
    },
    
    /**
     * 模拟登录
     */
    mockLogin() {
      const userInfo = {
        id: '12345',
        username: 'user123',
        avatar: '',
        loginTime: new Date().toISOString()
      }
      
      this.isLoggedIn = true
      this.userInfo = userInfo
      
      // 保存到本地存储
      uni.setStorageSync('userInfo', userInfo)
      
      uni.showToast({
        title: '登录成功',
        icon: 'success',
        duration: 1500
      })
    },
    
    /**
     * 显示用户菜单
     */
    showUserMenu() {
      uni.showActionSheet({
        itemList: ['退出登录'],
        success: (res) => {
          if (res.tapIndex === 0) {
            this.logout()
          }
        }
      })
    },
    
    /**
     * 退出登录
     */
    logout() {
      uni.showModal({
        title: '确认退出',
        content: '是否要退出登录？',
        confirmText: '退出',
        success: (res) => {
          if (res.confirm) {
            this.isLoggedIn = false
            this.userInfo = null
            
            // 清除本地存储
            uni.removeStorageSync('userInfo')
            
            uni.showToast({
              title: '已退出登录',
              icon: 'success',
              duration: 1500
            })
          }
        }
      })
    },
    
    /**
     * 切换自动刷新
     */
    toggleAutoRefresh() {
      this.autoRefresh = !this.autoRefresh
      uni.setStorageSync('autoRefresh', this.autoRefresh)
      
      uni.showToast({
        title: this.autoRefresh ? '已开启自动刷新' : '已关闭自动刷新',
        icon: 'none',
        duration: 1500
      })
    },
    
    /**
     * 切换数据缓存
     */
    toggleDataCache() {
      this.dataCache = !this.dataCache
      uni.setStorageSync('dataCache', this.dataCache)
      
      uni.showToast({
        title: this.dataCache ? '已开启数据缓存' : '已关闭数据缓存',
        icon: 'none',
        duration: 1500
      })
    },
    
    /**
     * 切换自动订阅
     */
    toggleAutoSubscribe() {
      this.autoSubscribe = !this.autoSubscribe
      uni.setStorageSync('autoSubscribe', this.autoSubscribe)
      
      uni.showToast({
        title: this.autoSubscribe ? '已开启自动订阅' : '已关闭自动订阅',
        icon: 'none',
        duration: 1500
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.settings-page {
  min-height: 100vh;
  background-color: #f4f0eb;
  padding-bottom: $safe-area-bottom;
}

.user-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 64rpx 32rpx;
  margin-bottom: 96rpx; // 增加到96rpx，提供更明显的间距
  background-color: #f4f0eb;
  
  .user-avatar {
    width: 200rpx;
    height: 200rpx;
    background-color: #cd853f;  // 橙色圆形头像
    border-radius: 50%;
  }
  
  .login-btn {
    background-color: #64a347;  // brand primary
    border-radius: 32rpx;
    padding: 16rpx 32rpx;
    
    .login-text {
      font-size: 32rpx;
      font-weight: 400;
      color: #ffffff;
      font-family: 'Inter', sans-serif;
    }
    
    &:active {
      opacity: 0.8;
    }
  }
}

.settings-section {
  padding: 32rpx 32rpx 0 32rpx; // 顶部增加32rpx内边距，进一步分离区域
  
  .setting-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: #f4f0eb;
    padding: 48rpx 0;
    border-bottom: 2rpx solid #e0e0e0;
    
    &:last-child {
      border-bottom: none;
    }
    
    .setting-label {
      font-size: 36rpx;
      font-weight: 400;
      color: #333333;
      font-family: 'Inter', sans-serif;
    }
    
    .setting-switch {
      width: 120rpx;
      height: 60rpx;
      background-color: #64a347;  // 默认开启状态为绿色
      border-radius: 30rpx;
      position: relative;
      transition: background-color 0.3s ease;
      
      &:not(.active) {
        background-color: #999999;  // 关闭状态为灰色
      }
      
      .switch-handle {
        width: 48rpx;
        height: 48rpx;
        background-color: #ffffff;
        border-radius: 50%;
        position: absolute;
        top: 6rpx;
        left: 6rpx;
        transition: transform 0.3s ease;
      }
      
      &.active .switch-handle {
        transform: translateX(60rpx);
      }
      
      &:active {
        opacity: 0.8;
      }
    }
  }
}

/* 分隔线样式 */
.section-divider {
  height: 2rpx;
  background-color: rgba(0, 0, 0, 0.1);
  margin: 0 32rpx;
  opacity: 0.5;
}
</style>
