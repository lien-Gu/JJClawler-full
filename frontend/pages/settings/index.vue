<template>
  <view class="settings-page">
    <!-- 用户信息区域 -->
    <view class="user-section">
      <BaseCard class="user-card">
        <view class="user-info">
          <view class="avatar-section">
            <view class="user-avatar" @tap="selectAvatar">
              <image v-if="userAvatar" :src="userAvatar" class="avatar-image" />
              <view v-else class="avatar-placeholder">
                <text class="avatar-icon">👤</text>
              </view>
            </view>
          </view>
          
          <view class="user-details">
            <text class="user-name">游客用户</text>
            <text class="user-status">未登录</text>
          </view>
        </view>
      </BaseCard>
    </view>
    
    <!-- 功能设置区域 -->
    <view class="settings-section">
      <BaseCard class="settings-card">
        <template #header>
          <text class="settings-title">功能设置</text>
        </template>
        
        <!-- 设置项列表 -->
        <view class="settings-list">
          <!-- 自动更新 -->
          <view class="setting-item">
            <view class="item-left">
              <view class="item-icon auto-update">
                <text class="icon-text">🔁</text>
              </view>
              <view class="item-info">
                <text class="item-title">自动更新</text>
                <text class="item-desc">自动获取最新数据</text>
              </view>
            </view>
            <switch 
              :checked="settings.autoUpdate" 
              @change="toggleAutoUpdate"
              color="#4A4459"
            />
          </view>
          
          <!-- 本地缓存 -->
          <view class="setting-item">
            <view class="item-left">
              <view class="item-icon local-cache">
                <text class="icon-text">💾</text>
              </view>
              <view class="item-info">
                <text class="item-title">本地缓存</text>
                <text class="item-desc">启用本地数据缓存</text>
              </view>
            </view>
            <switch 
              :checked="settings.localCache" 
              @change="toggleLocalCache"
              color="#4A4459"
            />
          </view>
          
          <!-- 清理数据 -->
          <view class="setting-item clickable" @tap="clearData">
            <view class="item-left">
              <view class="item-icon clear-data">
                <text class="icon-text">🗑️</text>
              </view>
              <view class="item-info">
                <text class="item-title">清理数据</text>
                <text class="item-desc">清除本地数据和缓存</text>
              </view>
            </view>
            <text class="item-arrow">›</text>
          </view>
        </view>
      </BaseCard>
    </view>
    
    <!-- 其他设置 -->
    <view class="other-section">
      <BaseCard class="other-card">
        <view class="other-list">
          <view class="setting-item clickable" @tap="showEnvSelector">
            <view class="item-left">
              <view class="item-icon">
                <text class="icon-text">🔧</text>
              </view>
              <view class="item-info">
                <text class="item-title">环境切换</text>
                <text class="item-desc">当前: {{ currentEnvName }}</text>
              </view>
            </view>
            <text class="item-arrow">›</text>
          </view>
          
          <view class="setting-item clickable" @tap="showAbout">
            <view class="item-left">
              <view class="item-icon">
                <text class="icon-text">ℹ️</text>
              </view>
              <view class="item-info">
                <text class="item-title">关于应用</text>
                <text class="item-desc">版本信息和反馈</text>
              </view>
            </view>
            <text class="item-arrow">›</text>
          </view>
        </view>
      </BaseCard>
    </view>
    
  </view>
</template>

<script>
import BaseCard from '@/components/BaseCard.vue'
import navigation from '@/utils/navigation.js'
import { getCurrentEnvironment, getAvailableEnvironments, setEnvironment } from '@/utils/config.js'

export default {
  name: 'SettingsPage',
  components: {
    BaseCard
  },
  mixins: [navigationMixin],
  
  data() {
    return {
      userAvatar: '',
      settings: {
        autoUpdate: true,
        localCache: true
      },
      currentEnv: '',
      currentEnvName: ''
    }
  },
  
  onLoad() {
    this.loadSettings()
    this.loadCurrentEnv()
  },
  
  methods: {
    loadSettings() {
      try {
        const savedSettings = uni.getStorageSync('appSettings')
        if (savedSettings) {
          this.settings = { ...this.settings, ...savedSettings }
        }
        
        const savedAvatar = uni.getStorageSync('userAvatar')
        if (savedAvatar) {
          this.userAvatar = savedAvatar
        }
      } catch (error) {
        console.error('加载设置失败:', error)
      }
    },
    
    saveSettings() {
      try {
        uni.setStorageSync('appSettings', this.settings)
      } catch (error) {
        console.error('保存设置失败:', error)
      }
    },
    
    toggleAutoUpdate(e) {
      this.settings.autoUpdate = e.detail.value
      this.saveSettings()
    },
    
    toggleLocalCache(e) {
      this.settings.localCache = e.detail.value
      this.saveSettings()
    },
    
    selectAvatar() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          const tempFilePath = res.tempFilePaths[0]
          this.userAvatar = tempFilePath
          try {
            uni.setStorageSync('userAvatar', tempFilePath)
          } catch (error) {
            console.error('保存头像失败:', error)
          }
        }
      })
    },
    
    loadCurrentEnv() {
      this.currentEnv = getCurrentEnvironment()
      const envNames = {
        'test': '测试环境',
        'dev': '开发环境', 
        'prod': '生产环境'
      }
      this.currentEnvName = envNames[this.currentEnv] || this.currentEnv
    },
    
    showEnvSelector() {
      const envs = getAvailableEnvironments()
      const envNames = envs.map(env => {
        const displayNames = {
          'test': '测试环境 (假数据)',
          'dev': '开发环境 (localhost:8000)',
          'prod': '生产环境 (服务器)'
        }
        return displayNames[env.key] || env.name
      })
      
      uni.showActionSheet({
        itemList: envNames,
        success: (res) => {
          const selectedEnv = envs[res.tapIndex]
          if (selectedEnv && !selectedEnv.current) {
            this.switchEnvironment(selectedEnv.key)
          }
        }
      })
    },
    
    switchEnvironment(env) {
      uni.showModal({
        title: '切换环境',
        content: `确定要切换到${env === 'test' ? '测试' : env === 'dev' ? '开发' : '生产'}环境吗？`,
        success: (res) => {
          if (res.confirm) {
            const success = setEnvironment(env)
            if (success) {
              this.loadCurrentEnv()
              uni.showToast({
                title: '环境切换成功',
                icon: 'success',
                duration: 1500
              })
              
              // 重新加载页面数据
              setTimeout(() => {
                uni.reLaunch({
                  url: '/pages/index/index'
                })
              }, 1500)
            } else {
              uni.showToast({
                title: '环境切换失败',
                icon: 'none'
              })
            }
          }
        }
      })
    },
    
    clearData() {
      uni.showModal({
        title: '确认清理',
        content: '确定要清理所有本地数据和缓存吗？此操作不可恢复。',
        confirmColor: '#ff3b30',
        success: (res) => {
          if (res.confirm) {
            try {
              uni.clearStorageSync()
              this.settings = {
                autoUpdate: true,
                localCache: true
              }
              this.userAvatar = ''
              uni.showToast({
                title: '清理成功',
                icon: 'success',
                duration: 1500
              })
            } catch (error) {
              uni.showToast({
                title: '清理失败',
                icon: 'none',
                duration: 2000
              })
            }
          }
        }
      })
    },
    
    showAbout() {
      uni.showModal({
        title: '关于晋江数据中心',
        content: '版本 1.0.0\n\n一个简单的晋江文学城数据查看工具',
        showCancel: false,
        confirmText: '确定'
      })
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.settings-page {
  min-height: 100vh;
  background: $surface-white;
  padding-bottom: env(safe-area-inset-bottom);
}

.user-section {
  padding: $spacing-lg;
  
  .user-card {
    .user-info {
      display: flex;
      align-items: center;
      gap: $spacing-lg;
      padding: $spacing-md 0;
      
      .avatar-section {
        .user-avatar {
          width: 120rpx;
          height: 120rpx;
          border-radius: $radius-full;
          overflow: hidden;
          cursor: pointer;
          
          .avatar-image {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
          
          .avatar-placeholder {
            width: 100%;
            height: 100%;
            background: $surface-container-high;
            display: flex;
            align-items: center;
            justify-content: center;
            
            .avatar-icon {
              font-size: 60rpx;
              opacity: 0.6;
            }
          }
        }
      }
      
      .user-details {
        flex: 1;
        
        .user-name {
          display: block;
          font-size: 32rpx;
          font-weight: 600;
          color: $text-primary;
          margin-bottom: 8rpx;
        }
        
        .user-status {
          font-size: 24rpx;
          color: $text-secondary;
        }
      }
    }
  }
}

.settings-section {
  padding: 0 $spacing-lg $spacing-lg;
  
  .settings-card {
    .settings-title {
      font-size: 28rpx;
      font-weight: 600;
      color: $text-primary;
    }
  }
}

.other-section {
  padding: 0 $spacing-lg;
}

.settings-list,
.other-list {
  .setting-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: $spacing-lg 0;
    
    border-bottom: 1px solid rgba($text-secondary, 0.1);
    
    &:last-child {
      border-bottom: none;
    }
    
    &.clickable {
      &:active {
        background: rgba($text-secondary, 0.05);
        margin: 0 (-$spacing-md);
        padding-left: $spacing-md;
        padding-right: $spacing-md;
        border-radius: $radius-sm;
      }
    }
    
    .item-left {
      display: flex;
      align-items: center;
      gap: $spacing-md;
      flex: 1;
      
      .item-icon {
        width: 56rpx;
        height: 56rpx;
        border-radius: $radius-md;
        display: flex;
        align-items: center;
        justify-content: center;
        
        .icon-text {
          font-size: 28rpx;
        }
        
        &.auto-update {
          background: rgba(#34c759, 0.1);
        }
        
        &.local-cache {
          background: rgba(#007aff, 0.1);
        }
        
        &.clear-data {
          background: rgba(#ff3b30, 0.1);
        }
      }
      
      .item-info {
        flex: 1;
        
        .item-title {
          display: block;
          font-size: 28rpx;
          font-weight: 500;
          color: $text-primary;
          margin-bottom: 4rpx;
        }
        
        .item-desc {
          font-size: 22rpx;
          color: $text-secondary;
          line-height: 1.3;
        }
      }
    }
    
    .item-arrow {
      font-size: 28rpx;
      color: rgba($text-secondary, 0.6);
      font-weight: 300;
    }
  }
}

/* 微信小程序 switch 组件样式调整 */
switch {
  transform: scale(0.8);
}
</style>