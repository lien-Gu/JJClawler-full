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
    
    <!-- 未登录提示 -->
    <view v-if="!isLoggedIn" class="login-prompt">
      <BaseCard class="login-card">
        <view class="prompt-content">
          <view class="prompt-icon">🔒</view>
          <text class="prompt-title">请先登录</text>
          <text class="prompt-desc">登录后可以查看和管理您的关注列表</text>
          <BaseButton 
            type="primary"
            text="立即登录"
            @click="showLogin"
          />
        </view>
      </BaseCard>
    </view>

    <!-- 关注书籍列表 -->
    <ScrollableList
      v-if="isLoggedIn"
      :items="followData"
      :loading="false"
      :refreshing="refreshing"
      :has-more="false"
      :show-no-more="false"
      :refresher-enabled="true"
      empty-icon="📚"
      empty-title="还没有关注的书籍"
      empty-description="在榜单中发现感兴趣的书籍并关注它们"
      @refresh="onRefresh"
    >
      <view class="books-list">
        <view
          v-for="item in followData" 
          :key="item.id"
          class="book-item-wrapper"
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
            <view class="book-actions">
              <BaseButton
                type="text"
                icon="✖"
                size="small"
                @click="unfollowItem(item, $event)"
              />
            </view>
          </view>
        </view>
      </view>
      
      <template #empty-action>
        <BaseButton 
          type="primary"
          text="去发现书籍"
          @click="goToRanking"
        />
      </template>
    </ScrollableList>
    
    <!-- 登录弹窗 -->
    <LoginModal 
      :visible="showLoginModal"
      @close="hideLogin"
      @login-success="onLoginSuccess"
    />
    
  </view>
</template>

<script>
import BaseCard from '@/components/BaseCard.vue'
import BaseButton from '@/components/BaseButton.vue'
import ScrollableList from '@/components/ScrollableList.vue'
import LoginModal from '@/components/LoginModal.vue'
import userStore from '@/store/userStore.js'
import requestManager from '@/api/request.js'
import { formatNumber, formatTime } from '@/utils/format.js'
import navigation from '@/utils/navigation.js'

export default {
  name: 'FollowPage',
  components: {
    BaseCard,
    BaseButton,
    ScrollableList,
    LoginModal
  },
  data() {
    return {
      refreshing: false,
      showLoginModal: false
    }
  },

  computed: {
    isLoggedIn() {
      return userStore.state.isLoggedIn
    },
    
    followData() {
      return userStore.state.followList
    },
    
    followStats() {
      return userStore.followStats
    }
  },
  
  onLoad() {
    this.loadFollowData()
  },
  
  onShow() {
    this.loadFollowData()
  },
  
  methods: {
    ...navigation,
    formatNumber,
    formatTime,
    
    loadFollowData() {
      if (!this.isLoggedIn) {
        console.log('用户未登录，跳过加载关注数据')
        return
      }
      
      try {
        // 刷新用户状态管理中的关注列表
        userStore.refreshFollowList()
        console.log('关注数据加载成功')
      } catch (error) {
        console.error('加载关注数据失败:', error)
        uni.showToast({
          title: '加载失败',
          icon: 'none'
        })
      }
    },
    
    onRefresh() {
      this.refreshing = true
      this.loadFollowData()
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
    
    unfollowItem(item, event) {
      // 阻止事件冒泡
      if (event) {
        event.stopPropagation()
      }
      
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
        userStore.removeFollow(item.id, item.type)
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
    },

    // 显示登录弹窗
    showLogin() {
      this.showLoginModal = true
    },

    // 隐藏登录弹窗
    hideLogin() {
      this.showLoginModal = false
    },

    // 登录成功回调
    onLoginSuccess(userInfo) {
      console.log('登录成功，用户状态已自动更新')
      // userStore会自动更新状态，不需要手动处理
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

.login-prompt {
  padding: $spacing-lg;
  
  .login-card {
    .prompt-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: $spacing-xl $spacing-lg;
      
      .prompt-icon {
        font-size: 80rpx;
        margin-bottom: $spacing-lg;
        opacity: 0.8;
      }
      
      .prompt-title {
        font-size: 32rpx;
        font-weight: 600;
        color: $text-primary;
        margin-bottom: $spacing-md;
      }
      
      .prompt-desc {
        font-size: 26rpx;
        color: $text-secondary;
        text-align: center;
        line-height: 1.4;
        margin-bottom: $spacing-xl;
      }
    }
  }
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
  .book-item-wrapper {
    margin-bottom: $spacing-md;
    
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
      
      .book-actions {
        margin-left: $spacing-sm;
        flex-shrink: 0;
      }
    }
  }
}

</style>