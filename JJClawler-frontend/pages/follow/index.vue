<template>
  <view class="follow-page">
    <!-- 我的关注标题卡片 -->
    <view class="header-card">
      <text class="header-title">我的关注</text>
    </view>
    
    <!-- 搜索栏 -->
    <view class="search-section">
      <view class="search-container">
        <view class="search-icon">🔍</view>
        <input 
          class="search-input" 
          type="text" 
          placeholder="搜索"
          v-model="searchKeyword"
          @input="onSearchInput"
        />
      </view>
    </view>
    
    <!-- Follow Books 标题 -->
    <view class="section-header">
      <text class="section-title">Follow Books</text>
    </view>
    
    <!-- 书籍列表 -->
    <view class="books-section">
      <BookList 
        :books="followedBooks"
        :show-count="false"
        :show-rank="true"
        :show-actions="true"
        action-type="unfollow"
        empty-text="暂无关注的书籍"
        @book-tap="handleBookTap"
        @unfollow="handleUnfollow"
      />
    </view>
  </view>
</template>

<script>
import BookList from '@/components/BookList.vue'

/**
 * 关注页面
 * @description 展示用户关注的书籍列表，按照Figma设计样式
 */
export default {
  name: 'FollowPage',
  
  components: {
    BookList
  },
  
  data() {
    return {
      searchKeyword: '',
      followedBooks: []
    }
  },
  
  onLoad() {
    this.loadFollowedBooks()
  },
  
  onShow() {
    // 每次显示时刷新关注列表
    this.loadFollowedBooks()
  },
  
  // 下拉刷新
  onPullDownRefresh() {
    this.loadFollowedBooks().finally(() => {
      uni.stopPullDownRefresh()
    })
  },
  
  methods: {
    /**
     * 加载关注的书籍列表
     */
    async loadFollowedBooks() {
      try {
        // 这里应该调用API获取用户关注的书籍
        // const response = await this.$http.get('/api/user/followed-books')
        // this.followedBooks = response.data
        
        // 模拟数据
        this.followedBooks = Array.from({ length: 20 }, (_, index) => ({
          id: `book_${index + 1}`,
          title: '重生之农女',
          clicks: 193,
          collections: 34
        }))
        
        console.log('加载关注书籍列表:', this.followedBooks.length)
      } catch (error) {
        console.error('加载关注书籍失败:', error)
        uni.showToast({
          title: '加载失败',
          icon: 'none',
          duration: 2000
        })
      }
    },
    
    /**
     * 搜索输入
     */
    onSearchInput(e) {
      console.log('搜索关注书籍:', e.detail.value)
      // 这里可以实现搜索逻辑
      this.searchKeyword = e.detail.value
      // 可以添加防抖搜索功能
    },
    
    /**
     * 处理书籍点击（BookList组件事件）
     */
    handleBookTap({ book, index }) {
      this.goToBookDetail(book)
    },

    /**
     * 处理取消关注（BookList组件事件）
     */
    handleUnfollow({ book, index }) {
      this.unfollowBook(book)
    },

    /**
     * 跳转到书籍详情
     */
    goToBookDetail(book) {
      uni.navigateTo({
        url: `/pages/book/detail?id=${book.id}`
      })
    },
    
    /**
     * 取消关注书籍
     */
    async unfollowBook(book) {
      try {
        // 这里应该调用API取消关注
        // await this.$http.delete(`/api/user/follow/${book.id}`)
        
        // 从列表中移除
        const index = this.followedBooks.findIndex(item => item.id === book.id)
        if (index > -1) {
          this.followedBooks.splice(index, 1)
        }
        
        uni.showToast({
          title: '已取消关注',
          icon: 'success',
          duration: 1500
        })
      } catch (error) {
        console.error('取消关注失败:', error)
        uni.showToast({
          title: '操作失败',
          icon: 'none',
          duration: 2000
        })
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.follow-page {
  min-height: 100vh;
  background-color: #f4f0eb;
  padding-bottom: $safe-area-bottom;
}

.header-card {
  margin: 32rpx;
  background-color: #c3c3c3;
  border-radius: 16rpx;
  padding: 80rpx 40rpx;
  text-align: center;
  
  .header-title {
    font-size: 64rpx;
    font-weight: 600;
    color: #ffffff;
    font-family: 'Inter', sans-serif;
  }
}

.search-section {
  padding: 0 32rpx 32rpx;
  
  .search-container {
    display: flex;
    align-items: center;
    background-color: #ffffff;
    border-radius: 48rpx;
    padding: 0 32rpx;
    height: 96rpx;
    
    .search-icon {
      font-size: 32rpx;
      color: #999999;
      margin-right: 16rpx;
    }
    
    .search-input {
      flex: 1;
      font-size: 32rpx;
      color: #333333;
      
      &::placeholder {
        color: #999999;
      }
    }
  }
}

.section-header {
  padding: 0 32rpx 32rpx;
  
  .section-title {
    font-size: 36rpx;
    font-weight: 600;
    color: #000000;
    font-family: 'Inter', sans-serif;
  }
}

.books-section {
  padding: 0 32rpx;
  
  .books-list {
    .book-item {
      display: flex;
      align-items: center;
      background-color: #c3c3c3;
      border-radius: 16rpx;
      padding: 24rpx;
      margin-bottom: 16rpx;
      
      .book-rank {
        width: 48rpx;
        height: 48rpx;
        background-color: #999999;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24rpx;
        font-weight: 600;
        color: #ffffff;
        margin-right: 24rpx;
      }
      
      .book-info {
        flex: 1;
        
        .book-title {
          display: block;
          font-size: 32rpx;
          font-weight: 500;
          color: #333333;
          margin-bottom: 8rpx;
        }
        
        .book-stats {
          display: flex;
          gap: 24rpx;
          
          .book-stat {
            font-size: 24rpx;
            color: #666666;
          }
        }
      }
      
      &:active {
        opacity: 0.8;
      }
    }
  }
}
</style>
