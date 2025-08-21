<template>
  <view class="report-detail-page">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">{{ reportTitle }}</text>
    </view>

    <!-- 报告内容 -->
    <view class="report-content">
      <!-- 总览统计卡片 -->
      <BaseCard class="overview-card" v-if="reportType === 'overview'">
        <template #header>
          <text class="card-title">数据概览</text>
        </template>
        
        <view class="stats-grid">
          <view class="stat-item">
            <text class="stat-number">{{ overviewData.total_books || 0 }}</text>
            <text class="stat-label">总书籍数</text>
          </view>
          <view class="stat-item">
            <text class="stat-number">{{ overviewData.total_rankings || 0 }}</text>
            <text class="stat-label">总榜单数</text>
          </view>
          <view class="stat-item">
            <text class="stat-number">{{ overviewData.total_authors || 0 }}</text>
            <text class="stat-label">作者数量</text>
          </view>
          <view class="stat-item">
            <text class="stat-number">{{ overviewData.recent_updates || 0 }}</text>
            <text class="stat-label">近期更新</text>
          </view>
        </view>
      </BaseCard>

      <!-- 热门榜单卡片 -->
      <BaseCard class="hot-rankings-card" v-if="reportType === 'rankings'">
        <template #header>
          <text class="card-title">热门榜单</text>
        </template>
        
        <view class="rankings-list">
          <view 
            class="ranking-item"
            v-for="(ranking, index) in hotRankings"
            :key="ranking.id"
            @tap="goToRankingDetail(ranking)"
          >
            <view class="ranking-rank">
              <text class="rank-number">{{ index + 1 }}</text>
            </view>
            <view class="ranking-info">
              <text class="ranking-name">{{ ranking.name }}</text>
              <text class="ranking-score">活跃度: {{ ranking.activity_score }}%</text>
            </view>
            <view class="ranking-stats">
              <text class="ranking-changes">{{ ranking.recent_changes }}本变动</text>
              <text class="ranking-total">共{{ ranking.total_books }}本</text>
            </view>
          </view>
        </view>
      </BaseCard>

      <!-- 趋势图表区域 -->
      <BaseCard class="chart-card">
        <template #header>
          <text class="card-title">数据趋势</text>
        </template>
        
        <view class="chart-container">
          <view class="chart-placeholder">
            <text class="chart-icon">📊</text>
            <text class="chart-text">图表数据加载中...</text>
            <text class="chart-desc">此处将显示{{ reportTitle }}的趋势变化</text>
          </view>
        </view>
      </BaseCard>

      <!-- 数据表格 -->
      <BaseCard class="table-card">
        <template #header>
          <text class="card-title">详细数据</text>
        </template>
        
        <scroll-view class="table-container" scroll-x>
          <view class="data-table">
            <view class="table-header">
              <text class="table-cell">时间</text>
              <text class="table-cell">数值</text>
              <text class="table-cell">变化</text>
              <text class="table-cell">状态</text>
            </view>
            <view 
              class="table-row"
              v-for="(row, index) in tableData"
              :key="index"
            >
              <text class="table-cell">{{ row.time }}</text>
              <text class="table-cell">{{ row.value }}</text>
              <text class="table-cell" :class="getChangeClass(row.change)">
                {{ formatChange(row.change) }}
              </text>
              <text class="table-cell">{{ row.status }}</text>
            </view>
          </view>
        </scroll-view>
      </BaseCard>
    </view>
  </view>
</template>

<script>
import BaseCard from '@/components/BaseCard.vue'
import dataManager from '@/utils/data-manager.js'
import formatterMixin from '@/mixins/formatter.js'
import navigationMixin from '@/mixins/navigation.js'

export default {
  name: 'ReportDetailPage',
  components: {
    BaseCard
  },
  mixins: [formatterMixin, navigationMixin],
  
  data() {
    return {
      reportType: '',
      reportTitle: '统计报告',
      overviewData: {},
      hotRankings: [],
      tableData: [],
      loading: false
    }
  },
  
  onLoad(options) {
    if (options.type) {
      this.reportType = options.type
      this.setReportTitle()
      this.loadReportData()
    }
  },
  
  methods: {
    setReportTitle() {
      const titles = {
        overview: '数据概览报告',
        rankings: '热门榜单报告',
        books: '书籍统计报告',
        trends: '趋势分析报告'
      }
      this.reportTitle = titles[this.reportType] || '统计报告'
      
      // 设置页面标题
      uni.setNavigationBarTitle({
        title: this.reportTitle
      })
    },
    
    async loadReportData() {
      this.loading = true
      try {
        if (this.reportType === 'overview') {
          await this.loadOverviewData()
        } else if (this.reportType === 'rankings') {
          await this.loadRankingsData()
        }
        
        // 加载表格数据
        await this.loadTableData()
      } catch (error) {
        console.error('加载报告数据失败:', error)
        uni.showToast({
          title: '加载失败',
          icon: 'none'
        })
      } finally {
        this.loading = false
      }
    },
    
    async loadOverviewData() {
      const data = await dataManager.getOverviewStats()
      this.overviewData = data || {}
    },
    
    async loadRankingsData() {
      const data = await dataManager.getHotRankings({ limit: 10 })
      this.hotRankings = data || []
    },
    
    async loadTableData() {
      // 生成模拟表格数据
      this.tableData = Array.from({ length: 10 }, (_, index) => ({
        time: new Date(Date.now() - index * 24 * 60 * 60 * 1000).toLocaleDateString(),
        value: Math.floor(Math.random() * 1000) + 500,
        change: Math.floor(Math.random() * 200) - 100,
        status: Math.random() > 0.5 ? '正常' : '异常'
      }))
    },
    
    formatChange(change) {
      if (change > 0) {
        return `+${change}`
      } else if (change < 0) {
        return `${change}`
      } else {
        return '0'
      }
    },
    
    getChangeClass(change) {
      if (change > 0) return 'positive'
      if (change < 0) return 'negative'
      return 'neutral'
    },
    
    goToRankingDetail(ranking) {
      this.navigateTo('/pages/ranking/detail', {
        id: ranking.id,
        name: ranking.name
      })
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.report-detail-page {
  min-height: 100vh;
  background: $surface-white;
  padding-bottom: env(safe-area-inset-bottom);
}

.page-header {
  padding: $spacing-lg;
  background: $surface-default;
  border-bottom: 1px solid rgba($text-secondary, 0.1);
  
  .page-title {
    font-size: 36rpx;
    font-weight: 600;
    color: $text-primary;
  }
}

.report-content {
  padding: $spacing-lg;
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
  
  .card-title {
    font-size: 28rpx;
    font-weight: 600;
    color: $text-primary;
  }
}

.overview-card {
  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: $spacing-lg;
    
    .stat-item {
      text-align: center;
      padding: $spacing-md;
      background: $surface-container-high;
      border-radius: $radius-md;
      
      .stat-number {
        display: block;
        font-size: 48rpx;
        font-weight: 700;
        color: $brand-primary;
        margin-bottom: 8rpx;
      }
      
      .stat-label {
        font-size: 24rpx;
        color: $text-secondary;
      }
    }
  }
}

.hot-rankings-card {
  .rankings-list {
    .ranking-item {
      display: flex;
      align-items: center;
      padding: $spacing-md 0;
      
      border-bottom: 1px solid rgba($text-secondary, 0.1);
      
      &:last-child {
        border-bottom: none;
      }
      
      &:active {
        background: rgba($text-secondary, 0.05);
        margin: 0 (-$spacing-sm);
        padding-left: $spacing-sm;
        padding-right: $spacing-sm;
        border-radius: $radius-sm;
      }
      
      .ranking-rank {
        width: 48rpx;
        height: 48rpx;
        background: $brand-primary;
        border-radius: $radius-full;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: $spacing-md;
        
        .rank-number {
          font-size: 20rpx;
          font-weight: 600;
          color: $surface-default;
        }
      }
      
      .ranking-info {
        flex: 1;
        
        .ranking-name {
          display: block;
          font-size: 28rpx;
          font-weight: 500;
          color: $text-primary;
          margin-bottom: 4rpx;
        }
        
        .ranking-score {
          font-size: 22rpx;
          color: $text-secondary;
        }
      }
      
      .ranking-stats {
        text-align: right;
        
        .ranking-changes {
          display: block;
          font-size: 22rpx;
          color: $brand-primary;
          margin-bottom: 4rpx;
        }
        
        .ranking-total {
          font-size: 20rpx;
          color: $text-secondary;
        }
      }
    }
  }
}

.chart-card {
  .chart-container {
    .chart-placeholder {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 120rpx $spacing-lg;
      background: $surface-container-high;
      border-radius: $radius-md;
      
      .chart-icon {
        font-size: 80rpx;
        margin-bottom: $spacing-md;
        opacity: 0.6;
      }
      
      .chart-text {
        font-size: 28rpx;
        color: $text-primary;
        margin-bottom: 8rpx;
      }
      
      .chart-desc {
        font-size: 22rpx;
        color: $text-secondary;
        text-align: center;
        line-height: 1.4;
      }
    }
  }
}

.table-card {
  .table-container {
    width: 100%;
    
    .data-table {
      min-width: 600rpx;
      
      .table-header,
      .table-row {
        display: flex;
        
        .table-cell {
          flex: 1;
          padding: $spacing-sm;
          font-size: 24rpx;
          text-align: center;
          
          &:first-child {
            text-align: left;
          }
        }
      }
      
      .table-header {
        background: $surface-container-high;
        border-radius: $radius-sm;
        
        .table-cell {
          font-weight: 600;
          color: $text-primary;
        }
      }
      
      .table-row {
        border-bottom: 1px solid rgba($text-secondary, 0.1);
        
        .table-cell {
          color: $text-secondary;
          
          &.positive {
            color: #34c759;
          }
          
          &.negative {
            color: #ff3b30;
          }
          
          &.neutral {
            color: $text-secondary;
          }
        }
        
      }
    }
  }
}
</style>