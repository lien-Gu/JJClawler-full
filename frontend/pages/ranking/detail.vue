<template>
  <view class="ranking-detail-page">
    <!-- 榜单头部信息 -->
    <view class="ranking-header">
      <view class="header-bg"></view>
      <view class="header-content">
        <view class="ranking-info">
          <text class="ranking-title">{{ rankingData.name || '榜单详情' }}</text>
          <text class="ranking-desc" v-if="rankingData.description">{{ rankingData.description }}</text>
          <view class="ranking-meta">
            <text class="meta-item">{{ rankingData.siteName }}</text>
            <text class="meta-divider">·</text>
            <text class="meta-item">{{ rankingData.channelName }}</text>
            <text class="meta-divider">·</text>
            <text class="meta-item">{{ formatTime(rankingData.updateTime) }}</text>
          </view>
        </view>
        
        <view class="ranking-actions">
          <view class="action-btn follow-btn" :class="{ 'followed': rankingData.isFollowed }" @tap="toggleFollow">
            <text class="btn-text">{{ rankingData.isFollowed ? '已关注' : '关注' }}</text>
          </view>
          <view class="action-btn share-btn" @tap="shareRanking">
            <text class="btn-text">分享</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 第一层：变化曲线 -->
    <view class="layer-section chart-section">
      <view class="layer-header">
        <text class="layer-title">📈 数据变化趋势</text>
      </view>
      
      <!-- Tab切换 -->
      <view class="chart-tabs">
        <view 
          class="tab-item" 
          :class="{ 'active': activeTab === 'totalClicks' }"
          @tap="switchTab('totalClicks')"
        >
          <text class="tab-text">点击量总和</text>
        </view>
        <view 
          class="tab-item" 
          :class="{ 'active': activeTab === 'avgClicks' }"
          @tap="switchTab('avgClicks')"
        >
          <text class="tab-text">点击量均值</text>
        </view>
        <view 
          class="tab-item" 
          :class="{ 'active': activeTab === 'totalCollects' }"
          @tap="switchTab('totalCollects')"
        >
          <text class="tab-text">收藏量总和</text>
        </view>
        <view 
          class="tab-item" 
          :class="{ 'active': activeTab === 'avgCollects' }"
          @tap="switchTab('avgCollects')"
        >
          <text class="tab-text">收藏量均值</text>
        </view>
      </view>
      
      <!-- 图表区域 -->
      <view class="chart-container">
        <view class="chart-area" v-if="chartData.length > 0">
          <!-- 网格线 -->
          <view class="chart-grid">
            <view class="grid-line" v-for="i in 5" :key="i"></view>
          </view>
          
          <!-- 数据点和连线 -->
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
            
            <!-- SVG连接线 -->
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
          <text class="empty-text">暂无数据</text>
        </view>
      </view>
      
      <!-- 数据概览 -->
      <view class="chart-summary" v-if="chartData.length > 0">
        <view class="summary-item">
          <text class="summary-label">最高值</text>
          <text class="summary-value">{{ formatNumber(getMaxValue()) }}</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">最低值</text>
          <text class="summary-value">{{ formatNumber(getMinValue()) }}</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">总变化</text>
          <text class="summary-value">{{ getTotalChange() }}</text>
        </view>
      </view>
    </view>
    
    <!-- 第二层：书籍列表 -->
    <view class="layer-section books-section">
      <view class="layer-header">
        <text class="layer-title">📚 榜单书籍</text>
        <text class="book-count">共{{ booksList.length }}本</text>
      </view>
      
      <view class="books-list" v-if="booksList.length > 0">
        <view 
          class="book-item"
          v-for="(book, index) in booksList" 
          :key="book.id"
          @tap="goToBookDetail(book)"
        >
          <view class="book-rank">{{ index + 1 }}</view>
          <view class="book-info">
            <view class="book-title">{{ book.title }}</view>
            <view class="book-stats">
              <text class="stat-item">
                收藏: {{ formatNumber(book.collections) }}
                <text class="change-indicator" :class="book.collectionChange > 0 ? 'up' : 'down'">
                  {{ book.collectionChange > 0 ? '↑' : '↓' }}{{ Math.abs(book.collectionChange) }}
                </text>
              </text>
              <text class="stat-item">
                排名: 
                <text class="change-indicator" :class="book.rankChange > 0 ? 'down' : 'up'">
                  {{ book.rankChange === 0 ? '—' : (book.rankChange > 0 ? '↓' : '↑') }}{{ Math.abs(book.rankChange) }}
                </text>
              </text>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 加载更多 -->
      <view class="load-more" v-if="hasMore">
        <view class="load-btn" @tap="loadMore" v-if="!loadingMore">
          <text class="load-text">加载更多</text>
        </view>
        <view class="loading" v-else>
          <text class="loading-text">加载中...</text>
        </view>
      </view>
      
      <!-- 无更多数据 -->
      <view class="no-more" v-else-if="booksList.length > 0">
        <text class="no-more-text">没有更多数据了</text>
      </view>
      
      <!-- 空状态 -->
      <view class="empty-state" v-if="!loading && booksList.length === 0">
        <text class="empty-icon">📚</text>
        <text class="empty-text">暂无书籍数据</text>
        <view class="empty-btn" @tap="refreshData">
          <text class="btn-text">重新加载</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { get } from '@/utils/request.js'
import { getSync, setSync } from '@/utils/storage.js'

/**
 * 榜单详情页面 - 两层数据展示
 * @description 第一层：变化曲线，第二层：书籍列表
 */
export default {
  name: 'RankingDetailPage',
  
  data() {
    return {
      // 榜单ID
      rankingId: '',
      
      // 榜单数据
      rankingData: {
        name: '',
        description: '',
        siteName: '',
        channelName: '',
        updateTime: ''
      },
      
      // 当前选中的tab
      activeTab: 'totalClicks', // 'totalClicks' | 'avgClicks' | 'totalCollects' | 'avgCollects'
      
      // 图表数据
      chartStats: {
        dates: [],
        totalClicksData: [],    // 点击量增量总和
        avgClicksData: [],      // 点击量增量平均值
        totalCollectsData: [],  // 收藏量增量总和
        avgCollectsData: []     // 收藏量增量平均值
      },
      
      // 书籍列表
      booksList: [],
      
      // 分页信息
      currentPage: 1,
      pageSize: 20,
      hasMore: true,
      
      // 加载状态
      loading: false,
      loadingMore: false
    }
  },
  
  computed: {
    /**
     * 当前显示的图表数据
     */
    chartData() {
      switch (this.activeTab) {
        case 'totalClicks':
          return this.chartStats.totalClicksData || []
        case 'avgClicks':
          return this.chartStats.avgClicksData || []
        case 'totalCollects':
          return this.chartStats.totalCollectsData || []
        case 'avgCollects':
          return this.chartStats.avgCollectsData || []
        default:
          return []
      }
    },
    
    /**
     * 图表点位数据
     */
    chartPoints() {
      if (this.chartData.length === 0) return []
      
      const maxValue = Math.max(...this.chartData)
      const minValue = Math.min(...this.chartData)
      const range = maxValue - minValue || 1
      
      return this.chartData.map((value, index) => ({
        x: (index / (this.chartData.length - 1)) * 100,
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
      this.rankingId = options.id
      this.initData()
    }
  },
  
  // 下拉刷新
  onPullDownRefresh() {
    this.refreshData().finally(() => {
      uni.stopPullDownRefresh()
    })
  },
  
  // 上拉加载更多
  onReachBottom() {
    if (this.hasMore && !this.loadingMore) {
      this.loadMore()
    }
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
          this.fetchRankingInfo(),
          this.fetchChartStats(),
          this.fetchBooksList(true)
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
      const cachedRanking = getSync(`ranking_detail_${this.rankingId}`)
      const cachedChart = getSync(`ranking_chart_${this.rankingId}`)
      const cachedBooks = getSync(`ranking_books_${this.rankingId}`)
      
      if (cachedRanking) {
        this.rankingData = { ...this.rankingData, ...cachedRanking }
      }
      
      if (cachedChart) {
        this.chartStats = cachedChart
      }
      
      if (cachedBooks) {
        this.booksList = cachedBooks
      }
    },
    
    /**
     * 获取榜单信息
     */
    async fetchRankingInfo() {
      try {
        // 模拟API调用
        const data = await this.getMockRankingData()
        
        this.rankingData = { ...this.rankingData, ...data }
        setSync(`ranking_detail_${this.rankingId}`, data, 30 * 60 * 1000) // 缓存30分钟
      } catch (error) {
        console.error('获取榜单信息失败:', error)
        throw error
      }
    },
    
    /**
     * 获取图表统计数据
     */
    async fetchChartStats() {
      try {
        // 模拟API调用
        const data = await this.getMockChartData()
        
        this.chartStats = data
        setSync(`ranking_chart_${this.rankingId}`, data, 15 * 60 * 1000) // 缓存15分钟
      } catch (error) {
        console.error('获取图表数据失败:', error)
        throw error
      }
    },
    
    /**
     * 获取书籍列表
     */
    async fetchBooksList(reset = false) {
      try {
        if (reset) {
          this.currentPage = 1
          this.hasMore = true
        }
        
        // 模拟API调用
        const data = await this.getMockBooksData(this.currentPage)
        
        if (reset) {
          this.booksList = data.list
        } else {
          this.booksList.push(...data.list)
        }
        
        this.hasMore = data.hasMore || false
        this.currentPage++
        
        // 缓存第一页数据
        if (reset) {
          setSync(`ranking_books_${this.rankingId}`, data.list, 15 * 60 * 1000) // 缓存15分钟
        }
      } catch (error) {
        console.error('获取书籍列表失败:', error)
        throw error
      }
    },
    
    /**
     * 获取模拟榜单数据
     */
    async getMockRankingData() {
      await new Promise(resolve => setTimeout(resolve, 500))
      
      return {
        name: '言情总榜',
        description: '言情分站综合排行榜单',
        siteName: '言情',
        channelName: '总榜',
        updateTime: '2024-01-15T10:30:00'
      }
    },
    
    /**
     * 获取模拟图表数据
     */
    async getMockChartData() {
      await new Promise(resolve => setTimeout(resolve, 300))
      
      // 生成30天的模拟数据
      const dates = []
      const totalClicksData = []
      const avgClicksData = []
      const totalCollectsData = []
      const avgCollectsData = []
      
      const now = new Date()
      for (let i = 29; i >= 0; i--) {
        const date = new Date(now)
        date.setDate(date.getDate() - i)
        dates.push(date.toISOString().split('T')[0])
        
        // 模拟点击量增量总和（有波动）
        const baseTotalClicks = 50000 + i * 1000
        const totalClicksVariation = Math.random() * 10000 - 5000
        totalClicksData.push(Math.max(0, Math.floor(baseTotalClicks + totalClicksVariation)))
        
        // 模拟点击量增量平均值
        const baseAvgClicks = 250 + i * 5
        const avgClicksVariation = Math.random() * 50 - 25
        avgClicksData.push(Math.max(0, Math.floor(baseAvgClicks + avgClicksVariation)))
        
        // 模拟收藏量增量总和
        const baseTotalCollects = 5000 + i * 100
        const totalCollectsVariation = Math.random() * 1000 - 500
        totalCollectsData.push(Math.max(0, Math.floor(baseTotalCollects + totalCollectsVariation)))
        
        // 模拟收藏量增量平均值
        const baseAvgCollects = 25 + i * 0.5
        const avgCollectsVariation = Math.random() * 5 - 2.5
        avgCollectsData.push(Math.max(0, Math.floor(baseAvgCollects + avgCollectsVariation)))
      }
      
      return {
        dates,
        totalClicksData,
        avgClicksData,
        totalCollectsData,
        avgCollectsData
      }
    },
    
    /**
     * 获取模拟书籍数据
     */
    async getMockBooksData(page = 1) {
      await new Promise(resolve => setTimeout(resolve, 200))
      
      const pageSize = 20
      const totalBooks = 100
      const startIndex = (page - 1) * pageSize
      
      const books = []
      for (let i = 0; i < pageSize && startIndex + i < totalBooks; i++) {
        const index = startIndex + i
        books.push({
          id: `book_${index + 1}`,
          title: `榜单书籍${index + 1}`,
          collections: Math.floor(Math.random() * 50000) + 10000,
          collectionChange: Math.floor(Math.random() * 1000) - 500,
          rankChange: Math.floor(Math.random() * 10) - 5
        })
      }
      
      return {
        list: books,
        hasMore: startIndex + pageSize < totalBooks
      }
    },
    
    /**
     * 刷新数据
     */
    async refreshData() {
      try {
        await Promise.all([
          this.fetchRankingInfo(),
          this.fetchChartStats(),
          this.fetchBooksList(true)
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
     * 加载更多
     */
    async loadMore() {
      if (this.loadingMore || !this.hasMore) return
      
      this.loadingMore = true
      
      try {
        await this.fetchBooksList()
      } catch (error) {
        this.showError('加载失败')
      } finally {
        this.loadingMore = false
      }
    },
    
    /**
     * 切换图表Tab
     */
    switchTab(tab) {
      this.activeTab = tab
    },
    
    /**
     * 获取最大值
     */
    getMaxValue() {
      return Math.max(...this.chartData)
    },
    
    /**
     * 获取最小值
     */
    getMinValue() {
      return Math.min(...this.chartData)
    },
    
    /**
     * 获取总变化
     */
    getTotalChange() {
      if (this.chartData.length < 2) return '0%'
      
      const first = this.chartData[0]
      const last = this.chartData[this.chartData.length - 1]
      const change = ((last - first) / first * 100).toFixed(1)
      
      return change > 0 ? `+${change}%` : `${change}%`
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
    },
    
    /**
     * 跳转到书籍详情
     */
    goToBookDetail(book) {
      uni.navigateTo({
        url: `/pages/book/detail?id=${book.id}`
      })
    },
    
    /**
     * 切换关注状态
     */
    async toggleFollow() {
      try {
        const action = this.rankingData.isFollowed ? 'unfollow' : 'follow'
        await get(`/api/rankings/${this.rankingId}/${action}`, {}, { method: 'POST' })
        
        this.rankingData.isFollowed = !this.rankingData.isFollowed
        
        uni.showToast({
          title: this.rankingData.isFollowed ? '关注成功' : '取消关注',
          icon: 'success',
          duration: 1500
        })
      } catch (error) {
        this.showError('操作失败')
      }
    },
    
    /**
     * 分享榜单
     */
    shareRanking() {
      uni.share({
        provider: 'weixin',
        scene: 'WXSceneSession',
        type: 0,
        title: this.rankingData.name,
        summary: this.rankingData.description || '来看看这个热门榜单',
        success: () => {
          uni.showToast({
            title: '分享成功',
            icon: 'success'
          })
        },
        fail: () => {
          this.showError('分享失败')
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.ranking-detail-page {
  min-height: 100vh;
  background-color: $page-background;
  padding-bottom: $safe-area-bottom;
}

// 榜单头部信息
.ranking-header {
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
    .ranking-info {
      .ranking-title {
        display: block;
        font-size: $font-size-xl;
        font-weight: bold;
        margin-bottom: $spacing-xs;
        line-height: 1.3;
      }
      
      .ranking-desc {
        display: block;
        font-size: $font-size-sm;
        opacity: 0.9;
        margin-bottom: $spacing-sm;
        line-height: 1.4;
      }
      
      .ranking-meta {
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
}

// 层级区域通用样式
.layer-section {
  background-color: white;
  margin-bottom: $spacing-sm;
  padding: $spacing-lg;
  
  .layer-header {
    @include flex-between;
    align-items: center;
    margin-bottom: $spacing-lg;
    
    .layer-title {
      font-size: $font-size-lg;
      font-weight: bold;
      color: $text-primary;
    }
    
    .book-count {
      font-size: $font-size-sm;
      color: $text-secondary;
    }
  }
}

// 第一层：图表区域
.chart-section {
  .chart-tabs {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: $spacing-xs;
    background-color: $background-color;
    border-radius: $border-radius-medium;
    padding: 6rpx;
    margin-bottom: $spacing-lg;
    
    .tab-item {
      @include flex-center;
      padding: $spacing-sm;
      border-radius: $border-radius-small;
      transition: all 0.3s ease;
      
      .tab-text {
        font-size: $font-size-xs;
        color: $text-secondary;
        text-align: center;
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
      height: 300rpx;
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
            width: 8rpx;
            height: 8rpx;
            background-color: $primary-color;
            border-radius: 50%;
            margin: 0 auto;
          }
          
          .point-value {
            display: block;
            font-size: $font-size-xs;
            color: $text-secondary;
            text-align: center;
            margin-top: 6rpx;
            white-space: nowrap;
          }
        }
      }
    }
    
    .empty-chart {
      @include flex-column-center;
      height: 300rpx;
      background-color: #fafbfc;
      border-radius: $border-radius-medium;
      
      .empty-icon {
        font-size: 60rpx;
        margin-bottom: $spacing-sm;
      }
      
      .empty-text {
        color: $text-placeholder;
        font-size: $font-size-sm;
      }
    }
  }
  
  .chart-summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: $spacing-md;
    
    .summary-item {
      @include flex-column-center;
      padding: $spacing-sm;
      background-color: $background-color;
      border-radius: $border-radius-medium;
      
      .summary-label {
        font-size: $font-size-xs;
        color: $text-secondary;
        margin-bottom: 4rpx;
      }
      
      .summary-value {
        font-size: $font-size-sm;
        font-weight: bold;
        color: $text-primary;
      }
    }
  }
}

// 第二层：书籍列表
.books-section {
  .books-list {
    .book-item {
      @include flex-center;
      padding: $spacing-lg;
      border-bottom: 2rpx solid $border-light;
      transition: background-color 0.3s ease;
      
      &:last-child {
        border-bottom: none;
      }
      
      &:active {
        background-color: $background-color;
      }
      
      .book-rank {
        @include flex-center;
        width: 60rpx;
        height: 60rpx;
        background-color: $primary-color;
        color: white;
        border-radius: 50%;
        font-size: $font-size-sm;
        font-weight: bold;
        margin-right: $spacing-md;
        flex-shrink: 0;
      }
      
      .book-info {
        flex: 1;
        
        .book-title {
          font-size: $font-size-md;
          font-weight: bold;
          color: $text-primary;
          margin-bottom: $spacing-xs;
          @include text-ellipsis;
        }
        
        .book-stats {
          @include flex-center;
          gap: $spacing-lg;
          
          .stat-item {
            font-size: $font-size-sm;
            color: $text-secondary;
            
            .change-indicator {
              margin-left: $spacing-xs;
              font-size: $font-size-xs;
              
              &.up {
                color: #22c55e;
              }
              
              &.down {
                color: #ef4444;
              }
            }
          }
        }
      }
    }
  }
  
  .load-more {
    padding: $spacing-lg 0;
    
    .load-btn {
      @include flex-center;
      padding: $spacing-md;
      background-color: $background-color;
      border-radius: $border-radius-medium;
      
      .load-text {
        color: $primary-color;
        font-size: $font-size-sm;
      }
      
      &:active {
        opacity: 0.7;
      }
    }
    
    .loading {
      @include flex-center;
      padding: $spacing-md;
      
      .loading-text {
        color: $text-placeholder;
        font-size: $font-size-sm;
      }
    }
  }
  
  .no-more {
    @include flex-center;
    padding: $spacing-lg 0;
    
    .no-more-text {
      color: $text-placeholder;
      font-size: $font-size-sm;
    }
  }
  
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
      margin-bottom: $spacing-lg;
    }
    
    .empty-btn {
      @include flex-center;
      padding: $spacing-sm $spacing-lg;
      background-color: $primary-color;
      border-radius: $border-radius-medium;
      
      .btn-text {
        color: white;
        font-size: $font-size-sm;
      }
      
      &:active {
        opacity: 0.8;
      }
    }
  }
}
</style> 