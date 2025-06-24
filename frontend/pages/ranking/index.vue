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
      
      <!-- 夹子榜单：显示书籍列表 -->
      <view v-if="currentSite.type === 'special'" class="book-list-container">
        <view class="jiazi-header">
          <text class="jiazi-title">{{ currentSite.name }}</text>
          <text class="jiazi-count">共{{ bookList.length }}本</text>
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
import dataManager from '@/utils/data-manager.js'

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
      
      // 夹子：选中即显示书籍列表
      if (this.currentSite.type === 'special') {
        return true
      }
      
      // 简单榜单：选中即显示榜单列表
      if (this.currentSite.type === 'simple') {
        return true
      }
      
      // 复杂榜单：选中分站即显示分站榜单，选中频道则显示频道榜单
      if (this.currentSite.type === 'complex') {
        return true
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
      } else {
        // 简单榜单和复杂榜单：都加载分站的榜单列表
        this.loadRankings(site.id)
      }
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
     * 加载榜单数据
     */
    async loadRankings(siteId, channelId = '') {
      try {
        console.log('加载榜单数据:', siteId, channelId)
        
        // 使用数据管理器获取榜单数据
        const rankingsData = await dataManager.getRankingsList({
          site: siteId,
          channel: channelId
        })
        
        if (rankingsData && Array.isArray(rankingsData)) {
          this.rankingList = rankingsData.map(ranking => ({
            id: ranking.id,
            name: ranking.name,
            desc: ranking.description || `${ranking.name}榜单`,
            bookCount: ranking.book_count || 0,
            updateTime: this.formatUpdateTime(ranking.last_updated)
          }))
        } else {
          // 如果没有数据，使用生成的测试数据作为后备
          this.rankingList = this.generateTestRankings(siteId, channelId)
        }
        
        // 在调试模式下显示数据源信息
        if (dataManager.getEnvironmentInfo().debug) {
          console.log('榜单数据源:', dataManager.getEnvironmentInfo().environment)
          console.log('榜单数据:', this.rankingList)
        }
        
      } catch (error) {
        console.error('加载榜单数据失败:', error)
        // 出错时使用测试数据
        this.rankingList = this.generateTestRankings(siteId, channelId)
      }
    },
    
    /**
     * 生成测试榜单数据
     */
    generateTestRankings(siteId, channelId = '') {
      const baseRankings = {
        // 书城榜单
        index: [
          { id: 'index_1', name: '书城热门榜', desc: '书城最受欢迎的作品', bookCount: 100, updateTime: '1小时前更新' },
          { id: 'index_2', name: '书城新书榜', desc: '书城最新发布的作品', bookCount: 80, updateTime: '2小时前更新' },
          { id: 'index_3', name: '书城完结榜', desc: '书城已完结的优质作品', bookCount: 60, updateTime: '3小时前更新' }
        ],
        
        // 言情分站榜单
        yq: [
          { id: 'yq_1', name: '言情总榜', desc: '言情分站综合排行', bookCount: 200, updateTime: '30分钟前更新' },
          { id: 'yq_2', name: '言情月榜', desc: '本月最受欢迎的言情作品', bookCount: 150, updateTime: '1小时前更新' },
          { id: 'yq_3', name: '言情新作榜', desc: '最新发布的言情作品', bookCount: 120, updateTime: '2小时前更新' },
          { id: 'yq_4', name: '言情完结榜', desc: '已完结的优质言情作品', bookCount: 90, updateTime: '4小时前更新' }
        ],
        
        // 纯爱分站榜单
        ca: [
          { id: 'ca_1', name: '纯爱总榜', desc: '纯爱分站综合排行', bookCount: 180, updateTime: '45分钟前更新' },
          { id: 'ca_2', name: '纯爱热门榜', desc: '最受欢迎的纯爱作品', bookCount: 140, updateTime: '1小时前更新' },
          { id: 'ca_3', name: '纯爱新书榜', desc: '最新发布的纯爱作品', bookCount: 110, updateTime: '2小时前更新' },
          { id: 'ca_4', name: '纯爱收藏榜', desc: '收藏量最高的纯爱作品', bookCount: 85, updateTime: '3小时前更新' }
        ],
        
        // 衍生分站榜单
        ys: [
          { id: 'ys_1', name: '衍生总榜', desc: '衍生分站综合排行', bookCount: 160, updateTime: '20分钟前更新' },
          { id: 'ys_2', name: '衍生热门榜', desc: '最受欢迎的衍生作品', bookCount: 130, updateTime: '1小时前更新' },
          { id: 'ys_3', name: '衍生新作榜', desc: '最新发布的衍生作品', bookCount: 100, updateTime: '2小时前更新' }
        ],
        
        // 无CP+分站榜单
        nocp_plus: [
          { id: 'nocp_1', name: '无CP+总榜', desc: '无CP+分站综合排行', bookCount: 140, updateTime: '35分钟前更新' },
          { id: 'nocp_2', name: '无CP+热门榜', desc: '最受欢迎的无CP+作品', bookCount: 110, updateTime: '1小时前更新' },
          { id: 'nocp_3', name: '无CP+新书榜', desc: '最新发布的无CP+作品', bookCount: 90, updateTime: '3小时前更新' }
        ],
        
        // 百合分站榜单
        bh: [
          { id: 'bh_1', name: '百合热门榜', desc: '最受欢迎的百合作品', bookCount: 80, updateTime: '1小时前更新' },
          { id: 'bh_2', name: '百合新书榜', desc: '最新发布的百合作品', bookCount: 60, updateTime: '2小时前更新' },
          { id: 'bh_3', name: '百合完结榜', desc: '已完结的优质百合作品', bookCount: 45, updateTime: '4小时前更新' }
        ]
      }
      
      // 如果有选中频道，生成频道特定榜单
      if (channelId) {
        const channelName = this.currentChannel.name || '频道'
        return [
          { id: `${channelId}_1`, name: `${channelName}热门榜`, desc: `${channelName}最受欢迎的作品`, bookCount: 80, updateTime: '30分钟前更新' },
          { id: `${channelId}_2`, name: `${channelName}新书榜`, desc: `${channelName}最新发布的作品`, bookCount: 60, updateTime: '1小时前更新' },
          { id: `${channelId}_3`, name: `${channelName}完结榜`, desc: `${channelName}已完结的优质作品`, bookCount: 40, updateTime: '2小时前更新' }
        ]
      }
      
      // 返回分站榜单，如果没有对应分站则返回默认榜单
      return baseRankings[siteId] || [
        { id: 'default_1', name: '热门榜单', desc: '当前最受欢迎的作品', bookCount: 50, updateTime: '2小时前更新' },
        { id: 'default_2', name: '新书榜单', desc: '最新发布的优质作品', bookCount: 30, updateTime: '1小时前更新' },
        { id: 'default_3', name: '完结榜单', desc: '已完结的优质作品', bookCount: 25, updateTime: '6小时前更新' }
      ]
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
    },

    /**
     * 格式化更新时间
     */
    formatUpdateTime(timeStr) {
      if (!timeStr) return '未知时间'
      
      try {
        const updateTime = new Date(timeStr)
        const now = new Date()
        const diff = now - updateTime
        
        const minutes = Math.floor(diff / (1000 * 60))
        const hours = Math.floor(diff / (1000 * 60 * 60))
        const days = Math.floor(diff / (1000 * 60 * 60 * 24))
        
        if (minutes < 60) {
          return `${minutes}分钟前更新`
        } else if (hours < 24) {
          return `${hours}小时前更新`
        } else if (days < 7) {
          return `${days}天前更新`
        } else {
          return updateTime.toLocaleDateString() + '更新'
        }
      } catch (error) {
        return '未知时间'
      }
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

.jiazi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 0;
  margin-bottom: 20rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.jiazi-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.jiazi-count {
  font-size: 24rpx;
  color: #999;
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