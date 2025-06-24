<template>
  <view class="follow-page">
    <!-- 页面头部 -->
    <view class="page-header">
      <text class="page-title">我的关注</text>
      <view class="header-stats">
        <text class="stats-text">榜单 {{ followData.length }}</text>
      </view>
    </view>
    
    <!-- 关注列表 -->
    <view class="content-section">
      <view class="follow-list" v-if="followData.length > 0">
        <view 
          class="follow-item" 
          v-for="item in followData" 
          :key="item.id"
          @tap="goToDetail(item)"
        >
          <view class="item-info">
            <text class="item-title">{{ item.name || item.title }}</text>
            <text class="item-desc">{{ item.description || item.author }}</text>
          </view>
          <view class="item-action">
            <view class="unfollow-btn" @tap.stop="unfollowItem(item)">
              <text class="action-text">取消关注</text>
            </view>
          </view>
        </view>
      </view>
      
      <view class="empty-state" v-else>
        <text class="empty-icon">💫</text>
        <text class="empty-title">还没有关注内容</text>
        <text class="empty-desc">去榜单页面关注感兴趣的内容吧</text>
        <view class="goto-btn" @tap="goToRanking">
          <text class="btn-text">去看看</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import dataManager from '@/utils/data-manager.js'

export default {
  name: 'FollowPage',
  
  data() {
    return {
      followData: []
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
      } catch (error) {
        console.error('加载关注数据失败:', error)
        // 备用方案：从本地存储获取
        try {
          const followList = uni.getStorageSync('followList') || []
          this.followData = followList
        } catch (localError) {
          console.error('本地关注数据也获取失败:', localError)
          this.followData = []
        }
      }
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
      uni.switchTab({
        url: '/pages/ranking/index'
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.follow-page {
  min-height: 100vh;
  background-color: #f4f0eb;
  padding-bottom: $safe-area-bottom;
}

.page-header {
  background-color: white;
  padding: $spacing-lg;
  border-bottom: 2rpx solid $border-light;
  
  .page-title {
    font-size: $font-size-xl;
    font-weight: bold;
    color: $text-primary;
    margin-bottom: $spacing-xs;
  }
  
  .header-stats {
    .stats-text {
      font-size: $font-size-sm;
      color: $text-secondary;
    }
  }
}

.content-section {
  padding: $spacing-lg;
}

.follow-list {
  .follow-item {
    @include flex-between;
    align-items: center;
    padding: $spacing-lg;
    background-color: #c3c3c3;
    border-radius: $border-radius-medium;
    margin-bottom: $spacing-md;
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
    
    &:active {
      opacity: 0.8;
    }
    
    .item-info {
      flex: 1;
      
      .item-title {
        display: block;
        font-size: $font-size-md;
        font-weight: bold;
        color: $text-primary;
        margin-bottom: 4rpx;
        @include text-ellipsis;
      }
      
      .item-desc {
        font-size: $font-size-sm;
        color: $text-secondary;
        @include text-ellipsis;
      }
    }
    
    .item-action {
      margin-left: $spacing-md;
      
      .unfollow-btn {
        padding: $spacing-xs $spacing-md;
        background-color: $background-color;
        border-radius: $border-radius-small;
        border: 2rpx solid $border-light;
        
        .action-text {
          font-size: $font-size-xs;
          color: $text-secondary;
        }
        
        &:active {
          background-color: #fee;
          border-color: #faa;
          
          .action-text {
            color: #f56565;
          }
        }
      }
    }
  }
}

.empty-state {
  @include flex-column-center;
  padding: $spacing-xl;
  text-align: center;
  
  .empty-icon {
    font-size: 120rpx;
    margin-bottom: $spacing-lg;
  }
  
  .empty-title {
    font-size: $font-size-lg;
    font-weight: bold;
    color: $text-primary;
    margin-bottom: $spacing-xs;
  }
  
  .empty-desc {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-bottom: $spacing-lg;
    line-height: 1.5;
  }
  
  .goto-btn {
    @include flex-center;
    padding: $spacing-md $spacing-xl;
    background-color: #64a347;
    color: white;
    border-radius: $border-radius-medium;
    
    .btn-text {
      font-size: $font-size-md;
      font-weight: bold;
    }
    
    &:active {
      opacity: 0.8;
    }
  }
}
</style>