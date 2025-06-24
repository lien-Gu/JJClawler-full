<template>
  <view class="index-page">
    <!-- 主要内容区域 -->
    <view class="content-container">
      <!-- 问候语 -->
      <view class="greeting-section">
        <text class="greeting-text">嗨~</text>
      </view>
      
      <!-- 统计报告卡片 -->
      <view class="summary-card" @tap="goToStatisticsDetail">
        <view class="summary-content">
          <text class="summary-title">统计报告</text>
          <view class="summary-stats">
            <text class="stats-text">总书籍: {{ overviewStats.total_books || 0 }}</text>
            <text class="stats-text">总榜单: {{ overviewStats.total_rankings || 0 }}</text>
          </view>
          <view class="summary-button" @tap.stop="refreshData">
            <text class="button-text">刷新数据</text>
          </view>
        </view>
      </view>
      
      <!-- 分项统计 -->
      <view class="reports-section">
        <text class="section-title">分项</text>
        <scroll-view class="reports-scroll" scroll-x show-scrollbar="false">
          <view class="reports-container">
            <view class="report-card" @tap="goToRankingStats">
              <text class="report-title">榜单统计</text>
              <text class="report-desc">查看榜单数据</text>
            </view>
            <view class="report-card" @tap="goToBookStats">
              <text class="report-title">书籍统计</text>
              <text class="report-desc">查看书籍数据</text>
            </view>
            <view class="report-card" @tap="goToChannelStats">
              <text class="report-title">频道统计</text>
              <text class="report-desc">查看频道数据</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 热门榜单 -->
      <view class="hot-rankings-section">
        <text class="section-title">热门榜单</text>
        <view class="rankings-list">
          <view 
            class="ranking-item" 
            v-for="ranking in hotRankings" 
            :key="ranking.id"
            @tap="goToRankingDetail(ranking)"
          >
            <text class="ranking-name">{{ ranking.name }}</text>
            <text class="ranking-count">{{ ranking.total_books || 0 }}本</text>
          </view>
        </view>
        <view class="view-more" @tap="goToRanking">
          <text class="more-text">查看更多</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import dataManager from '@/utils/data-manager.js'

export default {
	name: 'IndexPage',
	
	data() {
		return {
      overviewStats: {},
      hotRankings: []
		}
	},
	
	onLoad() {
		this.loadData()
	},

  onShow() {
    // 每次显示页面时检查数据
    this.loadData()
  },
	
	methods: {
    async loadData() {
      try {
        const [statsRes, rankingsRes] = await Promise.all([
          dataManager.getOverviewStats(),
          dataManager.getHotRankings({ limit: 4 })
        ])
        
        if (statsRes) {
          this.overviewStats = statsRes
        }
        
        if (rankingsRes && Array.isArray(rankingsRes)) {
          this.hotRankings = rankingsRes
        }
      } catch (error) {
        console.error('数据加载失败:', error)
      }
    },

    async refreshData() {
      try {
        await this.loadData()
        uni.showToast({
          title: '刷新成功',
          icon: 'success',
          duration: 1500
        })
      } catch (error) {
        uni.showToast({
          title: '刷新失败',
          icon: 'none',
          duration: 2000
        })
      }
    },
		
		goToStatisticsDetail() {
			// 可以跳转到统计详情页面
			console.log('跳转到统计详情')
		},
		
		goToRankingStats() {
			uni.switchTab({
				url: '/pages/ranking/index'
			})
		},
		
		goToBookStats() {
			// 可以跳转到书籍统计页面
			console.log('跳转到书籍统计')
		},
		
		goToChannelStats() {
			// 可以跳转到频道统计页面
			console.log('跳转到频道统计')
		},

    goToRankingDetail(ranking) {
      uni.navigateTo({
        url: `/pages/ranking/detail?id=${ranking.id}`
      })
    },

    goToRanking() {
      uni.switchTab({
        url: '/pages/ranking/index'
      })
    }
	}
}
</script>

<style lang="scss" scoped>
.index-page {
  min-height: 100vh;
  background: linear-gradient(to bottom, #f4f0eb 0%, #e8e1d7 100%);
  padding-bottom: $safe-area-bottom;
}

.content-container {
  padding: 32rpx;
}

.greeting-section {
  margin-bottom: 48rpx;
  padding-top: 24rpx;
  
  .greeting-text {
    font-size: 64rpx;
    font-weight: 700;
    color: #2c2c2c;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  }
}

.summary-card {
  background-color: #c3c3c3;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 48rpx;
  
  .summary-content {
    .summary-title {
      display: block;
      font-size: 36rpx;
      font-weight: 600;
      color: #2c2c2c;
      margin-bottom: 16rpx;
    }

    .summary-stats {
      display: flex;
      gap: 24rpx;
      margin-bottom: 24rpx;
      
      .stats-text {
        font-size: 28rpx;
        color: #666666;
      }
    }
    
    .summary-button {
      background-color: #64a347;
      border-radius: 16rpx;
      padding: 16rpx 32rpx;
      align-self: flex-start;
      
      .button-text {
        font-size: 28rpx;
        font-weight: 500;
        color: #ffffff;
      }
      
      &:active {
        opacity: 0.8;
      }
    }
  }
  
  &:active {
    opacity: 0.95;
  }
}

.reports-section {
  margin-bottom: 48rpx;
  
  .section-title {
    display: block;
    font-size: 36rpx;
    font-weight: 600;
    color: #2c2c2c;
    margin-bottom: 24rpx;
  }
  
  .reports-scroll {
    white-space: nowrap;
  }
  
  .reports-container {
    display: flex;
    gap: 16rpx;
    
    .report-card {
      flex-shrink: 0;
      width: 240rpx;
      background-color: #c3c3c3;
      border-radius: 16rpx;
      padding: 24rpx;
      
      .report-title {
        display: block;
        font-size: 32rpx;
        font-weight: 500;
        color: #2c2c2c;
        margin-bottom: 8rpx;
      }
      
      .report-desc {
        font-size: 24rpx;
        color: #666666;
        line-height: 1.4;
      }
      
      &:active {
        opacity: 0.8;
      }
    }
  }
}

.hot-rankings-section {
  .section-title {
    display: block;
    font-size: 36rpx;
    font-weight: 600;
    color: #2c2c2c;
    margin-bottom: 24rpx;
  }

  .rankings-list {
    margin-bottom: 24rpx;

    .ranking-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background-color: #c3c3c3;
      border-radius: 16rpx;
      padding: 24rpx;
      margin-bottom: 12rpx;

      .ranking-name {
        font-size: 32rpx;
        font-weight: 500;
        color: #2c2c2c;
      }

      .ranking-count {
        font-size: 24rpx;
        color: #666666;
      }

      &:active {
        opacity: 0.8;
      }
    }
  }

  .view-more {
    display: flex;
    justify-content: center;
    padding: 16rpx;

    .more-text {
      font-size: 28rpx;
      color: #64a347;
      font-weight: 500;
    }

    &:active {
      opacity: 0.7;
    }
  }
}
</style>