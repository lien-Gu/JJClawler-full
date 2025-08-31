<template>
  <view
      class="book-list-item"
      @tap="$emit('click', book)"
  >
    <view class="book-rank">
      <text class="rank-number">{{ index + 1 }}</text>
    </view>

    <view class="book-info">
      <view class="book-title-row">
        <text class="book-title">{{ book.title || book.novel_id || "未知书名" }}</text>
        <text class="book-author">{{ book.author || "未知作者" }}</text>
      </view>
      <view class="book-stats">
        <text class="stat-item" v-if="book.collectCount">
          收藏: {{ formatNumber(book.collectCount) }}
        </text>
        <text class="stat-item" v-if="book.clickCount">
          点击: {{ formatNumber(book.clickCount) }}
        </text>
        <text class="stat-item" v-if="book.wordCount">
          {{ formatNumber(book.wordCount) }}字
        </text>
      </view>
    </view>

    <view class="book-actions">
      <BaseButton
          :type="book.isFollowed ? 'secondary' : 'text'"
          :icon="book.isFollowed ? '★' : '☆'"
          size="small"
          round
          @click="handleFollowClick"
      />
    </view>
  </view>
</template>

<script>
import BaseButton from '@/components/BaseButton.vue'
import {formatNumber} from '@/utils/format.js'

export default {
  name: 'BookListItem',
  components: {
    BaseButton
  },
  props: {
    book: {
      type: Object,
      required: true
    },
    index: {
      type: Number,
      required: true
    }
  },
  emits: ['click', 'follow'],
  methods: {
    formatNumber(num) {
      return formatNumber(num);
    },

    handleFollowClick(e) {
      e.stopPropagation();
      this.$emit('follow', this.book);
    },

  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.book-list-item {
  display: flex;
  align-items: center;
  padding: $spacing-md 0;
  border-bottom: 1px solid rgba(108, 117, 125, 0.1);

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background: rgba(108, 117, 125, 0.05);
    margin: 0 (-$spacing-sm);
    padding-left: $spacing-sm;
    padding-right: $spacing-sm;
    border-radius: $radius-sm;
  }

  .book-rank {
    width: 48rpx;
    height: 48rpx;
    background: $brand-primary;
    border-radius: $radius-full;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: $spacing-md;
    flex-shrink: 0;

    .rank-number {
      font-size: 20rpx;
      font-weight: 600;
      color: $surface-default;
    }
  }

  .book-info {
    flex: 1;
    min-width: 0;

    .book-title-row {
      display: flex;
      align-items: center;
      margin-bottom: 8rpx;
      gap: 16rpx;

      .book-title {
        font-size: 28rpx;
        font-weight: 500;
        color: $text-primary;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex: 1;
        min-width: 0;
      }

      .book-author {
        font-size: 22rpx;
        color: $text-secondary;
        white-space: nowrap;
        flex-shrink: 0;
        max-width: 120rpx;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }

    .book-stats {
      display: flex;
      gap: $spacing-md;

      .stat-item {
        font-size: 20rpx;
        color: rgba(108, 117, 125, 0.8);
      }
    }
  }

  .book-actions {
    margin-left: $spacing-sm;
    flex-shrink: 0;
  }
}
</style>