<template>
  <view class="book-detail-page">
    <!-- 书籍头部信息 -->
    <view class="book-header">
      <view class="header-bg"></view>
      <view class="header-content">
        <view class="book-cover-section">
          <view class="book-cover" v-if="bookData.cover">
            <image :src="bookData.cover" mode="aspectFit" class="cover-image" />
          </view>
          <view class="book-cover placeholder" v-else>
            <text class="cover-text">📖</text>
          </view>
        </view>
        
        <view class="book-info-section">
          <text class="book-title">{{ bookData.name || bookData.title || '书籍详情' }}</text>
          <text class="book-author" v-if="bookData.author">作者：{{ bookData.author }}</text>
          <view class="book-meta">
            <text class="meta-item" v-if="bookData.category">{{ bookData.category }}</text>
            <text class="meta-divider" v-if="bookData.category && bookData.status">·</text>
            <text class="meta-item" v-if="bookData.status">{{ bookData.status }}</text>
            <text class="meta-divider" v-if="bookData.status && bookData.wordCount">·</text>
            <text class="meta-item" v-if="bookData.wordCount">{{ formatWordCount(bookData.wordCount) }}字</text>
          </view>
          
          <view class="book-actions">
            <view class="action-btn follow-btn" :class="{ 'followed': bookData.isFollowed }" @tap="toggleFollow">
              <text class="btn-text">{{ bookData.isFollowed ? '已关注' : '关注' }}</text>
            </view>
            <view class="action-btn read-btn" @tap="readBook">
              <text class="btn-text">阅读</text>
            </view>
            <view class="action-btn share-btn" @tap="shareBook">
              <text class="btn-text">分享</text>
            </view>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 统计数据 -->
    <view class="stats-section">
      <view class="stats-grid">
        <view class="stat-item">
          <text class="stat-value">{{ formatNumber(bookData.readCount || 0) }}</text>
          <text class="stat-label">阅读量</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ formatNumber(bookData.collectCount || 0) }}</text>
          <text class="stat-label">收藏量</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ bookData.score || '暂无' }}</text>
          <text class="stat-label">评分</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ formatTime(bookData.updateTime) }}</text>
          <text class="stat-label">更新时间</text>
        </view>
      </view>
    </view>
    
    <!-- 书籍简介 -->
    <view class="description-section" v-if="bookData.description">
      <view class="section-header">
        <text class="section-title">作品简介</text>
      </view>
      <view class="description-content">
        <text class="description-text" :class="{ 'expanded': descriptionExpanded }">{{ bookData.description }}</text>
        <view class="expand-btn" @tap="toggleDescription" v-if="bookData.description && bookData.description.length > 100">
          <text class="expand-text">{{ descriptionExpanded ? '收起' : '展开' }}</text>
        </view>
      </view>
    </view>
    
    <!-- 标签信息 -->
    <view class="tags-section" v-if="bookData.tags && bookData.tags.length">
      <view class="section-header">
        <text class="section-title">作品标签</text>
      </view>
      <view class="tags-list">
        <text class="tag" v-for="tag in bookData.tags" :key="tag">{{ tag }}</text>
      </view>
    </view>
    
    <!-- 榜单历史 -->
    <view class="rankings-section">
      <view class="section-header">
        <text class="section-title">榜单历史</text>
        <text class="section-more" @tap="showAllRankings" v-if="rankingsList.length > 3">查看全部</text>
      </view>
      
      <view class="rankings-list" v-if="rankingsList.length > 0">
        <RankingCard 
          v-for="ranking in displayRankings" 
          :key="ranking.id"
          :ranking="ranking"
          :showActions="false"
          :showPreview="false"
          @click="goToRankingDetail"
        />
      </view>
      
      <!-- 空状态 -->
      <view class="empty-state" v-else-if="!loadingRankings">
        <text class="empty-icon">📊</text>
        <text class="empty-text">暂无榜单记录</text>
      </view>
      
      <!-- 加载状态 -->
      <view class="loading-state" v-if="loadingRankings">
        <text class="loading-text">加载中...</text>
      </view>
    </view>
    
    <!-- 相关推荐 -->
    <view class="recommendations-section" v-if="recommendedBooks.length > 0">
      <view class="section-header">
        <text class="section-title">相关推荐</text>
      </view>
      <scroll-view class="recommendations-scroll" scroll-x>
        <view class="recommendations-list">
          <view 
            class="recommendation-item" 
            v-for="book in recommendedBooks" 
            :key="book.id"
            @tap="goToBookDetail(book)"
          >
            <view class="rec-cover" v-if="book.cover">
              <image :src="book.cover" mode="aspectFit" class="rec-cover-image" />
            </view>
            <view class="rec-cover placeholder" v-else>
              <text class="rec-cover-text">📖</text>
            </view>
            <text class="rec-title">{{ book.name || book.title }}</text>
            <text class="rec-author" v-if="book.author">{{ book.author }}</text>
          </view>
        </view>
      </scroll-view>
    </view>
    
    <!-- 榜单历史详情弹窗 -->
    <view class="rankings-popup" v-if="showRankingsPopup" @tap="hideRankingsPopup">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="popup-title">完整榜单历史</text>
          <view class="popup-close" @tap="hideRankingsPopup">
            <text class="close-text">×</text>
          </view>
        </view>
        <scroll-view class="popup-scroll" scroll-y>
          <view class="popup-rankings">
            <RankingCard 
              v-for="ranking in rankingsList" 
              :key="ranking.id"
              :ranking="ranking"
              :showActions="false"
              :showPreview="false"
              @click="goToRankingDetail"
            />
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script>
import RankingCard from '@/components/RankingCard.vue'
import { get } from '@/utils/request.js'
import { getSync, setSync } from '@/utils/storage.js'

/**
 * 书籍详情页面
 * @description 展示书籍详细信息和历史榜单记录
 */
export default {
  name: 'BookDetailPage',
  components: {
    RankingCard
  },
  
  data() {
    return {
      // 书籍ID
      bookId: '',
      
      // 书籍数据
      bookData: {},
      
      // 榜单历史列表
      rankingsList: [],
      
      // 相关推荐书籍
      recommendedBooks: [],
      
      // 简介展开状态
      descriptionExpanded: false,
      
      // 榜单弹窗显示状态
      showRankingsPopup: false,
      
      // 加载状态
      loading: false,
      loadingRankings: false
    }
  },
  
  computed: {
    /**
     * 显示的榜单列表（前3个）
     */
    displayRankings() {
      return this.rankingsList.slice(0, 3)
    }
  },
  
  onLoad(options) {
    if (options.id) {
      this.bookId = options.id
      this.initData()
    }
  },
  
  // 下拉刷新
  onPullDownRefresh() {
    this.refreshData().finally(() => {
      uni.stopPullDownRefresh()
    })
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
          this.fetchBookInfo(),
          this.fetchRankingsHistory(),
          this.fetchRecommendations()
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
      const cachedBook = getSync(`book_${this.bookId}`)
      const cachedRankings = getSync(`book_rankings_${this.bookId}`)
      const cachedRecommendations = getSync(`book_recommendations_${this.bookId}`)
      
      if (cachedBook) {
        this.bookData = cachedBook
      }
      
      if (cachedRankings) {
        this.rankingsList = cachedRankings
      }
      
      if (cachedRecommendations) {
        this.recommendedBooks = cachedRecommendations
      }
    },
    
    /**
     * 获取书籍信息
     */
    async fetchBookInfo() {
      try {
        const data = await get(`/api/books/${this.bookId}`)
        if (data) {
          this.bookData = data
          setSync(`book_${this.bookId}`, data, 30 * 60 * 1000) // 缓存30分钟
        }
      } catch (error) {
        console.error('获取书籍信息失败:', error)
        throw error
      }
    },
    
    /**
     * 获取榜单历史
     */
    async fetchRankingsHistory() {
      this.loadingRankings = true
      
      try {
        const data = await get(`/api/books/${this.bookId}/rankings`)
        if (data && data.list) {
          this.rankingsList = data.list
          setSync(`book_rankings_${this.bookId}`, data.list, 15 * 60 * 1000) // 缓存15分钟
        }
      } catch (error) {
        console.error('获取榜单历史失败:', error)
        throw error
      } finally {
        this.loadingRankings = false
      }
    },
    
    /**
     * 获取相关推荐
     */
    async fetchRecommendations() {
      try {
        const data = await get(`/api/books/${this.bookId}/recommendations`, { limit: 8 })
        if (data && data.list) {
          this.recommendedBooks = data.list
          setSync(`book_recommendations_${this.bookId}`, data.list, 60 * 60 * 1000) // 缓存1小时
        }
      } catch (error) {
        console.error('获取相关推荐失败:', error)
        // 推荐失败不影响主要功能
      }
    },
    
    /**
     * 刷新数据
     */
    async refreshData() {
      try {
        await Promise.all([
          this.fetchBookInfo(),
          this.fetchRankingsHistory(),
          this.fetchRecommendations()
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
     * 切换关注状态
     */
    async toggleFollow() {
      try {
        const action = this.bookData.isFollowed ? 'unfollow' : 'follow'
        await get(`/api/books/${this.bookId}/${action}`, {}, { method: 'POST' })
        
        this.bookData.isFollowed = !this.bookData.isFollowed
        
        uni.showToast({
          title: this.bookData.isFollowed ? '关注成功' : '取消关注',
          icon: 'success',
          duration: 1500
        })
      } catch (error) {
        this.showError('操作失败')
      }
    },
    
    /**
     * 阅读书籍
     */
    readBook() {
      // 这里可以跳转到阅读页面或外部链接
      if (this.bookData.readUrl) {
        uni.navigateTo({
          url: `/pages/reader/index?bookId=${this.bookId}`
        })
      } else {
        uni.showToast({
          title: '阅读功能开发中',
          icon: 'none'
        })
      }
    },
    
    /**
     * 分享书籍
     */
    shareBook() {
      uni.share({
        provider: 'weixin',
        scene: 'WXSceneSession',
        type: 0,
        title: this.bookData.name || this.bookData.title,
        summary: `推荐一本好书：${this.bookData.author ? '作者 ' + this.bookData.author : ''}`,
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
     * 切换简介展开状态
     */
    toggleDescription() {
      this.descriptionExpanded = !this.descriptionExpanded
    },
    
    /**
     * 显示全部榜单
     */
    showAllRankings() {
      this.showRankingsPopup = true
    },
    
    /**
     * 隐藏榜单弹窗
     */
    hideRankingsPopup() {
      this.showRankingsPopup = false
    },
    
    /**
     * 格式化字数
     */
    formatWordCount(count) {
      if (typeof count !== 'number') return count || '0'
      
      if (count >= 10000) {
        return (count / 10000).toFixed(1) + '万'
      } else if (count >= 1000) {
        return (count / 1000).toFixed(1) + 'k'
      }
      
      return count.toString()
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
     * 跳转到榜单详情
     */
    goToRankingDetail(ranking) {
      uni.navigateTo({
        url: `/pages/ranking/detail?id=${ranking.id}`
      })
    },
    
    /**
     * 跳转到书籍详情
     */
    goToBookDetail(book) {
      if (book.id === this.bookId) return
      
      uni.redirectTo({
        url: `/pages/book/detail?id=${book.id}`
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.book-detail-page {
  min-height: 100vh;
  background-color: $page-background;
  padding-bottom: $safe-area-bottom;
}

.book-header {
  position: relative;
  padding: $spacing-lg;
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
    @include flex-center;
    align-items: flex-start;
    gap: $spacing-lg;
  }
  
  .book-cover-section {
    flex-shrink: 0;
    
    .book-cover {
      width: 200rpx;
      height: 280rpx;
      border-radius: $border-radius-medium;
      overflow: hidden;
      background-color: rgba(255, 255, 255, 0.1);
      @include flex-center;
      
      .cover-image {
        width: 100%;
        height: 100%;
      }
      
      &.placeholder {
        .cover-text {
          font-size: 60rpx;
          opacity: 0.7;
        }
      }
    }
  }
  
  .book-info-section {
    flex: 1;
    
    .book-title {
      display: block;
      font-size: $font-size-xl;
      font-weight: bold;
      margin-bottom: $spacing-xs;
      line-height: 1.3;
    }
    
    .book-author {
      display: block;
      font-size: $font-size-sm;
      opacity: 0.9;
      margin-bottom: $spacing-xs;
    }
    
    .book-meta {
      @include flex-center;
      gap: $spacing-xs;
      margin-bottom: $spacing-lg;
      
      .meta-item {
        font-size: $font-size-xs;
        opacity: 0.8;
      }
      
      .meta-divider {
        opacity: 0.6;
      }
    }
    
    .book-actions {
      @include flex-center;
      gap: $spacing-sm;
      
      .action-btn {
        @include flex-center;
        padding: $spacing-xs $spacing-md;
        border-radius: $border-radius-medium;
        transition: all 0.3s ease;
        
        .btn-text {
          font-size: $font-size-sm;
          color: white;
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
      }
      
      .read-btn {
        background-color: $accent-color;
      }
      
      .share-btn {
        background-color: transparent;
        border: 2rpx solid rgba(255, 255, 255, 0.3);
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

.description-section,
.tags-section,
.rankings-section,
.recommendations-section {
  background-color: white;
  margin-bottom: $spacing-sm;
  padding: $spacing-lg;
}

.section-header {
  @include flex-between;
  align-items: center;
  margin-bottom: $spacing-md;
  
  .section-title {
    font-size: $font-size-lg;
    font-weight: bold;
    color: $text-primary;
  }
  
  .section-more {
    font-size: $font-size-sm;
    color: $primary-color;
    
    &:active {
      opacity: 0.7;
    }
  }
}

.description-content {
  .description-text {
    display: block;
    font-size: $font-size-md;
    color: $text-primary;
    line-height: 1.6;
    
    &:not(.expanded) {
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  }
  
  .expand-btn {
    margin-top: $spacing-sm;
    
    .expand-text {
      color: $primary-color;
      font-size: $font-size-sm;
    }
    
    &:active {
      opacity: 0.7;
    }
  }
}

.tags-list {
  @include flex-center;
  gap: $spacing-sm;
  flex-wrap: wrap;
  
  .tag {
    padding: $spacing-xs $spacing-md;
    background-color: $background-color;
    border-radius: $border-radius-medium;
    font-size: $font-size-sm;
    color: $text-secondary;
  }
}

.rankings-list {
  .ranking-card {
    margin-bottom: $spacing-sm;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

.empty-state,
.loading-state {
  @include flex-column-center;
  padding: $spacing-xl;
  
  .empty-icon {
    font-size: 80rpx;
    margin-bottom: $spacing-md;
  }
  
  .empty-text,
  .loading-text {
    color: $text-placeholder;
    font-size: $font-size-md;
  }
}

.recommendations-scroll {
  white-space: nowrap;
  
  .recommendations-list {
    @include flex-center;
    gap: $spacing-md;
    padding-bottom: $spacing-xs;
  }
  
  .recommendation-item {
    @include flex-column-center;
    width: 160rpx;
    
    .rec-cover {
      width: 120rpx;
      height: 160rpx;
      border-radius: $border-radius-small;
      overflow: hidden;
      background-color: $background-color;
      @include flex-center;
      margin-bottom: $spacing-xs;
      
      .rec-cover-image {
        width: 100%;
        height: 100%;
      }
      
      &.placeholder {
        .rec-cover-text {
          font-size: 40rpx;
          color: $text-placeholder;
        }
      }
    }
    
    .rec-title {
      display: block;
      font-size: $font-size-sm;
      color: $text-primary;
      text-align: center;
      margin-bottom: 4rpx;
      @include text-ellipsis;
      width: 100%;
    }
    
    .rec-author {
      font-size: $font-size-xs;
      color: $text-secondary;
      text-align: center;
      @include text-ellipsis;
      width: 100%;
    }
    
    &:active {
      opacity: 0.7;
    }
  }
}

.rankings-popup {
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
    max-width: 700rpx;
    width: 100%;
    max-height: 80vh;
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
  
  .popup-scroll {
    max-height: 60vh;
    
    .popup-rankings {
      padding: $spacing-lg;
      
      .ranking-card {
        margin-bottom: $spacing-sm;
        
        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }
}
</style>
