<template>
  <scroll-view 
    class="scrollable-list"
    scroll-y
    :refresher-enabled="refresherEnabled"
    :refresher-triggered="refreshing"
    @refresherrefresh="onRefresh"
    @scrolltolower="onLoadMore"
    :style="{ height: height }"
  >
    <view class="list-content" :style="{ padding: contentPadding }">
      <slot></slot>
      
      <!-- 加载状态 -->
      <LoadingMore
        :loading="loading"
        :has-more="hasMore"
        :show-no-more="showNoMore && items.length > 0"
        :loading-text="loadingText"
        :no-more-text="noMoreText"
      />
      
      <!-- 空状态 -->
      <EmptyState
        v-if="items.length === 0 && !loading"
        :icon="emptyIcon"
        :title="emptyTitle"
        :description="emptyDescription"
      >
        <template #action>
          <slot name="empty-action"></slot>
        </template>
      </EmptyState>
    </view>
  </scroll-view>
</template>

<script>
import LoadingMore from '@/components/LoadingMore/LoadingMore.vue'
import EmptyState from '@/components/EmptyState/EmptyState.vue'

export default {
  name: 'ScrollableList',
  components: {
    LoadingMore,
    EmptyState
  },
  props: {
    items: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    refreshing: {
      type: Boolean,
      default: false
    },
    hasMore: {
      type: Boolean,
      default: true
    },
    refresherEnabled: {
      type: Boolean,
      default: true
    },
    height: {
      type: String,
      default: 'auto'
    },
    contentPadding: {
      type: String,
      default: '0 32rpx'
    },
    loadingText: {
      type: String,
      default: '加载中...'
    },
    noMoreText: {
      type: String,
      default: '没有更多数据了'
    },
    showNoMore: {
      type: Boolean,
      default: true
    },
    emptyIcon: {
      type: String,
      default: '📝'
    },
    emptyTitle: {
      type: String,
      default: '暂无数据'
    },
    emptyDescription: {
      type: String,
      default: ''
    }
  },
  emits: ['refresh', 'load-more'],
  methods: {
    onRefresh() {
      this.$emit('refresh')
    },
    onLoadMore() {
      this.$emit('load-more')
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.scrollable-list {
  flex: 1;
}

.list-content {
  padding-bottom: $spacing-lg;
}
</style>