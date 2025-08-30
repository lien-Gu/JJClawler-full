<template>
  <view class="empty-state">
    <view class="empty-icon">
      <text class="icon-text">{{ icon }}</text>
    </view>
    
    <text class="empty-title" v-if="title">{{ title }}</text>
    
    <text class="empty-description" v-if="description">{{ description }}</text>
    
    <!-- 操作按钮插槽 -->
    <view class="empty-action" v-if="$slots.action">
      <slot name="action"></slot>
    </view>
  </view>
</template>

<script>
export default {
  name: 'EmptyState',
  props: {
    icon: {
      type: String,
      default: '📝'
    },
    title: {
      type: String,
      default: '暂无数据'
    },
    description: {
      type: String,
      default: ''
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx $spacing-lg;
  text-align: center;
  
  .empty-icon {
    margin-bottom: $spacing-lg;
    
    .icon-text {
      font-size: 80rpx;
      opacity: 0.6;
    }
  }
  
  .empty-title {
    font-size: 28rpx;
    font-weight: 500;
    color: $text-primary;
    margin-bottom: $spacing-sm;
  }
  
  .empty-description {
    font-size: 24rpx;
    color: $text-secondary;
    line-height: 1.4;
    margin-bottom: $spacing-lg;
  }
  
  .empty-action {
    margin-top: $spacing-md;
  }
}
</style>