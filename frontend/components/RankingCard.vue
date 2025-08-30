<template>
  <BaseCard
    :clickable="clickable"
    :title="ranking.name || ranking.title"
    :subtitle="ranking.description"
    @click="onClick"
  >
    <!-- 头部操作区域 -->
    <template #header-action>
      <view v-if="ranking.isHot" class="ranking-badge">
        <text class="badge-text">热门</text>
      </view>
    </template>
    
    <!-- 统计信息 -->
    <view class="ranking-stats">
      <view class="stat-item">
        <text class="stat-label">书籍数量</text>
        <text class="stat-value">{{ formatNumber(ranking.bookCount || 0) }}</text>
      </view>
      <view class="stat-item">
        <text class="stat-label">更新时间</text>
        <text class="stat-value">{{ formatTime(ranking.updateTime) }}</text>
      </view>
      <view class="stat-item" v-if="ranking.viewCount">
        <text class="stat-label">浏览量</text>
        <text class="stat-value">{{ formatNumber(ranking.viewCount) }}</text>
      </view>
    </view>
    
    <!-- 书籍预览 -->
    <view v-if="showPreview && ranking.topBooks" class="ranking-preview">
      <text class="preview-label">热门书籍预览：</text>
      <view class="book-preview">
        <text 
          class="book-name" 
          v-for="(book, index) in ranking.topBooks.slice(0, 3)" 
          :key="book.id || index"
        >
          {{ book.name || book.title }}
        </text>
      </view>
    </view>
    
    <!-- 操作按钮 -->
    <template #footer v-if="showActions">
      <view class="ranking-actions">
        <BaseButton 
          :type="ranking.isFollowed ? 'secondary' : 'primary'"
          :text="ranking.isFollowed ? '已关注' : '关注'"
          size="small"
          @click="onFollow"
        />
        <BaseButton 
          type="text"
          text="分享"
          size="small"
          @click="onShare"
        />
      </view>
    </template>
  </BaseCard>
</template>

<script>
import BaseCard from '@/components/BaseCard.vue'
import BaseButton from '@/components/BaseButton.vue'
import { formatNumber, formatTime } from '@/utils/format.js'
import navigation from '@/utils/navigation.js'

/**
 * 榜单卡片组件
 * @description 用于展示榜单信息的卡片组件，支持统计数据、预览、操作等
 * @property {Object} ranking 榜单数据对象
 * @property {Boolean} clickable 是否可点击
 * @property {Boolean} showPreview 是否显示书籍预览
 * @property {Boolean} showActions 是否显示操作按钮
 * @event {Function} click 点击事件
 * @event {Function} follow 关注事件
 * @event {Function} share 分享事件
 */
export default {
  name: 'RankingCard',
  components: {
    BaseCard,
    BaseButton
  },
  mixins: [formatterMixin, navigationMixin],
  props: {
    ranking: {
      type: Object,
      required: true,
      default: () => ({})
    },
    clickable: {
      type: Boolean,
      default: true
    },
    showPreview: {
      type: Boolean,
      default: true
    },
    showActions: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click', 'follow', 'share'],
  
  methods: {
    /**
     * 点击卡片事件
     */
    onClick() {
      if (this.clickable) {
        this.$emit('click', this.ranking)
      }
    },
    
    /**
     * 关注/取消关注
     */
    onFollow(e) {
      e.stopPropagation()
      this.$emit('follow', {
        ranking: this.ranking,
        isFollowed: !this.ranking.isFollowed
      })
    },
    
    /**
     * 分享榜单
     */
    onShare(e) {
      e.stopPropagation()
      this.$emit('share', this.ranking)
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.ranking-badge {
  .badge-text {
    display: inline-block;
    padding: 8rpx 24rpx;
    background: linear-gradient(135deg, #ff6b6b, #ff8e8e);
    color: $surface-default;
    font-size: 20rpx;
    font-weight: 500;
    border-radius: $radius-full;
    box-shadow: 0 4rpx 12rpx rgba(255, 107, 107, 0.3);
  }
}

.ranking-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-md 0;
  border-top: 1px solid rgba($text-secondary, 0.1);
  border-bottom: 1px solid rgba($text-secondary, 0.1);
  margin: $spacing-md 0;
  
  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    
    .stat-label {
      font-size: 20rpx;
      color: $text-secondary;
      margin-bottom: 8rpx;
    }
    
    .stat-value {
      font-size: 28rpx;
      font-weight: 600;
      color: $brand-primary;
    }
  }
}

.ranking-preview {
  margin-top: $spacing-md;
  
  .preview-label {
    font-size: 24rpx;
    color: $text-secondary;
    margin-bottom: $spacing-sm;
  }
  
  .book-preview {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-xs;
    
    .book-name {
      padding: 8rpx 16rpx;
      background: $surface-container-high;
      color: $text-primary;
      font-size: 20rpx;
      border-radius: $radius-md;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 200rpx;
    }
  }
}

.ranking-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: $spacing-md;
  margin-top: $spacing-sm;
}
</style> 