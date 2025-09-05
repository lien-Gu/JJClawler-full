<template>
  <view 
    class="base-button"
    :class="[
      `btn-${type}`,
      `btn-${size}`,
      { 
        'btn-disabled': disabled,
        'btn-loading': loading,
        'btn-block': block,
        'btn-round': round
      }
    ]"
    @click="handleClick"
  >
    <!-- 加载图标 -->
    <view v-if="loading" class="btn-loading-icon">
      <text class="loading-spinner">⟳</text>
    </view>
    
    <!-- 图标 -->
    <view v-if="icon && !loading" class="btn-icon">
      <image v-if="isImageIcon" :src="icon" class="icon-image" mode="aspectFit" />
      <text v-else class="icon-text">{{ icon }}</text>
    </view>
    
    <!-- 文字内容 -->
    <view class="btn-content">
      <slot>{{ text }}</slot>
    </view>
  </view>
</template>

<script>
export default {
  name: 'BaseButton',
  props: {
    // 按钮类型
    type: {
      type: String,
      default: 'default',
      validator: (value) => ['default', 'primary', 'secondary', 'success', 'warning', 'error', 'text'].includes(value)
    },
    // 按钮尺寸
    size: {
      type: String,
      default: 'medium',
      validator: (value) => ['small', 'medium', 'large'].includes(value)
    },
    // 按钮文字
    text: {
      type: String,
      default: ''
    },
    // 图标
    icon: {
      type: String,
      default: ''
    },
    // 是否禁用
    disabled: {
      type: Boolean,
      default: false
    },
    // 是否加载中
    loading: {
      type: Boolean,
      default: false
    },
    // 是否块级按钮
    block: {
      type: Boolean,
      default: false
    },
    // 是否圆形按钮
    round: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click'],
  computed: {
    isImageIcon() {
      return this.icon && (this.icon.includes('/') || this.icon.includes('.'))
    }
  },
  methods: {
    handleClick(e) {
      if (this.disabled || this.loading) return;
      
      // 阻止事件冒泡，防止触发父元素的点击事件
      e.stopPropagation();
      
      this.$emit('click', e);
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.base-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-xs;
  border: none;
  border-radius: $radius-md;
  font-family: $font-family-base;
  font-weight: 500;
  text-align: center;
  cursor: pointer;
  user-select: none;
  transition: all $transition-normal;
  position: relative;
  overflow: hidden;
  
  &:active {
    transform: scale(0.95);
  }
  
  // 禁用状态
  &.btn-disabled {
    opacity: 0.5;
    cursor: not-allowed;
    
    &:active {
      transform: none;
    }
  }
  
  // 块级按钮
  &.btn-block {
    width: 100%;
  }
  
  // 圆形按钮
  &.btn-round {
    border-radius: $radius-full;
  }
}

// 尺寸样式
.btn-small {
  height: 60rpx; // 30px
  padding: 0 $spacing-md;
  font-size: 24rpx; // 12px
  
  .btn-icon {
    .icon-text {
      font-size: 20rpx; // 10px
    }
    .icon-image {
      width: 20rpx;
      height: 20rpx;
    }
  }
}

.btn-medium {
  height: 80rpx; // 40px  
  padding: 0 $spacing-lg;
  font-size: $caption-font-size-rpx;
  
  .btn-icon {
    .icon-text {
      font-size: 28rpx; // 14px
    }
    .icon-image {
      width: 28rpx;
      height: 28rpx;
    }
  }
}

.btn-large {
  height: 96rpx; // 48px
  padding: 0 $spacing-xl;
  font-size: 32rpx; // 16px
  
  .btn-icon {
    .icon-text {
      font-size: 32rpx; // 16px
    }
    .icon-image {
      width: 32rpx;
      height: 32rpx;
    }
  }
}

// 类型样式
.btn-default {
  background: $surface-container-high;
  color: $text-primary;
  
  &:active {
    background: darken($surface-container-high, 5%);
  }
}

.btn-primary {
  background: $brand-primary;
  color: $surface-default;
  
  &:active {
    background: darken($brand-primary, 10%);
  }
}

.btn-secondary {
  background: $surface-dark;
  color: $text-primary;
  
  &:active {
    background: darken($surface-dark, 5%);
  }
}

.btn-success {
  background: #34c759;
  color: $surface-default;
  
  &:active {
    background: darken(#34c759, 10%);
  }
}

.btn-warning {
  background: #ff9500;
  color: $surface-default;
  
  &:active {
    background: darken(#ff9500, 10%);
  }
}

.btn-error {
  background: #ff3b30;
  color: $surface-default;
  
  &:active {
    background: darken(#ff3b30, 10%);
  }
}

.btn-text {
  background: transparent;
  color: $brand-primary;
  
  &:active {
    background: rgba($brand-primary, 0.1);
  }
}

// 加载状态
.btn-loading-icon {
  .loading-spinner {
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 内容样式
.btn-content {
  flex: 1;
  text-align: center;
}

.btn-icon {
  flex-shrink: 0;
  
  .icon-image {
    width: 24rpx;
    height: 24rpx;
  }
}
</style>