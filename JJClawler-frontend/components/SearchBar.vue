<template>
  <view class="search-bar">
    <view class="search-input-wrapper">
      <input 
        class="search-input"
        type="text"
        :placeholder="placeholder"
        :value="value"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
        @confirm="onConfirm"
      />
      <view class="search-icon" v-if="!value">
        <text class="icon">🔍</text>
      </view>
      <view class="clear-icon" v-if="value" @tap="onClear">
        <text class="icon">✕</text>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 搜索栏组件
 * @description 可复用的搜索输入框组件，支持占位符、清空、确认等功能
 * @property {String} placeholder 占位符文本
 * @property {String} value 输入框的值
 * @event {Function} input 输入事件
 * @event {Function} search 搜索事件（点击确认或回车）
 * @event {Function} clear 清空事件
 * @event {Function} focus 获得焦点事件
 * @event {Function} blur 失去焦点事件
 */
export default {
  name: 'SearchBar',
  props: {
    placeholder: {
      type: String,
      default: '搜索'
    },
    value: {
      type: String,
      default: ''
    }
  },
  
  methods: {
    /**
     * 输入框内容变化
     */
    onInput(e) {
      const value = e.detail.value
      this.$emit('input', value)
      this.$emit('update:value', value)
    },
    
    /**
     * 获得焦点
     */
    onFocus(e) {
      this.$emit('focus', e)
    },
    
    /**
     * 失去焦点
     */
    onBlur(e) {
      this.$emit('blur', e)
    },
    
    /**
     * 确认搜索（回车或点击搜索）
     */
    onConfirm(e) {
      const value = e.detail.value
      this.$emit('search', value)
      this.$emit('confirm', value)
    },
    
    /**
     * 清空输入框
     */
    onClear() {
      this.$emit('input', '')
      this.$emit('update:value', '')
      this.$emit('clear')
    }
  }
}
</script>

<style lang="scss" scoped>
.search-bar {
  width: 100%;
  padding: $spacing-sm 0;
}

.search-input-wrapper {
  position: relative;
  @include flex-center;
  background-color: $background-color;
  border-radius: $border-radius-large;
  border: 2rpx solid $border-light;
  transition: border-color 0.3s ease;
  
  &:focus-within {
    border-color: $primary-color;
  }
}

.search-input {
  flex: 1;
  height: 80rpx;
  padding: 0 $spacing-md;
  font-size: $font-size-md;
  color: $text-primary;
  background-color: transparent;
  border: none;
  outline: none;
  
  &::placeholder {
    color: $text-placeholder;
  }
}

.search-icon,
.clear-icon {
  position: absolute;
  right: $spacing-md;
  @include flex-center;
  width: 40rpx;
  height: 40rpx;
  
  .icon {
    font-size: $font-size-lg;
    color: $text-placeholder;
  }
}

.clear-icon {
  .icon {
    color: $text-secondary;
    font-size: $font-size-md;
  }
  
  &:active {
    opacity: 0.6;
  }
}

// 适配不同主题
.search-bar.theme-dark {
  .search-input-wrapper {
    background-color: #2c2c2c;
    border-color: #444;
  }
  
  .search-input {
    color: #fff;
    
    &::placeholder {
      color: #999;
    }
  }
}
</style> 