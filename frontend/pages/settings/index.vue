<template>
  <view class="settings-page">
    <!-- 用户信息区域 -->
    <view class="user-section">
      <view class="user-info">
        <view class="avatar-section">
          <view class="user-avatar placeholder">
            <text class="avatar-text">👤</text>
          </view>
        </view>
        
        <view class="user-details">
          <text class="user-name">游客用户</text>
          <text class="user-status">未登录</text>
        </view>
      </view>
    </view>
    
    <!-- 功能设置区域 -->
    <view class="settings-section">
      <view class="section-title">功能设置</view>
      
      <!-- 设置项列表 -->
      <view class="settings-list">
        <view class="setting-item" @tap="goToApiConfig">
          <view class="item-content">
            <text class="item-icon">🔧</text>
            <view class="item-info">
              <text class="item-title">API配置</text>
              <text class="item-desc">配置数据源和环境</text>
            </view>
          </view>
          <text class="item-arrow">></text>
        </view>
        
        <view class="setting-item" @tap="clearCache">
          <view class="item-content">
            <text class="item-icon">🗑️</text>
            <view class="item-info">
              <text class="item-title">清除缓存</text>
              <text class="item-desc">清除本地存储的数据</text>
            </view>
          </view>
          <text class="item-arrow">></text>
        </view>
        
        <view class="setting-item" @tap="showAbout">
          <view class="item-content">
            <text class="item-icon">ℹ️</text>
            <view class="item-info">
              <text class="item-title">关于应用</text>
              <text class="item-desc">版本信息和反馈</text>
            </view>
          </view>
          <text class="item-arrow">></text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'SettingsPage',
  
  data() {
    return {}
  },
  
  methods: {
    goToApiConfig() {
      uni.navigateTo({
        url: '/pages/settings/api-config'
      })
    },
    
    clearCache() {
      uni.showModal({
        title: '确认清除',
        content: '确定要清除所有本地缓存数据吗？',
        success: (res) => {
          if (res.confirm) {
            try {
              uni.clearStorageSync()
              uni.showToast({
                title: '清除成功',
                icon: 'success',
                duration: 1500
              })
            } catch (error) {
              uni.showToast({
                title: '清除失败',
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
.settings-page {
  min-height: 100vh;
  background-color: $page-background;
  padding-bottom: $safe-area-bottom;
}

.user-section {
  background-color: white;
  margin-bottom: $spacing-md;
  padding: $spacing-lg;
  
  .user-info {
    @include flex-center;
    gap: $spacing-md;
    
    .avatar-section {
      .user-avatar {
        width: 120rpx;
        height: 120rpx;
        border-radius: 50%;
        overflow: hidden;
        background-color: $background-color;
        @include flex-center;
        
        &.placeholder {
          .avatar-text {
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
        font-size: $font-size-lg;
        font-weight: bold;
        color: $text-primary;
        margin-bottom: 4rpx;
      }
      
      .user-status {
        font-size: $font-size-sm;
        color: $text-secondary;
      }
    }
  }
}

.settings-section {
  background-color: white;
  padding: $spacing-lg;
  
  .section-title {
    font-size: $font-size-lg;
    font-weight: bold;
    color: $text-primary;
    margin-bottom: $spacing-lg;
  }
  
  .settings-list {
    .setting-item {
      @include flex-between;
      align-items: center;
      padding: $spacing-lg 0;
      border-bottom: 2rpx solid $border-light;
      
      &:last-child {
        border-bottom: none;
      }
      
      &:active {
        background-color: $background-color;
      }
      
      .item-content {
        @include flex-center;
        gap: $spacing-md;
        flex: 1;
        
        .item-icon {
          font-size: 40rpx;
        }
        
        .item-info {
          flex: 1;
          
          .item-title {
            display: block;
            font-size: $font-size-md;
            color: $text-primary;
            margin-bottom: 4rpx;
          }
          
          .item-desc {
            font-size: $font-size-sm;
            color: $text-secondary;
          }
        }
      }
      
      .item-arrow {
        font-size: $font-size-md;
        color: $text-placeholder;
      }
    }
  }
}
</style>