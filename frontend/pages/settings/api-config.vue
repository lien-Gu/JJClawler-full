<template>
  <view class="api-config-page">
    <view class="header">
      <view class="title">API配置</view>
      <view class="subtitle">配置后端服务器地址</view>
    </view>

    <view class="config-section">
      <view class="section-title">当前环境</view>
      <view class="env-selector">
        <view 
          v-for="env in environments" 
          :key="env.key"
          class="env-item"
          :class="{ active: env.key === currentEnvironment }"
          @click="switchEnvironment(env.key)"
        >
          <view class="env-name">{{ env.description }}</view>
          <view class="env-url">{{ env.baseURL }}</view>
        </view>
      </view>
    </view>

    <view class="config-section">
      <view class="section-title">自定义配置</view>
      <view class="form-group">
        <view class="label">API基础地址</view>
        <input 
          class="input"
          v-model="customBaseURL"
          placeholder="例如: http://192.168.1.100:8000/api/v1"
        />
      </view>
      
      <view class="form-group">
        <view class="label">请求超时时间（毫秒）</view>
        <input 
          class="input"
          type="number"
          v-model="customTimeout"
          placeholder="默认: 10000"
        />
      </view>

      <view class="button-group">
        <button class="btn btn-primary" @click="saveCustomConfig">保存自定义配置</button>
        <button class="btn btn-secondary" @click="testConnection">测试连接</button>
      </view>
    </view>

    <view class="config-section">
      <view class="section-title">当前状态</view>
      <view class="status-info">
        <view class="info-item">
          <text class="info-label">当前环境:</text>
          <text class="info-value">{{ currentEnvironment }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">API地址:</text>
          <text class="info-value">{{ currentConfig.BASE_URL }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">超时时间:</text>
          <text class="info-value">{{ currentConfig.TIMEOUT }}ms</text>
        </view>
        <view class="info-item">
          <text class="info-label">连接状态:</text>
          <text class="info-value" :class="connectionStatus.class">{{ connectionStatus.text }}</text>
        </view>
      </view>
    </view>

    <view class="help-section">
      <view class="section-title">使用说明</view>
      <view class="help-content">
        <text>• 开发环境: 本地开发时使用，通常为 localhost:8000</text>
        <text>• 测试环境: 内部测试使用的服务器地址</text>
        <text>• 生产环境: 正式环境的服务器地址</text>
        <text>• 自定义配置: 可以输入任意的服务器地址进行连接</text>
        <text>• 修改配置后建议测试连接以确保服务正常</text>
      </view>
    </view>
  </view>
</template>

<script>
import configManager from '../../utils/config.js'
import request from '../../utils/request.js'

export default {
  name: 'APIConfigPage',
  data() {
    return {
      currentEnvironment: 'development',
      environments: [],
      customBaseURL: '',
      customTimeout: 10000,
      currentConfig: {},
      connectionStatus: {
        text: '未测试',
        class: 'status-unknown'
      }
    }
  },
  onLoad() {
    this.loadConfig()
  },
  methods: {
    /**
     * 加载配置信息
     */
    loadConfig() {
      this.currentEnvironment = configManager.getCurrentEnvironment()
      this.environments = configManager.getAvailableEnvironments()
      this.currentConfig = request.getCurrentConfig()
      this.customBaseURL = this.currentConfig.BASE_URL
      this.customTimeout = this.currentConfig.TIMEOUT
    },

    /**
     * 切换环境
     */
    switchEnvironment(environment) {
      try {
        if (configManager.setEnvironment(environment)) {
          this.currentEnvironment = environment
          request.refreshConfig()
          this.currentConfig = request.getCurrentConfig()
          configManager.saveToStorage()
          
          uni.showToast({
            title: `已切换到${this.environments.find(e => e.key === environment)?.description}`,
            icon: 'success'
          })
        }
      } catch (error) {
        uni.showToast({
          title: '切换环境失败',
          icon: 'error'
        })
        console.error('切换环境失败:', error)
      }
    },

    /**
     * 保存自定义配置
     */
    saveCustomConfig() {
      try {
        if (!this.customBaseURL.trim()) {
          uni.showToast({
            title: '请输入API地址',
            icon: 'none'
          })
          return
        }

        // 验证URL格式
        if (!this.isValidURL(this.customBaseURL)) {
          uni.showToast({
            title: 'API地址格式不正确',
            icon: 'none'
          })
          return
        }

        // 更新配置
        request.setBaseURL(this.customBaseURL.trim())
        request.setTimeout(Number(this.customTimeout) || 10000)
        
        this.currentConfig = request.getCurrentConfig()
        configManager.saveToStorage()

        uni.showToast({
          title: '配置已保存',
          icon: 'success'
        })
      } catch (error) {
        uni.showToast({
          title: '保存配置失败',
          icon: 'error'
        })
        console.error('保存配置失败:', error)
      }
    },

    /**
     * 测试连接
     */
    async testConnection() {
      this.connectionStatus = {
        text: '测试中...',
        class: 'status-testing'
      }

      try {
        // 测试健康检查接口
        const response = await request.get('/health', {}, { showLoading: false, showError: false })
        
        this.connectionStatus = {
          text: '连接正常',
          class: 'status-success'
        }
        
        uni.showToast({
          title: '连接测试成功',
          icon: 'success'
        })
      } catch (error) {
        this.connectionStatus = {
          text: '连接失败',
          class: 'status-error'
        }
        
        uni.showToast({
          title: '连接测试失败',
          icon: 'error'
        })
        console.error('连接测试失败:', error)
      }
    },

    /**
     * 验证URL格式
     */
    isValidURL(url) {
      try {
        new URL(url)
        return true
      } catch {
        // 简单的HTTP URL检查
        return /^https?:\/\/.+/.test(url)
      }
    },

    /**
     * 返回上一页
     */
    goBack() {
      uni.navigateBack()
    }
  }
}
</script>

<style lang="scss" scoped>
.api-config-page {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 20rpx;
}

.header {
  background: white;
  padding: 30rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
  text-align: center;
  
  .title {
    font-size: 36rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 10rpx;
  }
  
  .subtitle {
    font-size: 28rpx;
    color: #666;
  }
}

.config-section {
  background: white;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
  overflow: hidden;
}

.section-title {
  padding: 30rpx;
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  border-bottom: 1px solid #f0f0f0;
}

.env-selector {
  .env-item {
    padding: 30rpx;
    border-bottom: 1px solid #f0f0f0;
    transition: background-color 0.3s;
    
    &:last-child {
      border-bottom: none;
    }
    
    &.active {
      background-color: #e8f4fd;
      border-left: 6rpx solid #007aff;
    }
    
    &:active {
      background-color: #f0f0f0;
    }
    
    .env-name {
      font-size: 30rpx;
      color: #333;
      margin-bottom: 10rpx;
    }
    
    .env-url {
      font-size: 26rpx;
      color: #666;
      word-break: break-all;
    }
  }
}

.form-group {
  padding: 30rpx;
  border-bottom: 1px solid #f0f0f0;
  
  &:last-child {
    border-bottom: none;
  }
  
  .label {
    font-size: 30rpx;
    color: #333;
    margin-bottom: 20rpx;
  }
  
  .input {
    width: 100%;
    height: 80rpx;
    border: 2rpx solid #e0e0e0;
    border-radius: 8rpx;
    padding: 0 20rpx;
    font-size: 28rpx;
    background: white;
    
    &:focus {
      border-color: #007aff;
    }
  }
}

.button-group {
  padding: 30rpx;
  display: flex;
  gap: 20rpx;
  
  .btn {
    flex: 1;
    height: 80rpx;
    border-radius: 8rpx;
    font-size: 30rpx;
    border: none;
    
    &.btn-primary {
      background: #007aff;
      color: white;
    }
    
    &.btn-secondary {
      background: #f0f0f0;
      color: #333;
    }
    
    &:active {
      opacity: 0.8;
    }
  }
}

.status-info {
  padding: 30rpx;
  
  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20rpx;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .info-label {
      font-size: 28rpx;
      color: #666;
    }
    
    .info-value {
      font-size: 28rpx;
      color: #333;
      word-break: break-all;
      text-align: right;
      max-width: 60%;
      
      &.status-unknown {
        color: #999;
      }
      
      &.status-testing {
        color: #ff9500;
      }
      
      &.status-success {
        color: #34c759;
      }
      
      &.status-error {
        color: #ff3b30;
      }
    }
  }
}

.help-section {
  .help-content {
    padding: 30rpx;
    
    text {
      display: block;
      font-size: 26rpx;
      color: #666;
      line-height: 1.5;
      margin-bottom: 10rpx;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}
</style>