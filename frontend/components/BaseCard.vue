<template>
  <view 
    class="base-card"
    :class="[
      `card-${variant}`,
      { 
        'card-clickable': clickable,
        'card-elevated': elevated,
        'card-bordered': bordered,
        'no-header': !hasHeader
      }
    ]"
    @click="handleClick"
  >
    <!-- 卡片头部 -->
    <view v-if="hasHeader" class="card-header">
      <slot name="header">
        <view class="header-content">
          <text v-if="title" class="card-title">{{ title }}</text>
          <text v-if="subtitle" class="card-subtitle">{{ subtitle }}</text>
        </view>
        <view v-if="hasHeaderAction" class="header-action">
          <slot name="header-action"></slot>
        </view>
      </slot>
    </view>
    
    <!-- 卡片内容 -->
    <view class="card-body">
      <slot></slot>
    </view>
    
    <!-- 卡片底部 -->
    <view v-if="hasFooter" class="card-footer">
      <slot name="footer"></slot>
    </view>
  </view>
</template>

<script>
export default {
  name: 'BaseCard',
  props: {
    // 卡片变体
    variant: {
      type: String,
      default: 'default',
      validator: (value) => ['default', 'outlined', 'filled', 'minimal'].includes(value)
    },
    // 标题
    title: {
      type: String,
      default: ''
    },
    // 副标题
    subtitle: {
      type: String,
      default: ''
    },
    // 是否可点击
    clickable: {
      type: Boolean,
      default: false
    },
    // 是否有阴影
    elevated: {
      type: Boolean,
      default: true
    },
    // 是否有边框
    bordered: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click'],
  computed: {
    hasHeader() {
      return this.$slots.header || this.title || this.subtitle;
    },
    hasFooter() {
      return this.$slots.footer;
    },
    hasHeaderAction() {
      return this.$slots['header-action'];
    }
  },
  methods: {
    handleClick(e) {
      if (this.clickable) {
        this.$emit('click', e);
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.base-card {
  background: $surface-default;
  border-radius: $radius-lg;
  overflow: hidden;
  transition: all $transition-normal;
  
  // 可点击状态
  &.card-clickable {
    cursor: pointer;
    
    &:active {
      transform: scale(0.98);
    }
  }
  
  // 阴影
  &.card-elevated {
    box-shadow: $shadow-sm;
  }
  
  // 边框
  &.card-bordered {
    border: 1px solid rgba($text-secondary, 0.1);
  }
}

// 卡片变体
.card-default {
  background: $surface-default;
}

.card-outlined {
  background: $surface-default;
  border: 1px solid rgba($text-secondary, 0.2);
  box-shadow: none;
}

.card-filled {
  background: $surface-container-high;
}

.card-minimal {
  background: transparent;
  box-shadow: none;
  border-radius: 0;
}

// 卡片结构
.card-header {
  padding: $spacing-lg $spacing-lg $spacing-md;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: $spacing-md;
  
  .header-content {
    flex: 1;
    min-width: 0;
  }
  
  .header-action {
    flex-shrink: 0;
  }
}

.card-title {
  font-family: $font-family-base;
  font-size: 32rpx; // 16px
  font-weight: 600;
  color: $text-primary;
  line-height: 1.3;
  margin-bottom: $spacing-xs;
  
  // 单行省略
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-subtitle {
  font-family: $font-family-base;
  font-size: $caption-font-size-rpx;
  color: $text-secondary;
  line-height: 1.4;
  
  // 两行省略
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-body {
  padding: 0 $spacing-lg $spacing-lg;
}

// 如果没有header，则增加顶部padding
.base-card.no-header .card-body {
  padding-top: $spacing-lg;
}

.card-footer {
  padding: $spacing-md $spacing-lg $spacing-lg;
  border-top: 1px solid rgba($text-secondary, 0.1);
  margin-top: $spacing-md;
}

// 紧凑模式
.card-compact {
  .card-header {
    padding: $spacing-md $spacing-md $spacing-sm;
  }
  
  .card-body {
    padding: 0 $spacing-md $spacing-md;
  }
  
  .card-footer {
    padding: $spacing-sm $spacing-md $spacing-md;
  }
}
</style>