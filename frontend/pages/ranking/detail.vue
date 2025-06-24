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
            <text class="meta-item">{{ formatTime(rankingData.updateTime) }}</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 书籍列表 -->
    <view class="books-section">
      <view class="section-header">
        <text class="section-title">📚 榜单书籍</text>
        <text class="book-count">共{{ bookList.length }}本</text>
      </view>
      
      <view class="book-list" v-if="bookList.length > 0">
        <view 
          class="book-item" 
          v-for="(book, index) in bookList" 
          :key="book.id"
          @tap="goToBookDetail(book)"
        >
          <view class="book-rank">{{ index + 1 }}</view>
          <view class="book-info">
            <text class="book-title">{{ book.title }}</text>
            <text class="book-author">{{ book.author }}</text>
            <view class="book-stats">
              <text class="stat-item">收藏: {{ formatNumber(book.collectCount) }}</text>
            </view>
          </view>
        </view>
      </view>
      
      <view class="empty-state" v-else>
        <text class="empty-icon">📖</text>
        <text class="empty-text">暂无书籍数据</text>
      </view>
    </view>
  </view>
</template>

<script>
import dataManager from '@/utils/data-manager.js'

export default {
  name: 'RankingDetailPage',
  
  data() {
    return {
      rankingId: '',
      rankingData: {
        name: '',
        description: '',
        updateTime: ''
      },
      bookList: []
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
      try {
        // 加载榜单基本信息和书籍列表
        const [rankingInfo, books] = await Promise.all([
          dataManager.getRankingDetail(this.rankingId),
          dataManager.getRankingBooks(this.rankingId)
        ])
        
        if (rankingInfo) {
          this.rankingData = rankingInfo
        }
        
        if (books && Array.isArray(books)) {
          this.bookList = books
        }
      } catch (error) {
        console.error('数据加载失败:', error)
      }
    },
    
    goToBookDetail(book) {
      uni.navigateTo({
        url: `/pages/book/detail?id=${book.id}`
      })
    },
    
    formatNumber(num) {
      if (typeof num !== 'number') return num || '0'
      
      if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k'
      }
      
      return num.toString()
    },
    
    formatTime(time) {
      if (!time) return '未知时间'
      
      const now = new Date()
      const updateTime = new Date(time)
      const diff = now - updateTime
      
      const hours = Math.floor(diff / (1000 * 60 * 60))
      
      if (hours < 24) {
        return `${hours}小时前更新`
      } else {
        return updateTime.toLocaleDateString() + '更新'
      }
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
        margin-bottom: $spacing-xs;
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

.books-section {
  background-color: white;
  margin-top: $spacing-md;
  padding: $spacing-lg;
  
  .section-header {
    @include flex-between;
    align-items: center;
    margin-bottom: $spacing-lg;
    
    .section-title {
      font-size: $font-size-lg;
      font-weight: bold;
      color: $text-primary;
    }
    
    .book-count {
      font-size: $font-size-sm;
      color: $text-secondary;
    }
  }
  
  .book-list {
    .book-item {
      @include flex-center;
      gap: $spacing-md;
      padding: $spacing-lg;
      border: 2rpx solid $border-light;
      border-radius: $border-radius-medium;
      margin-bottom: $spacing-md;
      background-color: white;
      transition: all 0.3s ease;
      
      &:active {
        background-color: $background-color;
        transform: scale(0.98);
      }
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .book-rank {
        width: 60rpx;
        height: 60rpx;
        @include flex-center;
        background-color: $primary-color;
        color: white;
        border-radius: 50%;
        font-size: $font-size-sm;
        font-weight: bold;
        flex-shrink: 0;
      }
      
      .book-info {
        flex: 1;
        
        .book-title {
          display: block;
          font-size: $font-size-md;
          font-weight: bold;
          color: $text-primary;
          margin-bottom: 4rpx;
          @include text-ellipsis;
        }
        
        .book-author {
          display: block;
          font-size: $font-size-sm;
          color: $text-secondary;
          margin-bottom: $spacing-xs;
          @include text-ellipsis;
        }
        
        .book-stats {
          .stat-item {
            font-size: $font-size-xs;
            color: $text-placeholder;
          }
        }
      }
    }
  }
}

.empty-state {
  @include flex-column-center;
  padding: $spacing-xl;
  
  .empty-icon {
    font-size: 120rpx;
    margin-bottom: $spacing-md;
  }
  
  .empty-text {
    color: $text-placeholder;
    font-size: $font-size-md;
  }
}
</style>