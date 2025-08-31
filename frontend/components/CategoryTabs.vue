<template>
  <view class="category-tabs">
    <!-- 主分类标签 -->
    <scroll-view class="main-tabs" scroll-x show-scrollbar="false">
      <view class="tabs-container">
        <view 
          v-for="(tab, index) in mainTabs" 
          :key="tab.key"
          class="tab-item"
          :class="{ 'tab-active': currentMainTab === tab.key }"
          @click="selectMainTab(tab, index)"
        >
          <text class="tab-text">{{ tab.name }}</text>
        </view>
      </view>
    </scroll-view>
    
    <!-- 子分类标签 -->
    <scroll-view 
      v-if="subTabs.length > 0"
      class="sub-tabs" 
      scroll-x 
      show-scrollbar="false"
    >
      <view class="tabs-container">
        <view 
          v-for="(tab, index) in subTabs" 
          :key="tab.key"
          class="sub-tab-item"
          :class="{ 'sub-tab-active': currentSubTab === tab.key }"
          @click="selectSubTab(tab, index)"
        >
          <text class="sub-tab-text">{{ tab.name }}</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
export default {
  name: 'CategoryTabs',
  props: {
    categories: {
      type: Array,
      default: () => []
    },
    currentMainTab: {
      type: String,
      default: ''
    },
    currentSubTab: {
      type: String,
      default: ''
    }
  },
  emits: ['change'],
  computed: {
    mainTabs() {
      return this.categories.map(cat => ({
        key: cat.key,
        name: cat.name,
        children: cat.children || []
      }));
    },
    
    subTabs() {
      const currentMain = this.categories.find(cat => cat.key === this.currentMainTab);
      return currentMain?.children || [];
    }
  },
  methods: {
    selectMainTab(tab, index) {
      // 如果当前已经是这个主分类，且没有选择子分类，则不需要重复处理
      if (this.currentMainTab === tab.key && this.currentSubTab === '') {
        console.log(`主分类${tab.name}已经是当前选中状态，无需重复处理`);
        return;
      }
      
      // 选择主分类时，不自动选择子分类，让用户明确选择
      // 清空当前子分类选择，显示主分类的榜单内容
      console.log(`切换到主分类: ${tab.name}，从子分类${this.currentSubTab || '无'}回到主分类`);
      
      this.$emit('change', {
        mainTab: tab.key,
        subTab: '', // 不自动选择子分类
        tab: tab
      });
    },
    
    selectSubTab(tab, index) {
      if (this.currentSubTab === tab.key) return;
      
      this.$emit('change', {
        mainTab: this.currentMainTab,
        subTab: tab.key,
        tab: tab
      });
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.category-tabs {
  background: $surface-default;
}

.main-tabs, .sub-tabs {
  white-space: nowrap;
}

.tabs-container {
  display: flex;
  padding: 0 $spacing-md;
  gap: $spacing-sm;
}

// 主分类标签样式
.tab-item {
  flex-shrink: 0;
  padding: $spacing-md $spacing-lg;
  border-radius: $radius-lg;
  transition: all $transition-normal;
  cursor: pointer;
  
  &.tab-active {
    background: $surface-dark;
    
    .tab-text {
      color: $text-primary;
      font-weight: 600;
    }
  }
  
  &:active {
    transform: scale(0.95);
  }
}

.tab-text {
  font-family: $font-family-base;
  font-size: 30rpx; // 15px
  color: $text-secondary;
  transition: color $transition-normal;
}

// 子分类标签样式
.sub-tabs {
  border-bottom: 1rpx solid rgba(69, 68, 68, 0.1);
  padding-bottom: $spacing-sm;
}

.sub-tab-item {
  flex-shrink: 0;
  padding: $spacing-sm $spacing-md;
  border-radius: $radius-md;
  position: relative;
  cursor: pointer;
  transition: all $transition-normal;
  
  &.sub-tab-active {
    background: $surface-dark;
    
    .sub-tab-text {
      color: $text-primary;
      font-weight: 600;
    }
  }
  
  &:active {
    transform: scale(0.95);
  }
}

.sub-tab-text {
  font-family: $font-family-base;
  font-size: $caption-font-size-rpx;
  color: $text-secondary;
  transition: color $transition-normal;
}
</style>