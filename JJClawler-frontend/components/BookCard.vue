<template>
  <view class="book-card" :class="{ 'clickable': clickable }" @tap="onClick">
    <view class="book-header">
      <view class="book-cover" v-if="book.cover">
        <image :src="book.cover" mode="aspectFit" class="cover-image" />
      </view>
      <view class="book-cover placeholder" v-else>
        <text class="cover-text">📖</text>
      </view>
      
      <view class="book-info">
        <text class="book-title">{{ book.name || book.title }}</text>
        <text class="book-author" v-if="book.author">{{ book.author }}</text>
        <text class="book-category" v-if="book.category">{{ book.category }}</text>
        
        <view class="book-tags" v-if="book.tags && book.tags.length">
          <text 
            class="tag" 
            v-for="tag in book.tags.slice(0, 3)" 
            :key="tag"
          >
            {{ tag }}
          </text>
        </view>
      </view>
      
      <view class="book-rank" v-if="book.rank">
        <text class="rank-number">{{ book.rank }}</text>
        <text class="rank-label">名</text>
      </view>
    </view>
    
    <view class="book-description" v-if="book.description && showDescription">
      <text class="desc-text">{{ book.description }}</text>
    </view>
    
    <view class="book-stats">
      <view class="stat-item" v-if="book.wordCount">
        <text class="stat-label">字数</text>
        <text class="stat-value">{{ formatWordCount(book.wordCount) }}</text>
      </view>
      <view class="stat-item" v-if="book.updateTime">
        <text class="stat-label">更新</text>
        <text class="stat-value">{{ formatTime(book.updateTime) }}</text>
      </view>
      <view class="stat-item" v-if="book.status">
        <text class="stat-label">状态</text>
        <text class="stat-value" :class="statusClass">{{ book.status }}</text>
      </view>
      <view class="stat-item" v-if="book.score">
        <text class="stat-label">评分</text>
        <text class="stat-value score">{{ book.score }}</text>
      </view>
    </view>
    
    <view class="book-rankings" v-if="showRankings && book.rankings && book.rankings.length">
      <text class="rankings-label">榜单历史：</text>
      <view class="rankings-list">
        <text 
          class="ranking-item" 
          v-for="ranking in book.rankings.slice(0, 2)" 
          :key="ranking.id"
        >
          {{ ranking.name }}
        </text>
      </view>
    </view>
    
    <view class="book-actions" v-if="showActions">
      <view class="action-btn follow-btn" @tap.stop="onFollow">
        <text class="btn-text">{{ book.isFollowed ? '已关注' : '关注' }}</text>
      </view>
      <view class="action-btn read-btn" @tap.stop="onRead">
        <text class="btn-text">阅读</text>
      </view>
      <view class="action-btn share-btn" @tap.stop="onShare">
        <text class="btn-text">分享</text>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 书籍卡片组件
 * @description 用于展示书籍信息的卡片组件，支持封面、统计数据、操作等
 * @property {Object} book 书籍数据对象
 * @property {Boolean} clickable 是否可点击
 * @property {Boolean} showDescription 是否显示描述
 * @property {Boolean} showRankings 是否显示榜单历史
 * @property {Boolean} showActions 是否显示操作按钮
 * @event {Function} click 点击事件
 * @event {Function} follow 关注事件
 * @event {Function} read 阅读事件
 * @event {Function} share 分享事件
 */
export default {
  name: 'BookCard',
  props: {
    book: {
      type: Object,
      required: true,
      default: () => ({})
    },
    clickable: {
      type: Boolean,
      default: true
    },
    showDescription: {
      type: Boolean,
      default: false
    },
    showRankings: {
      type: Boolean,
      default: true
    },
    showActions: {
      type: Boolean,
      default: false
    }
  },
  
  computed: {
    /**
     * 状态样式类
     */
    statusClass() {
      const status = this.book.status
      if (status === '完结') return 'status-completed'
      if (status === '连载') return 'status-ongoing'
      return 'status-default'
    }
  },
  
  methods: {
    /**
     * 格式化字数显示
     */
    formatWordCount(count) {
      if (typeof count !== 'number') return count || '未知'
      
      if (count >= 10000) {
        return (count / 10000).toFixed(1) + '万字'
      } else if (count >= 1000) {
        return (count / 1000).toFixed(1) + '千字'
      }
      
      return count + '字'
    },
    
    /**
     * 格式化时间显示
     */
    formatTime(time) {
      if (!time) return '未知'
      
      const now = new Date()
      const updateTime = new Date(time)
      const diff = now - updateTime
      
      const minutes = Math.floor(diff / (1000 * 60))
      const hours = Math.floor(diff / (1000 * 60 * 60))
      const days = Math.floor(diff / (1000 * 60 * 60 * 24))
      
      if (minutes < 60) {
        return `${minutes}分钟前`
      } else if (hours < 24) {
        return `${hours}小时前`
      } else if (days < 30) {
        return `${days}天前`
      } else {
        return updateTime.toLocaleDateString()
      }
    },
    
    /**
     * 点击卡片事件
     */
    onClick() {
      if (this.clickable) {
        this.$emit('click', this.book)
      }
    },
    
    /**
     * 关注/取消关注
     */
    onFollow() {
      this.$emit('follow', {
        book: this.book,
        isFollowed: !this.book.isFollowed
      })
    },
    
    /**
     * 阅读书籍
     */
    onRead() {
      this.$emit('read', this.book)
    },
    
    /**
     * 分享书籍
     */
    onShare() {
      this.$emit('share', this.book)
    }
  }
}
</script>

<style lang="scss" scoped>
.book-card {
  @include card-style;
  padding: $spacing-lg;
  margin-bottom: $spacing-sm;
  transition: all 0.3s ease;
  
  &.clickable {
    cursor: pointer;
    
    &:hover {
      transform: translateY(-2rpx);
      box-shadow: $shadow-dark;
    }
    
    &:active {
      transform: translateY(0);
    }
  }
}

.book-header {
  @include flex-between;
  align-items: flex-start;
  margin-bottom: $spacing-md;
}

.book-cover {
  flex-shrink: 0;
  width: 100rpx;
  height: 140rpx;
  border-radius: $border-radius-small;
  overflow: hidden;
  margin-right: $spacing-md;
  
  &.placeholder {
    @include flex-center;
    background-color: $background-color;
    border: 2rpx solid $border-light;
    
    .cover-text {
      font-size: 40rpx;
    }
  }
  
  .cover-image {
    width: 100%;
    height: 100%;
  }
}

.book-info {
  flex: 1;
  
  .book-title {
    display: block;
    font-size: $font-size-lg;
    font-weight: bold;
    color: $text-primary;
    margin-bottom: $spacing-xs;
    @include text-ellipsis;
  }
  
  .book-author {
    display: block;
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-bottom: 4rpx;
  }
  
  .book-category {
    display: block;
    font-size: $font-size-xs;
    color: $text-placeholder;
    margin-bottom: $spacing-xs;
  }
  
  .book-tags {
    @include flex-center;
    flex-wrap: wrap;
    gap: $spacing-xs;
    
    .tag {
      padding: 2rpx 8rpx;
      background-color: $background-color;
      color: $text-secondary;
      font-size: $font-size-xs;
      border-radius: $border-radius-small;
      border: 1rpx solid $border-light;
    }
  }
}

.book-rank {
  @include flex-column-center;
  flex-shrink: 0;
  margin-left: $spacing-sm;
  
  .rank-number {
    font-size: $font-size-xl;
    font-weight: bold;
    color: $accent-color;
  }
  
  .rank-label {
    font-size: $font-size-xs;
    color: $text-placeholder;
  }
}

.book-description {
  margin-bottom: $spacing-md;
  padding: $spacing-sm;
  background-color: $background-color;
  border-radius: $border-radius-small;
  
  .desc-text {
    font-size: $font-size-sm;
    color: $text-secondary;
    line-height: 1.5;
    @include text-ellipsis-multiline(3);
  }
}

.book-stats {
  @include flex-between;
  padding: $spacing-sm 0;
  border-top: 2rpx solid $border-light;
  border-bottom: 2rpx solid $border-light;
  margin-bottom: $spacing-sm;
  
  .stat-item {
    @include flex-column-center;
    flex: 1;
    
    .stat-label {
      font-size: $font-size-xs;
      color: $text-placeholder;
      margin-bottom: 4rpx;
    }
    
    .stat-value {
      font-size: $font-size-sm;
      font-weight: bold;
      color: $text-primary;
      
      &.status-completed {
        color: #4cd964;
      }
      
      &.status-ongoing {
        color: $primary-color;
      }
      
      &.score {
        color: $accent-color;
      }
    }
  }
}

.book-rankings {
  margin-bottom: $spacing-sm;
  
  .rankings-label {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-bottom: $spacing-xs;
  }
  
  .rankings-list {
    @include flex-center;
    gap: $spacing-xs;
    
    .ranking-item {
      padding: 4rpx 12rpx;
      background-color: $primary-color;
      color: white;
      font-size: $font-size-xs;
      border-radius: $border-radius-small;
      @include text-ellipsis;
      max-width: 150rpx;
    }
  }
}

.book-actions {
  @include flex-center;
  gap: $spacing-sm;
  
  .action-btn {
    @include flex-center;
    padding: $spacing-xs $spacing-md;
    border-radius: $border-radius-medium;
    transition: all 0.3s ease;
    flex: 1;
    
    .btn-text {
      font-size: $font-size-sm;
    }
    
    &:active {
      opacity: 0.7;
    }
  }
  
  .follow-btn {
    background-color: $secondary-color;
    
    .btn-text {
      color: white;
    }
  }
  
  .read-btn {
    background-color: $primary-color;
    
    .btn-text {
      color: white;
    }
  }
  
  .share-btn {
    background-color: transparent;
    border: 2rpx solid $border-medium;
    
    .btn-text {
      color: $text-secondary;
    }
  }
}
</style> 