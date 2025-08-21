<template>
  <view class="webview-page">
    <!-- 自定义导航栏 -->
    <view class="custom-navbar">
      <view class="navbar-content">
        <view class="back-btn" @tap="goBack">
          <text class="back-icon">←</text>
        </view>
        <text class="navbar-title">{{ pageTitle }}</text>
        <view class="placeholder"></view>
      </view>
    </view>
    
    <!-- 内容区域 -->
    <view class="content-area">
      <!-- 加载状态 -->
      <view v-if="loading" class="loading-container">
        <view class="loading-spinner"></view>
        <text class="loading-text">正在加载...</text>
      </view>
      
      <!-- 错误状态 -->
      <view v-else-if="error" class="error-container">
        <text class="error-icon">⚠️</text>
        <text class="error-title">加载失败</text>
        <text class="error-message">{{ error }}</text>
        <view class="retry-btn" @tap="retryLoad">
          <text class="retry-text">重试</text>
        </view>
      </view>
      
      <!-- 内容显示 -->
      <view v-else class="content-container">
        <!-- H5环境使用iframe -->
        <view v-if="isH5" class="iframe-container">
          <iframe :src="targetUrl" class="content-iframe"></iframe>
        </view>
        
        <!-- 小程序环境使用web-view -->
        <web-view v-else-if="isMiniProgram" :src="targetUrl" @message="onWebViewMessage"></web-view>
        
        <!-- APP环境或其他情况显示提示 -->
        <view v-else class="fallback-container">
          <text class="fallback-title">即将跳转</text>
          <text class="fallback-url">{{ targetUrl }}</text>
          <view class="open-btn" @tap="openInBrowser">
            <text class="open-text">在浏览器中打开</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * WebView页面
 * @description 用于显示外部链接内容，支持多平台
 */
export default {
  name: 'WebViewPage',
  
  data() {
    return {
      targetUrl: '',
      pageTitle: '加载中...',
      loading: true,
      error: '',
      
      // 平台检测
      isH5: false,
      isMiniProgram: false,
      isApp: false
    }
  },
  
  onLoad(options) {
    // 检测平台
    this.detectPlatform()
    
    // 获取URL参数
    if (options.url) {
      this.targetUrl = decodeURIComponent(options.url)
    }
    
    if (options.title) {
      this.pageTitle = decodeURIComponent(options.title)
    }
    
    // 开始加载
    this.loadContent()
  },
  
  methods: {
    /**
     * 检测当前平台
     */
    detectPlatform() {
      // #ifdef H5
      this.isH5 = true
      // #endif
      
      // #ifdef MP-WEIXIN
      this.isMiniProgram = true
      // #endif
      
      // #ifdef APP-PLUS
      this.isApp = true
      // #endif
    },
    
    /**
     * 加载内容
     */
    async loadContent() {
      if (!this.targetUrl) {
        this.error = '缺少URL参数'
        this.loading = false
        return
      }
      
      try {
        this.loading = true
        this.error = ''
        
        // 模拟加载延迟
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // 根据平台处理URL
        await this.handleUrlByPlatform()
        
        this.loading = false
      } catch (err) {
        console.error('加载内容失败:', err)
        this.error = err.message || '加载失败'
        this.loading = false
      }
    },
    
    /**
     * 根据平台处理URL
     */
    async handleUrlByPlatform() {
      if (this.isH5) {
        // H5环境直接使用iframe
        console.log('H5环境，使用iframe加载:', this.targetUrl)
      } else if (this.isMiniProgram) {
        // 小程序环境使用web-view
        console.log('小程序环境，使用web-view加载:', this.targetUrl)
        
        // 检查URL是否在小程序业务域名白名单中
        if (!this.isValidMiniProgramUrl(this.targetUrl)) {
          throw new Error('URL不在小程序业务域名白名单中')
        }
      } else if (this.isApp) {
        // APP环境使用系统浏览器
        console.log('APP环境，准备在系统浏览器中打开:', this.targetUrl)
      }
    },
    
    /**
     * 检查URL是否适用于小程序
     */
    isValidMiniProgramUrl(url) {
      // 这里应该检查URL是否在小程序的业务域名白名单中
      // 暂时返回true，实际项目中需要根据具体配置判断
      return true
    },
    
    /**
     * 重试加载
     */
    retryLoad() {
      this.loadContent()
    },
    
    /**
     * 返回上一页
     */
    goBack() {
      uni.navigateBack({
        fail: () => {
          // 如果无法返回，则跳转到首页
          uni.switchTab({
            url: '/pages/index/index'
          })
        }
      })
    },
    
    /**
     * 在浏览器中打开
     */
    openInBrowser() {
      // #ifdef APP-PLUS
      plus.runtime.openURL(this.targetUrl)
      // #endif
      
      // #ifdef H5
      window.open(this.targetUrl, '_blank')
      // #endif
      
      // #ifdef MP-WEIXIN
      uni.showModal({
        title: '提示',
        content: '请复制链接到浏览器中打开',
        showCancel: true,
        cancelText: '取消',
        confirmText: '复制链接',
        success: (res) => {
          if (res.confirm) {
            uni.setClipboardData({
              data: this.targetUrl,
              success: () => {
                uni.showToast({
                  title: '链接已复制',
                  icon: 'success'
                })
              }
            })
          }
        }
      })
      // #endif
    },
    
    /**
     * Web-view消息处理
     */
    onWebViewMessage(event) {
      console.log('收到web-view消息:', event.detail.data)
    }
  }
}
</script>

<style lang="scss" scoped>
.webview-page {
  height: 100vh;
  background-color: #f4f0eb;
  display: flex;
  flex-direction: column;
}

.custom-navbar {
  background-color: #ffffff;
  border-bottom: 1rpx solid #e0e0e0;
  
  .navbar-content {
    display: flex;
    align-items: center;
    height: 88rpx;
    padding: 0 32rpx;
    padding-top: var(--status-bar-height, 0);
    
    .back-btn {
      width: 80rpx;
      height: 60rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .back-icon {
        font-size: 36rpx;
        color: #333333;
      }
      
      &:active {
        opacity: 0.6;
      }
    }
    
    .navbar-title {
      flex: 1;
      text-align: center;
      font-size: 32rpx;
      font-weight: 500;
      color: #333333;
      margin: 0 20rpx;
      
      /* 文字溢出处理 */
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }
    
    .placeholder {
      width: 80rpx;
    }
  }
}

.content-area {
  flex: 1;
  position: relative;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  
  .loading-spinner {
    width: 60rpx;
    height: 60rpx;
    border: 4rpx solid #e0e0e0;
    border-top: 4rpx solid #64a347;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 32rpx;
  }
  
  .loading-text {
    font-size: 28rpx;
    color: #666666;
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 64rpx;
  
  .error-icon {
    font-size: 120rpx;
    margin-bottom: 32rpx;
  }
  
  .error-title {
    font-size: 36rpx;
    font-weight: 500;
    color: #333333;
    margin-bottom: 16rpx;
  }
  
  .error-message {
    font-size: 28rpx;
    color: #666666;
    text-align: center;
    margin-bottom: 64rpx;
    line-height: 1.5;
  }
  
  .retry-btn {
    background-color: #64a347;
    border-radius: 32rpx;
    padding: 24rpx 48rpx;
    
    .retry-text {
      font-size: 32rpx;
      color: #ffffff;
      font-weight: 500;
    }
    
    &:active {
      opacity: 0.8;
    }
  }
}

.content-container {
  height: 100%;
}

.iframe-container {
  height: 100%;
  
  .content-iframe {
    width: 100%;
    height: 100%;
    border: none;
  }
}

.fallback-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 64rpx;
  
  .fallback-title {
    font-size: 36rpx;
    font-weight: 500;
    color: #333333;
    margin-bottom: 32rpx;
  }
  
  .fallback-url {
    font-size: 24rpx;
    color: #666666;
    text-align: center;
    margin-bottom: 64rpx;
    word-break: break-all;
    line-height: 1.5;
  }
  
  .open-btn {
    background-color: #64a347;
    border-radius: 32rpx;
    padding: 24rpx 48rpx;
    
    .open-text {
      font-size: 32rpx;
      color: #ffffff;
      font-weight: 500;
    }
    
    &:active {
      opacity: 0.8;
    }
  }
}
</style> 