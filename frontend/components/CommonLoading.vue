<template>
  <view class="loading-state">
    <view v-if="loading" class="loading-more">
      <text class="loading-text">{{ loadingText }}</text>
    </view>
    
    <view v-else-if="!hasMore && showNoMore" class="no-more">
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

.loading-state {
  .loading-more,
  .no-more {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: $spacing-lg;
    
    .loading-text,
    .no-more-text {
      font-size: 24rpx;
      color: $text-secondary;
    }
    
    .no-more-text {
      opacity: 0.6;
    }
  }
}
</style>