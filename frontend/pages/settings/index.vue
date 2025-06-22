<template>
  <view class="settings-page">
    <!-- 用户信息区域 -->
    <view class="user-section">
      <view class="user-info">
        <view class="avatar-section">
          <view class="user-avatar" v-if="userInfo.avatar">
            <image :src="userInfo.avatar" mode="aspectFill" class="avatar-image" />
          </view>
          <view class="user-avatar placeholder" v-else>
            <text class="avatar-text">👤</text>
          </view>
        </view>
        
        <view class="user-details">
          <text class="user-name">{{ userInfo.nickname || '未设置昵称' }}</text>
          <text class="user-id" v-if="userInfo.id">ID: {{ userInfo.id }}</text>
          <text class="user-status">{{ userInfo.isLogin ? '已登录' : '未登录' }}</text>
        </view>
        
        <view class="user-actions">
          <view class="action-btn" v-if="!userInfo.isLogin" @tap="showLogin">
            <text class="btn-text">登录</text>
          </view>
          <view class="action-btn" v-else @tap="showProfile">
            <text class="btn-text">编辑</text>
          </view>
        </view>
      </view>
      
      <!-- 统计信息 -->
      <view class="user-stats">
        <view class="stat-item">
          <text class="stat-value">{{ userStats.followRankings || 0 }}</text>
          <text class="stat-label">关注榜单</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ userStats.followBooks || 0 }}</text>
          <text class="stat-label">关注书籍</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ userStats.readHistory || 0 }}</text>
          <text class="stat-label">浏览记录</text>
        </view>
      </view>
    </view>
    
    <!-- 功能设置区域 -->
    <view class="settings-section">
      <view class="section-title">
        <text class="title-text">功能设置</text>
      </view>
      
      <view class="settings-list">
        <!-- 通知设置 -->
        <view class="setting-item">
          <view class="item-info">
            <text class="item-icon">🔔</text>
            <view class="item-content">
              <text class="item-title">推送通知</text>
              <text class="item-desc">榜单更新、关注书籍更新提醒</text>
            </view>
          </view>
          <switch 
            :checked="settings.pushNotification" 
            @change="toggleSetting('pushNotification', $event)"
            color="#3CC51F"
          />
        </view>
        
        <!-- 自动刷新 -->
        <view class="setting-item">
          <view class="item-info">
            <text class="item-icon">🔄</text>
            <view class="item-content">
              <text class="item-title">自动刷新</text>
              <text class="item-desc">打开应用时自动获取最新数据</text>
            </view>
          </view>
          <switch 
            :checked="settings.autoRefresh" 
            @change="toggleSetting('autoRefresh', $event)"
            color="#3CC51F"
          />
        </view>
        
        <!-- 数据缓存 -->
        <view class="setting-item">
          <view class="item-info">
            <text class="item-icon">💾</text>
            <view class="item-content">
              <text class="item-title">数据缓存</text>
              <text class="item-desc">缓存数据以提升加载速度</text>
            </view>
          </view>
          <switch 
            :checked="settings.enableCache" 
            @change="toggleSetting('enableCache', $event)"
            color="#3CC51F"
          />
        </view>
        
        <!-- 深色模式 -->
        <view class="setting-item">
          <view class="item-info">
            <text class="item-icon">🌙</text>
            <view class="item-content">
              <text class="item-title">深色模式</text>
              <text class="item-desc">跟随系统或手动设置</text>
            </view>
          </view>
          <view class="setting-value" @tap="showThemeOptions">
            <text class="value-text">{{ themeLabels[settings.theme] }}</text>
            <text class="arrow-icon">›</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 应用信息区域 -->
    <view class="app-section">
      <view class="section-title">
        <text class="title-text">应用信息</text>
      </view>
      
      <view class="app-list">
        <!-- 缓存管理 -->
        <view class="app-item" @tap="showCacheManager">
          <view class="item-info">
            <text class="item-icon">🗂</text>
            <text class="item-title">缓存管理</text>
          </view>
          <view class="item-extra">
            <text class="extra-text">{{ formatCacheSize(cacheSize) }}</text>
            <text class="arrow-icon">›</text>
          </view>
        </view>
        
        <!-- 版本信息 -->
        <view class="app-item">
          <view class="item-info">
            <text class="item-icon">📱</text>
            <text class="item-title">当前版本</text>
          </view>
          <view class="item-extra">
            <text class="extra-text">{{ appVersion }}</text>
          </view>
        </view>
        
        <!-- 检查更新 -->
        <view class="app-item" @tap="checkUpdate">
          <view class="item-info">
            <text class="item-icon">⬆️</text>
            <text class="item-title">检查更新</text>
          </view>
          <view class="item-extra">
            <text class="extra-text" v-if="updateChecking">检查中...</text>
            <text class="arrow-icon" v-else>›</text>
          </view>
        </view>
        
        <!-- 意见反馈 -->
        <view class="app-item" @tap="goToFeedback">
          <view class="item-info">
            <text class="item-icon">💬</text>
            <text class="item-title">意见反馈</text>
          </view>
          <view class="item-extra">
            <text class="arrow-icon">›</text>
          </view>
        </view>
        
        <!-- 关于我们 -->
        <view class="app-item" @tap="showAbout">
          <view class="item-info">
            <text class="item-icon">ℹ️</text>
            <text class="item-title">关于我们</text>
          </view>
          <view class="item-extra">
            <text class="arrow-icon">›</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 退出登录 -->
    <view class="logout-section" v-if="userInfo.isLogin">
      <view class="logout-btn" @tap="showLogoutConfirm">
        <text class="logout-text">退出登录</text>
      </view>
    </view>
    
    <!-- 主题选择弹窗 -->
    <view class="theme-popup" v-if="showThemePopup" @tap="hideThemePopup">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="popup-title">选择主题</text>
          <view class="popup-close" @tap="hideThemePopup">
            <text class="close-text">×</text>
          </view>
        </view>
        <view class="theme-options">
          <view 
            class="theme-option" 
            :class="{ 'active': theme.value === settings.theme }"
            v-for="theme in themeOptions" 
            :key="theme.value"
            @tap="selectTheme(theme.value)"
          >
            <text class="theme-icon">{{ theme.icon }}</text>
            <text class="theme-label">{{ theme.label }}</text>
            <text class="theme-check" v-if="theme.value === settings.theme">✓</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 缓存管理弹窗 -->
    <view class="cache-popup" v-if="showCachePopup" @tap="hideCachePopup">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="popup-title">缓存管理</text>
          <view class="popup-close" @tap="hideCachePopup">
            <text class="close-text">×</text>
          </view>
        </view>
        <view class="cache-info">
          <view class="cache-item">
            <text class="cache-label">图片缓存</text>
            <text class="cache-size">{{ formatCacheSize(cacheInfo.images) }}</text>
          </view>
          <view class="cache-item">
            <text class="cache-label">数据缓存</text>
            <text class="cache-size">{{ formatCacheSize(cacheInfo.data) }}</text>
          </view>
          <view class="cache-item">
            <text class="cache-label">总缓存</text>
            <text class="cache-size">{{ formatCacheSize(cacheSize) }}</text>
          </view>
        </view>
        <view class="cache-actions">
          <view class="cache-btn" @tap="clearCache('images')">
            <text class="btn-text">清理图片缓存</text>
          </view>
          <view class="cache-btn" @tap="clearCache('data')">
            <text class="btn-text">清理数据缓存</text>
          </view>
          <view class="cache-btn danger" @tap="clearCache('all')">
            <text class="btn-text">清理全部缓存</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { get, post } from '@/utils/request.js'
import { getSync, setSync, removeSync, clearSync } from '@/utils/storage.js'

/**
 * 设置页面
 * @description 用户设置、应用配置、系统信息等
 */
export default {
  name: 'SettingsPage',
  
  data() {
    return {
      // 用户信息
      userInfo: {
        id: '',
        nickname: '',
        avatar: '',
        isLogin: false
      },
      
      // 用户统计
      userStats: {
        followRankings: 0,
        followBooks: 0,
        readHistory: 0
      },
      
      // 应用设置
      settings: {
        pushNotification: true,
        autoRefresh: true,
        enableCache: true,
        theme: 'auto' // auto, light, dark
      },
      
      // 主题选项
      themeOptions: [
        { value: 'auto', label: '跟随系统', icon: '🔄' },
        { value: 'light', label: '浅色模式', icon: '☀️' },
        { value: 'dark', label: '深色模式', icon: '🌙' }
      ],
      
      themeLabels: {
        auto: '跟随系统',
        light: '浅色模式',
        dark: '深色模式'
      },
      
      // 缓存信息
      cacheSize: 0,
      cacheInfo: {
        images: 0,
        data: 0
      },
      
      // 应用信息
      appVersion: '1.0.0',
      
      // 弹窗状态
      showThemePopup: false,
      showCachePopup: false,
      
      // 加载状态
      updateChecking: false
    }
  },
  
  onLoad() {
    this.initData()
  },
  
  onShow() {
    this.refreshUserStats()
  },
  
  methods: {
    /**
     * 初始化数据
     */
    async initData() {
      try {
        // 加载用户信息
        this.loadUserInfo()
        
        // 加载应用设置
        this.loadSettings()
        
        // 获取缓存信息
        await this.getCacheInfo()
        
        // 获取用户统计
        await this.fetchUserStats()
      } catch (error) {
        console.error('初始化设置页面失败:', error)
      }
    },
    
    /**
     * 加载用户信息
     */
    loadUserInfo() {
      const cachedUser = getSync('user_info')
      if (cachedUser) {
        this.userInfo = {
          ...this.userInfo,
          ...cachedUser,
          isLogin: true
        }
      }
    },
    
    /**
     * 加载应用设置
     */
    loadSettings() {
      const cachedSettings = getSync('app_settings')
      if (cachedSettings) {
        this.settings = {
          ...this.settings,
          ...cachedSettings
        }
      }
    },
    
    /**
     * 获取用户统计
     */
    async fetchUserStats() {
      try {
        const data = await get('/api/user/stats')
        if (data) {
          this.userStats = data
        }
      } catch (error) {
        console.error('获取用户统计失败:', error)
        // 从本地缓存获取
        const followRankings = getSync('follow_rankings') || []
        const followBooks = getSync('follow_books') || []
        
        this.userStats = {
          followRankings: followRankings.length,
          followBooks: followBooks.length,
          readHistory: 0
        }
      }
    },
    
    /**
     * 刷新用户统计
     */
    async refreshUserStats() {
      await this.fetchUserStats()
    },
    
    /**
     * 获取缓存信息
     */
    async getCacheInfo() {
      try {
        // 这里模拟获取缓存大小
        // 实际项目中可能需要调用uni的API或自己统计
        const imageCache = Math.random() * 10 * 1024 * 1024 // 0-10MB
        const dataCache = Math.random() * 5 * 1024 * 1024 // 0-5MB
        
        this.cacheInfo = {
          images: imageCache,
          data: dataCache
        }
        
        this.cacheSize = imageCache + dataCache
      } catch (error) {
        console.error('获取缓存信息失败:', error)
      }
    },
    
    /**
     * 切换设置项
     */
    toggleSetting(key, event) {
      this.settings[key] = event.detail.value
      this.saveSettings()
    },
    
    /**
     * 保存设置
     */
    saveSettings() {
      setSync('app_settings', this.settings)
      
      uni.showToast({
        title: '设置已保存',
        icon: 'success',
        duration: 1500
      })
    },
    
    /**
     * 显示主题选择
     */
    showThemeOptions() {
      this.showThemePopup = true
    },
    
    /**
     * 隐藏主题弹窗
     */
    hideThemePopup() {
      this.showThemePopup = false
    },
    
    /**
     * 选择主题
     */
    selectTheme(theme) {
      this.settings.theme = theme
      this.saveSettings()
      this.hideThemePopup()
      
      // 这里可以应用主题
      this.applyTheme(theme)
    },
    
    /**
     * 应用主题
     */
    applyTheme(theme) {
      // 根据主题设置页面样式
      // 这里是示例实现
      console.log('应用主题:', theme)
    },
    
    /**
     * 显示缓存管理
     */
    showCacheManager() {
      this.getCacheInfo()
      this.showCachePopup = true
    },
    
    /**
     * 隐藏缓存弹窗
     */
    hideCachePopup() {
      this.showCachePopup = false
    },
    
    /**
     * 清理缓存
     */
    async clearCache(type) {
      try {
        uni.showLoading({ title: '清理中...' })
        
        switch (type) {
          case 'images':
            // 清理图片缓存
            this.cacheInfo.images = 0
            break
          case 'data':
            // 清理数据缓存
            clearSync()
            this.cacheInfo.data = 0
            break
          case 'all':
            // 清理全部缓存
            clearSync()
            this.cacheInfo.images = 0
            this.cacheInfo.data = 0
            break
        }
        
        this.cacheSize = this.cacheInfo.images + this.cacheInfo.data
        
        uni.showToast({
          title: '清理完成',
          icon: 'success'
        })
      } catch (error) {
        uni.showToast({
          title: '清理失败',
          icon: 'none'
        })
      } finally {
        uni.hideLoading()
      }
    },
    
    /**
     * 检查更新
     */
    async checkUpdate() {
      this.updateChecking = true
      
      try {
        // 模拟检查更新
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        uni.showToast({
          title: '已是最新版本',
          icon: 'success'
        })
      } catch (error) {
        uni.showToast({
          title: '检查更新失败',
          icon: 'none'
        })
      } finally {
        this.updateChecking = false
      }
    },
    
    /**
     * 显示登录
     */
    showLogin() {
      uni.showToast({
        title: '登录功能开发中',
        icon: 'none'
      })
    },
    
    /**
     * 显示个人资料
     */
    showProfile() {
      uni.showToast({
        title: '个人资料功能开发中',
        icon: 'none'
      })
    },
    
    /**
     * 跳转到反馈页面
     */
    goToFeedback() {
      // 这里暂时不开发反馈页面
      uni.showToast({
        title: '反馈功能开发中',
        icon: 'none'
      })
    },
    
    /**
     * 显示关于我们
     */
    showAbout() {
      uni.showModal({
        title: '关于 JJClawler',
        content: `JJClawler 是一个晋江文学城数据展示小程序\n\n版本：${this.appVersion}\n开发者：JJClawler Team`,
        showCancel: false,
        confirmText: '确定'
      })
    },
    
    /**
     * 显示退出登录确认
     */
    showLogoutConfirm() {
      uni.showModal({
        title: '退出登录',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            this.logout()
          }
        }
      })
    },
    
    /**
     * 退出登录
     */
    logout() {
      // 清除用户信息
      removeSync('user_info')
      
      this.userInfo = {
        id: '',
        nickname: '',
        avatar: '',
        isLogin: false
      }
      
      this.userStats = {
        followRankings: 0,
        followBooks: 0,
        readHistory: 0
      }
      
      uni.showToast({
        title: '已退出登录',
        icon: 'success'
      })
    },
    
    /**
     * 格式化缓存大小
     */
    formatCacheSize(size) {
      if (typeof size !== 'number') return '0B'
      
      const units = ['B', 'KB', 'MB', 'GB']
      let unitIndex = 0
      
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024
        unitIndex++
      }
      
      return `${size.toFixed(1)}${units[unitIndex]}`
    }
  }
}
</script>

<style lang="scss" scoped>
.settings-page {
  min-height: 100vh;
  background-color: $page-background;
  padding-bottom: $safe-area-bottom;
}

.user-section {
  background-color: white;
  margin-bottom: $spacing-sm;
  
  .user-info {
    @include flex-center;
    gap: $spacing-lg;
    padding: $spacing-lg;
    
    .avatar-section {
      flex-shrink: 0;
      
      .user-avatar {
        width: 120rpx;
        height: 120rpx;
        border-radius: 50%;
        overflow: hidden;
        background-color: $background-color;
        @include flex-center;
        
        .avatar-image {
          width: 100%;
          height: 100%;
        }
        
        &.placeholder {
          .avatar-text {
            font-size: 50rpx;
            color: $text-placeholder;
          }
        }
      }
    }
    
    .user-details {
      flex: 1;
      
      .user-name {
        display: block;
        font-size: $font-size-lg;
        font-weight: bold;
        color: $text-primary;
        margin-bottom: 4rpx;
      }
      
      .user-id {
        display: block;
        font-size: $font-size-sm;
        color: $text-secondary;
        margin-bottom: 4rpx;
      }
      
      .user-status {
        display: block;
        font-size: $font-size-sm;
        color: $success-color;
      }
    }
    
    .user-actions {
      .action-btn {
        @include flex-center;
        padding: $spacing-xs $spacing-md;
        background-color: $primary-color;
        border-radius: $border-radius-medium;
        
        .btn-text {
          font-size: $font-size-sm;
          color: white;
        }
        
        &:active {
          opacity: 0.7;
        }
      }
    }
  }
  
  .user-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    border-top: 2rpx solid $border-light;
    
    .stat-item {
      @include flex-column-center;
      padding: $spacing-lg;
      border-right: 2rpx solid $border-light;
      
      &:last-child {
        border-right: none;
      }
      
      .stat-value {
        font-size: $font-size-lg;
        font-weight: bold;
        color: $primary-color;
        margin-bottom: 4rpx;
      }
      
      .stat-label {
        font-size: $font-size-xs;
        color: $text-secondary;
      }
    }
  }
}

.settings-section,
.app-section {
  background-color: white;
  margin-bottom: $spacing-sm;
  
  .section-title {
    padding: $spacing-lg $spacing-lg $spacing-md;
    border-bottom: 2rpx solid $border-light;
    
    .title-text {
      font-size: $font-size-lg;
      font-weight: bold;
      color: $text-primary;
    }
  }
}

.settings-list,
.app-list {
  .setting-item,
  .app-item {
    @include flex-between;
    align-items: center;
    padding: $spacing-lg;
    border-bottom: 2rpx solid $border-light;
    
    &:last-child {
      border-bottom: none;
    }
    
    .item-info {
      @include flex-center;
      gap: $spacing-md;
      flex: 1;
      
      .item-icon {
        font-size: $font-size-lg;
      }
      
      .item-content {
        flex: 1;
        
        .item-title {
          display: block;
          font-size: $font-size-md;
          color: $text-primary;
          margin-bottom: 2rpx;
        }
        
        .item-desc {
          display: block;
          font-size: $font-size-xs;
          color: $text-secondary;
        }
      }
    }
    
    .setting-value,
    .item-extra {
      @include flex-center;
      gap: $spacing-xs;
      
      .value-text,
      .extra-text {
        font-size: $font-size-sm;
        color: $text-secondary;
      }
      
      .arrow-icon {
        font-size: $font-size-md;
        color: $text-placeholder;
      }
    }
    
    &:active {
      background-color: $background-color;
    }
  }
}

.logout-section {
  padding: $spacing-lg;
  
  .logout-btn {
    @include flex-center;
    padding: $spacing-md;
    background-color: $error-color;
    border-radius: $border-radius-medium;
    
    .logout-text {
      font-size: $font-size-md;
      color: white;
    }
    
    &:active {
      opacity: 0.7;
    }
  }
}

.theme-popup,
.cache-popup {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  @include flex-center;
  z-index: 1000;
  
  .popup-content {
    background-color: white;
    border-radius: $border-radius-large;
    margin: $spacing-lg;
    max-width: 600rpx;
    width: 100%;
    overflow: hidden;
  }
  
  .popup-header {
    @include flex-between;
    align-items: center;
    padding: $spacing-lg;
    border-bottom: 2rpx solid $border-light;
    
    .popup-title {
      font-size: $font-size-lg;
      font-weight: bold;
      color: $text-primary;
    }
    
    .popup-close {
      @include flex-center;
      width: 60rpx;
      height: 60rpx;
      border-radius: 50%;
      
      .close-text {
        font-size: $font-size-xl;
        color: $text-placeholder;
      }
      
      &:active {
        background-color: $background-color;
      }
    }
  }
}

.theme-options {
  padding: $spacing-md;
  
  .theme-option {
    @include flex-between;
    align-items: center;
    padding: $spacing-md;
    border-radius: $border-radius-medium;
    transition: background-color 0.3s ease;
    
    .theme-icon {
      font-size: $font-size-lg;
      margin-right: $spacing-md;
    }
    
    .theme-label {
      flex: 1;
      font-size: $font-size-md;
      color: $text-primary;
    }
    
    .theme-check {
      font-size: $font-size-lg;
      color: $primary-color;
    }
    
    &.active {
      background-color: rgba(0, 122, 255, 0.1);
      
      .theme-label {
        color: $primary-color;
        font-weight: bold;
      }
    }
    
    &:active {
      background-color: $background-color;
    }
  }
}

.cache-info {
  padding: $spacing-lg;
  
  .cache-item {
    @include flex-between;
    align-items: center;
    padding: $spacing-sm 0;
    border-bottom: 2rpx solid $border-light;
    
    &:last-child {
      border-bottom: none;
      font-weight: bold;
    }
    
    .cache-label {
      font-size: $font-size-md;
      color: $text-primary;
    }
    
    .cache-size {
      font-size: $font-size-md;
      color: $text-secondary;
    }
  }
}

.cache-actions {
  padding: $spacing-lg;
  @include flex-column-center;
  gap: $spacing-md;
  
  .cache-btn {
    @include flex-center;
    width: 100%;
    padding: $spacing-md;
    background-color: $primary-color;
    border-radius: $border-radius-medium;
    
    .btn-text {
      font-size: $font-size-md;
      color: white;
    }
    
    &.danger {
      background-color: $error-color;
    }
    
    &:active {
      opacity: 0.7;
    }
  }
}
</style>
