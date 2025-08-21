<template>
  <view class="book-list">
    <!-- 列表标题 -->
    <view v-if="title" class="list-header">
      <text class="list-title">{{ title }}</text>
      <text v-if="showCount" class="list-count">共{{ books.length }}本</text>
    </view>
    
    <!-- 书籍列表 -->
    <view class="books-container">
      <view 
        class="book-item" 
        v-for="(book, index) in books" 
        :key="book.id"
        @tap="handleBookTap(book, index)"
      >
        <!-- 排名 -->
        <view v-if="showRank" class="book-rank">
          <text class="rank-number">{{ index + 1 }}</text>
        </view>
        
        <!-- 书籍信息 -->
        <view class="book-info">
          <view class="book-title-row">
            <text class="book-title">{{ book.title }}</text>
          </view>
          
          <view class="book-stats">
            <!-- 点击量 -->
            <view v-if="book.clicks !== undefined" class="stat-item">
              <text class="stat-label">点击:</text>
              <text class="stat-value">{{ formatNumber(book.clicks) }}</text>
            </view>
            
            <!-- 收藏量 -->
            <view v-if="book.collections !== undefined" class="stat-item">
              <text class="stat-label">收藏:</text>
              <text class="stat-value">{{ formatNumber(book.collections) }}</text>
            </view>
            
            <!-- 收藏量变化 -->
            <view v-if="book.collectionChange !== undefined" class="stat-item change">
              <text class="stat-label">收藏变化:</text>
              <text class="stat-value" :class="getChangeClass(book.collectionChange)">
                {{ formatChange(book.collectionChange) }}
              </text>
            </view>
            
            <!-- 排名变化 -->
            <view v-if="book.rankChange !== undefined" class="stat-item change">
              <text class="stat-label">排名变化:</text>
              <text class="stat-value" :class="getChangeClass(book.rankChange)">
                {{ formatRankChange(book.rankChange) }}
              </text>
            </view>
          </view>
        </view>
        
        <!-- 操作按钮 -->
        <view v-if="showActions" class="book-actions">
          <view 
            v-if="actionType === 'unfollow'" 
            class="action-btn unfollow-btn"
            @tap.stop="handleUnfollow(book, index)"
          >
            <text class="action-text">取消关注</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 空状态 -->
    <view v-if="books.length === 0" class="empty-state">
      <text class="empty-text">{{ emptyText || '暂无数据' }}</text>
    </view>
  </view>
</template>

<script>
import formatterMixin from '@/mixins/formatter.js'
import navigationMixin from '@/mixins/navigation.js'

/**
 * 书籍列表组件
 * @description 可复用的书籍列表展示组件，支持多种显示模式
 */
export default {
  name: 'BookList',
  mixins: [formatterMixin, navigationMixin],
  
  props: {
    // 书籍列表数据
    books: {
      type: Array,
      default: () => []
    },
    
    // 列表标题
    title: {
      type: String,
      default: ''
    },
    
    // 是否显示数量
    showCount: {
      type: Boolean,
      default: false
    },
    
    // 是否显示排名
    showRank: {
      type: Boolean,
      default: true
    },
    
    // 是否显示操作按钮
    showActions: {
      type: Boolean,
      default: false
    },
    
    // 操作类型 unfollow-取消关注
    actionType: {
      type: String,
      default: 'unfollow'
    },
    
    // 空状态文本
    emptyText: {
      type: String,
      default: '暂无数据'
    }
  },
  emits: ['book-tap', 'unfollow'],
  
  methods: {
    /**
     * 处理书籍点击
     */
    handleBookTap(book, index) {
      this.$emit('book-tap', { book, index })
    },
    
    /**
     * 处理取消关注
     */
    handleUnfollow(book, index) {
      this.$emit('unfollow', { book, index })
    },
    
    /**
     * 格式化变化值
     */
    formatChange(change) {
      if (change > 0) {
        return `+${change}`
      } else if (change < 0) {
        return change.toString()
      } else {
        return '0'
      }
    },
    
    /**
     * 格式化排名变化
     */
    formatRankChange(change) {
      if (change > 0) {
        return `↗ +${change}`
      } else if (change < 0) {
        return `↘ ${change}`
      } else {
        return `— 0`
      }
    },
    
    /**
     * 获取变化样式类名
     */
    getChangeClass(change) {
      if (change > 0) {
        return 'positive'
      } else if (change < 0) {
        return 'negative'
      } else {
        return 'neutral'
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.book-list {
  .list-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 $spacing-lg $spacing-md;
    
    .list-title {
      font-size: 36rpx;
      font-weight: 600;
      color: $text-primary;
      font-family: $font-family-base;
    }
    
    .list-count {
      font-size: 28rpx;
      font-weight: 400;
      color: $text-secondary;
      font-family: $font-family-base;
    }
  }
  
  .books-container {
    padding: 0 $spacing-lg;
    
    .book-item {
      display: flex;
      align-items: center;
      background: $surface-container-high;
      border-radius: $radius-md;
      padding: $spacing-md;
      margin-bottom: $spacing-sm;
      transition: $transition-normal;
      
      &:active {
        opacity: 0.8;
        transform: scale(0.98);
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
          font-size: 24rpx;
          font-weight: 600;
          color: $surface-default;
        }
      }
      
      .book-info {
        flex: 1;
        min-width: 0;
        
        .book-title-row {
          margin-bottom: $spacing-xs;
          
          .book-title {
            font-size: 32rpx;
            font-weight: 500;
            color: $text-primary;
            font-family: $font-family-base;
            display: -webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 1;
            overflow: hidden;
            text-overflow: ellipsis;
          }
        }
        
        .book-stats {
          display: flex;
          flex-wrap: wrap;
          gap: $spacing-sm;
          
          .stat-item {
            display: flex;
            align-items: center;
            font-size: 24rpx;
            
            .stat-label {
              color: $text-secondary;
              margin-right: 8rpx;
            }
            
            .stat-value {
              color: $text-primary;
              font-weight: 500;
              
              &.positive {
                color: #34c759;
              }
              
              &.negative {
                color: #ff3b30;
              }
              
              &.neutral {
                color: rgba($text-secondary, 0.7);
              }
            }
          }
        }
      }
      
      .book-actions {
        margin-left: $spacing-sm;
        flex-shrink: 0;
        
        .action-btn {
          padding: $spacing-xs $spacing-md;
          border-radius: $radius-md;
          
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
  
  .empty-state {
    padding: 120rpx $spacing-lg;
    text-align: center;
    
    .empty-text {
      font-size: 28rpx;
      color: rgba($text-secondary, 0.7);
      font-family: $font-family-base;
    }
  }
}
</style> 