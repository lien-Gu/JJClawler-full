<template>
  <view class="ranking-detail-page">
    <!-- 榜单头部信息 -->
    <view class="ranking-header">
      <BaseCard class="header-card">
        <view class="ranking-info">
          <text class="ranking-name">{{ rankingData.name || '榜单详情' }}</text>
          <text class="ranking-level">{{ rankingData.level || '未知层级' }}</text>
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
              <text class="chart-desc">显示{{ rankingData.name }}的变化趋势</text>
            </view>
            
            <view v-if="currentStatsTab === 'analysis'" class="analysis-chart">
              <text class="chart-placeholder">📊 数据分析</text>
              <text class="chart-desc">榜单的详细数据分析</text>
            </view>
            
            <view v-if="currentStatsTab === 'history'" class="history-chart">
              <text class="chart-placeholder">📋 历史记录</text>
              <text class="chart-desc">榜单的历史变化记录</text>
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
            <text class="books-count">共{{ booksList.length }}本</text>
          </view>
        </template>
        
        <scroll-view 
          class="books-container"
          scroll-y
          :refresher-enabled="true"
          :refresher-triggered="refreshing"
          @refresherrefresh="onRefresh"
          @scrolltolower="onLoadMore"
        >
          <view class="books-list">
            <view 
              class="book-item"
              v-for="(book, index) in booksList"
              :key="book.id"
              @tap="goToBookDetail(book)"
            >
              <view class="book-rank">
                <text class="rank-number">{{ index + 1 }}</text>
              </view>
              
              <view class="book-info">
                <text class="book-title">{{ book.title }}</text>
                <text class="book-author" v-if="book.author">{{ book.author }}</text>
                <view class="book-stats">
                  <text class="stat-item" v-if="book.collectCount">
                    收藏: {{ formatNumber(book.collectCount) }}
                  </text>
                  <text class="stat-item" v-if="book.clickCount">
                    点击: {{ formatNumber(book.clickCount) }}
                  </text>
                </view>
              </view>
              
              <view class="book-actions">
                <BaseButton
                  :type="book.isFollowed ? 'secondary' : 'text'"
                  :icon="book.isFollowed ? '★' : '☆'"
                  size="small"
                  round
                  @click="toggleBookFollow(book, $event)"
                />
              </view>
            </view>
          </view>
          
          <!-- 加载更多提示 -->
          <view v-if="loading" class="loading-more">
            <text class="loading-text">加载中...</text>
          </view>
          
          <!-- 没有更多数据提示 -->
          <view v-if="!hasMore && booksList.length > 0" class="no-more">
            <text class="no-more-text">没有更多书籍了</text>
          </view>
          
          <!-- 空状态 -->
          <view v-if="booksList.length === 0 && !loading" class="empty-state">
            <text class="empty-text">暂无书籍数据</text>
          </view>
        </scroll-view>
      </BaseCard>
    </view>
  </view>
</template>

<script>
import BaseCard from '@/components/BaseCard.vue'
import BaseButton from '@/components/BaseButton.vue'
import dataManager from '@/utils/data-manager.js'
import formatterMixin from '@/mixins/formatter.js'
import navigationMixin from '@/mixins/navigation.js'

export default {
  name: 'RankingDetailPage',
  components: {
    BaseCard,
    BaseButton
  },
  mixins: [formatterMixin, navigationMixin],
  
  data() {
    return {
      rankingId: '',
      rankingData: {},
      booksList: [],
      isStatsExpanded: false,
      currentStatsTab: 'trend',
      statsTabs: [
        { key: 'trend', label: '趋势' },
        { key: 'analysis', label: '分析' },
        { key: 'history', label: '历史' }
      ],
      refreshing: false,
      loading: false,
      hasMore: true,
      page: 1,
      pageSize: 20
    }
  },
  
  onLoad(options) {
    if (options.id) {
      this.rankingId = options.id
      this.loadData()
    }
  },
  
  methods: {
    async loadData() {
      await Promise.all([
        this.loadRankingData(),
        this.loadBooksList(true)
      ])
    },
    
    async loadRankingData() {
      try {
        const data = await dataManager.getRankingDetail(this.rankingId)
        if (data) {
          this.rankingData = data
          uni.setNavigationBarTitle({
            title: this.rankingData.name || '榜单详情'
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
    
    async loadBooksList(reset = false) {
      if (this.loading) return
      
      this.loading = true
      try {
        if (reset) {
          this.page = 1
          this.booksList = []
          this.hasMore = true
        }
        
        const params = {
          page: this.page,
          limit: this.pageSize
        }
        
        const data = await dataManager.getRankingBooks(this.rankingId, params)
        if (data && Array.isArray(data.books)) {
          if (reset) {
            this.booksList = data.books
          } else {
            this.booksList.push(...data.books)
          }
          
          // 检查是否还有更多数据
          this.hasMore = data.books.length === this.pageSize
          this.page++
          
          // 检查关注状态
          this.checkBooksFollowStatus()
        } else {
          this.hasMore = false
        }
      } catch (error) {
        console.error('加载书籍列表失败:', error)
        if (reset) {
          uni.showToast({
            title: '加载失败',
            icon: 'none'
          })
        }
      } finally {
        this.loading = false
      }
    },
    
    checkBooksFollowStatus() {
      try {
        const followList = uni.getStorageSync('followList') || []
        this.booksList.forEach(book => {
          book.isFollowed = followList.some(item => item.id === book.id)
        })
      } catch (error) {
        console.error('检查关注状态失败:', error)
      }
    },
    
    toggleStats() {
      this.isStatsExpanded = !this.isStatsExpanded
    },
    
    switchStatsTab(tabKey) {
      this.currentStatsTab = tabKey
    },
    
    async onRefresh() {
      this.refreshing = true
      await this.loadData()
      this.refreshing = false
    },
    
    async onLoadMore() {
      if (this.hasMore && !this.loading) {
        await this.loadBooksList()
      }
    },
    
    goToBookDetail(book) {
      this.navigateTo('/pages/book/detail', {
        id: book.id
      })
    },
    
    async toggleBookFollow(book, event) {
      // 阻止事件冒泡
      event.stopPropagation()
      
      try {
        const isCurrentlyFollowed = book.isFollowed
        
        if (isCurrentlyFollowed) {
          this.removeBookFromFollow(book)
        } else {
          this.addBookToFollow(book)
        }
        
        book.isFollowed = !isCurrentlyFollowed
      } catch (error) {
        console.error('关注操作失败:', error)
        uni.showToast({
          title: '操作失败',
          icon: 'none'
        })
      }
    },
    
    addBookToFollow(book) {
      try {
        const followList = uni.getStorageSync('followList') || []
        const followItem = {
          id: book.id,
          type: 'book',
          name: book.title,
          author: book.author,
          category: book.category,
          isOnList: true, // 从榜单页关注的书籍都在榜上
          weeklyGrowth: book.weeklyGrowth || 0,
          followDate: new Date().toISOString()
        }
        
        const existingIndex = followList.findIndex(item => item.id === book.id)
        if (existingIndex === -1) {
          followList.push(followItem)
          uni.setStorageSync('followList', followList)
          
          uni.showToast({
            title: '已关注',
            icon: 'success',
            duration: 1000
          })
        }
      } catch (error) {
        console.error('添加关注失败:', error)
      }
    },
    
    removeBookFromFollow(book) {
      try {
        const followList = uni.getStorageSync('followList') || []
        const newList = followList.filter(item => item.id !== book.id)
        uni.setStorageSync('followList', newList)
        
        uni.showToast({
          title: '已取消关注',
          icon: 'success',
          duration: 1000
        })
      } catch (error) {
        console.error('取消关注失败:', error)
      }
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
      
      .books-count {
        font-size: 22rpx;
        color: $text-secondary;
      }
    }
    
    .books-container {
      max-height: 1000rpx;
      
      .books-list {
        .book-item {
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
          
          .book-rank {
            width: 48rpx;
            height: 48rpx;
            background: $brand-primary;
            border-radius: $radius-full;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: $spacing-md;
            flex-shrink: 0;
            
            .rank-number {
              font-size: 20rpx;
              font-weight: 600;
              color: $surface-default;
            }
          }
          
          .book-info {
            flex: 1;
            min-width: 0;
            
            .book-title {
              display: block;
              font-size: 28rpx;
              font-weight: 500;
              color: $text-primary;
              margin-bottom: 8rpx;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }
            
            .book-author {
              display: block;
              font-size: 22rpx;
              color: $text-secondary;
              margin-bottom: 8rpx;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }
            
            .book-stats {
              display: flex;
              gap: $spacing-md;
              
              .stat-item {
                font-size: 20rpx;
                color: rgba($text-secondary, 0.8);
              }
            }
          }
          
          .book-actions {
            margin-left: $spacing-sm;
            flex-shrink: 0;
          }
        }
      }
      
      .loading-more,
      .no-more {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: $spacing-lg;
        
        .loading-text,
        .no-more-text {
          font-size: 24rpx;
          color: $text-secondary;
        }
      }
      
      .empty-state {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 120rpx;
        
        .empty-text {
          font-size: 24rpx;
          color: $text-secondary;
        }
      }
    }
  }
}
</style>