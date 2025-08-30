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
    <ScrollableList
      :items="filteredRankings"
      :loading="loading"
      :refreshing="refreshing"
      :has-more="hasMore"
      :height="'calc(100vh - 300rpx - env(safe-area-inset-top) - env(safe-area-inset-bottom))'"
      empty-icon="📋"
      empty-title="暂无榜单数据"
      no-more-text="没有更多榜单了"
      @refresh="onRefresh"
      @load-more="onLoadMore"
    >
      <RankingListItem
        v-for="(ranking, index) in filteredRankings"
        :key="ranking.id"
        :ranking="ranking"
        :index="index"
        @click="handleRankingClick"
      />
    </ScrollableList>
  </view>
</template>

<script>
import SearchBar from '@/components/SearchBar.vue';
import CategoryTabs from '@/components/CategoryTabs.vue';
import RankingListItem from '@/components/RankingListItem.vue';
import ScrollableList from '@/components/ScrollableList.vue';
import requestManager from '@/api/request.js';
import { getSitesList } from '@/data/url.js';

export default {
  name: 'RankingPage',
  components: {
    SearchBar,
    CategoryTabs,
    RankingListItem,
    ScrollableList
  },
  data() {
    return {
      searchKeyword: '',
      currentMainTab: '',
      currentSubTab: '',
      categories: [],
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
    this.initCategories();
    this.initData();
    this.loadRankings();
  },
  
  onShow() {
    // 页面显示时刷新数据
    this.refreshRankings();
  },
  
  methods: {
    initCategories() {
      // 从 url.js 加载分类数据
      const sites = getSitesList();
      this.categories = sites.map(site => ({
        key: site.id,
        name: site.name,
        children: site.channels.map(channel => ({
          key: channel.id,
          name: channel.name,
          channel: channel.channel
        }))
      }));
    },
    
    initData() {
      // 默认选择第一个分类
      if (this.categories.length > 0) {
        this.currentMainTab = this.categories[0].key;
        if (this.categories[0].children && this.categories[0].children.length > 0) {
          this.currentSubTab = this.categories[0].children[0].key;
        }
      }
    },
    
    getCurrentPageId() {
      // 根据当前主分类和子分类获取对应的page_id
      const mainCategory = this.categories.find(cat => cat.key === this.currentMainTab);
      if (!mainCategory) return 'index'; // 默认返回书城首页
      
      const subCategory = mainCategory.children?.find(sub => sub.key === this.currentSubTab);
      if (!subCategory) return 'index';
      
      // 返回子分类对应的channel值作为page_id
      return subCategory.channel || 'index';
    },
    
    async loadRankings() {
      if (this.loading || !this.hasMore) return;
      
      this.loading = true;
      
      try {
        const apiParams = {
          page_id: this.getCurrentPageId(),
          page: this.page,
          size: this.pageSize
        };
        
        console.log(`正在请求榜单数据: /api/v1/rankings/?page_id=${apiParams.page_id}&page=${apiParams.page}&size=${apiParams.size}`);
        
        // 调用真实API获取榜单数据
        const response = await requestManager.getRankingsList(apiParams);
        
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
      const pageId = this.getCurrentPageId();
      const mockRankings = Array.from({ length: this.pageSize }, (_, index) => ({
        id: `ranking_${pageId}_${this.page}_${index + 1}`,
        name: `${pageId}榜单${(this.page - 1) * this.pageSize + index + 1}`,
        description: `${pageId}分类榜单`,
        hierarchy: `${pageId} > 子分类`,
        total_books: Math.floor(Math.random() * 1000) + 100,
        page_id: pageId
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
      
      // 只根据搜索关键词过滤，API已经返回了对应分类的榜单
      if (this.searchKeyword.trim()) {
        const keyword = this.searchKeyword.toLowerCase();
        filtered = filtered.filter(ranking => 
          ranking.name.toLowerCase().includes(keyword) ||
          (ranking.description && ranking.description.toLowerCase().includes(keyword))
        );
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
  padding-bottom: env(safe-area-inset-bottom);
}
</style>