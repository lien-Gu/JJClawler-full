<template>
  <view class="ranking-page">
    <!-- 搜索栏 -->
    <SearchBar 
      :value="searchKeyword"
      placeholder="Hinted search text"
      @input="onSearchInput"
      @search="onSearch"
    />
    
    <!-- 分类标签 -->
    <CategoryTabs 
      :categories="categories"
      :current-main-tab="currentMainTab"
      :current-sub-tab="currentSubTab"
      @change="onTabChange"
    />
    
    <!-- 榜单列表 -->
    <scroll-view 
      class="rankings-container"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      @scrolltolower="onLoadMore"
    >
      <view class="rankings-list">
        <RankingListItem
          v-for="(ranking, index) in filteredRankings"
          :key="ranking.id"
          :ranking="ranking"
          :index="index"
          @click="handleRankingClick"
        />
        
        <!-- 加载更多提示 -->
        <view v-if="loading" class="loading-more">
          <text class="loading-text">加载中...</text>
        </view>
        
        <!-- 没有更多数据提示 -->
        <view v-if="!hasMore && filteredRankings.length > 0" class="no-more">
          <text class="no-more-text">没有更多榜单了</text>
        </view>
        
        <!-- 空状态 -->
        <view v-if="filteredRankings.length === 0 && !loading" class="empty-state">
          <text class="empty-text">暂无榜单数据</text>
        </view>
      </view>
    </scroll-view>
    
    <!-- TabBar -->
    <TabBar :current-index="1" />
  </view>
</template>

<script>
import TabBar from '@/components/TabBar.vue';
import SearchBar from '@/components/SearchBar.vue';
import CategoryTabs from '@/components/CategoryTabs.vue';
import RankingListItem from '@/components/RankingListItem.vue';
import dataManager from '@/utils/data-manager.js';

export default {
  name: 'RankingPage',
  components: {
    TabBar,
    SearchBar,
    CategoryTabs,
    RankingListItem
  },
  data() {
    return {
      searchKeyword: '',
      currentMainTab: '',
      currentSubTab: '',
      categories: [
        {
          key: 'jiazi',
          name: '夹子',
          children: []
        },
        {
          key: 'yanqing',
          name: '言情',
          children: [
            { key: 'guyan', name: '古言' },
            { key: 'xiandai', name: '现言' },
            { key: 'guchuan', name: '古穿' },
            { key: 'weilai', name: '未来' }
          ]
        },
        {
          key: 'chunai',
          name: '纯爱',
          children: [
            { key: 'dushi', name: '都市' },
            { key: 'gudai', name: '古代' },
            { key: 'weilai', name: '未来' }
          ]
        },
        {
          key: 'yanshen',
          name: '衍生',
          children: []
        },
        {
          key: 'baihe',
          name: '百合',
          children: []
        }
      ],
      allRankings: [],
      filteredRankings: [],
      loading: false,
      refreshing: false,
      hasMore: true,
      page: 1,
      pageSize: 20
    };
  },
  
  onLoad(options) {
    this.initData();
    this.loadRankings();
  },
  
  onShow() {
    // 页面显示时刷新数据
    this.refreshRankings();
  },
  
  methods: {
    initData() {
      // 默认选择第一个分类
      if (this.categories.length > 0) {
        this.currentMainTab = this.categories[0].key;
        if (this.categories[0].children && this.categories[0].children.length > 0) {
          this.currentSubTab = this.categories[0].children[0].key;
        }
      }
    },
    
    async loadRankings() {
      if (this.loading || !this.hasMore) return;
      
      this.loading = true;
      
      try {
        // 调用真实API获取榜单数据
        const response = await dataManager.getRankingsList({
          page: this.page,
          pageSize: this.pageSize,
          category: this.currentMainTab,
          subCategory: this.currentSubTab
        });
        
        if (response && Array.isArray(response)) {
          if (this.page === 1) {
            this.allRankings = response;
          } else {
            this.allRankings.push(...response);
          }
          
          this.hasMore = response.length === this.pageSize;
          this.page++;
          
          this.filterRankings();
        }
      } catch (error) {
        console.error('加载榜单失败:', error);
        // 使用模拟数据
        this.loadMockRankings();
      } finally {
        this.loading = false;
        this.refreshing = false;
      }
    },

    loadMockRankings() {
      // 模拟榜单数据
      const mockRankings = Array.from({ length: this.pageSize }, (_, index) => ({
        id: `ranking_${this.page}_${index + 1}`,
        name: `榜单名称${(this.page - 1) * this.pageSize + index + 1}`,
        description: '榜单层级',
        hierarchy: `分类 > 子分类`,
        total_books: Math.floor(Math.random() * 1000) + 100,
        category: this.currentMainTab,
        subCategory: this.currentSubTab
      }));
      
      if (this.page === 1) {
        this.allRankings = mockRankings;
      } else {
        this.allRankings.push(...mockRankings);
      }
      
      this.hasMore = this.page < 3; // 模拟3页数据
      this.page++;
      
      this.filterRankings();
    },

    filterRankings() {
      let filtered = [...this.allRankings];
      
      // 根据搜索关键词过滤
      if (this.searchKeyword.trim()) {
        const keyword = this.searchKeyword.toLowerCase();
        filtered = filtered.filter(ranking => 
          ranking.name.toLowerCase().includes(keyword) ||
          ranking.description.toLowerCase().includes(keyword)
        );
      }
      
      // 根据分类过滤
      if (this.currentMainTab) {
        filtered = filtered.filter(ranking => ranking.category === this.currentMainTab);
      }
      
      if (this.currentSubTab) {
        filtered = filtered.filter(ranking => ranking.subCategory === this.currentSubTab);
      }
      
      this.filteredRankings = filtered;
    },
    
    onTabChange({ mainTab, subTab, tab }) {
      this.currentMainTab = mainTab;
      this.currentSubTab = subTab;
      
      // 重新加载榜单数据
      this.refreshRankings();
    },
    
    onSearchInput(value) {
      this.searchKeyword = value;
      // 延迟搜索，避免频繁请求
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(() => {
        this.filterRankings();
      }, 300);
    },
    
    onSearch(value) {
      this.searchKeyword = value;
      this.filterRankings();
    },
    
    onRefresh() {
      this.refreshing = true;
      this.refreshRankings();
    },
    
    refreshRankings() {
      this.page = 1;
      this.hasMore = true;
      this.allRankings = [];
      this.filteredRankings = [];
      this.loadRankings();
    },
    
    onLoadMore() {
      this.loadRankings();
    },
    
    handleRankingClick(ranking) {
      console.log('点击榜单:', ranking);
      
      // 跳转到榜单详情页
      uni.navigateTo({
        url: `/pages/ranking/detail?id=${ranking.id}&name=${encodeURIComponent(ranking.name)}`
      });
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.ranking-page {
  min-height: 100vh;
  background: $surface-default;
  padding-bottom: calc(#{$tabbar-height} + env(safe-area-inset-bottom));
}

.rankings-container {
  flex: 1;
  height: calc(100vh - 300rpx - #{$tabbar-height} - env(safe-area-inset-top) - env(safe-area-inset-bottom));
}

.rankings-list {
  padding: 0 $spacing-md;
  padding-bottom: $spacing-lg;
}

.loading-more {
  display: flex;
  justify-content: center;
  padding: $spacing-md 0;
}

.loading-text {
  font-family: $font-family-base;
  font-size: $caption-font-size-rpx;
  color: $text-secondary;
}

.no-more {
  display: flex;
  justify-content: center;
  padding: $spacing-md 0;
}

.no-more-text {
  font-family: $font-family-base;
  font-size: $caption-font-size-rpx;
  color: $text-secondary;
  opacity: 0.6;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400rpx;
}

.empty-text {
  font-family: $font-family-base;
  font-size: 32rpx;
  color: $text-secondary;
  opacity: 0.6;
}
</style> 