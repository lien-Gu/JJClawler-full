<template>
  <view class="ranking-page">
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
    
    <!-- 第一层级：分站选择 -->
    <view class="sites-section">
      <scroll-view class="sites-scroll" scroll-x>
        <view class="sites-container">
          <view 
            class="site-tag"
            :class="{ active: selectedSite && selectedSite.id === site.id }"
            v-for="site in sites" 
            :key="site.id"
            @tap="selectSite(site)"
          >
            <text class="site-text">{{ site.name }}</text>
          </view>
        </view>
      </scroll-view>
    </view>
    
    <!-- 第二层级：频道选择（仅复杂分站显示） -->
    <view v-if="selectedSite && selectedSite.type === 'complex'" class="channels-section">
      <scroll-view class="channels-scroll" scroll-x>
        <view class="channels-container">
          <view 
            class="channel-tag"
            :class="{ active: selectedChannel && selectedChannel.id === channel.id }"
            v-for="channel in currentChannels" 
            :key="channel.id"
            @tap="selectChannel(channel)"
          >
            <text class="channel-text">{{ channel.name }}</text>
          </view>
        </view>
      </scroll-view>
    </view>
    
    <!-- 第三层级：内容显示 -->
    <view class="content-section">
      <!-- 夹子：显示书籍列表 -->
      <view v-if="selectedSite && selectedSite.id === 'jj' && level >= 2" class="books-section">
        <BookList 
          :books="books"
          :title="currentRankingTitle"
          :show-count="true"
          :show-rank="true"
          :show-actions="false"
          @book-tap="handleBookTap"
        />
      </view>
      
      <!-- 其他分站：显示榜单列表 -->
      <view v-else-if="selectedSite && level >= 2" class="rankings-section">
        <view class="rankings-list">
          <view 
            class="ranking-item" 
            v-for="ranking in currentRankings" 
            :key="ranking.id"
            @tap="goToRankingDetail(ranking)"
          >
            <text class="ranking-name">{{ ranking.name }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getSitesList, getSiteById, getChannelsBySiteId } from '@/data/url.js'
import BookList from '@/components/BookList.vue'

/**
 * 榜单页面
 * @description 多层级导航展示榜单和书籍信息，按照Figma设计样式
 */
export default {
  name: 'RankingPage',
  
  components: {
    BookList
  },
  
  data() {
    return {
      searchKeyword: '',
      sites: [],
      selectedSite: null,
      selectedChannel: null,
      currentChannels: [],
      currentRankings: [],
      books: [],
      level: 1, // 1: 分站选择, 2: 频道选择, 3: 内容显示
      currentRankingTitle: ''
    }
  },
  
  onLoad(options) {
    this.initData()
    
    // 处理外部传入的参数
    if (options.site) {
      const site = getSiteById(options.site)
      if (site) {
        this.selectSite(site)
      }
    } else {
      // 没有外部参数时，尝试恢复历史选择
      this.restoreLastSelection()
    }
  },
  
  methods: {
    /**
     * 初始化数据
     */
    initData() {
      try {
        this.sites = getSitesList()
        console.log('加载分站列表:', this.sites)
      } catch (error) {
        console.error('加载分站数据失败:', error)
        // 提供备用数据
        this.sites = [
          { id: 'jj', name: '夹子', type: 'special' },
          { id: 'shu', name: '书城', type: 'simple' },
          { id: 'yan', name: '言情', type: 'complex' }
        ]
      }
    },
    
    /**
     * 恢复上次选择的tab
     */
    restoreLastSelection() {
      try {
        const lastSelection = uni.getStorageSync('ranking_last_selection')
        if (lastSelection && lastSelection.siteId) {
          console.log('恢复历史选择:', lastSelection)
          const site = getSiteById(lastSelection.siteId)
          if (site) {
            this.selectSite(site, false) // 不保存历史，避免重复保存
            
            // 如果有频道选择历史，也恢复
            if (lastSelection.channelId && site.type === 'complex') {
              const channels = getChannelsBySiteId(site.id)
              const channel = channels.find(ch => ch.id === lastSelection.channelId)
              if (channel) {
                setTimeout(() => {
                  this.selectChannel(channel, false)
                }, 100)
              }
            }
            return
          }
        }
      } catch (error) {
        console.error('恢复历史选择失败:', error)
      }
      
      // 没有历史信息或恢复失败，默认选中夹子
      const jiaziSite = this.sites.find(site => site.id === 'jj')
      if (jiaziSite) {
        this.selectSite(jiaziSite)
      }
    },

    /**
     * 保存当前选择到历史
     */
    saveCurrentSelection() {
      try {
        const selection = {
          siteId: this.selectedSite?.id,
          channelId: this.selectedChannel?.id,
          timestamp: Date.now()
        }
        uni.setStorageSync('ranking_last_selection', selection)
        console.log('保存选择历史:', selection)
      } catch (error) {
        console.error('保存选择历史失败:', error)
      }
    },

    /**
     * 选择分站
     */
    selectSite(site, saveHistory = true) {
      this.selectedSite = site
      this.selectedChannel = null
      
      console.log('选择分站:', site)
      
      // 保存选择历史
      if (saveHistory) {
        this.saveCurrentSelection()
      }
      
      if (site.type === 'special' && site.id === 'jj') {
        // 夹子：直接在第一层级下方显示书籍列表
        this.level = 2
        this.currentRankingTitle = '夹子榜单'
        this.loadJiaziBooks()
      } else if (site.type === 'complex') {
        // 复杂分站：显示分站榜单 + 频道选择
        this.level = 2
        this.currentChannels = getChannelsBySiteId(site.id)
        this.loadSiteRankings(site)
      } else {
        // 简单分站：直接显示榜单
        this.level = 2
        this.loadSiteRankings(site)
      }
    },
    
    /**
     * 选择频道
     */
    selectChannel(channel, saveHistory = true) {
      this.selectedChannel = channel
      this.level = 3
      console.log('选择频道:', channel)
      
      // 保存选择历史
      if (saveHistory) {
        this.saveCurrentSelection()
      }
      
      this.loadChannelRankings(this.selectedSite, channel)
    },
    
    /**
     * 加载分站榜单
     */
    loadSiteRankings(site) {
      // 模拟分站榜单数据
      const siteRankings = {
        jj: [
          { id: 'jj_main', name: '夹子总榜', type: 'books' },
          { id: 'jj_rising', name: '夹子新星榜', type: 'books' },
          { id: 'jj_hot', name: '夹子热门榜', type: 'books' }
        ],
        shu: [
          { id: 'shu_hot', name: '热门榜' },
          { id: 'shu_new', name: '新书榜' },
          { id: 'shu_finish', name: '完结榜' }
        ],
        yan: [
          { id: 'yan_monthly', name: '月榜' },
          { id: 'yan_weekly', name: '周榜' },
          { id: 'yan_daily', name: '日榜' }
        ],
        chun: [
          { id: 'chun_popular', name: '人气榜' },
          { id: 'chun_recommend', name: '推荐榜' }
        ]
      }
      
      this.currentRankings = siteRankings[site.id] || [
        { id: `${site.id}_default`, name: '默认榜单' }
      ]
    },
    
    /**
     * 加载频道榜单
     */
    loadChannelRankings(site, channel) {
      // 模拟频道榜单数据
      this.currentRankings = [
        { id: `${site.id}_${channel.id}_hot`, name: `${channel.name}热门榜` },
        { id: `${site.id}_${channel.id}_new`, name: `${channel.name}新作榜` }
      ]
    },
    
    /**
     * 加载夹子书籍列表
     */
    loadJiaziBooks() {
      // 模拟夹子书籍数据
      this.books = Array.from({ length: 50 }, (_, index) => ({
        id: `book_${index + 1}`,
        title: `重生之农女${index + 1}`,
        collections: 193 + Math.floor(Math.random() * 1000),
        collectionChange: Math.floor(Math.random() * 100) - 50,
        rankChange: Math.floor(Math.random() * 10) - 5
      }))
    },
    
    /**
     * 搜索输入
     */
    onSearchInput(e) {
      console.log('搜索:', e.detail.value)
      // 这里可以实现搜索逻辑
    },
    
    /**
     * 跳转到榜单详情
     */
    goToRankingDetail(ranking) {
      // 如果是夹子榜单，直接在当前页面显示书籍列表
      if (ranking.type === 'books') {
        this.level = 3
        this.currentRankingTitle = ranking.name
        this.loadJiaziBooks()
        return
      }
      
      // 其他榜单跳转到详情页
      uni.navigateTo({
        url: `/pages/ranking/detail?id=${ranking.id}&name=${encodeURIComponent(ranking.name)}`
      })
    },
    
    /**
     * 处理书籍点击（BookList组件事件）
     */
    handleBookTap({ book, index }) {
      this.goToBookDetail(book)
    },

    /**
     * 跳转到书籍详情
     */
    goToBookDetail(book) {
      uni.navigateTo({
        url: `/pages/book/detail?id=${book.id}`
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.ranking-page {
  min-height: 100vh;
  background-color: #f4f0eb;
  padding-bottom: $safe-area-bottom;
}

.search-section {
  padding: 32rpx;
  
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

.sites-section {
  padding: 0 32rpx 32rpx;
  
  .sites-scroll {
    white-space: nowrap;
  }
  
  .sites-container {
    display: flex;
    gap: 16rpx;
    
    .site-tag {
      flex-shrink: 0;
      background-color: #c3c3c3;
      border-radius: 32rpx;
      padding: 16rpx 32rpx;
      
      .site-text {
        font-size: 28rpx;
        color: #333333;
        white-space: nowrap;
      }
      
      &.active {
        background-color: #64a347;
        
        .site-text {
          color: #ffffff;
          font-weight: 600;
        }
      }
    }
  }
}

.channels-section {
  padding: 0 32rpx 32rpx;
  
  .channels-scroll {
    white-space: nowrap;
  }
  
  .channels-container {
    display: flex;
    gap: 16rpx;
    
    .channel-tag {
      flex-shrink: 0;
      background-color: #e0e0e0;
      border-radius: 24rpx;
      padding: 12rpx 24rpx;
      
      .channel-text {
        font-size: 24rpx;
        color: #666666;
        white-space: nowrap;
      }
      
      &.active {
        background-color: #64a347;
        
        .channel-text {
          color: #ffffff;
          font-weight: 500;
        }
      }
    }
  }
}

.content-section {
  padding: 0 32rpx;
}

.books-section {
  .books-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32rpx;
    
    .books-title {
      font-size: 36rpx;
      font-weight: 600;
      color: #333333;
    }
    
    .books-count {
      font-size: 28rpx;
      color: #666666;
    }
  }
  
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
          align-items: center;
          gap: 24rpx;
          
          .book-collections {
            font-size: 24rpx;
            color: #666666;
          }
          
          .book-changes {
            display: flex;
            gap: 16rpx;
            
            .collection-change,
            .rank-change {
              font-size: 24rpx;
              font-weight: 500;
              
              &.positive {
                color: #34c759;
              }
              
              &.negative {
                color: #ff3b30;
              }
            }
          }
        }
      }
      
      &:active {
        opacity: 0.8;
      }
    }
  }
}

.rankings-section {
  .rankings-list {
    .ranking-item {
      background-color: #c3c3c3;
      border-radius: 16rpx;
      padding: 32rpx;
      margin-bottom: 16rpx;
      
      .ranking-name {
        font-size: 32rpx;
        font-weight: 500;
        color: #333333;
      }
      
      &:active {
        opacity: 0.8;
      }
    }
  }
}
</style> 