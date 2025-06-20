<template>
  <view class="ranking-container">
    <!-- 调试信息 -->
    <view class="debug-info" style="background: #f0f0f0; padding: 10rpx; margin-bottom: 20rpx; font-size: 24rpx;">
      <text>当前层级: {{ currentLevel }}</text>
      <text> | 分站数量: {{ sites.length }}</text>
      <text> | 选中分站: {{ selectedSite }}</text>
      <text> | 榜单数量: {{ rankingList.length }}</text>
    </view>
    
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
    <view class="breadcrumb" v-if="currentLevel > 1">
      <text class="breadcrumb-item" @tap="goToLevel(1)">{{ currentSite.name }}</text>
      <text class="breadcrumb-separator" v-if="currentLevel > 2"> > </text>
      <text class="breadcrumb-item" v-if="currentLevel > 2">{{ currentChannel.name }}</text>
    </view>

    <!-- 层级1: 分站选择 -->
    <view class="level-container" v-if="currentLevel === 1">
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

    <!-- 层级2: 频道选择 -->
    <view class="level-container" v-if="currentLevel === 2 && currentSite.channels.length > 0">
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

    <!-- 层级3: 榜单列表 -->
    <view class="level-container" v-if="currentLevel === 3">
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
</template>

<script>
import { getSitesList } from '@/data/url.js'

export default {
  data() {
    return {
      searchKeyword: '',
      currentLevel: 1, // 1: 分站选择, 2: 频道选择, 3: 榜单列表
      selectedSite: '',
      selectedChannel: '',
      currentSite: {},
      currentChannel: {},
      sites: [],
      rankingList: []
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
      
      if (site.channels && site.channels.length > 0) {
        this.currentLevel = 2
      } else {
        this.currentLevel = 3
        this.loadRankings(site.id)
      }
    },
    
    /**
     * 选择频道
     */
    selectChannel(channel) {
      this.selectedChannel = channel.id
      this.currentChannel = channel
      this.currentLevel = 3
      this.loadRankings(this.selectedSite, channel.id)
    },
    
    /**
     * 返回指定层级
     */
    goToLevel(level) {
      this.currentLevel = level
      if (level === 1) {
        this.selectedSite = ''
        this.selectedChannel = ''
        this.currentSite = {}
        this.currentChannel = {}
      }
    },
    
    /**
     * 加载榜单数据
     */
    async loadRankings(siteId, channelId = '') {
      try {
        // 这里应该调用API获取榜单数据
        // const response = await this.$http.get('/api/rankings', { siteId, channelId })
        // this.rankingList = response.data
        
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
          }
        ]
      } catch (error) {
        console.error('加载榜单数据失败:', error)
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
  
  &.active {
    background-color: #007aff;
    color: white;
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
</style> 