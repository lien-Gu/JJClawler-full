<template>
  <view class="ranking-card" :class="{ 'clickable': clickable }" @tap="onClick">
    <view class="ranking-header">
      <view class="ranking-info">
        <text class="ranking-title">{{ ranking.name || ranking.title }}</text>
        <text class="ranking-desc" v-if="ranking.description">{{ ranking.description }}</text>
      </view>
      <view class="ranking-badge" v-if="ranking.isHot">
        <text class="badge-text">热门</text>
      </view>
    </view>
    
    <view class="ranking-stats">
      <view class="stat-item">
        <text class="stat-label">书籍数量</text>
        <text class="stat-value">{{ formatNumber(ranking.bookCount || 0) }}</text>
      </view>
      <view class="stat-item">
        <text class="stat-label">更新时间</text>
        <text class="stat-value">{{ formatTime(ranking.updateTime) }}</text>
      </view>
      <view class="stat-item" v-if="ranking.viewCount">
        <text class="stat-label">浏览量</text>
        <text class="stat-value">{{ formatNumber(ranking.viewCount) }}</text>
      </view>
    </view>
    
    <view class="ranking-footer" v-if="showPreview && ranking.topBooks">
      <text class="preview-label">热门书籍预览：</text>
      <view class="book-preview">
        <text 
          class="book-name" 
          v-for="(book, index) in ranking.topBooks.slice(0, 3)" 
          :key="book.id || index"
        >
          {{ book.name || book.title }}
        </text>
      </view>
    </view>
    
    <view class="ranking-actions" v-if="showActions">
      <view class="action-btn follow-btn" @tap.stop="onFollow">
        <text class="btn-text">{{ ranking.isFollowed ? '已关注' : '关注' }}</text>
      </view>
      <view class="action-btn share-btn" @tap.stop="onShare">
        <text class="btn-text">分享</text>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 榜单卡片组件
 * @description 用于展示榜单信息的卡片组件，支持统计数据、预览、操作等
 * @property {Object} ranking 榜单数据对象
 * @property {Boolean} clickable 是否可点击
 * @property {Boolean} showPreview 是否显示书籍预览
 * @property {Boolean} showActions 是否显示操作按钮
 * @event {Function} click 点击事件
 * @event {Function} follow 关注事件
 * @event {Function} share 分享事件
 */
export default {
  name: 'RankingCard',
  props: {
    ranking: {
      type: Object,
      required: true,
      default: () => ({})
    },
    clickable: {
      type: Boolean,
      default: true
    },
    showPreview: {
      type: Boolean,
      default: true
    },
    showActions: {
      type: Boolean,
      default: false
    }
  },
  
  methods: {
    /**
     * 格式化数字显示
     */
    formatNumber(num) {
      if (typeof num !== 'number') return num || '0'
      
      if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k'
      }
      
      return num.toString()
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
      } else if (days < 7) {
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
        this.$emit('click', this.ranking)
      }
    },
    
    /**
     * 关注/取消关注
     */
    onFollow() {
      this.$emit('follow', {
        ranking: this.ranking,
        isFollowed: !this.ranking.isFollowed
      })
    },
    
    /**
     * 分享榜单
     */
    onShare() {
      this.$emit('share', this.ranking)
    }
  }
}
</script>

<style lang="scss" scoped>
.ranking-card {
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

.ranking-header {
  @include flex-between;
  align-items: flex-start;
  margin-bottom: $spacing-md;
}

.ranking-info {
  flex: 1;
  
  .ranking-title {
    display: block;
    font-size: $font-size-lg;
    font-weight: bold;
    color: $text-primary;
    margin-bottom: $spacing-xs;
    @include text-ellipsis;
  }
  
  .ranking-desc {
    font-size: $font-size-sm;
    color: $text-secondary;
    line-height: 1.4;
    @include text-ellipsis-multiline(2);
  }
}

.ranking-badge {
  flex-shrink: 0;
  margin-left: $spacing-sm;
  
  .badge-text {
    display: inline-block;
    padding: 4rpx 12rpx;
    background-color: $accent-color;
    color: white;
    font-size: $font-size-xs;
    border-radius: $border-radius-small;
  }
}

.ranking-stats {
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
      font-size: $font-size-md;
      font-weight: bold;
      color: $primary-color;
    }
  }
}

.ranking-footer {
  margin-bottom: $spacing-sm;
  
  .preview-label {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-bottom: $spacing-xs;
  }
  
  .book-preview {
    @include flex-center;
    flex-wrap: wrap;
    gap: $spacing-xs;
    
    .book-name {
      padding: 4rpx 12rpx;
      background-color: $background-color;
      color: $text-primary;
      font-size: $font-size-xs;
      border-radius: $border-radius-small;
      @include text-ellipsis;
      max-width: 200rpx;
    }
  }
}

.ranking-actions {
  @include flex-center;
  gap: $spacing-sm;
  
  .action-btn {
    @include flex-center;
    padding: $spacing-xs $spacing-md;
    border-radius: $border-radius-medium;
    transition: all 0.3s ease;
    
    .btn-text {
      font-size: $font-size-sm;
    }
    
    &:active {
      opacity: 0.7;
    }
  }
  
  .follow-btn {
    background-color: $primary-color;
    color: white;
    
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

// 关注状态样式
.ranking-card .follow-btn.followed {
  background-color: $text-placeholder;
  
  .btn-text {
    color: white;
  }
}
</style> 