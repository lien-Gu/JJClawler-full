<template>
  <view class="follow-page">
    <!-- 页面头部 -->
    <view class="page-header">
      <text class="page-title">我的关注</text>
      <view class="header-stats">
        <text class="stats-text">榜单 {{ followRankings.length }} · 书籍 {{ followBooks.length }}</text>
      </view>
    </view>
    
    <!-- 分类标签栏 -->
    <view class="category-tabs">
      <view 
        class="tab-item" 
        :class="{ 'active': activeTab === 'rankings' }"
        @tap="switchTab('rankings')"
      >
        <text class="tab-text">关注榜单</text>
        <view class="tab-badge" v-if="followRankings.length > 0">
          <text class="badge-text">{{ followRankings.length }}</text>
        </view>
      </view>
      <view 
        class="tab-item" 
        :class="{ 'active': activeTab === 'books' }"
        @tap="switchTab('books')"
      >
        <text class="tab-text">关注书籍</text>
        <view class="tab-badge" v-if="followBooks.length > 0">
          <text class="badge-text">{{ followBooks.length }}</text>
        </view>
      </view>
    </view>
    
    <!-- 榜单关注列表 -->
    <view class="rankings-content" v-if="activeTab === 'rankings'">
      <!-- 筛选和排序 -->
      <view class="content-header">
        <view class="filter-section">
          <view class="filter-item" @tap="showSiteFilter">
            <text class="filter-text">{{ selectedSite || '全部分站' }}</text>
            <text class="filter-arrow">▼</text>
          </view>
          <view class="filter-item" @tap="showSortOptions">
            <text class="filter-text">{{ sortLabels[sortBy] }}</text>
            <text class="filter-arrow">▼</text>
          </view>
        </view>
        <view class="action-section">
          <view class="batch-btn" @tap="toggleBatchMode" :class="{ 'active': batchMode }">
            <text class="batch-text">{{ batchMode ? '完成' : '管理' }}</text>
          </view>
        </view>
      </view>
      
      <!-- 榜单列表 -->
      <view class="rankings-list" v-if="filteredRankings.length > 0">
        <view 
          class="ranking-item" 
          :class="{ 'batch-mode': batchMode, 'selected': selectedRankings.includes(ranking.id) }"
          v-for="ranking in filteredRankings" 
          :key="ranking.id"
          @tap="handleRankingTap(ranking)"
        >
          <!-- 批量选择复选框 -->
          <view class="batch-checkbox" v-if="batchMode" @tap.stop="toggleRankingSelection(ranking.id)">
            <view class="checkbox" :class="{ 'checked': selectedRankings.includes(ranking.id) }">
              <text class="check-icon" v-if="selectedRankings.includes(ranking.id)">✓</text>
            </view>
          </view>
          
          <!-- 榜单卡片 -->
          <RankingCard 
            :ranking="ranking"
            :showActions="!batchMode"
            :showPreview="true"
            @click="goToRankingDetail"
            @follow="unfollowRanking"
          />
          
          <!-- 关注时间 -->
          <view class="follow-info">
            <text class="follow-time">关注于 {{ formatFollowTime(ranking.followTime) }}</text>
            <text class="update-status" v-if="ranking.hasUpdate">有更新</text>
          </view>
        </view>
      </view>
      
      <!-- 空状态 - 榜单 -->
      <view class="empty-state" v-else-if="!loadingRankings">
        <text class="empty-icon">📊</text>
        <text class="empty-title">还没有关注任何榜单</text>
        <text class="empty-desc">去榜单页面发现感兴趣的内容吧</text>
        <view class="empty-action" @tap="goToRankings">
          <text class="action-text">浏览榜单</text>
        </view>
      </view>
    </view>
    
    <!-- 书籍关注列表 -->
    <view class="books-content" v-if="activeTab === 'books'">
      <!-- 筛选和排序 -->
      <view class="content-header">
        <view class="filter-section">
          <view class="filter-item" @tap="showCategoryFilter">
            <text class="filter-text">{{ selectedCategory || '全部分类' }}</text>
            <text class="filter-arrow">▼</text>
          </view>
          <view class="filter-item" @tap="showBookSortOptions">
            <text class="filter-text">{{ bookSortLabels[bookSortBy] }}</text>
            <text class="filter-arrow">▼</text>
          </view>
        </view>
        <view class="action-section">
          <view class="batch-btn" @tap="toggleBookBatchMode" :class="{ 'active': bookBatchMode }">
            <text class="batch-text">{{ bookBatchMode ? '完成' : '管理' }}</text>
          </view>
        </view>
      </view>
      
      <!-- 书籍列表 -->
      <view class="books-list" v-if="filteredBooks.length > 0">
        <view 
          class="book-item" 
          :class="{ 'batch-mode': bookBatchMode, 'selected': selectedBooks.includes(book.id) }"
          v-for="book in filteredBooks" 
          :key="book.id"
          @tap="handleBookTap(book)"
        >
          <!-- 批量选择复选框 -->
          <view class="batch-checkbox" v-if="bookBatchMode" @tap.stop="toggleBookSelection(book.id)">
            <view class="checkbox" :class="{ 'checked': selectedBooks.includes(book.id) }">
              <text class="check-icon" v-if="selectedBooks.includes(book.id)">✓</text>
            </view>
          </view>
          
          <!-- 书籍卡片 -->
          <BookCard 
            :book="book"
            :showActions="!bookBatchMode"
            @click="goToBookDetail"
            @follow="unfollowBook"
          />
          
          <!-- 关注时间和更新状态 -->
          <view class="follow-info">
            <text class="follow-time">关注于 {{ formatFollowTime(book.followTime) }}</text>
            <text class="update-status" v-if="book.hasUpdate">有更新</text>
          </view>
        </view>
      </view>
      
      <!-- 空状态 - 书籍 -->
      <view class="empty-state" v-else-if="!loadingBooks">
        <text class="empty-icon">📖</text>
        <text class="empty-title">还没有关注任何书籍</text>
        <text class="empty-desc">去榜单中发现好书吧</text>
        <view class="empty-action" @tap="goToRankings">
          <text class="action-text">浏览榜单</text>
        </view>
      </view>
    </view>
    
    <!-- 批量操作栏 -->
    <view class="batch-actions" v-if="(batchMode && selectedRankings.length > 0) || (bookBatchMode && selectedBooks.length > 0)">
      <view class="batch-info">
        <text class="selected-count">
          已选择 {{ batchMode ? selectedRankings.length : selectedBooks.length }} 项
        </text>
      </view>
      <view class="batch-buttons">
        <view class="batch-btn cancel" @tap="clearSelection">
          <text class="btn-text">取消</text>
        </view>
        <view class="batch-btn confirm" @tap="batchUnfollow">
          <text class="btn-text">取消关注</text>
        </view>
      </view>
    </view>
    
    <!-- 加载状态 -->
    <view class="loading-state" v-if="loadingRankings || loadingBooks">
      <text class="loading-text">加载中...</text>
    </view>
    
    <!-- 筛选弹窗 -->
    <view class="filter-popup" v-if="showFilterPopup" @tap="hideFilterPopup">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="popup-title">{{ filterTitle }}</text>
          <view class="popup-close" @tap="hideFilterPopup">
            <text class="close-text">×</text>
          </view>
        </view>
        <scroll-view class="popup-scroll" scroll-y>
          <view class="filter-options">
            <view 
              class="filter-option" 
              :class="{ 'active': option.value === filterSelectedValue }"
              v-for="option in filterOptions" 
              :key="option.value"
              @tap="selectFilterOption(option)"
            >
              <text class="option-text">{{ option.label }}</text>
              <text class="option-check" v-if="option.value === filterSelectedValue">✓</text>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script>
import RankingCard from '@/components/RankingCard.vue'
import BookCard from '@/components/BookCard.vue'
import { get } from '@/utils/request.js'
import { getSync, setSync } from '@/utils/storage.js'

/**
 * 关注页面
 * @description 展示用户关注的榜单和书籍
 */
export default {
  name: 'FollowPage',
  components: {
    RankingCard,
    BookCard
  },
  
  data() {
    return {
      // 当前激活的标签页
      activeTab: 'rankings',
      
      // 关注的榜单列表
      followRankings: [],
      
      // 关注的书籍列表
      followBooks: [],
      
      // 筛选条件
      selectedSite: '',
      selectedCategory: '',
      
      // 排序方式
      sortBy: 'followTime',
      bookSortBy: 'followTime',
      
      // 排序标签映射
      sortLabels: {
        followTime: '关注时间',
        updateTime: '更新时间',
        name: '名称'
      },
      
      bookSortLabels: {
        followTime: '关注时间',
        updateTime: '更新时间',
        name: '书名',
        author: '作者'
      },
      
      // 批量操作模式
      batchMode: false,
      bookBatchMode: false,
      
      // 选中的项目
      selectedRankings: [],
      selectedBooks: [],
      
      // 筛选弹窗
      showFilterPopup: false,
      filterTitle: '',
      filterOptions: [],
      filterSelectedValue: '',
      filterType: '',
      
      // 加载状态
      loadingRankings: false,
      loadingBooks: false
    }
  },
  
  computed: {
    /**
     * 筛选后的榜单列表
     */
    filteredRankings() {
      let list = [...this.followRankings]
      
      // 分站筛选
      if (this.selectedSite) {
        list = list.filter(ranking => ranking.site === this.selectedSite)
      }
      
      // 排序
      list.sort((a, b) => {
        switch (this.sortBy) {
          case 'followTime':
            return new Date(b.followTime) - new Date(a.followTime)
          case 'updateTime':
            return new Date(b.updateTime || 0) - new Date(a.updateTime || 0)
          case 'name':
            return (a.name || '').localeCompare(b.name || '')
          default:
            return 0
        }
      })
      
      return list
    },
    
    /**
     * 筛选后的书籍列表
     */
    filteredBooks() {
      let list = [...this.followBooks]
      
      // 分类筛选
      if (this.selectedCategory) {
        list = list.filter(book => book.category === this.selectedCategory)
      }
      
      // 排序
      list.sort((a, b) => {
        switch (this.bookSortBy) {
          case 'followTime':
            return new Date(b.followTime) - new Date(a.followTime)
          case 'updateTime':
            return new Date(b.updateTime || 0) - new Date(a.updateTime || 0)
          case 'name':
            return (a.name || a.title || '').localeCompare(b.name || b.title || '')
          case 'author':
            return (a.author || '').localeCompare(b.author || '')
          default:
            return 0
        }
      })
      
      return list
    }
  },
  
  onLoad() {
    this.initData()
  },
  
  // 页面显示时刷新数据
  onShow() {
    this.refreshData()
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
      try {
        // 加载缓存数据
        this.loadCachedData()
        
        // 获取最新数据
        await this.fetchFollowData()
      } catch (error) {
        console.error('初始化数据失败:', error)
        this.showError('数据加载失败')
      }
    },
    
    /**
     * 加载缓存数据
     */
    loadCachedData() {
      const cachedRankings = getSync('follow_rankings')
      const cachedBooks = getSync('follow_books')
      
      if (cachedRankings) {
        this.followRankings = cachedRankings
      }
      
      if (cachedBooks) {
        this.followBooks = cachedBooks
      }
    },
    
    /**
     * 获取关注数据
     */
    async fetchFollowData() {
      this.loadingRankings = true
      this.loadingBooks = true
      
      try {
        const [rankingsData, booksData] = await Promise.all([
          get('/api/user/follows/rankings'),
          get('/api/user/follows/books')
        ])
        
        if (rankingsData && rankingsData.list) {
          this.followRankings = rankingsData.list
          setSync('follow_rankings', rankingsData.list, 15 * 60 * 1000) // 缓存15分钟
        }
        
        if (booksData && booksData.list) {
          this.followBooks = booksData.list
          setSync('follow_books', booksData.list, 15 * 60 * 1000) // 缓存15分钟
        }
      } catch (error) {
        console.error('获取关注数据失败:', error)
        throw error
      } finally {
        this.loadingRankings = false
        this.loadingBooks = false
      }
    },
    
    /**
     * 刷新数据
     */
    async refreshData() {
      try {
        await this.fetchFollowData()
        
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
     * 切换标签页
     */
    switchTab(tab) {
      this.activeTab = tab
      // 重置批量操作状态
      this.batchMode = false
      this.bookBatchMode = false
      this.selectedRankings = []
      this.selectedBooks = []
    },
    
    /**
     * 显示分站筛选
     */
    showSiteFilter() {
      const sites = [...new Set(this.followRankings.map(r => r.site).filter(Boolean))]
      
      this.filterTitle = '选择分站'
      this.filterOptions = [
        { label: '全部分站', value: '' },
        ...sites.map(site => ({ label: site, value: site }))
      ]
      this.filterSelectedValue = this.selectedSite
      this.filterType = 'site'
      this.showFilterPopup = true
    },
    
    /**
     * 显示分类筛选
     */
    showCategoryFilter() {
      const categories = [...new Set(this.followBooks.map(b => b.category).filter(Boolean))]
      
      this.filterTitle = '选择分类'
      this.filterOptions = [
        { label: '全部分类', value: '' },
        ...categories.map(category => ({ label: category, value: category }))
      ]
      this.filterSelectedValue = this.selectedCategory
      this.filterType = 'category'
      this.showFilterPopup = true
    },
    
    /**
     * 显示排序选项
     */
    showSortOptions() {
      this.filterTitle = '排序方式'
      this.filterOptions = Object.entries(this.sortLabels).map(([value, label]) => ({
        label,
        value
      }))
      this.filterSelectedValue = this.sortBy
      this.filterType = 'sort'
      this.showFilterPopup = true
    },
    
    /**
     * 显示书籍排序选项
     */
    showBookSortOptions() {
      this.filterTitle = '排序方式'
      this.filterOptions = Object.entries(this.bookSortLabels).map(([value, label]) => ({
        label,
        value
      }))
      this.filterSelectedValue = this.bookSortBy
      this.filterType = 'bookSort'
      this.showFilterPopup = true
    },
    
    /**
     * 选择筛选选项
     */
    selectFilterOption(option) {
      switch (this.filterType) {
        case 'site':
          this.selectedSite = option.value
          break
        case 'category':
          this.selectedCategory = option.value
          break
        case 'sort':
          this.sortBy = option.value
          break
        case 'bookSort':
          this.bookSortBy = option.value
          break
      }
      
      this.hideFilterPopup()
    },
    
    /**
     * 隐藏筛选弹窗
     */
    hideFilterPopup() {
      this.showFilterPopup = false
    },
    
    /**
     * 切换批量操作模式
     */
    toggleBatchMode() {
      this.batchMode = !this.batchMode
      if (!this.batchMode) {
        this.selectedRankings = []
      }
    },
    
    /**
     * 切换书籍批量操作模式
     */
    toggleBookBatchMode() {
      this.bookBatchMode = !this.bookBatchMode
      if (!this.bookBatchMode) {
        this.selectedBooks = []
      }
    },
    
    /**
     * 切换榜单选择状态
     */
    toggleRankingSelection(id) {
      const index = this.selectedRankings.indexOf(id)
      if (index > -1) {
        this.selectedRankings.splice(index, 1)
      } else {
        this.selectedRankings.push(id)
      }
    },
    
    /**
     * 切换书籍选择状态
     */
    toggleBookSelection(id) {
      const index = this.selectedBooks.indexOf(id)
      if (index > -1) {
        this.selectedBooks.splice(index, 1)
      } else {
        this.selectedBooks.push(id)
      }
    },
    
    /**
     * 处理榜单点击
     */
    handleRankingTap(ranking) {
      if (this.batchMode) {
        this.toggleRankingSelection(ranking.id)
      } else {
        this.goToRankingDetail(ranking)
      }
    },
    
    /**
     * 处理书籍点击
     */
    handleBookTap(book) {
      if (this.bookBatchMode) {
        this.toggleBookSelection(book.id)
      } else {
        this.goToBookDetail(book)
      }
    },
    
    /**
     * 清除选择
     */
    clearSelection() {
      this.selectedRankings = []
      this.selectedBooks = []
    },
    
    /**
     * 批量取消关注
     */
    async batchUnfollow() {
      const items = this.batchMode ? this.selectedRankings : this.selectedBooks
      const type = this.batchMode ? 'rankings' : 'books'
      
      if (items.length === 0) return
      
      try {
        uni.showLoading({ title: '处理中...' })
        
        await get(`/api/user/follows/${type}/batch`, {
          ids: items,
          action: 'unfollow'
        }, { method: 'POST' })
        
        // 更新本地数据
        if (this.batchMode) {
          this.followRankings = this.followRankings.filter(r => !items.includes(r.id))
        } else {
          this.followBooks = this.followBooks.filter(b => !items.includes(b.id))
        }
        
        // 重置选择状态
        this.clearSelection()
        this.batchMode = false
        this.bookBatchMode = false
        
        uni.showToast({
          title: '取消关注成功',
          icon: 'success'
        })
      } catch (error) {
        this.showError('操作失败')
      } finally {
        uni.hideLoading()
      }
    },
    
    /**
     * 取消关注榜单
     */
    async unfollowRanking(ranking) {
      try {
        await get(`/api/rankings/${ranking.id}/unfollow`, {}, { method: 'POST' })
        
        const index = this.followRankings.findIndex(r => r.id === ranking.id)
        if (index > -1) {
          this.followRankings.splice(index, 1)
        }
        
        uni.showToast({
          title: '取消关注成功',
          icon: 'success'
        })
      } catch (error) {
        this.showError('操作失败')
      }
    },
    
    /**
     * 取消关注书籍
     */
    async unfollowBook(book) {
      try {
        await get(`/api/books/${book.id}/unfollow`, {}, { method: 'POST' })
        
        const index = this.followBooks.findIndex(b => b.id === book.id)
        if (index > -1) {
          this.followBooks.splice(index, 1)
        }
        
        uni.showToast({
          title: '取消关注成功',
          icon: 'success'
        })
      } catch (error) {
        this.showError('操作失败')
      }
    },
    
    /**
     * 格式化关注时间
     */
    formatFollowTime(time) {
      if (!time) return '未知'
      
      const followTime = new Date(time)
      const now = new Date()
      const diff = now - followTime
      
      const days = Math.floor(diff / (1000 * 60 * 60 * 24))
      const hours = Math.floor(diff / (1000 * 60 * 60))
      
      if (days > 30) {
        return followTime.toLocaleDateString()
      } else if (days > 0) {
        return `${days}天前`
      } else if (hours > 0) {
        return `${hours}小时前`
      } else {
        return '刚刚'
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
      uni.navigateTo({
        url: `/pages/book/detail?id=${book.id}`
      })
    },
    
    /**
     * 跳转到榜单页面
     */
    goToRankings() {
      uni.switchTab({
        url: '/pages/ranking/index'
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.follow-page {
  min-height: 100vh;
  background-color: $page-background;
  padding-bottom: $safe-area-bottom;
}

.page-header {
  padding: $spacing-lg;
  background-color: white;
  border-bottom: 2rpx solid $border-light;
  
  .page-title {
    display: block;
    font-size: $font-size-xl;
    font-weight: bold;
    color: $text-primary;
    margin-bottom: $spacing-xs;
  }
  
  .header-stats {
    .stats-text {
      font-size: $font-size-sm;
      color: $text-secondary;
    }
  }
}

.category-tabs {
  @include flex-center;
  background-color: white;
  border-bottom: 2rpx solid $border-light;
  
  .tab-item {
    @include flex-center;
    flex: 1;
    padding: $spacing-md;
    position: relative;
    
    .tab-text {
      font-size: $font-size-md;
      color: $text-secondary;
      transition: color 0.3s ease;
    }
    
    .tab-badge {
      @include flex-center;
      background-color: $primary-color;
      border-radius: 20rpx;
      min-width: 32rpx;
      height: 32rpx;
      margin-left: $spacing-xs;
      
      .badge-text {
        font-size: 20rpx;
        color: white;
        padding: 0 8rpx;
      }
    }
    
    &.active {
      .tab-text {
        color: $primary-color;
        font-weight: bold;
      }
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 60rpx;
        height: 4rpx;
        background-color: $primary-color;
        border-radius: 2rpx;
      }
    }
    
    &:active {
      background-color: $background-color;
    }
  }
}

.rankings-content,
.books-content {
  flex: 1;
}

.content-header {
  @include flex-between;
  align-items: center;
  padding: $spacing-md $spacing-lg;
  background-color: white;
  border-bottom: 2rpx solid $border-light;
  
  .filter-section {
    @include flex-center;
    gap: $spacing-md;
  }
  
  .filter-item {
    @include flex-center;
    gap: $spacing-xs;
    padding: $spacing-xs $spacing-sm;
    background-color: $background-color;
    border-radius: $border-radius-medium;
    
    .filter-text {
      font-size: $font-size-sm;
      color: $text-secondary;
    }
    
    .filter-arrow {
      font-size: $font-size-xs;
      color: $text-placeholder;
      transition: transform 0.3s ease;
    }
    
    &:active {
      opacity: 0.7;
      
      .filter-arrow {
        transform: rotate(180deg);
      }
    }
  }
  
  .action-section {
    .batch-btn {
      @include flex-center;
      padding: $spacing-xs $spacing-md;
      border-radius: $border-radius-medium;
      background-color: $background-color;
      transition: all 0.3s ease;
      
      .batch-text {
        font-size: $font-size-sm;
        color: $text-secondary;
      }
      
      &.active {
        background-color: $primary-color;
        
        .batch-text {
          color: white;
        }
      }
      
      &:active {
        opacity: 0.7;
      }
    }
  }
}

.rankings-list,
.books-list {
  padding: $spacing-md;
}

.ranking-item,
.book-item {
  @include flex-center;
  gap: $spacing-md;
  background-color: white;
  border-radius: $border-radius-medium;
  margin-bottom: $spacing-md;
  overflow: hidden;
  transition: all 0.3s ease;
  
  &.batch-mode {
    padding-left: $spacing-md;
  }
  
  &.selected {
    border: 2rpx solid $primary-color;
    box-shadow: $shadow-medium;
  }
  
  .batch-checkbox {
    @include flex-center;
    
    .checkbox {
      @include flex-center;
      width: 40rpx;
      height: 40rpx;
      border: 2rpx solid $border-medium;
      border-radius: 50%;
      transition: all 0.3s ease;
      
      .check-icon {
        font-size: $font-size-sm;
        color: white;
      }
      
      &.checked {
        background-color: $primary-color;
        border-color: $primary-color;
      }
    }
  }
  
  .ranking-card,
  .book-card {
    flex: 1;
  }
  
  .follow-info {
    @include flex-column-center;
    align-items: flex-end;
    padding: $spacing-md;
    
    .follow-time {
      font-size: $font-size-xs;
      color: $text-placeholder;
      margin-bottom: 4rpx;
    }
    
    .update-status {
      font-size: $font-size-xs;
      color: $accent-color;
      background-color: rgba(255, 107, 53, 0.1);
      padding: 2rpx 8rpx;
      border-radius: 10rpx;
    }
  }
  
  &:active:not(.batch-mode) {
    opacity: 0.7;
  }
}

.empty-state {
  @include flex-column-center;
  padding: $spacing-xl;
  
  .empty-icon {
    font-size: 120rpx;
    margin-bottom: $spacing-lg;
  }
  
  .empty-title {
    font-size: $font-size-lg;
    color: $text-primary;
    margin-bottom: $spacing-xs;
  }
  
  .empty-desc {
    font-size: $font-size-md;
    color: $text-secondary;
    text-align: center;
    margin-bottom: $spacing-lg;
  }
  
  .empty-action {
    @include flex-center;
    padding: $spacing-md $spacing-xl;
    background-color: $primary-color;
    border-radius: $border-radius-medium;
    
    .action-text {
      font-size: $font-size-md;
      color: white;
    }
    
    &:active {
      opacity: 0.7;
    }
  }
}

.batch-actions {
  position: fixed;
  bottom: $safe-area-bottom;
  left: 0;
  right: 0;
  @include flex-between;
  align-items: center;
  padding: $spacing-md $spacing-lg;
  background-color: white;
  border-top: 2rpx solid $border-light;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.1);
  
  .batch-info {
    .selected-count {
      font-size: $font-size-md;
      color: $text-primary;
    }
  }
  
  .batch-buttons {
    @include flex-center;
    gap: $spacing-md;
    
    .batch-btn {
      @include flex-center;
      padding: $spacing-sm $spacing-lg;
      border-radius: $border-radius-medium;
      transition: all 0.3s ease;
      
      .btn-text {
        font-size: $font-size-md;
      }
      
      &.cancel {
        background-color: $background-color;
        
        .btn-text {
          color: $text-secondary;
        }
      }
      
      &.confirm {
        background-color: $accent-color;
        
        .btn-text {
          color: white;
        }
      }
      
      &:active {
        opacity: 0.7;
      }
    }
  }
}

.loading-state {
  @include flex-center;
  padding: $spacing-xl;
  
  .loading-text {
    font-size: $font-size-md;
    color: $text-placeholder;
  }
}

.filter-popup {
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
    max-height: 70vh;
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
    max-height: 50vh;
    
    .filter-options {
      padding: $spacing-md;
      
      .filter-option {
        @include flex-between;
        align-items: center;
        padding: $spacing-md;
        border-radius: $border-radius-medium;
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
          background-color: rgba(0, 122, 255, 0.1);
          
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
  }
}
</style>
