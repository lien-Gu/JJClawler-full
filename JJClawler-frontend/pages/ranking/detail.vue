<template>
  <view class="ranking-detail-page">
    <!-- 榜单头部信息 -->
    <view class="ranking-header">
      <view class="header-bg"></view>
      <view class="header-content">
        <view class="ranking-info">
          <text class="ranking-title">{{ rankingData.name || '榜单详情' }}</text>
          <text class="ranking-desc" v-if="rankingData.description">{{ rankingData.description }}</text>
          <view class="ranking-meta">
            <text class="meta-item">{{ rankingData.siteName }}</text>
            <text class="meta-divider">·</text>
            <text class="meta-item">{{ rankingData.channelName }}</text>
            <text class="meta-divider">·</text>
            <text class="meta-item">{{ formatTime(rankingData.updateTime) }}</text>
          </view>
        </view>
        
        <view class="ranking-actions">
          <view class="action-btn follow-btn" :class="{ 'followed': rankingData.isFollowed }" @tap="toggleFollow">
            <text class="btn-text">{{ rankingData.isFollowed ? '已关注' : '关注' }}</text>
          </view>
          <view class="action-btn share-btn" @tap="shareRanking">
            <text class="btn-text">分享</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 统计数据 -->
    <view class="stats-section">
      <view class="stats-grid">
        <view class="stat-item">
          <text class="stat-value">{{ rankingData.bookCount || 0 }}</text>
          <text class="stat-label">书籍总数</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ formatNumber(rankingData.totalViews || 0) }}</text>
          <text class="stat-label">总浏览量</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ rankingData.updateFrequency || '每日' }}</text>
          <text class="stat-label">更新频率</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ rankingData.followCount || 0 }}</text>
          <text class="stat-label">关注人数</text>
        </view>
      </view>
    </view>
    
    <!-- 筛选和排序 -->
    <view class="filter-section">
      <scroll-view class="filter-scroll" scroll-x>
        <view class="filter-list">
          <view 
            class="filter-item" 
            :class="{ 'active': currentFilter === filter.key }"
            v-for="filter in filterOptions" 
            :key="filter.key"
            @tap="changeFilter(filter.key)"
          >
            <text class="filter-text">{{ filter.name }}</text>
          </view>
        </view>
      </scroll-view>
      
      <view class="sort-btn" @tap="showSortOptions">
        <text class="sort-text">{{ currentSortName }}</text>
        <text class="sort-icon">▼</text>
      </view>
    </view>
    
    <!-- 书籍列表 -->
    <view class="books-section">
      <view class="books-list">
        <BookCard 
          v-for="(book, index) in booksList" 
          :key="book.id"
          :book="{ ...book, rank: index + 1 + (currentPage - 1) * pageSize }"
          :showRankings="false"
          :showActions="true"
          @click="goToBookDetail"
          @follow="onBookFollow"
          @read="onBookRead"
          @share="onBookShare"
        />
      </view>
      
      <!-- 加载更多 -->
      <view class="load-more" v-if="hasMore">
        <view class="load-btn" @tap="loadMore" v-if="!loadingMore">
          <text class="load-text">加载更多</text>
        </view>
        <view class="loading" v-else>
          <text class="loading-text">加载中...</text>
        </view>
      </view>
      
      <!-- 无更多数据 -->
      <view class="no-more" v-else-if="booksList.length > 0">
        <text class="no-more-text">没有更多数据了</text>
      </view>
      
      <!-- 空状态 -->
      <view class="empty-state" v-if="!loading && booksList.length === 0">
        <text class="empty-icon">📚</text>
        <text class="empty-text">暂无书籍数据</text>
        <view class="empty-btn" @tap="refreshData">
          <text class="btn-text">重新加载</text>
        </view>
      </view>
    </view>
    
    <!-- 排序选择弹窗 -->
    <view class="sort-popup" v-if="showSortPopup" @tap="hideSortOptions">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="popup-title">选择排序方式</text>
          <view class="popup-close" @tap="hideSortOptions">
            <text class="close-text">×</text>
          </view>
        </view>
        <view class="sort-options">
          <view 
            class="sort-option" 
            :class="{ 'active': currentSort === option.key }"
            v-for="option in sortOptions" 
            :key="option.key"
            @tap="changeSort(option.key)"
          >
            <text class="option-text">{{ option.name }}</text>
            <text class="option-check" v-if="currentSort === option.key">✓</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import BookCard from '@/components/BookCard.vue'
import { get } from '@/utils/request.js'
import { getSync, setSync } from '@/utils/storage.js'

/**
 * 榜单详情页面
 * @description 展示榜单统计信息和书籍列表
 */
export default {
  name: 'RankingDetailPage',
  components: {
    BookCard
  },
  
  data() {
    return {
      // 榜单ID
      rankingId: '',
      
      // 榜单数据
      rankingData: {},
      
      // 书籍列表
      booksList: [],
      
      // 分页信息
      currentPage: 1,
      pageSize: 20,
      hasMore: true,
      
      // 筛选选项
      filterOptions: [
        { key: 'all', name: '全部' },
        { key: 'completed', name: '已完结' },
        { key: 'ongoing', name: '连载中' },
        { key: 'new', name: '新书' }
      ],
      currentFilter: 'all',
      
      // 排序选项
      sortOptions: [
        { key: 'rank', name: '榜单排名' },
        { key: 'updateTime', name: '最近更新' },
        { key: 'wordCount', name: '字数排序' },
        { key: 'score', name: '评分排序' }
      ],
      currentSort: 'rank',
      showSortPopup: false,
      
      // 加载状态
      loading: false,
      loadingMore: false
    }
  },
  
  computed: {
    /**
     * 当前排序名称
     */
    currentSortName() {
      const option = this.sortOptions.find(item => item.key === this.currentSort)
      return option ? option.name : '榜单排名'
    }
  },
  
  onLoad(options) {
    if (options.id) {
      this.rankingId = options.id
      this.initData()
    }
  },
  
  // 下拉刷新
  onPullDownRefresh() {
    this.refreshData().finally(() => {
      uni.stopPullDownRefresh()
    })
  },
  
  // 上拉加载更多
  onReachBottom() {
    if (this.hasMore && !this.loadingMore) {
      this.loadMore()
    }
  },
  
  methods: {
    /**
     * 初始化数据
     */
    async initData() {
      this.loading = true
      
      try {
        // 加载缓存数据
        this.loadCachedData()
        
        // 获取最新数据
        await Promise.all([
          this.fetchRankingInfo(),
          this.fetchBooksList(true)
        ])
      } catch (error) {
        console.error('初始化数据失败:', error)
        this.showError('数据加载失败')
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 加载缓存数据
     */
    loadCachedData() {
      const cachedRanking = getSync(`ranking_${this.rankingId}`)
      const cachedBooks = getSync(`ranking_books_${this.rankingId}`)
      
      if (cachedRanking) {
        this.rankingData = cachedRanking
      }
      
      if (cachedBooks) {
        this.booksList = cachedBooks
      }
    },
    
    /**
     * 获取榜单信息
     */
    async fetchRankingInfo() {
      try {
        const data = await get(`/api/rankings/${this.rankingId}`)
        if (data) {
          this.rankingData = data
          setSync(`ranking_${this.rankingId}`, data, 30 * 60 * 1000) // 缓存30分钟
        }
      } catch (error) {
        console.error('获取榜单信息失败:', error)
        throw error
      }
    },
    
    /**
     * 获取书籍列表
     */
    async fetchBooksList(reset = false) {
      try {
        if (reset) {
          this.currentPage = 1
          this.hasMore = true
        }
        
        const params = {
          page: this.currentPage,
          pageSize: this.pageSize,
          filter: this.currentFilter,
          sort: this.currentSort
        }
        
        const data = await get(`/api/rankings/${this.rankingId}/books`, params)
        
        if (data && data.list) {
          if (reset) {
            this.booksList = data.list
          } else {
            this.booksList.push(...data.list)
          }
          
          this.hasMore = data.hasMore || false
          this.currentPage++
          
          // 缓存第一页数据
          if (reset) {
            setSync(`ranking_books_${this.rankingId}`, data.list, 15 * 60 * 1000) // 缓存15分钟
          }
        }
      } catch (error) {
        console.error('获取书籍列表失败:', error)
        throw error
      }
    },
    
    /**
     * 刷新数据
     */
    async refreshData() {
      try {
        await Promise.all([
          this.fetchRankingInfo(),
          this.fetchBooksList(true)
        ])
        
        uni.showToast({
          title: '刷新成功',
          icon: 'success',
          duration: 1500
        })
      } catch (error) {
        this.showError('刷新失败')
      }
    },
    
    /**
     * 加载更多
     */
    async loadMore() {
      if (this.loadingMore || !this.hasMore) return
      
      this.loadingMore = true
      
      try {
        await this.fetchBooksList()
      } catch (error) {
        this.showError('加载失败')
      } finally {
        this.loadingMore = false
      }
    },
    
    /**
     * 切换筛选条件
     */
    changeFilter(filterKey) {
      if (this.currentFilter === filterKey) return
      
      this.currentFilter = filterKey
      this.fetchBooksList(true)
    },
    
    /**
     * 显示排序选项
     */
    showSortOptions() {
      this.showSortPopup = true
    },
    
    /**
     * 隐藏排序选项
     */
    hideSortOptions() {
      this.showSortPopup = false
    },
    
    /**
     * 切换排序方式
     */
    changeSort(sortKey) {
      if (this.currentSort === sortKey) {
        this.hideSortOptions()
        return
      }
      
      this.currentSort = sortKey
      this.hideSortOptions()
      this.fetchBooksList(true)
    },
    
    /**
     * 切换关注状态
     */
    async toggleFollow() {
      try {
        const action = this.rankingData.isFollowed ? 'unfollow' : 'follow'
        await get(`/api/rankings/${this.rankingId}/${action}`, {}, { method: 'POST' })
        
        this.rankingData.isFollowed = !this.rankingData.isFollowed
        
        uni.showToast({
          title: this.rankingData.isFollowed ? '关注成功' : '取消关注',
          icon: 'success',
          duration: 1500
        })
      } catch (error) {
        this.showError('操作失败')
      }
    },
    
    /**
     * 分享榜单
     */
    shareRanking() {
      uni.share({
        provider: 'weixin',
        scene: 'WXSceneSession',
        type: 0,
        title: this.rankingData.name,
        summary: this.rankingData.description || '来看看这个热门榜单',
        success: () => {
          uni.showToast({
            title: '分享成功',
            icon: 'success'
          })
        },
        fail: () => {
          this.showError('分享失败')
        }
      })
    },
    
    /**
     * 格式化数字
     */
    formatNumber(num) {
      if (typeof num !== 'number') return num || '0'
      
      if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k'
      }
      
      return num.toString()
    },
    
    /**
     * 格式化时间
     */
    formatTime(time) {
      if (!time) return '未知'
      
      const now = new Date()
      const updateTime = new Date(time)
      const diff = now - updateTime
      
      const hours = Math.floor(diff / (1000 * 60 * 60))
      const days = Math.floor(diff / (1000 * 60 * 60 * 24))
      
      if (hours < 24) {
        return `${hours}小时前`
      } else if (days < 7) {
        return `${days}天前`
      } else {
        return updateTime.toLocaleDateString()
      }
    },
    
    /**
     * 显示错误提示
     */
    showError(message) {
      uni.showToast({
        title: message,
        icon: 'none',
        duration: 2000
      })
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
     * 书籍关注事件
     */
    async onBookFollow(event) {
      try {
        const { book, isFollowed } = event
        const action = isFollowed ? 'follow' : 'unfollow'
        
        await get(`/api/books/${book.id}/${action}`, {}, { method: 'POST' })
        
        // 更新本地状态
        const bookIndex = this.booksList.findIndex(item => item.id === book.id)
        if (bookIndex !== -1) {
          this.booksList[bookIndex].isFollowed = isFollowed
        }
        
        uni.showToast({
          title: isFollowed ? '关注成功' : '取消关注',
          icon: 'success',
          duration: 1500
        })
      } catch (error) {
        this.showError('操作失败')
      }
    },
    
    /**
     * 书籍阅读事件
     */
    onBookRead(book) {
      // 这里可以跳转到阅读页面或外部链接
      console.log('阅读书籍:', book)
      uni.showToast({
        title: '功能开发中',
        icon: 'none'
      })
    },
    
    /**
     * 书籍分享事件
     */
    onBookShare(book) {
      uni.share({
        provider: 'weixin',
        scene: 'WXSceneSession',
        type: 0,
        title: book.name || book.title,
        summary: `推荐一本好书：${book.author ? '作者 ' + book.author : ''}`,
        success: () => {
          uni.showToast({
            title: '分享成功',
            icon: 'success'
          })
        },
        fail: () => {
          this.showError('分享失败')
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.ranking-detail-page {
  min-height: 100vh;
  background-color: $page-background;
  padding-bottom: $safe-area-bottom;
}

.ranking-header {
  position: relative;
  padding: $spacing-lg $spacing-lg $spacing-xl;
  color: white;
  overflow: hidden;
  
  .header-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, $primary-color, $secondary-color);
    z-index: -1;
  }
  
  .header-content {
    @include flex-between;
    align-items: flex-start;
  }
  
  .ranking-info {
    flex: 1;
    margin-right: $spacing-md;
    
    .ranking-title {
      display: block;
      font-size: $font-size-xl;
      font-weight: bold;
      margin-bottom: $spacing-xs;
      line-height: 1.3;
    }
    
    .ranking-desc {
      display: block;
      font-size: $font-size-sm;
      opacity: 0.9;
      margin-bottom: $spacing-sm;
      line-height: 1.4;
    }
    
    .ranking-meta {
      @include flex-center;
      gap: $spacing-xs;
      
      .meta-item {
        font-size: $font-size-xs;
        opacity: 0.8;
      }
      
      .meta-divider {
        opacity: 0.6;
      }
    }
  }
  
  .ranking-actions {
    @include flex-center;
    gap: $spacing-sm;
    
    .action-btn {
      @include flex-center;
      padding: $spacing-xs $spacing-md;
      border-radius: $border-radius-medium;
      transition: all 0.3s ease;
      
      .btn-text {
        font-size: $font-size-sm;
      }
      
      &:active {
        opacity: 0.7;
      }
    }
    
    .follow-btn {
      background-color: rgba(255, 255, 255, 0.2);
      
      &.followed {
        background-color: rgba(255, 255, 255, 0.3);
      }
      
      .btn-text {
        color: white;
      }
    }
    
    .share-btn {
      background-color: transparent;
      border: 2rpx solid rgba(255, 255, 255, 0.3);
      
      .btn-text {
        color: white;
      }
    }
  }
}

.stats-section {
  padding: $spacing-lg;
  background-color: white;
  margin-bottom: $spacing-sm;
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: $spacing-md;
    
    .stat-item {
      @include flex-column-center;
      
      .stat-value {
        font-size: $font-size-lg;
        font-weight: bold;
        color: $primary-color;
        margin-bottom: 4rpx;
      }
      
      .stat-label {
        font-size: $font-size-xs;
        color: $text-secondary;
      }
    }
  }
}

.filter-section {
  @include flex-between;
  align-items: center;
  padding: $spacing-md $spacing-lg;
  background-color: white;
  margin-bottom: $spacing-sm;
  
  .filter-scroll {
    flex: 1;
    margin-right: $spacing-md;
  }
  
  .filter-list {
    @include flex-center;
    gap: $spacing-md;
    white-space: nowrap;
    
    .filter-item {
      padding: $spacing-xs $spacing-md;
      border-radius: $border-radius-medium;
      transition: all 0.3s ease;
      
      .filter-text {
        font-size: $font-size-sm;
        color: $text-secondary;
      }
      
      &.active {
        background-color: $primary-color;
        
        .filter-text {
          color: white;
        }
      }
    }
  }
  
  .sort-btn {
    @include flex-center;
    gap: 4rpx;
    padding: $spacing-xs $spacing-sm;
    border: 2rpx solid $border-medium;
    border-radius: $border-radius-medium;
    
    .sort-text {
      font-size: $font-size-sm;
      color: $text-primary;
    }
    
    .sort-icon {
      font-size: $font-size-xs;
      color: $text-placeholder;
      transition: transform 0.3s ease;
    }
    
    &:active {
      background-color: $background-color;
    }
  }
}

.books-section {
  .books-list {
    padding: 0 $spacing-lg;
  }
  
  .load-more {
    padding: $spacing-lg;
    
    .load-btn {
      @include flex-center;
      padding: $spacing-md;
      background-color: white;
      border-radius: $border-radius-medium;
      
      .load-text {
        color: $primary-color;
        font-size: $font-size-sm;
      }
      
      &:active {
        background-color: $background-color;
      }
    }
    
    .loading {
      @include flex-center;
      padding: $spacing-md;
      
      .loading-text {
        color: $text-placeholder;
        font-size: $font-size-sm;
      }
    }
  }
  
  .no-more {
    @include flex-center;
    padding: $spacing-lg;
    
    .no-more-text {
      color: $text-placeholder;
      font-size: $font-size-sm;
    }
  }
  
  .empty-state {
    @include flex-column-center;
    padding: $spacing-xl;
    
    .empty-icon {
      font-size: 80rpx;
      margin-bottom: $spacing-md;
    }
    
    .empty-text {
      color: $text-placeholder;
      font-size: $font-size-md;
      margin-bottom: $spacing-lg;
    }
    
    .empty-btn {
      @include flex-center;
      padding: $spacing-sm $spacing-lg;
      background-color: $primary-color;
      border-radius: $border-radius-medium;
      
      .btn-text {
        color: white;
        font-size: $font-size-sm;
      }
      
      &:active {
        opacity: 0.8;
      }
    }
  }
}

.sort-popup {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  @include flex-center;
  z-index: 1000;
  
  .popup-content {
    background-color: white;
    border-radius: $border-radius-large;
    margin: $spacing-lg;
    max-width: 600rpx;
    width: 100%;
    max-height: 60vh;
    overflow: hidden;
  }
  
  .popup-header {
    @include flex-between;
    align-items: center;
    padding: $spacing-lg;
    border-bottom: 2rpx solid $border-light;
    
    .popup-title {
      font-size: $font-size-lg;
      font-weight: bold;
      color: $text-primary;
    }
    
    .popup-close {
      @include flex-center;
      width: 60rpx;
      height: 60rpx;
      border-radius: 50%;
      
      .close-text {
        font-size: $font-size-xl;
        color: $text-placeholder;
      }
      
      &:active {
        background-color: $background-color;
      }
    }
  }
  
  .sort-options {
    max-height: 50vh;
    overflow-y: auto;
  }
  
  .sort-option {
    @include flex-between;
    align-items: center;
    padding: $spacing-lg;
    transition: background-color 0.3s ease;
    
    .option-text {
      font-size: $font-size-md;
      color: $text-primary;
    }
    
    .option-check {
      font-size: $font-size-lg;
      color: $primary-color;
    }
    
    &.active {
      background-color: $background-color;
      
      .option-text {
        color: $primary-color;
        font-weight: bold;
      }
    }
    
    &:active {
      background-color: $background-color;
    }
  }
}
</style> 