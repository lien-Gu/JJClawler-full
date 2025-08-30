<template>
  <view class="loading-more" v-if="loading || (!hasMore && showNoMore)">
    <!-- 加载中状态 -->
    <view v-if="loading" class="loading-state">
      <text class="loading-icon">⏳</text>
      <text class="loading-text">{{ loadingText }}</text>
    </view>
    
    <!-- 没有更多数据状态 -->
    <view v-else-if="!hasMore && showNoMore" class="no-more-state">
      <text class="no-more-text">{{ noMoreText }}</text>
    </view>
  </view>
</template>

<script>
export default {
  name: 'LoadingMore',
  props: {
    loading: {
      type: Boolean,
      default: false
    },
    hasMore: {
      type: Boolean,
      default: true
    },
    showNoMore: {
      type: Boolean,
      default: true
    },
    loadingText: {
      type: String,
      default: '加载中...'
    },
    noMoreText: {
      type: String,
      default: '没有更多数据了'
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-lg;
  
  .loading-state,
  .no-more-state {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: $spacing-sm;
  }
  
  .loading-icon {
    font-size: 24rpx;
    animation: spin 1s linear infinite;
  }
  
  .loading-text,
  .no-more-text {
    font-size: 24rpx;
    color: $text-secondary;
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>