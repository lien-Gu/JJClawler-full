<template>
  <scroll-view
      class="books-container"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      @scrolltolower="onLoadMore"
  >
    <view class="books-list">
      <view
          class="book-item"
          v-for="(book, index) in booksList"
          :key="book.id"
          @tap="goToBookDetail(book)"
      >
        <view class="book-rank">
          <text class="rank-number">{{ index + 1 }}</text>
        </view>

        <view class="book-info">
          <view class="book-title-row">
            <text class="book-title">{{ book.title || book.novel_id || '未知' }}</text>
            <text class="book-author" v-if="book.author">{{ book.author}}</text>
          </view>
          <view class="book-stats">
            <text class="stat-item" v-if="book.collectCount">
              收藏: {{ formatNumber(book.collectCount)}}
            </text>
            <text class="stat-item" v-if="book.clickCount">
              点击: {{ formatNumber(book.clickCount)}}
            </text>
          </view>
        </view>

        <view class="book-actions">
          <BaseButton
              :type="book.isFollowed ? 'secondary' : 'text'"
              :icon="book.isFollowed ? '★' : '☆'"
              size="small"
              round
              @click="toggleBookFollow(book, $event)"
          />
        </view>
      </view>
    </view>

    <!-- 加载更多提示 -->
    <view v-if="loading" class="loading-more">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 没有更多数据提示 -->
    <view v-if="!hasMore && booksList.length > 0" class="no-more">
      <text class="no-more-text">没有更多书籍了</text>
    </view>

    <!-- 空状态 -->
    <view v-if="booksList.length === 0 && !loading" class="empty-state">
      <text class="empty-text">{{ emptyText || '暂无书籍数据' }}</text>
    </view>
  </scroll-view>
</template>

<script>
import BaseButton from '@/components/BaseButton.vue'
import requestManager from '@/api/request.js'
import { formatNumber } from '@/utils/format.js'
import navigation from '@/utils/navigation.js'

export default {
  name: 'BooksList',
  components: {
    BaseButton
  },
  props: {
    rankingId: {
      type: [String, Number],
      required: true
    },
    height: {
      type: String,
      default: '600rpx'
    },
    emptyText: {
      type: String,
      default: '暂无书籍数据'
    },
    pageSize: {
      type: Number,
      default: 20
    }
  },
  data() {
    return {
      booksList: [],
      loading: false,
      refreshing: false,
      hasMore: true,
      page: 1
    }
  },
  mounted() {
    this.loadBooksList(true)
  },
  methods: {
    ...navigation,

    formatNumber,

    async loadBooksList(reset = false) {
      if (this.loading) return

      this.loading = true
      try {
        if (reset) {
          this.page = 1
          this.booksList = []
          this.hasMore = true
        }

        const params = {
          page: this.page,
          limit: this.pageSize
        }

        const response = await requestManager.getRankingBooksDetail(this.rankingId, params)

        if (response && response.success && response.data && Array.isArray(response.data.books)) {
          const books = response.data.books

          if (reset) {
            this.booksList = books
          } else {
            this.booksList.push(...books)
          }

          const totalPages = Math.ceil(response.data.total / this.pageSize)
          this.hasMore = this.page < totalPages
          this.page++

          this.checkBooksFollowStatus()
        } else {
          this.hasMore = false
        }
      } catch (error) {
        console.error('加载书籍列表失败:', error)
        if (reset) {
          uni.showToast({
            title: '加载失败',
            icon: 'none'
          })
        }
      } finally {
        this.loading = false
      }
    },

    checkBooksFollowStatus() {
      try {
        const followList = uni.getStorageSync('followList') || []
        this.booksList.forEach(book => {
          book.isFollowed = followList.some(item => item.id === book.id)
        })
      } catch (error) {
        console.error('检查关注状态失败:', error)
      }
    },

    async onRefresh() {
      this.refreshing = true
      await this.loadBooksList(true)
      this.refreshing = false
    },

    async onLoadMore() {
      if (this.hasMore && !this.loading) {
        await this.loadBooksList()
      }
    },

    goToBookDetail(book) {
      this.navigateTo('/pages/book/detail', {
        id: book.id
      })
    },

    async toggleBookFollow(book, event) {
      event.stopPropagation()

      try {
        if (book.isFollowed) {
          this.removeBookFromFollow(book)
        } else {
          this.addBookToFollow(book)
        }
        book.isFollowed = !book.isFollowed
      } catch (error) {
        console.error('关注操作失败:', error)
        uni.showToast({
          title: '操作失败',
          icon: 'none'
        })
      }
    },

    addBookToFollow(book) {
      try {
        const followList = uni.getStorageSync('followList') || []
        const followItem = {
          id: book.id,
          type: 'book',
          name: book.title,
          author: book.author,
          category: book.category,
          isOnList: true,
          weeklyGrowth: book.weeklyGrowth || 0,
          followDate: new Date().toISOString()
        }

        const existingIndex = followList.findIndex(item => item.id === book.id)
        if (existingIndex === -1) {
          followList.push(followItem)
          uni.setStorageSync('followList', followList)

          uni.showToast({
            title: '已关注',
            icon: 'success',
            duration: 1000
          })
        }
      } catch (error) {
        console.error('添加关注失败:', error)
      }
    },

    removeBookFromFollow(book) {
      try {
        const followList = uni.getStorageSync('followList') || []
        const newList = followList.filter(item => item.id !== book.id)
        uni.setStorageSync('followList', newList)

        uni.showToast({
          title: '已取消关注',
          icon: 'success',
          duration: 1000
        })
      } catch (error) {
        console.error('取消关注失败:', error)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.books-container {
  height: v-bind(height);
}

.books-list {
  .book-item {
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
}

.loading-more,
.no-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-lg;

  .loading-text,
  .no-more-text {
    font-size: 24rpx;
    color: $text-secondary;
  }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 120rpx;

  .empty-text {
    font-size: 24rpx;
    color: $text-secondary;
  }
}
</style>