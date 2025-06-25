<template>
  <view class="custom-tabbar">
    <view class="tabbar-container">
      <view 
        v-for="(item, index) in tabList" 
        :key="item.pagePath"
        class="tabbar-item"
        @click="switchTab(item, index)"
      >
        <view class="tabbar-item-inner">
          <view 
            class="tabbar-icon-container"
            :class="{ 'tabbar-icon-active': currentIndex === index }"
          >
            <image 
              class="tabbar-icon" 
              :src="currentIndex === index ? item.selectedIconPath : item.iconPath"
              mode="aspectFit"
            />
          </view>
          <text 
            class="tabbar-text"
            :class="{ 'tabbar-text-active': currentIndex === index }"
          >
            {{ item.text }}
          </text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'TabBar',
  props: {
    currentIndex: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      tabList: [
        {
          pagePath: '/pages/index/index',
          text: '首页',
          iconPath: '/static/icons/tab-home.png',
          selectedIconPath: '/static/icons/tab-home-current.png'
        },
        {
          pagePath: '/pages/ranking/index',
          text: '榜单',
          iconPath: '/static/icons/tab-ranking.png', 
          selectedIconPath: '/static/icons/tab-ranking-current.png'
        },
        {
          pagePath: '/pages/follow/index',
          text: '关注',
          iconPath: '/static/icons/tab-follow.png',
          selectedIconPath: '/static/icons/tab-follow-current.png'
        },
        {
          pagePath: '/pages/settings/index',
          text: '设置',
          iconPath: '/static/icons/tab-settings.png',
          selectedIconPath: '/static/icons/tab-settings-current.png'
        }
      ]
    }
  },
  methods: {
    switchTab(item, index) {
      if (this.currentIndex === index) return;
      
      uni.switchTab({
        url: item.pagePath,
        fail: (err) => {
          // 如果switchTab失败，尝试navigateTo
          uni.navigateTo({
            url: item.pagePath
          });
        }
      });
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.custom-tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: $z-index-tabbar;
  padding-bottom: env(safe-area-inset-bottom);
}

.tabbar-container {
  height: $tabbar-height;
  background: $tabbar-background;
  border-radius: $radius-3xl $radius-3xl 0 0;
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 0 $spacing-md;
  margin: 0 $spacing-sm;
  box-shadow: $shadow-md;
}

.tabbar-item {
  width: $tabbar-item-width;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tabbar-item-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-sm 0;
  width: 100%;
}

.tabbar-icon-container {
  width: 120rpx; // 60px
  height: 80rpx; // 40px
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color $transition-normal;
  
  &.tabbar-icon-active {
    background-color: $surface-dark;
  }
}

.tabbar-icon {
  width: $tabbar-icon-size;
  height: $tabbar-icon-size;
}

.tabbar-text {
  font-family: $font-family-base;
  font-size: $caption-font-size-rpx;
  font-weight: $caption-font-weight;
  line-height: $caption-line-height-rpx;
  color: $text-secondary;
  text-align: center;
  transition: color $transition-normal;
  
  &.tabbar-text-active {
    color: $text-primary;
    font-weight: 700; // Bold when active
  }
}
</style>