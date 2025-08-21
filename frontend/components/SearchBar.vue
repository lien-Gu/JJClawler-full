<template>
  <view class="search-bar">
    <view class="search-container">
      <view class="search-icon">
        <text class="icon">⚙</text>
      </view>
      <input 
        class="search-input"
        type="text"
        :value="value"
        :placeholder="placeholder"
        @input="onInput"
        @confirm="onConfirm"
        @focus="onFocus"
        @blur="onBlur"
      />
      <view class="search-action" @click="onSearch">
        <text class="search-icon-text">🔍</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'SearchBar',
  props: {
    value: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: 'Hinted search text'
    }
  },
  emits: ['input', 'search', 'focus', 'blur'],
  methods: {
    onInput(e) {
      this.$emit('input', e.detail.value);
    },
    
    onConfirm(e) {
      this.$emit('search', e.detail.value);
    },
    
    onSearch() {
      this.$emit('search', this.value);
    },
    
    onFocus(e) {
      this.$emit('focus', e);
    },
    
    onBlur(e) {
      this.$emit('blur', e);
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.search-bar {
  padding: $spacing-md;
}

.search-container {
  height: 96rpx; // 48px
  background: $surface-container-high;
  border-radius: $radius-2xl;
  display: flex;
  align-items: center;
  padding: 0 $spacing-md;
  gap: $spacing-sm;
}

.search-icon {
  width: 48rpx; // 24px
  height: 48rpx; // 24px
  display: flex;
  align-items: center;
  justify-content: center;
  
  .icon {
    font-size: 32rpx; // 16px
    color: $text-secondary;
  }
}

.search-input {
  flex: 1;
  height: 100%;
  font-family: $font-family-base;
  font-size: 32rpx; // 16px
  color: $text-primary;
  background: transparent;
  border: none;
  outline: none;
  
  &::placeholder {
    color: $text-secondary;
    opacity: 0.6;
  }
}

.search-action {
  width: 48rpx; // 24px
  height: 48rpx; // 24px
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: opacity $transition-fast;
  
  &:active {
    opacity: 0.6;
  }
}

.search-icon-text {
  font-size: 32rpx; // 16px
  color: $text-secondary;
}
</style>