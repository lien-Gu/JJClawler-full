<template>
  <view class="book-detail-page">
    <!-- 页面头部 -->
    <view class="page-header">
      <view class="header-content">
        <view class="book-info">
          <text class="book-title">{{ bookData.title || '书籍详情' }}</text>
          <text class="book-category">{{ bookData.category || '未知分类' }}</text>
        </view>
        <view class="header-actions">
          <BaseButton
              :type="bookData.isFollowed ? 'secondary' : 'primary'"
              :icon="bookData.isFollowed ? '★' : '☆'"
              size="small"
              round
              @click="toggleFollow"
          />
        </view>
      </view>
    </view>

    <!-- 统计图表区域 -->
    <view class="stats-section">
      <BaseCard class="stats-card">
        <template #header>
          <text class="stats-title">数据统计</text>
        </template>

        <!-- 标签页切换 -->
        <view class="tab-group">
          <view
              class="tab-item"
              :class="{ 'active': currentTab === tab.key }"
              v-for="tab in statsTabs"
              :key="tab.key"
              @tap="switchTab(tab.key)"
          >
            <text class="tab-text">{{ tab.label }}</text>
          </view>
        </view>

        <!-- 图表展示区域 -->
        <view class="chart-container">
          <view v-if="currentTab === 'trend'" class="trend-chart">
            <text class="chart-placeholder">📈 趋势图表</text>
            <text class="chart-desc">显示{{ bookData.title }}的数据变化趋势</text>
          </view>

          <view v-if="currentTab === 'ranking'" class="ranking-chart">
            <text class="chart-placeholder">📊 排名分析</text>
            <text class="chart-desc">显示{{ bookData.title }}在各榜单的排名情况</text>
          </view>

          <view v-if="currentTab === 'compare'" class="compare-chart">
            <text class="chart-placeholder">📋 对比分析</text>
            <text class="chart-desc">与同类书籍的数据对比</text>
          </view>
        </view>
      </BaseCard>
    </view>

    <!-- 榜单历史 -->
    <view class="ranking-history-section">
      <BaseCard class="ranking-card">
        <template #header>
          <text class="ranking-title">上榜历史</text>
        </template>

        <view class="ranking-list" v-if="rankingHistory.length > 0">
          <view
              class="ranking-item"
              v-for="(ranking, index) in rankingHistory"
              :key="ranking.id"
              @tap="goToRankingDetail(ranking)"
          >
            <view class="ranking-info">
              <view class="ranking-header">
                <text class="ranking-index">{{ index + 1 }}</text>
                <text class="ranking-name">{{ ranking.name }}</text>
              </view>
              <view class="ranking-details">
                <text class="ranking-change" :class="getRankingChangeClass(ranking.change)">
                  {{ formatRankingChange(ranking.change) }}
                </text>
                <text class="ranking-period">{{ ranking.period }}</text>
              </view>
            </view>

            <view class="ranking-status">
              <view
                  class="status-badge"
                  :class="{ 'active': ranking.isActive }"
              >
                <text class="status-text">
                  {{ ranking.isActive ? '榜上' : '已出榜' }}
                </text>
              </view>
            </view>
          </view>
        </view>

        <view v-else class="empty-ranking">
          <text class="empty-text">暂无上榜记录</text>
        </view>
      </BaseCard>
    </view>
  </view>
</template>

<script>
import BaseCard from '@/components/BaseCard.vue'
import BaseButton from '@/components/BaseButton.vue'
import requestManager from '@/api/request.js'
import navigation from '@/utils/navigation.js'

export default {
  name: 'BookDetailPage',
  components: {
    BaseCard,
    BaseButton
  },

  data() {
    return {
      bookId: '',
      bookData: {
        title: '',
        author: '',
        category: '',
        collectCount: 0,
        clickCount: 0,
        rankings: [],
        isFollowed: false
      },
      currentTab: 'trend',
      statsTabs: [
        {key: 'trend', label: '趋势'},
        {key: 'ranking', label: '排名'},
        {key: 'compare', label: '对比'}
      ],
      rankingHistory: [],
      loading: false
    }
  },

  onLoad(options) {
    if (options.id) {
      this.bookId = options.id
      this.loadData()
    }
  },

  methods: {
    ...navigation,
    async loadData() {
      this.loading = true
      try {
        const data = await requestManager.getBookDetail(this.bookId)
        if (data) {
          this.bookData = data
          // 设置页面标题
          uni.setNavigationBarTitle({
            title: this.bookData.title || '书籍详情'
          })

          // 检查是否已关注
          this.checkFollowStatus()
        }

        // 加载榜单历史
        await this.loadRankingHistory()
      } catch (error) {
        console.error('数据加载失败:', error)
        uni.showToast({
          title: '加载失败',
          icon: 'none'
        })
      } finally {
        this.loading = false
      }
    },

    async loadRankingHistory() {
      try {
        const historyData = await requestManager.getBookRankings(this.bookId)
        if (historyData && Array.isArray(historyData)) {
          this.rankingHistory = historyData.map(item => ({
            ...item,
            change: item.rankChange || 0,
            period: this.formatPeriod(item.startDate, item.endDate),
            isActive: item.isActive || false
          }))
        }
      } catch (error) {
        console.error('加载榜单历史失败:', error)
      }
    },

    checkFollowStatus() {
      try {
        const followList = uni.getStorageSync('followList') || []
        this.bookData.isFollowed = followList.some(item => item.id === this.bookId)
      } catch (error) {
        console.error('检查关注状态失败:', error)
      }
    },

    switchTab(tabKey) {
      this.currentTab = tabKey
    },

    async toggleFollow() {
      try {
        const isCurrentlyFollowed = this.bookData.isFollowed

        if (isCurrentlyFollowed) {
          this.removeFromFollow()
        } else {
          this.addToFollow()
        }

        this.bookData.isFollowed = !isCurrentlyFollowed
      } catch (error) {
        console.error('关注操作失败:', error)
        uni.showToast({
          title: '操作失败',
          icon: 'none'
        })
      }
    },

    addToFollow() {
      try {
        const followList = uni.getStorageSync('followList') || []
        const followItem = {
          id: this.bookData.id || this.bookId,
          type: 'book',
          name: this.bookData.title,
          author: this.bookData.author,
          category: this.bookData.category,
          isOnList: this.rankingHistory.some(r => r.isActive),
          weeklyGrowth: this.bookData.weeklyGrowth || 0,
          followDate: new Date().toISOString()
        }

        const existingIndex = followList.findIndex(item => item.id === this.bookId)
        if (existingIndex === -1) {
          followList.push(followItem)
          uni.setStorageSync('followList', followList)

          uni.showToast({
            title: '已关注',
            icon: 'success'
          })
        }
      } catch (error) {
        console.error('添加关注失败:', error)
      }
    },

    removeFromFollow() {
      try {
        const followList = uni.getStorageSync('followList') || []
        const newList = followList.filter(item => item.id !== this.bookId)
        uni.setStorageSync('followList', newList)

        uni.showToast({
          title: '已取消关注',
          icon: 'success'
        })
      } catch (error) {
        console.error('取消关注失败:', error)
      }
    },

    formatPeriod(startDate, endDate) {
      if (!startDate && !endDate) return '未知周期'

      if (startDate && endDate) {
        const start = new Date(startDate)
        const end = new Date(endDate)
        return `${start.getMonth() + 1}/${start.getDate()} - ${end.getMonth() + 1}/${end.getDate()}`
      }

      if (startDate) {
        const date = new Date(startDate)
        return `${date.getMonth() + 1}/${date.getDate()} 至今`
      }

      return '未知周期'
    },

    formatRankingChange(change) {
      if (!change && change !== 0) return '无变化'

      if (change > 0) {
        return `↗ +${change}`
      } else if (change < 0) {
        return `↘ ${change}`
      } else {
        return '— 无变化'
      }
    },

    getRankingChangeClass(change) {
      if (!change && change !== 0) return 'neutral'
      if (change > 0) return 'positive'
      if (change < 0) return 'negative'
      return 'neutral'
    },

    goToRankingDetail(ranking) {
      this.navigateTo('/pages/ranking/detail', {
        id: ranking.rankingId,
        name: ranking.name
      })
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.book-detail-page {
  min-height: 100vh;
  background: $surface-white;
  padding-bottom: 40rpx;
}

.page-header {
  background: $surface-default;
  padding: $spacing-lg;
  border-bottom: 1px solid rgba($text-secondary, 0.1);

  .header-content {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: $spacing-md;

    .book-info {
      flex: 1;
      min-width: 0;

      .book-title {
        display: block;
        font-size: 36rpx;
        font-weight: 600;
        color: $text-primary;
        margin-bottom: 8rpx;
        line-height: 1.3;
      }

      .book-category {
        font-size: 24rpx;
        color: $text-secondary;
      }
    }

    .header-actions {
      flex-shrink: 0;
    }
  }
}

.stats-section {
  padding: $spacing-lg;

  .stats-card {
    .stats-title {
      font-size: 28rpx;
      font-weight: 600;
      color: $text-primary;
    }

    .tab-group {
      display: flex;
      background: $surface-container-high;
      border-radius: $radius-md;
      padding: 8rpx;
      margin: $spacing-md 0;

      .tab-item {
        flex: 1;
        padding: $spacing-sm;
        border-radius: $radius-sm;
        text-align: center;
        transition: $transition-normal;

        .tab-text {
          font-size: 24rpx;
          color: $text-secondary;
        }

        &.active {
          background: $surface-default;
          box-shadow: $shadow-sm;

          .tab-text {
            color: $brand-primary;
            font-weight: 500;
          }
        }

        &:active {
          transform: scale(0.95);
        }
      }
    }

    .chart-container {
      margin-top: $spacing-md;

      .trend-chart,
      .ranking-chart,
      .compare-chart {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 80rpx $spacing-lg;
        background: $surface-container-high;
        border-radius: $radius-md;

        .chart-placeholder {
          font-size: 48rpx;
          margin-bottom: $spacing-md;
        }

        .chart-desc {
          font-size: 24rpx;
          color: $text-secondary;
          text-align: center;
          line-height: 1.4;
        }
      }
    }
  }
}

.ranking-history-section {
  padding: 0 $spacing-lg;

  .ranking-card {
    .ranking-title {
      font-size: 28rpx;
      font-weight: 600;
      color: $text-primary;
    }

    .ranking-list {
      .ranking-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: $spacing-lg 0;

        border-bottom: 1px solid rgba($text-secondary, 0.1);

        &:last-child {
          border-bottom: none;
        }

        &:active {
          background: rgba($text-secondary, 0.05);
          margin: 0 (-$spacing-md);
          padding-left: $spacing-md;
          padding-right: $spacing-md;
          border-radius: $radius-sm;
        }

        .ranking-info {
          flex: 1;

          .ranking-header {
            display: flex;
            align-items: center;
            gap: $spacing-sm;
            margin-bottom: 8rpx;

            .ranking-index {
              width: 40rpx;
              height: 40rpx;
              background: $brand-primary;
              color: $surface-default;
              font-size: 20rpx;
              font-weight: 600;
              border-radius: $radius-full;
              display: flex;
              align-items: center;
              justify-content: center;
            }

            .ranking-name {
              font-size: 28rpx;
              font-weight: 500;
              color: $text-primary;
            }
          }

          .ranking-details {
            display: flex;
            align-items: center;
            gap: $spacing-md;

            .ranking-change {
              font-size: 22rpx;
              font-weight: 500;

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

            .ranking-period {
              font-size: 22rpx;
              color: $text-secondary;
            }
          }
        }

        .ranking-status {
          .status-badge {
            padding: 8rpx 16rpx;
            border-radius: $radius-full;
            background: rgba($text-secondary, 0.1);

            .status-text {
              font-size: 20rpx;
              color: $text-secondary;
            }

            &.active {
              background: rgba($brand-primary, 0.1);

              .status-text {
                color: $brand-primary;
              }
            }
          }
        }
      }
    }

    .empty-ranking {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 80rpx;

      .empty-text {
        font-size: 24rpx;
        color: $text-secondary;
      }
    }
  }
}
</style>