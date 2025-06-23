/**
 * 配置管理工具
 * @description 负责加载和管理应用配置，包括API地址、环境设置等
 */

import configData from '../data/config.json'

class ConfigManager {
  constructor() {
    this.config = configData
    this.currentEnvironment = this.config.api.environment || 'development'
  }

  /**
   * 获取当前API基础URL
   * @returns {string} API基础URL
   */
  getAPIBaseURL() {
    const envConfig = this.config.environments[this.currentEnvironment]
    return envConfig ? envConfig.baseURL : this.config.api.baseURL
  }

  /**
   * 获取API超时时间
   * @returns {number} 超时时间（毫秒）
   */
  getAPITimeout() {
    return this.config.api.timeout || 10000
  }

  /**
   * 获取当前环境
   * @returns {string} 环境名称
   */
  getCurrentEnvironment() {
    return this.currentEnvironment
  }

  /**
   * 设置当前环境
   * @param {string} environment 环境名称
   */
  setEnvironment(environment) {
    if (this.config.environments[environment]) {
      this.currentEnvironment = environment
      this.config.api.environment = environment
      console.log(`环境已切换到: ${environment}`)
      return true
    }
    console.error(`无效的环境: ${environment}`)
    return false
  }

  /**
   * 获取所有可用环境
   * @returns {Array} 环境列表
   */
  getAvailableEnvironments() {
    return Object.keys(this.config.environments).map(key => ({
      key,
      ...this.config.environments[key]
    }))
  }

  /**
   * 获取应用信息
   * @returns {Object} 应用信息
   */
  getAppInfo() {
    return this.config.app
  }

  /**
   * 是否为调试模式
   * @returns {boolean} 是否调试模式
   */
  isDebugMode() {
    return this.config.app.debug === true
  }

  /**
   * 更新配置（运行时）
   * @param {Object} updates 要更新的配置
   */
  updateConfig(updates) {
    if (updates.api) {
      Object.assign(this.config.api, updates.api)
    }
    if (updates.app) {
      Object.assign(this.config.app, updates.app)
    }
    console.log('配置已更新:', updates)
  }

  /**
   * 获取完整配置
   * @returns {Object} 完整配置对象
   */
  getFullConfig() {
    return { ...this.config }
  }

  /**
   * 从存储中加载配置（如果有保存的话）
   */
  loadFromStorage() {
    try {
      const savedConfig = uni.getStorageSync('app_config')
      if (savedConfig) {
        const parsed = JSON.parse(savedConfig)
        if (parsed.environment && this.config.environments[parsed.environment]) {
          this.setEnvironment(parsed.environment)
        }
        if (parsed.api) {
          Object.assign(this.config.api, parsed.api)
        }
        console.log('已加载保存的配置')
      }
    } catch (error) {
      console.error('加载配置失败:', error)
    }
  }

  /**
   * 保存配置到存储
   */
  saveToStorage() {
    try {
      const configToSave = {
        environment: this.currentEnvironment,
        api: this.config.api
      }
      uni.setStorageSync('app_config', JSON.stringify(configToSave))
      console.log('配置已保存')
    } catch (error) {
      console.error('保存配置失败:', error)
    }
  }
}

// 创建单例实例
const configManager = new ConfigManager()

// 应用启动时加载保存的配置
configManager.loadFromStorage()

export default configManager

// 导出便捷方法
export const getAPIBaseURL = () => configManager.getAPIBaseURL()
export const getAPITimeout = () => configManager.getAPITimeout()
export const getCurrentEnvironment = () => configManager.getCurrentEnvironment()
export const setEnvironment = (env) => configManager.setEnvironment(env)
export const isDebugMode = () => configManager.isDebugMode()
export const getAppInfo = () => configManager.getAppInfo()