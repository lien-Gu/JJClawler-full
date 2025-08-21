/**
 * 环境配置管理
 * 支持 test/dev/prod 三种环境切换
 */

// 环境配置
const ENV_CONFIG = {
  test: {
    name: 'Test Environment',
    baseURL: '',
    useLocalData: true,
    debug: true
  },
  dev: {
    name: 'Development Environment', 
    baseURL: 'http://localhost:8000/api/v1',
    useLocalData: false,
    debug: true
  },
  prod: {
    name: 'Production Environment',
    baseURL: 'https://api.jjclawler.com/api/v1', // 生产环境URL
    useLocalData: false,
    debug: false
  }
}

class EnvConfig {
  constructor() {
    // 从本地存储获取当前环境，默认为 dev
    this.currentEnv = uni.getStorageSync('currentEnv') || 'dev'
  }

  /**
   * 获取当前环境
   */
  getCurrentEnv() {
    return this.currentEnv
  }

  /**
   * 获取当前环境配置
   */
  getConfig() {
    return ENV_CONFIG[this.currentEnv] || ENV_CONFIG.dev
  }

  /**
   * 切换环境
   * @param {string} env - 环境名称 (test/dev/prod)
   */
  switchEnv(env) {
    if (ENV_CONFIG[env]) {
      this.currentEnv = env
      uni.setStorageSync('currentEnv', env)
      
      // 通知环境变化
      uni.$emit('env-changed', {
        env: env,
        config: this.getConfig()
      })
      
      return true
    }
    return false
  }

  /**
   * 获取API基础URL
   */
  getBaseURL() {
    return this.getConfig().baseURL
  }

  /**
   * 是否使用本地数据
   */
  useLocalData() {
    return this.getConfig().useLocalData
  }

  /**
   * 是否开启调试模式
   */
  isDebug() {
    return this.getConfig().debug
  }

  /**
   * 获取所有可用环境
   */
  getAvailableEnvs() {
    return Object.keys(ENV_CONFIG).map(key => ({
      key,
      name: ENV_CONFIG[key].name,
      current: key === this.currentEnv
    }))
  }

  /**
   * 日志输出（仅在调试模式下）
   */
  log(...args) {
    if (this.isDebug()) {
      console.log('[EnvConfig]', ...args)
    }
  }

  /**
   * 错误日志输出
   */
  error(...args) {
    console.error('[EnvConfig]', ...args)
  }
}

// 创建全局实例
const envConfig = new EnvConfig()

// 在小程序中添加全局方法
if (typeof uni !== 'undefined') {
  uni.$envConfig = envConfig
}

export default envConfig