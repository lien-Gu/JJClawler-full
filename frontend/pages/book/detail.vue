<template>
  <view class="book-detail-page">
    <!-- 书籍基本信息 -->
    <view class="book-header">
      <view class="header-bg"></view>
      <view class="header-content">
        <view class="book-cover-section">
          <view class="book-cover placeholder">
            <text class="cover-text">📖</text>
          </view>
        </view>
        
        <view class="book-info-section">
          <text class="book-title">{{ bookData.title || '书籍详情' }}</text>
          <text class="book-author" v-if="bookData.author">作者：{{ bookData.author }}</text>
          <view class="book-meta" v-if="bookData.category">
            <text class="meta-item">{{ bookData.category }}</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 当前统计数据 -->
    <view class="layer-section current-stats">
      <view class="layer-header">
        <text class="layer-title">📊 当前数据</text>
      </view>
      <view class="stats-grid">
        <view class="stat-card">
          <text class="stat-value">{{ formatNumber(bookData.collectCount || 0) }}</text>
          <text class="stat-label">收藏量</text>
        </view>
        <view class="stat-card">
          <text class="stat-value">{{ formatNumber(bookData.clickCount || 0) }}</text>
          <text class="stat-label">点击量</text>
        </view>
      </view>
    </view>
    
    <!-- 榜单信息 -->
    <view class="layer-section rankings-info">
      <view class="layer-header">
        <text class="layer-title">🏆 榜单排名</text>
      </view>
      
      <view class="rankings-list" v-if="bookData.rankings && bookData.rankings.length > 0">
        <view class="ranking-item" v-for="ranking in bookData.rankings" :key="ranking.id">
          <view class="ranking-main">
            <text class="ranking-name">{{ ranking.name }}</text>
            <text class="rank-text">第{{ ranking.currentRank }}名</text>
          </view>
        </view>
      </view>
      
      <view class="empty-state" v-else>
        <text class="empty-icon">📋</text>
        <text class="empty-text">暂无榜单记录</text>
      </view>
    </view>
  </view>
</template>

<script>
import dataManager from '@/utils/data-manager.js'

export default {
  name: 'BookDetailPage',
  
  data() {
    return {
      bookId: '',
      bookData: {
        title: '',
        author: '',
        category: '',
        collectCount: 0,
        clickCount: 0,
        rankings: []
      }
    }
  },
  
  onLoad(options) {
    if (options.id) {
      this.bookId = options.id
      this.loadData()
    }
  },
  
  methods: {
    async loadData() {
      try {
        const data = await dataManager.getBookDetail(this.bookId)
        if (data) {
          this.bookData = data
        }
      } catch (error) {
        console.error('数据加载失败:', error)
      }
    },
    
    formatNumber(num) {
      if (typeof num !== 'number') return num || '0'
      
      if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k'
      }
      
      return num.toString()
    }
  }
}
</script>

<style lang="scss" scoped>
.book-detail-page {
  min-height: 100vh;
  background-color: $page-background;
  padding-bottom: $safe-area-bottom;
}

.book-header {
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
    @include flex-center;
    align-items: flex-start;
    gap: $spacing-lg;
  }
  
  .book-cover-section {
    flex-shrink: 0;
    
    .book-cover {
      width: 160rpx;
      height: 220rpx;
      border-radius: $border-radius-medium;
      overflow: hidden;
      background-color: rgba(255, 255, 255, 0.1);
      @include flex-center;
      
      &.placeholder {
        .cover-text {
          font-size: 50rpx;
          opacity: 0.7;
        }
      }
    }
  }
  
  .book-info-section {
    flex: 1;
    
    .book-title {
      display: block;
      font-size: $font-size-xl;
      font-weight: bold;
      margin-bottom: $spacing-xs;
      line-height: 1.3;
    }
    
    .book-author {
      display: block;
      font-size: $font-size-sm;
      opacity: 0.9;
      margin-bottom: $spacing-xs;
    }
    
    .book-meta {
      @include flex-center;
      gap: $spacing-xs;
      
      .meta-item {
        font-size: $font-size-xs;
        opacity: 0.8;
      }
    }
  }
}

.layer-section {
  background-color: white;
  margin-bottom: $spacing-sm;
  padding: $spacing-lg;
  
  .layer-header {
    margin-bottom: $spacing-lg;
    
    .layer-title {
      font-size: $font-size-lg;
      font-weight: bold;
      color: $text-primary;
    }
  }
}

.current-stats {
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: $spacing-lg;
    
    .stat-card {
      @include flex-column-center;
      padding: $spacing-lg;
      background: linear-gradient(135deg, #f8f9ff, #e8f0ff);
      border-radius: $border-radius-large;
      border: 2rpx solid $border-light;
      
      .stat-value {
        font-size: $font-size-xxl;
        font-weight: bold;
        color: $primary-color;
        margin-bottom: $spacing-xs;
      }
      
      .stat-label {
        font-size: $font-size-sm;
        color: $text-secondary;
        text-align: center;
      }
    }
  }
}

.rankings-info {
  .rankings-list {
    .ranking-item {
      padding: $spacing-lg;
      border: 2rpx solid $border-light;
      border-radius: $border-radius-medium;
      margin-bottom: $spacing-md;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .ranking-main {
        @include flex-between;
        align-items: center;
        
        .ranking-name {
          font-size: $font-size-md;
          font-weight: bold;
          color: $text-primary;
        }
        
        .rank-text {
          font-size: $font-size-md;
          color: $primary-color;
          font-weight: bold;
        }
      }
    }
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
  }
}
</style>