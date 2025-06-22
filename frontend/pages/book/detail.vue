<template>
  <view class="book-detail-page">
    <!-- 书籍基本信息 -->
    <view class="book-header">
      <view class="header-bg"></view>
      <view class="header-content">
        <view class="book-cover-section">
          <view class="book-cover" v-if="bookData.cover">
            <image :src="bookData.cover" mode="aspectFit" class="cover-image" />
          </view>
          <view class="book-cover placeholder" v-else>
            <text class="cover-text">📖</text>
          </view>
        </view>
        
        <view class="book-info-section">
          <text class="book-title">{{ bookData.title || bookData.name || '书籍详情' }}</text>
          <text class="book-author" v-if="bookData.author">作者：{{ bookData.author }}</text>
          <view class="book-meta" v-if="bookData.category || bookData.status">
            <text class="meta-item" v-if="bookData.category">{{ bookData.category }}</text>
            <text class="meta-divider" v-if="bookData.category && bookData.status">·</text>
            <text class="meta-item" v-if="bookData.status">{{ bookData.status }}</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 第一层：当前统计数据 -->
    <view class="layer-section current-stats">
      <view class="layer-header">
        <text class="layer-title">📊 当前数据</text>
      </view>
      <view class="stats-grid">
        <view class="stat-card">
          <text class="stat-value">{{ formatNumber(bookData.currentStats?.collectCount || 0) }}</text>
          <text class="stat-label">当前收藏量</text>
        </view>
        <view class="stat-card">
          <text class="stat-value">{{ formatNumber(bookData.currentStats?.avgClickPerChapter || 0) }}</text>
          <text class="stat-label">章均点击量</text>
        </view>
      </view>
    </view>
    
    <!-- 第二层：榜单信息 -->
    <view class="layer-section rankings-info">
      <view class="layer-header">
        <text class="layer-title">🏆 榜单排名</text>
      </view>
      
      <view class="rankings-list" v-if="bookData.rankings && bookData.rankings.length > 0">
        <view class="ranking-item" v-for="ranking in bookData.rankings" :key="ranking.id">
          <view class="ranking-main">
            <text class="ranking-name">{{ ranking.name }}</text>
            <view class="ranking-rank">
              <text class="rank-text">第{{ ranking.currentRank }}名</text>
              <view class="rank-change" :class="getRankChangeClass(ranking.rankChange)">
                <text class="change-icon">{{ getRankChangeIcon(ranking.rankChange) }}</text>
                <text class="change-text">{{ Math.abs(ranking.rankChange || 0) }}</text>
              </view>
            </view>
          </view>
          <text class="ranking-time">{{ formatTime(ranking.updateTime) }}</text>
        </view>
      </view>
      
      <view class="empty-state" v-else>
        <text class="empty-icon">📋</text>
        <text class="empty-text">暂无榜单记录</text>
      </view>
    </view>
    
    <!-- 第三层：历史统计图表 -->
    <view class="layer-section history-stats">
      <view class="layer-header">
        <text class="layer-title">📈 历史统计</text>
      </view>
      
      <!-- Tab切换 -->
      <view class="stats-tabs">
        <view 
          class="tab-item" 
          :class="{ 'active': activeTab === 'collect' }"
          @tap="switchTab('collect')"
        >
          <text class="tab-text">收藏量变化</text>
        </view>
        <view 
          class="tab-item" 
          :class="{ 'active': activeTab === 'click' }"
          @tap="switchTab('click')"
        >
          <text class="tab-text">点击量变化</text>
        </view>
      </view>
      
      <!-- 图表区域 -->
      <view class="chart-container">
        <view class="chart-area" v-if="historyData.length > 0">
          <!-- 简单的折线图实现 -->
          <view class="chart-grid">
            <view class="grid-line" v-for="i in 5" :key="i"></view>
          </view>
          <view class="chart-line">
            <view 
              class="data-point" 
              v-for="(point, index) in chartPoints" 
              :key="index"
              :style="{ left: point.x + '%', bottom: point.y + '%' }"
            >
              <view class="point-dot"></view>
              <text class="point-value">{{ point.value }}</text>
            </view>
            <!-- 连接线 -->
            <svg class="chart-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
              <polyline 
                :points="chartLinePoints" 
                fill="none" 
                stroke="#007aff" 
                stroke-width="0.5"
              />
            </svg>
          </view>
        </view>
        
        <view class="empty-chart" v-else>
          <text class="empty-icon">📊</text>
          <text class="empty-text">暂无历史数据</text>
        </view>
      </view>
      
      <!-- 数据概览 -->
      <view class="stats-summary" v-if="historyData.length > 0">
        <view class="summary-item">
          <text class="summary-label">最高值</text>
          <text class="summary-value">{{ formatNumber(getMaxValue()) }}</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">最低值</text>
          <text class="summary-value">{{ formatNumber(getMinValue()) }}</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">平均增长</text>
          <text class="summary-value">{{ getAverageGrowth() }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { get } from '@/utils/request.js'
import { getSync, setSync } from '@/utils/storage.js'

/**
 * 书籍详情页面 - 三层数据展示
 * @description 第一层：当前统计，第二层：榜单排名，第三层：历史图表
 */
export default {
  name: 'BookDetailPage',
  
  data() {
    return {
      // 书籍ID
      bookId: '',
      
      // 书籍数据
      bookData: {
        title: '',
        author: '',
        cover: '',
        category: '',
        status: '',
        currentStats: {
          collectCount: 0,
          avgClickPerChapter: 0
        },
        rankings: []
      },
      
      // 当前选中的tab
      activeTab: 'collect', // 'collect' | 'click'
      
      // 历史数据
      historyStats: {
        dates: [],
        collectHistory: [],
        clickHistory: []
      },
      
      // 加载状态
      loading: false
    }
  },
  
  computed: {
    /**
     * 当前显示的历史数据
     */
    historyData() {
      if (this.activeTab === 'collect') {
        return this.historyStats.collectHistory || []
      } else {
        return this.historyStats.clickHistory || []
      }
    },
    
    /**
     * 图表点位数据
     */
    chartPoints() {
      if (this.historyData.length === 0) return []
      
      const maxValue = Math.max(...this.historyData)
      const minValue = Math.min(...this.historyData)
      const range = maxValue - minValue || 1
      
      return this.historyData.map((value, index) => ({
        x: (index / (this.historyData.length - 1)) * 100,
        y: ((value - minValue) / range) * 80 + 10,
        value: this.formatNumber(value)
      }))
    },
    
    /**
     * 图表连接线点位
     */
    chartLinePoints() {
      return this.chartPoints.map(point => `${point.x},${100 - point.y}`).join(' ')
    }
  },
  
  onLoad(options) {
    if (options.id) {
      this.bookId = options.id
      this.initData()
    }
  },
  
  // 下拉刷新
  onPullDownRefresh() {
    this.refreshData().finally(() => {
      uni.stopPullDownRefresh()
    })
  },
  
  methods: {
    /**
     * 初始化数据
     */
    async initData() {
      this.loading = true
      
      try {
        // 加载缓存数据
        this.loadCachedData()
        
        // 获取最新数据
        await Promise.all([
          this.fetchBookInfo(),
          this.fetchHistoryStats()
        ])
      } catch (error) {
        console.error('初始化数据失败:', error)
        this.showError('数据加载失败')
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 加载缓存数据
     */
    loadCachedData() {
      const cachedBook = getSync(`book_detail_${this.bookId}`)
      const cachedHistory = getSync(`book_history_${this.bookId}`)
      
      if (cachedBook) {
        this.bookData = { ...this.bookData, ...cachedBook }
      }
      
      if (cachedHistory) {
        this.historyStats = cachedHistory
      }
    },
    
    /**
     * 获取书籍详细信息
     */
    async fetchBookInfo() {
      try {
        // 模拟API调用，实际应调用真实接口
        const data = await this.getMockBookData()
        
        this.bookData = { ...this.bookData, ...data }
        setSync(`book_detail_${this.bookId}`, data, 30 * 60 * 1000) // 缓存30分钟
      } catch (error) {
        console.error('获取书籍信息失败:', error)
        throw error
      }
    },
    
    /**
     * 获取历史统计数据
     */
    async fetchHistoryStats() {
      try {
        // 模拟API调用，实际应调用真实接口
        const data = await this.getMockHistoryData()
        
        this.historyStats = data
        setSync(`book_history_${this.bookId}`, data, 15 * 60 * 1000) // 缓存15分钟
      } catch (error) {
        console.error('获取历史数据失败:', error)
        throw error
      }
    },
    
    /**
     * 获取模拟书籍数据
     */
    async getMockBookData() {
      // 模拟网络延迟
      await new Promise(resolve => setTimeout(resolve, 500))
      
      return {
        title: '霸道总裁的小娇妻',
        author: '言情作家',
        cover: '',
        category: '现代言情',
        status: '连载中',
        currentStats: {
          collectCount: 125847,
          avgClickPerChapter: 2156
        },
        rankings: [
          {
            id: 'ranking1',
            name: '言情总榜',
            currentRank: 15,
            rankChange: -2,
            updateTime: '2024-01-15T10:30:00'
          },
          {
            id: 'ranking2', 
            name: '新书榜',
            currentRank: 8,
            rankChange: 3,
            updateTime: '2024-01-15T10:30:00'
          },
          {
            id: 'ranking3',
            name: '收藏榜',
            currentRank: 22,
            rankChange: 0,
            updateTime: '2024-01-15T10:30:00'
          }
        ]
      }
    },
    
    /**
     * 获取模拟历史数据
     */
    async getMockHistoryData() {
      // 模拟网络延迟
      await new Promise(resolve => setTimeout(resolve, 300))
      
      // 生成30天的模拟数据
      const dates = []
      const collectHistory = []
      const clickHistory = []
      
      const now = new Date()
      for (let i = 29; i >= 0; i--) {
        const date = new Date(now)
        date.setDate(date.getDate() - i)
        dates.push(date.toISOString().split('T')[0])
        
        // 模拟收藏量增长（有波动）
        const baseCollect = 120000 + i * 200
        const collectVariation = Math.random() * 1000 - 500
        collectHistory.push(Math.max(0, Math.floor(baseCollect + collectVariation)))
        
        // 模拟点击量增长
        const baseClick = 2000000 + i * 5000
        const clickVariation = Math.random() * 10000 - 5000
        clickHistory.push(Math.max(0, Math.floor(baseClick + clickVariation)))
      }
      
      return {
        dates,
        collectHistory,
        clickHistory
      }
    },
    
    /**
     * 刷新数据
     */
    async refreshData() {
      try {
        await Promise.all([
          this.fetchBookInfo(),
          this.fetchHistoryStats()
        ])
        
        uni.showToast({
          title: '刷新成功',
          icon: 'success',
          duration: 1500
        })
      } catch (error) {
        this.showError('刷新失败')
      }
    },
    
    /**
     * 切换统计Tab
     */
    switchTab(tab) {
      this.activeTab = tab
    },
    
    /**
     * 获取排名变化样式类
     */
    getRankChangeClass(change) {
      if (!change || change === 0) return 'no-change'
      return change > 0 ? 'rank-up' : 'rank-down'
    },
    
    /**
     * 获取排名变化图标
     */
    getRankChangeIcon(change) {
      if (!change || change === 0) return '—'
      return change > 0 ? '↗' : '↘'
    },
    
    /**
     * 获取最大值
     */
    getMaxValue() {
      return Math.max(...this.historyData)
    },
    
    /**
     * 获取最小值
     */
    getMinValue() {
      return Math.min(...this.historyData)
    },
    
    /**
     * 获取平均增长
     */
    getAverageGrowth() {
      if (this.historyData.length < 2) return '0%'
      
      const first = this.historyData[0]
      const last = this.historyData[this.historyData.length - 1]
      const growth = ((last - first) / first * 100).toFixed(1)
      
      return growth > 0 ? `+${growth}%` : `${growth}%`
    },
    
    /**
     * 格式化数字
     */
    formatNumber(num) {
      if (typeof num !== 'number') return num || '0'
      
      if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k'
      }
      
      return num.toString()
    },
    
    /**
     * 格式化时间
     */
    formatTime(time) {
      if (!time) return '未知'
      
      const now = new Date()
      const updateTime = new Date(time)
      const diff = now - updateTime
      
      const hours = Math.floor(diff / (1000 * 60 * 60))
      const days = Math.floor(diff / (1000 * 60 * 60 * 24))
      
      if (hours < 24) {
        return `${hours}小时前`
      } else if (days < 7) {
        return `${days}天前`
      } else {
        return updateTime.toLocaleDateString()
      }
    },
    
    /**
     * 显示错误提示
     */
    showError(message) {
      uni.showToast({
        title: message,
        icon: 'none',
        duration: 2000
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.book-detail-page {
  min-height: 100vh;
  background-color: $page-background;
  padding-bottom: $safe-area-bottom;
}

// 书籍头部信息
.book-header {
  position: relative;
  padding: $spacing-lg;
  color: white;
  overflow: hidden;
  
  .header-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, $primary-color, $secondary-color);
    z-index: -1;
  }
  
  .header-content {
    @include flex-center;
    align-items: flex-start;
    gap: $spacing-lg;
  }
  
  .book-cover-section {
    flex-shrink: 0;
    
    .book-cover {
      width: 160rpx;
      height: 220rpx;
      border-radius: $border-radius-medium;
      overflow: hidden;
      background-color: rgba(255, 255, 255, 0.1);
      @include flex-center;
      
      .cover-image {
        width: 100%;
        height: 100%;
      }
      
      &.placeholder {
        .cover-text {
          font-size: 50rpx;
          opacity: 0.7;
        }
      }
    }
  }
  
  .book-info-section {
    flex: 1;
    
    .book-title {
      display: block;
      font-size: $font-size-xl;
      font-weight: bold;
      margin-bottom: $spacing-xs;
      line-height: 1.3;
    }
    
    .book-author {
      display: block;
      font-size: $font-size-sm;
      opacity: 0.9;
      margin-bottom: $spacing-xs;
    }
    
    .book-meta {
      @include flex-center;
      gap: $spacing-xs;
      
      .meta-item {
        font-size: $font-size-xs;
        opacity: 0.8;
      }
      
      .meta-divider {
        opacity: 0.6;
      }
    }
  }
}

// 层级区域通用样式
.layer-section {
  background-color: white;
  margin-bottom: $spacing-sm;
  padding: $spacing-lg;
  
  .layer-header {
    margin-bottom: $spacing-lg;
    
    .layer-title {
      font-size: $font-size-lg;
      font-weight: bold;
      color: $text-primary;
    }
  }
}

// 第一层：当前统计
.current-stats {
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: $spacing-lg;
    
    .stat-card {
      @include flex-column-center;
      padding: $spacing-lg;
      background: linear-gradient(135deg, #f8f9ff, #e8f0ff);
      border-radius: $border-radius-large;
      border: 2rpx solid $border-light;
      
      .stat-value {
        font-size: $font-size-xxl;
        font-weight: bold;
        color: $primary-color;
        margin-bottom: $spacing-xs;
      }
      
      .stat-label {
        font-size: $font-size-sm;
        color: $text-secondary;
        text-align: center;
      }
    }
  }
}

// 第二层：榜单信息
.rankings-info {
  .rankings-list {
    .ranking-item {
      padding: $spacing-lg;
      border: 2rpx solid $border-light;
      border-radius: $border-radius-medium;
      margin-bottom: $spacing-md;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .ranking-main {
        @include flex-between;
        align-items: center;
        margin-bottom: $spacing-xs;
        
        .ranking-name {
          font-size: $font-size-md;
          font-weight: bold;
          color: $text-primary;
        }
        
        .ranking-rank {
          @include flex-center;
          gap: $spacing-sm;
          
          .rank-text {
            font-size: $font-size-md;
            color: $primary-color;
            font-weight: bold;
          }
          
          .rank-change {
            @include flex-center;
            gap: 4rpx;
            padding: 4rpx $spacing-xs;
            border-radius: $border-radius-small;
            
            .change-icon {
              font-size: $font-size-sm;
            }
            
            .change-text {
              font-size: $font-size-xs;
            }
            
            &.rank-up {
              background-color: #e8f5e8;
              color: #22c55e;
            }
            
            &.rank-down {
              background-color: #fef2f2;
              color: #ef4444;
            }
            
            &.no-change {
              background-color: $background-color;
              color: $text-placeholder;
            }
          }
        }
      }
      
      .ranking-time {
        font-size: $font-size-xs;
        color: $text-placeholder;
      }
    }
  }
}

// 第三层：历史统计
.history-stats {
  .stats-tabs {
    @include flex-center;
    background-color: $background-color;
    border-radius: $border-radius-medium;
    padding: 6rpx;
    margin-bottom: $spacing-lg;
    
    .tab-item {
      flex: 1;
      @include flex-center;
      padding: $spacing-sm;
      border-radius: $border-radius-small;
      transition: all 0.3s ease;
      
      .tab-text {
        font-size: $font-size-sm;
        color: $text-secondary;
      }
      
      &.active {
        background-color: white;
        box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
        
        .tab-text {
          color: $primary-color;
          font-weight: bold;
        }
      }
    }
  }
  
  .chart-container {
    margin-bottom: $spacing-lg;
    
    .chart-area {
      position: relative;
      height: 400rpx;
      background-color: #fafbfc;
      border-radius: $border-radius-medium;
      padding: $spacing-lg;
      overflow: hidden;
      
      .chart-grid {
        position: absolute;
        top: $spacing-lg;
        left: $spacing-lg;
        right: $spacing-lg;
        bottom: $spacing-lg;
        
        .grid-line {
          position: absolute;
          left: 0;
          right: 0;
          height: 2rpx;
          background-color: #e5e7eb;
          
          &:nth-child(1) { top: 0; }
          &:nth-child(2) { top: 25%; }
          &:nth-child(3) { top: 50%; }
          &:nth-child(4) { top: 75%; }
          &:nth-child(5) { bottom: 0; }
        }
      }
      
      .chart-line {
        position: relative;
        width: 100%;
        height: 100%;
        
        .chart-svg {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
        }
        
        .data-point {
          position: absolute;
          transform: translate(-50%, 50%);
          
          .point-dot {
            width: 12rpx;
            height: 12rpx;
            background-color: $primary-color;
            border-radius: 50%;
            margin: 0 auto;
          }
          
          .point-value {
            display: block;
            font-size: $font-size-xs;
            color: $text-secondary;
            text-align: center;
            margin-top: 8rpx;
            white-space: nowrap;
          }
        }
      }
    }
    
    .empty-chart {
      @include flex-column-center;
      height: 400rpx;
      background-color: #fafbfc;
      border-radius: $border-radius-medium;
      
      .empty-icon {
        font-size: 80rpx;
        margin-bottom: $spacing-md;
      }
      
      .empty-text {
        color: $text-placeholder;
        font-size: $font-size-md;
      }
    }
  }
  
  .stats-summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: $spacing-md;
    
    .summary-item {
      @include flex-column-center;
      padding: $spacing-md;
      background-color: $background-color;
      border-radius: $border-radius-medium;
      
      .summary-label {
        font-size: $font-size-xs;
        color: $text-secondary;
        margin-bottom: 4rpx;
      }
      
      .summary-value {
        font-size: $font-size-md;
        font-weight: bold;
        color: $text-primary;
      }
    }
  }
}

// 空状态样式
.empty-state {
  @include flex-column-center;
  padding: $spacing-xl;
  
  .empty-icon {
    font-size: 80rpx;
    margin-bottom: $spacing-md;
  }
  
  .empty-text {
    color: $text-placeholder;
    font-size: $font-size-md;
  }
}
</style>
