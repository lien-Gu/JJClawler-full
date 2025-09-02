<template>
  <view class="login-modal" v-if="visible" @tap="closeModal">
    <view class="modal-content" @tap.stop="">
      <view class="modal-header">
        <text class="modal-title">登录晋江数据中心</text>
        <view class="close-btn" @tap="closeModal">
          <text class="close-icon">✕</text>
        </view>
      </view>
      
      <view class="modal-body">
        <view class="login-info">
          <view class="welcome-section">
            <view class="app-icon">📚</view>
            <text class="welcome-text">欢迎使用晋江数据中心</text>
            <text class="welcome-desc">登录后可以关注喜欢的书籍和榜单</text>
          </view>
          
          <view class="features-list">
            <view class="feature-item">
              <text class="feature-icon">⭐</text>
              <text class="feature-text">关注心仪的书籍</text>
            </view>
            <view class="feature-item">
              <text class="feature-icon">📊</text>
              <text class="feature-text">追踪榜单变化</text>
            </view>
            <view class="feature-item">
              <text class="feature-icon">🔔</text>
              <text class="feature-text">个性化数据推送</text>
            </view>
          </view>
        </view>
      </view>
      
      <view class="modal-footer">
        <BaseButton
          :loading="loginLoading"
          :disabled="loginLoading"
          type="primary"
          size="large"
          :text="loginLoading ? '登录中...' : '微信快速登录'"
          @click.stop="handleLogin"
        />
        <view class="login-tip">
          <text class="tip-text">点击登录即表示同意用户协议和隐私政策</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import BaseButton from './BaseButton.vue'
import userStore from '@/store/userStore.js'

export default {
  name: 'LoginModal',
  components: {
    BaseButton
  },
  
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  
  data() {
    return {
      loginLoading: false
    }
  },
  
  methods: {
    closeModal() {
      this.$emit('close')
    },
    
    handleLogin() {
      if (this.loginLoading) return
      
      this.loginLoading = true
      
      // 立即调用登录，不使用async/await，避免断开用户手势链
      userStore.login()
        .then((result) => {
          if (result.success) {
            uni.showToast({
              title: '登录成功',
              icon: 'success',
              duration: 1500
            })
            
            // 通知父组件登录成功
            this.$emit('login-success', result.userInfo)
            
            // 延迟关闭弹窗
            setTimeout(() => {
              this.closeModal()
            }, 1500)
          } else {
            uni.showToast({
              title: result.message || '登录失败',
              icon: 'none',
              duration: 2000
            })
          }
        })
        .catch((error) => {
          console.error('登录异常:', error)
          uni.showToast({
            title: '登录异常，请重试',
            icon: 'none',
            duration: 2000
          })
        })
        .finally(() => {
          this.loginLoading = false
        })
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.login-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: $spacing-lg;
}

.modal-content {
  background: $surface-white;
  border-radius: $radius-lg;
  width: 100%;
  max-width: 600rpx;
  overflow: hidden;
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    transform: translateY(50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  position: relative;
  padding: $spacing-lg;
  border-bottom: 1px solid rgba($text-secondary, 0.1);
  
  .modal-title {
    font-size: 32rpx;
    font-weight: 600;
    color: $text-primary;
    text-align: center;
    display: block;
  }
  
  .close-btn {
    position: absolute;
    right: $spacing-lg;
    top: 50%;
    transform: translateY(-50%);
    width: 48rpx;
    height: 48rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-full;
    
    &:active {
      background: rgba($text-secondary, 0.1);
    }
    
    .close-icon {
      font-size: 28rpx;
      color: $text-secondary;
    }
  }
}

.modal-body {
  padding: $spacing-xl $spacing-lg;
  
  .login-info {
    .welcome-section {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-bottom: $spacing-xl;
      
      .app-icon {
        font-size: 80rpx;
        margin-bottom: $spacing-md;
      }
      
      .welcome-text {
        font-size: 28rpx;
        font-weight: 600;
        color: $text-primary;
        margin-bottom: $spacing-sm;
      }
      
      .welcome-desc {
        font-size: 24rpx;
        color: $text-secondary;
        text-align: center;
        line-height: 1.4;
      }
    }
    
    .features-list {
      display: flex;
      flex-direction: column;
      gap: $spacing-md;
      
      .feature-item {
        display: flex;
        align-items: center;
        gap: $spacing-md;
        
        .feature-icon {
          font-size: 28rpx;
          width: 48rpx;
          text-align: center;
        }
        
        .feature-text {
          font-size: 26rpx;
          color: $text-primary;
          flex: 1;
        }
      }
    }
  }
}

.modal-footer {
  padding: 0 $spacing-lg $spacing-lg;
  
  .login-tip {
    margin-top: $spacing-md;
    text-align: center;
    
    .tip-text {
      font-size: 20rpx;
      color: $text-secondary;
      opacity: 0.7;
      line-height: 1.4;
    }
  }
}
</style>