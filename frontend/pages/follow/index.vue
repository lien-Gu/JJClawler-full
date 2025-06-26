<template>
  <view class="follow-page">
    <!-- 统计信息卡片 -->
    <view class="stats-section">
      <BaseCard variant="filled" class="stats-card">
        <view class="stats-content">
          <view class="stat-item">
            <text class="stat-number">{{ followStats.totalBooks }}</text>
            <text class="stat-label">关注书籍</text>
          </view>
          <view class="stat-divider"></view>
          <view class="stat-item">
            <text class="stat-number">{{ followStats.onListBooks }}</text>
            <text class="stat-label">正在上榜</text>
          </view>
        </view>
      </BaseCard>
    </view>
    
    <!-- 关注书籍列表 -->
    <ScrollableList
      :items="followData"
      :loading="false"
      :refreshing="refreshing"
      :has-more="false"
      :refresher-enabled="true"
      empty-icon="📚"
      empty-title="还没有关注的书籍"
      empty-description="在榜单中发现感兴趣的书籍并关注它们"
      @refresh="onRefresh"
    >
      <view class="books-list">
        <swiper-item
          v-for="item in followData" 
          :key="item.id"
          class="book-swiper-item"
        >
          <view class="book-item" @tap="goToDetail(item)">
            <view class="book-main-content">
              <text class="book-title">{{ item.name || item.title }}</text>
              <text class="book-growth" :class="getGrowthClass(item.weeklyGrowth)">
                本周 {{ formatGrowth(item.weeklyGrowth) }}
              </text>
            </view>
            <view class="book-status" :class="{ 'on-list': item.isOnList }">
              <view class="status-indicator">
                <text class="status-text">{{ item.isOnList ? '榜上' : '榜外' }}</text>
              </view>
            </view>
          </view>
          
          <!-- 滑动操作区域 -->
          <view class="swipe-actions">
            <view class="action-btn unfollow-btn" @tap="unfollowItem(item)">
              <text class="action-text">取消关注</text>
            </view>
          </view>
        </swiper-item>
      </view>
      
      <template #empty-action>
        <BaseButton 
          type="primary"
          text="去发现书籍"
          @click="goToRanking"
        />
      </template>
    </ScrollableList>
    
  </view>
</template>

<script>
import BaseCard from '@/components/BaseCard.vue'
import BaseButton from '@/components/BaseButton.vue'
import ScrollableList from '@/components/ScrollableList.vue'
import dataManager from '@/utils/data-manager.js'
import formatterMixin from '@/mixins/formatter.js'
import navigationMixin from '@/mixins/navigation.js'

export default {
  name: 'FollowPage',
  components: {
    BaseCard,
    BaseButton,
    ScrollableList
  },
  mixins: [formatterMixin, navigationMixin],
  
  data() {
    return {
      followData: [],
      refreshing: false,
      followStats: {
        totalBooks: 0,
        onListBooks: 0
      }
    }
  },
  
  onLoad() {
    this.loadFollowData()
  },
  
  onShow() {
    this.loadFollowData()
  },
  
  methods: {
    async loadFollowData() {
      try {
        // 优先从dataManager获取用户关注数据
        const userFollows = await dataManager.getUserFollows()
        if (userFollows && Array.isArray(userFollows)) {
          this.followData = userFollows
        } else {
          // 如果没有或失败，从本地存储获取关注数据
          const followList = uni.getStorageSync('followList') || []
          this.followData = followList
        }
        
        // 更新统计信息
        this.updateStats()
      } catch (error) {
        console.error('加载关注数据失败:', error)
        // 备用方案：从本地存储获取
        try {
          const followList = uni.getStorageSync('followList') || []
          this.followData = followList
          this.updateStats()
        } catch (localError) {
          console.error('本地关注数据也获取失败:', localError)
          this.followData = []
          this.updateStats()
        }
      }
    },
    
    updateStats() {
      this.followStats.totalBooks = this.followData.length
      this.followStats.onListBooks = this.followData.filter(item => item.isOnList).length
    },
    
    async onRefresh() {
      this.refreshing = true
      await this.loadFollowData()
      this.refreshing = false
    },
    
    formatGrowth(growth) {
      if (!growth && growth !== 0) return '无数据'
      if (growth > 0) {
        return `+${growth}%`
      } else if (growth < 0) {
        return `${growth}%`
      } else {
        return '0%'
      }
    },
    
    getGrowthClass(growth) {
      if (!growth && growth !== 0) return 'neutral'
      if (growth > 0) return 'positive'
      if (growth < 0) return 'negative'
      return 'neutral'
    },
    
    unfollowItem(item) {
      uni.showModal({
        title: '确认取消关注',
        content: `确定要取消关注"${item.name || item.title}"吗？`,
        success: (res) => {
          if (res.confirm) {
            this.removeFromFollow(item)
          }
        }
      })
    },
    
    removeFromFollow(item) {
      try {
        const followList = uni.getStorageSync('followList') || []
        const newList = followList.filter(follow => follow.id !== item.id)
        uni.setStorageSync('followList', newList)
        this.followData = newList
        this.updateStats()
        
        uni.showToast({
          title: '已取消关注',
          icon: 'success',
          duration: 1500
        })
      } catch (error) {
        console.error('取消关注失败:', error)
        uni.showToast({
          title: '操作失败',
          icon: 'none',
          duration: 2000
        })
      }
    },
    
    goToDetail(item) {
      if (item.type === 'ranking') {
        uni.navigateTo({
          url: `/pages/ranking/detail?id=${item.id}`
        })
      } else if (item.type === 'book') {
        uni.navigateTo({
          url: `/pages/book/detail?id=${item.id}`
        })
      }
    },
    
    goToRanking() {
      this.switchMainTab('ranking')
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.follow-page {
  min-height: 100vh;
  background: $surface-white;
  padding-bottom: env(safe-area-inset-bottom);
}

.stats-section {
  padding: $spacing-lg;
  
  .stats-card {
    .stats-content {
      display: flex;
      align-items: center;
      justify-content: space-around;
      padding: $spacing-md 0;
      
      .stat-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        
        .stat-number {
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
      
      .stat-divider {
        width: 1px;
        height: 60rpx;
        background: rgba($text-secondary, 0.2);
      }
    }
  }
}

.books-list {
  .book-swiper-item {
    margin-bottom: $spacing-sm;
    
    .book-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: $spacing-lg;
      background: $surface-container-high;
      border-radius: $radius-md;
      transition: $transition-normal;
      
      &:active {
        transform: scale(0.98);
        opacity: 0.8;
      }
      
      .book-main-content {
        flex: 1;
        min-width: 0;
        
        .book-title {
          display: block;
          font-size: 32rpx;
          font-weight: 500;
          color: $text-primary;
          margin-bottom: 8rpx;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        
        .book-growth {
          font-size: 24rpx;
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
      }
      
      .book-status {
        margin-left: $spacing-md;
        
        .status-indicator {
          padding: 8rpx 16rpx;
          border-radius: $radius-full;
          background: rgba($text-secondary, 0.1);
          
          .status-text {
            font-size: 20rpx;
            color: $text-secondary;
          }
        }
        
        &.on-list {
          .status-indicator {
            background: rgba($brand-primary, 0.1);
            
            .status-text {
              color: $brand-primary;
            }
          }
        }
      }
    }
    
    .swipe-actions {
      display: flex;
      align-items: center;
      height: 100%;
      
      .action-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 120rpx;
        height: 100%;
        
        &.unfollow-btn {
          background: #ff3b30;
          
          .action-text {
            font-size: 24rpx;
            color: $surface-default;
          }
        }
        
        &:active {
          opacity: 0.8;
        }
      }
    }
  }
}

</style>