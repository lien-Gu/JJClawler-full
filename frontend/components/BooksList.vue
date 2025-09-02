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
      <BookListItem
        v-for="(book, index) in booksList"
        :key="book.id"
        :book="book"
        :index="index"
        @click="goToBookDetail"
        @follow="toggleBookFollow"
      />
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
import BookListItem from '@/components/BookListItem.vue'
import requestManager from '@/api/request.js'
import navigation from '@/utils/navigation.js'

export default {
  name: 'BooksList',
  components: {
    BookListItem
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

    async toggleBookFollow(book) {
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