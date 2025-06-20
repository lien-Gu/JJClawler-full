<template>
  <view class="ranking-container">
    <!-- 搜索栏 -->
    <view class="search-section">
      <input 
        class="search-input" 
        placeholder="搜索榜单或书籍"
        v-model="searchKeyword"
        @input="onSearch"
      />
    </view>

    <!-- 面包屑导航 -->
    <view class="breadcrumb" v-if="selectedSite">
      <text class="breadcrumb-item" @tap="resetToSiteLevel">{{ currentSite.name }}</text>
      <text class="breadcrumb-separator" v-if="selectedChannel"> > </text>
      <text class="breadcrumb-item" v-if="selectedChannel" @tap="resetToChannelLevel">{{ currentChannel.name }}</text>
    </view>

    <!-- 第一层级: 分站选择 - 始终显示 -->
    <view class="level-container">
      <scroll-view class="site-scroll" scroll-x="true">
        <view class="site-tabs">
          <view 
            class="site-tab"
            :class="{ active: selectedSite === site.id }"
            v-for="site in sites" 
            :key="site.id"
            @tap="selectSite(site)"
          >
            {{ site.name }}
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- 第二层级: 频道选择 - 当选中分站有子频道时显示 -->
    <view class="level-container" v-if="showChannelLevel">
      <scroll-view class="channel-scroll" scroll-x="true">
        <view class="channel-tabs">
          <view 
            class="channel-tab"
            :class="{ active: selectedChannel === channel.id }"
            v-for="channel in currentSite.channels" 
            :key="channel.id"
            @tap="selectChannel(channel)"
          >
            {{ channel.name }}
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- 第三层级: 内容展示区域 -->
    <view class="content-container" v-if="showContentLevel">
      
      <!-- 夹子特殊处理：显示书籍列表 -->
      <view v-if="currentSite.type === 'special'" class="book-list-container">
        <view class="section-header">
          <text class="section-title">夹子榜单</text>
          <button class="detail-btn" @tap="goToJiaziDetail">查看详情</button>
        </view>
        
        <scroll-view class="book-list" scroll-y="true">
          <view 
            class="book-item"
            v-for="(book, index) in bookList" 
            :key="book.id"
          >
            <view class="book-rank">{{ index + 1 }}</view>
            <view class="book-info">
              <view class="book-title">{{ book.title }}</view>
              <view class="book-stats">
                <text class="stat-item">
                  收藏: {{ book.collections }}
                  <text class="change-indicator" :class="book.collectionChange > 0 ? 'up' : 'down'">
                    {{ book.collectionChange > 0 ? '↑' : '↓' }}{{ Math.abs(book.collectionChange) }}
                  </text>
                </text>
                <text class="stat-item">
                  排名变化: 
                  <text class="change-indicator" :class="book.rankChange > 0 ? 'down' : 'up'">
                    {{ book.rankChange > 0 ? '↓' : '↑' }}{{ Math.abs(book.rankChange) }}
                  </text>
                </text>
              </view>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 普通榜单：显示榜单列表 -->
      <view v-else class="ranking-list-container">
        <scroll-view class="ranking-list" scroll-y="true">
          <view 
            class="ranking-card"
            v-for="ranking in rankingList" 
            :key="ranking.id"
            @tap="goToRankingDetail(ranking)"
          >
            <view class="ranking-title">{{ ranking.name }}</view>
            <view class="ranking-desc">{{ ranking.desc }}</view>
            <view class="ranking-stats">
              <text class="stat-item">{{ ranking.bookCount }} 本书籍</text>
              <text class="stat-item">{{ ranking.updateTime }}</text>
            </view>
          </view>
        </scroll-view>
      </view>
      
    </view>
  </view>
</template>

<script>
import { getSitesList } from '@/data/url.js'

export default {
  data() {
    return {
      searchKeyword: '',
      selectedSite: '',
      selectedChannel: '',
      currentSite: {},
      currentChannel: {},
      sites: [],
      rankingList: [],
      bookList: [] // 夹子榜单的书籍列表
    }
  },
  
  computed: {
    // 是否显示频道选择层级
    showChannelLevel() {
      return this.selectedSite && 
             this.currentSite.type === 'complex' && 
             this.currentSite.channels && 
             this.currentSite.channels.length > 0
    },
    
    // 是否显示内容层级
    showContentLevel() {
      if (!this.selectedSite) return false
      
      // 夹子：选中即显示
      if (this.currentSite.type === 'special') {
        return true
      }
      
      // 简单榜单：选中即显示
      if (this.currentSite.type === 'simple') {
        return true
      }
      
      // 复杂榜单：需要选中频道才显示
      if (this.currentSite.type === 'complex') {
        return this.selectedChannel !== ''
      }
      
      return false
    }
  },
  
  onLoad() {
    this.loadSites()
  },
  
  methods: {
    /**
     * 加载分站数据
     */
    loadSites() {
      try {
        // 从本地数据文件加载
        this.sites = getSitesList()
        console.log('分站数据加载成功:', this.sites)
      } catch (error) {
        console.error('加载分站数据失败:', error)
      }
    },
    
    /**
     * 选择分站
     */
    selectSite(site) {
      this.selectedSite = site.id
      this.currentSite = site
      
      // 清空频道选择
      this.selectedChannel = ''
      this.currentChannel = {}
      
      // 根据分站类型加载对应内容
      if (site.type === 'special') {
        // 夹子：加载书籍列表
        this.loadBookList(site.id)
      } else if (site.type === 'simple') {
        // 简单榜单：加载榜单列表
        this.loadRankings(site.id)
      }
      // 复杂榜单：等待用户选择频道
    },
    
    /**
     * 选择频道
     */
    selectChannel(channel) {
      this.selectedChannel = channel.id
      this.currentChannel = channel
      
      // 加载频道对应的榜单
      this.loadRankings(this.selectedSite, channel.id)
    },
    
    /**
     * 重置到分站层级
     */
    resetToSiteLevel() {
      this.selectedChannel = ''
      this.currentChannel = {}
      
      // 重新加载分站内容
      if (this.currentSite.type === 'special') {
        this.loadBookList(this.selectedSite)
      } else if (this.currentSite.type === 'simple') {
        this.loadRankings(this.selectedSite)
      }
    },
    
    /**
     * 重置到频道层级
     */
    resetToChannelLevel() {
      // 重新加载频道内容
      this.loadRankings(this.selectedSite, this.selectedChannel)
    },
    
    /**
     * 加载榜单数据
     */
    async loadRankings(siteId, channelId = '') {
      try {
        // 这里应该调用API获取榜单数据
        // const response = await this.$http.get('/api/rankings', { siteId, channelId })
        // this.rankingList = response.data
        
        console.log('加载榜单数据:', siteId, channelId)
        
        // 临时模拟数据
        this.rankingList = [
          {
            id: '1',
            name: '热门榜单',
            desc: '当前最受欢迎的作品',
            bookCount: 50,
            updateTime: '2小时前更新'
          },
          {
            id: '2', 
            name: '新书榜单',
            desc: '最新发布的优质作品',
            bookCount: 30,
            updateTime: '1小时前更新'
          },
          {
            id: '3',
            name: '完结榜单',
            desc: '已完结的优质作品',
            bookCount: 25,
            updateTime: '6小时前更新'
          }
        ]
      } catch (error) {
        console.error('加载榜单数据失败:', error)
      }
    },
    
    /**
     * 加载夹子书籍列表
     */
    async loadBookList(siteId) {
      try {
        // 这里应该调用API获取夹子书籍数据
        // const response = await this.$http.get('/api/jiazi/books')
        // this.bookList = response.data
        
        console.log('加载夹子书籍数据:', siteId)
        
        // 临时模拟数据
        this.bookList = [
          {
            id: '1',
            title: '重生之商业帝国',
            collections: 15680,
            collectionChange: 245,  // 正数表示增加
            rankChange: -2  // 负数表示排名上升，正数表示排名下降
          },
          {
            id: '2',
            title: '穿越古代当皇后',
            collections: 12450,
            collectionChange: -89,
            rankChange: 1
          },
          {
            id: '3',
            title: '现代都市修仙录',
            collections: 11230,
            collectionChange: 156,
            rankChange: 0
          },
          {
            id: '4',
            title: '娱乐圈的那些事',
            collections: 9870,
            collectionChange: 78,
            rankChange: -1
          },
          {
            id: '5',
            title: '末世重生女配逆袭',
            collections: 8950,
            collectionChange: -23,
            rankChange: 3
          }
        ]
      } catch (error) {
        console.error('加载夹子书籍数据失败:', error)
      }
    },
    
    /**
     * 搜索功能
     */
    onSearch() {
      // 实现搜索逻辑
      console.log('搜索关键词:', this.searchKeyword)
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
     * 跳转到夹子榜单详情
     */
    goToJiaziDetail() {
      uni.navigateTo({
        url: `/pages/ranking/detail?id=jiazi&type=special`
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.ranking-container {
  padding: 20rpx;
}

.search-section {
  margin-bottom: 30rpx;
}

.search-input {
  width: 100%;
  height: 80rpx;
  padding: 0 30rpx;
  border: 2rpx solid #e0e0e0;
  border-radius: 40rpx;
  background-color: #f8f8f8;
  font-size: 28rpx;
}

.breadcrumb {
  margin-bottom: 20rpx;
  font-size: 24rpx;
  color: #666;
}

.breadcrumb-item {
  color: #007aff;
}

.breadcrumb-separator {
  margin: 0 10rpx;
}

.level-container {
  margin-bottom: 30rpx;
}

.site-scroll, .channel-scroll {
  white-space: nowrap;
}

.site-tabs, .channel-tabs {
  display: flex;
  padding: 10rpx 0;
}

.site-tab, .channel-tab {
  flex-shrink: 0;
  padding: 20rpx 40rpx;
  margin-right: 20rpx;
  background-color: #f0f0f0;
  border-radius: 50rpx;
  font-size: 28rpx;
  color: #333;
  transition: all 0.3s ease;
  
  &.active {
    background-color: #007aff;
    color: white;
    font-weight: bold;
  }
}

.ranking-list {
  height: 1000rpx;
}

.ranking-card {
  padding: 30rpx;
  margin-bottom: 20rpx;
  background-color: white;
  border-radius: 20rpx;
  box-shadow: 0 2rpx 10rpx rgba(0,0,0,0.1);
}

.ranking-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
}

.ranking-desc {
  font-size: 26rpx;
  color: #666;
  margin-bottom: 15rpx;
}

.ranking-stats {
  display: flex;
  justify-content: space-between;
  font-size: 24rpx;
  color: #999;
}

/* 夹子书籍列表样式 */
.book-list-container {
  margin-top: 20rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 0;
  margin-bottom: 20rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.detail-btn {
  padding: 10rpx 20rpx;
  background-color: #007aff;
  color: white;
  border: none;
  border-radius: 20rpx;
  font-size: 24rpx;
}

.book-list {
  height: 800rpx;
}

.book-item {
  display: flex;
  align-items: center;
  padding: 25rpx 20rpx;
  margin-bottom: 15rpx;
  background-color: white;
  border-radius: 15rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.1);
}

.book-rank {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #007aff;
  color: white;
  border-radius: 50%;
  font-size: 24rpx;
  font-weight: bold;
  margin-right: 20rpx;
}

.book-info {
  flex: 1;
}

.book-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
  line-height: 1.4;
}

.book-stats {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.stat-item {
  font-size: 24rpx;
  color: #666;
}

.change-indicator {
  margin-left: 10rpx;
  font-weight: bold;
  
  &.up {
    color: #ff4d4f; /* 红色表示上升/增加 */
  }
  
  &.down {
    color: #52c41a; /* 绿色表示下降/减少 */
  }
}

/* 内容容器样式 */
.content-container {
  margin-top: 20rpx;
}

.ranking-list-container {
  margin-top: 20rpx;
}
</style> 