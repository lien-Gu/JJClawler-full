<template>
  <view class="ranking-detail-page">
    <!-- 榜单头部信息 -->
    <view class="ranking-header">
      <BaseCard class="header-card">
        <view class="ranking-info">
          <text class="ranking-name">{{ rankingData.name || '榜单详情' }}</text>
          <text class="ranking-level">{{ rankingData.level + rankingData.description || '未知' }}</text>
        </view>

        <!-- 展开/收起按钮 -->
        <view class="expand-section">
          <BaseButton
              type="text"
              :icon="isStatsExpanded ? '▲' : '▼'"
              :text="isStatsExpanded ? '收起' : '展开统计'"
              size="small"
              @click="toggleStats"
          />
        </view>
      </BaseCard>

      <!-- 统计信息区域 -->
      <BaseCard v-if="isStatsExpanded" class="stats-card">
        <view class="stats-content">
          <view class="tab-group">
            <view
                class="tab-item"
                :class="{ 'active': currentStatsTab === tab.key }"
                v-for="tab in statsTabs"
                :key="tab.key"
                @tap="switchStatsTab(tab.key)"
            >
              <text class="tab-text">{{ tab.label }}</text>
            </view>
          </view>

          <!-- 统计图表展示 -->
          <view class="chart-container">
            <view v-if="currentStatsTab === 'trend'" class="trend-chart">
              <text class="chart-placeholder">📈 榜单趋势</text>
              <view class="stats-grid">
                <view class="stat-item">
                  <text class="stat-label">周增长率</text>
                  <text class="stat-value"
                        :class="{ 'positive': parseFloat(rankingData.statistics?.weekly_growth || 0) > 0, 'negative': parseFloat(rankingData.statistics?.weekly_growth || 0) < 0 }">
                    {{ rankingData.statistics?.weekly_growth || 0 }}%
                  </text>
                </view>
                <view class="stat-item">
                  <text class="stat-label">月增长率</text>
                  <text class="stat-value"
                        :class="{ 'positive': parseFloat(rankingData.statistics?.monthly_growth || 0) > 0, 'negative': parseFloat(rankingData.statistics?.monthly_growth || 0) < 0 }">
                    {{ rankingData.statistics?.monthly_growth || 0 }}%
                  </text>
                </view>
              </view>
            </view>

            <view v-if="currentStatsTab === 'analysis'" class="analysis-chart">
              <text class="chart-placeholder">📊 数据分析</text>
              <view class="stats-grid">
                <view class="stat-item">
                  <text class="stat-label">总浏览量</text>
                  <text class="stat-value">{{ formatNumber(rankingData.statistics?.total_views || 0) }}</text>
                </view>
                <view class="stat-item">
                  <text class="stat-label">书籍总数</text>
                  <text class="stat-value">{{ formatNumber(rankingData.total_books || 0) }}</text>
                </view>
              </view>
            </view>

            <view v-if="currentStatsTab === 'history'" class="history-chart">
              <text class="chart-placeholder">📋 历史记录</text>
              <view class="history-info">
                <text class="chart-desc">最后更新: {{ formatTime(rankingData.last_updated) }}</text>
                <text class="chart-desc">榜单等级: {{ rankingData.level }}</text>
                <text class="chart-desc" v-if="rankingData.description">{{ rankingData.description }}</text>
              </view>
            </view>
          </view>
        </view>
      </BaseCard>
    </view>

    <!-- 书籍列表 -->
    <view class="books-section">
      <BaseCard class="books-card">
        <template #header>
          <view class="books-header">
            <text class="books-title">榜单书籍</text>
          </view>
        </template>

        <BooksList
            :ranking-id="rankingId"
            :height="'1000rpx'"
            empty-text="暂无书籍数据"
            :page-size="20"
        />
      </BaseCard>
    </view>
  </view>
</template>

<script>
import BaseCard from '@/components/BaseCard.vue'
import BaseButton from '@/components/BaseButton.vue'
import BooksList from '@/components/BooksList.vue'
import requestManager from '@/api/request.js'
import { formatNumber, formatTime } from '@/utils/format.js'
import navigation from '@/utils/navigation.js'

export default {
  name: 'RankingDetailPage',
  components: {
    BaseCard,
    BaseButton,
    BooksList
  },
  data() {
    return {
      rankingId: '',
      rankingData: {},
      isStatsExpanded: false,
      currentStatsTab: 'trend',
      statsTabs: [
        {key: 'trend', label: '趋势'},
        {key: 'analysis', label: '分析'},
        {key: 'history', label: '历史'}
      ]
    }
  },

  onLoad(options) {
    if (options.id) {
      this.rankingId = options.id
      this.rankingName = decodeURIComponent(options.name)
      this.loadData()
    }
  },

  methods: {
    ...navigation,

    formatNumber(num) {
      return formatNumber(num)
    },

    formatTime(timeStr) {
      return formatTime(timeStr)
    },

    async loadData() {
      await this.loadRankingData()
    },

    async loadRankingData() {
      try {
        console.log(`开始加载排行榜数据，id: ${this.rankingId},name:${this.rankingName}`)
        uni.setNavigationBarTitle({
          title: this.rankingName || '榜单详情'
        })
        const response = await requestManager.getRankingReport(this.rankingId)

        if (response && response.success && response.data) {
          let report = response.data
          this.rankingData = {
            id: this.rankingId,
            name: this.rankingName,
            level: report.report_title || 'Level 1',
            description: report.report_content || '',
            total_books: report.total_books || 0,
            last_updated: report.last_updated,
            statistics: report.statistics || {}
          }

          console.log('排行榜数据加载成功:', this.rankingData)
        } else {
          console.warn('排行榜数据响应格式不正确')
          uni.showToast({
            title: '数据加载异常',
            icon: 'none'
          })
        }
      } catch (error) {
        console.error('加载榜单数据失败:', error)
        uni.showToast({
          title: '加载失败',
          icon: 'none'
        })
      }
    },


    toggleStats() {
      this.isStatsExpanded = !this.isStatsExpanded
    },

    switchStatsTab(tabKey) {
      this.currentStatsTab = tabKey
    }

  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.ranking-detail-page {
  min-height: 100vh;
  background: $surface-white;
  padding-bottom: 40rpx;
}

.ranking-header {
  padding: $spacing-lg;

  .header-card {
    margin-bottom: $spacing-md;

    .ranking-info {
      padding: $spacing-sm 0;

      .ranking-name {
        display: block;
        font-size: 32rpx;
        font-weight: 600;
        color: $text-primary;
        margin-bottom: 8rpx;
      }

      .ranking-level {
        font-size: 24rpx;
        color: $text-secondary;
      }
    }

    .expand-section {
      margin-top: $spacing-md;
      display: flex;
      justify-content: center;
    }
  }

  .stats-card {
    .stats-content {
      .tab-group {
        display: flex;
        background: $surface-container-high;
        border-radius: $radius-md;
        padding: 8rpx;
        margin-bottom: $spacing-md;

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
        .trend-chart,
        .analysis-chart,
        .history-chart {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40rpx $spacing-lg;
          background: $surface-container-high;
          border-radius: $radius-md;

          .chart-placeholder {
            font-size: 32rpx;
            margin-bottom: $spacing-lg;
            font-weight: 500;
          }

          .chart-desc {
            font-size: 24rpx;
            color: $text-secondary;
            text-align: center;
            line-height: 1.4;
            margin-bottom: 8rpx;
          }

          .stats-grid {
            display: flex;
            gap: 40rpx;
            width: 100%;
            justify-content: center;

            .stat-item {
              display: flex;
              flex-direction: column;
              align-items: center;
              text-align: center;

              .stat-label {
                font-size: 22rpx;
                color: $text-secondary;
                margin-bottom: 8rpx;
              }

              .stat-value {
                font-size: 28rpx;
                font-weight: 600;
                color: $text-primary;

                &.positive {
                  color: #22c55e;
                }

                &.negative {
                  color: #ef4444;
                }
              }
            }
          }

          .history-info {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12rpx;

            .chart-desc {
              margin-bottom: 0;
            }
          }
        }
      }
    }
  }
}

.books-section {
  padding: 0 $spacing-lg;

  .books-card {
    .books-header {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .books-title {
        font-size: 28rpx;
        font-weight: 600;
        color: $text-primary;
      }
    }
  }
}
</style>