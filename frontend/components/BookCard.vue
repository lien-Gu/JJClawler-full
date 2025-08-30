<template>
  <BaseCard
    :clickable="clickable"
    @click="onClick"
  >
    <!-- 书籍头部信息 -->
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
    
    <!-- 书籍描述 -->
    <view class="book-description" v-if="book.description && showDescription">
      <text class="desc-text">{{ book.description }}</text>
    </view>
    
    <!-- 统计信息 -->
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
    
    <!-- 榜单历史 -->
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
    
    <!-- 操作按钮 -->
    <template #footer v-if="showActions">
      <view class="book-actions">
        <BaseButton 
          :type="book.isFollowed ? 'secondary' : 'default'"
          :text="book.isFollowed ? '已关注' : '关注'"
          size="small"
          @click="onFollow"
        />
        <BaseButton 
          type="primary"
          text="阅读"
          size="small"
          @click="onRead"
        />
        <BaseButton 
          type="text"
          text="分享"
          size="small"
          @click="onShare"
        />
      </view>
    </template>
  </BaseCard>
</template>

<script>
import BaseCard from '@/components/BaseCard.vue'
import BaseButton from '@/components/BaseButton.vue'
import { formatNumber, formatWordCount } from '@/utils/format.js'
import navigation from '@/utils/navigation.js'

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
  components: {
    BaseCard,
    BaseButton
  },
  mixins: [formatterMixin, navigationMixin],
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
  emits: ['click', 'follow', 'read', 'share'],
  
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
    onFollow(e) {
      e.stopPropagation()
      this.$emit('follow', {
        book: this.book,
        isFollowed: !this.book.isFollowed
      })
    },
    
    /**
     * 阅读书籍
     */
    onRead(e) {
      e.stopPropagation()
      this.$emit('read', this.book)
    },
    
    /**
     * 分享书籍
     */
    onShare(e) {
      e.stopPropagation()
      this.$emit('share', this.book)
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.book-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $spacing-md;
}

.book-cover {
  flex-shrink: 0;
  width: 100rpx;
  height: 140rpx;
  border-radius: $radius-sm;
  overflow: hidden;
  margin-right: $spacing-md;
  
  &.placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    background: $surface-container-high;
    border: 1px solid rgba($text-secondary, 0.2);
    
    .cover-text {
      font-size: 40rpx;
      opacity: 0.6;
    }
  }
  
  .cover-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.book-info {
  flex: 1;
  min-width: 0;
  
  .book-title {
    display: block;
    font-size: 32rpx;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: $spacing-xs;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .book-author {
    display: block;
    font-size: 24rpx;
    color: $text-secondary;
    margin-bottom: 8rpx;
  }
  
  .book-category {
    display: block;
    font-size: 20rpx;
    color: rgba($text-secondary, 0.7);
    margin-bottom: $spacing-xs;
  }
  
  .book-tags {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: $spacing-xs;
    
    .tag {
      padding: 4rpx 12rpx;
      background: $surface-container-high;
      color: $text-secondary;
      font-size: 18rpx;
      border-radius: $radius-sm;
      border: 1px solid rgba($text-secondary, 0.1);
    }
  }
}

.book-rank {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  margin-left: $spacing-sm;
  
  .rank-number {
    font-size: 40rpx;
    font-weight: 700;
    color: $brand-primary;
  }
  
  .rank-label {
    font-size: 18rpx;
    color: rgba($text-secondary, 0.7);
  }
}

.book-description {
  margin-bottom: $spacing-md;
  padding: $spacing-sm;
  background: $surface-container-high;
  border-radius: $radius-sm;
  
  .desc-text {
    font-size: 24rpx;
    color: $text-secondary;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.book-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-sm 0;
  border-top: 1px solid rgba($text-secondary, 0.1);
  border-bottom: 1px solid rgba($text-secondary, 0.1);
  margin-bottom: $spacing-sm;
  
  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    
    .stat-label {
      font-size: 20rpx;
      color: rgba($text-secondary, 0.7);
      margin-bottom: 8rpx;
    }
    
    .stat-value {
      font-size: 24rpx;
      font-weight: 600;
      color: $text-primary;
      
      &.status-completed {
        color: #34c759;
      }
      
      &.status-ongoing {
        color: $brand-primary;
      }
      
      &.score {
        color: #ff9500;
      }
    }
  }
}

.book-rankings {
  margin-bottom: $spacing-sm;
  
  .rankings-label {
    font-size: 24rpx;
    color: $text-secondary;
    margin-bottom: $spacing-xs;
  }
  
  .rankings-list {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    
    .ranking-item {
      padding: 8rpx 16rpx;
      background: $brand-primary;
      color: $surface-default;
      font-size: 20rpx;
      border-radius: $radius-sm;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 150rpx;
    }
  }
}

.book-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: $spacing-md;
  margin-top: $spacing-sm;
}
</style> 