<template>
  <view class="ranking-item" @click="handleClick">
    <view class="item-content">
      <!-- 序号 -->
      <view class="ranking-number">
        <text class="number-text">{{ ranking.index || index + 1 }}</text>
      </view>
      
      <!-- 榜单信息 -->
      <view class="ranking-info">
        <text class="ranking-name">{{ ranking.name }}</text>
        <text class="ranking-description">{{ ranking.description || ranking.hierarchy }}</text>
      </view>
      
      <!-- 关注按钮 -->
      <view class="ranking-follow">
        <BaseButton
            :type="isFollowed ? 'primary' : 'secondary'"
            :icon="isFollowed ? '/static/icons/tab-follow-current.png' : '/static/icons/tab-follow.png'"
            size="small"
            round
            @click="handleFollowClick"
        />
      </view>
      
      <!-- 操作按钮 -->
      <view class="ranking-action">
        <text class="action-icon">→</text>
      </view>
    </view>
  </view>
</template>

<script>
import BaseButton from '@/components/BaseButton.vue'
import userStore from '@/store/userStore.js'

export default {
  name: 'RankingListItem',
  components: {
    BaseButton
  },
  props: {
    ranking: {
      type: Object,
      required: true
    },
    index: {
      type: Number,
      default: 0
    }
  },
  emits: ['click', 'follow', 'login-required'],

  computed: {
    isLoggedIn() {
      return userStore.state.isLoggedIn
    },
    
    isFollowed() {
      if (!this.isLoggedIn) return false
      return userStore.isFollowing(this.ranking.id, 'ranking')
    }
  },
  
  methods: {
    handleClick() {
      this.$emit('click', this.ranking);
    },

    handleFollowClick(e) {
      e.stopPropagation();
      
      if (!this.isLoggedIn) {
        this.$emit('login-required');
        return;
      }
      
      try {
        const followItem = {
          id: this.ranking.id,
          type: 'ranking',
          name: this.ranking.name,
          author: '', // 榜单没有作者
          category: '榜单',
          isOnList: true
        };
        
        userStore.toggleFollow(followItem);
        
        // 触发父组件的follow事件（如果需要额外处理）
        this.$emit('follow', this.ranking);
      } catch (error) {
        console.error('关注操作失败:', error);
        uni.showToast({
          title: error.message || '操作失败',
          icon: 'none'
        });
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.ranking-item {
  margin-bottom: $spacing-sm;
  cursor: pointer;
  transition: transform $transition-fast;
  
  &:active {
    transform: scale(0.98);
  }
}

.item-content {
  background: $surface-container-high;
  border-radius: $radius-2xl;
  padding: $spacing-md;
  display: flex;
  align-items: center;
  gap: $spacing-md;
  min-height: 120rpx; // 60px
}

.ranking-number {
  width: 60rpx; // 30px
  height: 60rpx; // 30px
  border-radius: $radius-full;
  background: $brand-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.number-text {
  font-family: $font-family-base;
  font-size: 24rpx; // 12px
  font-weight: 600;
  color: $surface-default;
}

.ranking-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: $spacing-xs;
  min-width: 0; // 防止文本溢出
}

.ranking-name {
  font-family: $font-family-base;
  font-size: 32rpx; // 16px
  font-weight: 600;
  color: $text-primary;
  line-height: 1.3;
  
  // 单行省略
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ranking-description {
  font-family: $font-family-base;
  font-size: $caption-font-size-rpx;
  color: $text-secondary;
  line-height: 1.4;
  
  // 单行省略
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ranking-follow {
  margin-right: $spacing-sm;
  flex-shrink: 0;
}

.ranking-action {
  width: 80rpx; // 40px
  height: 80rpx; // 40px
  background: $surface-dark;
  border-radius: $radius-lg;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background-color $transition-normal;
}

.action-icon {
  font-size: 32rpx; // 16px
  color: $text-secondary;
  font-weight: 300;
}
</style>