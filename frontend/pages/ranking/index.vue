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
        id: site.id,
        type: site.type,
        channel: site.channel,
        children: site.channels.map(channel => ({
          key: channel.id,
          name: channel.name,
          id: channel.id,
          channel: channel.channel
        }))
      }));
    },
    
    initData() {
      // 默认选择书城分类（index），而不是第一个分类
      const defaultCategory = this.categories.find(cat => cat.key === 'index');
      if (defaultCategory) {
        this.currentMainTab = defaultCategory.key;
        // 对于所有分类，初始时都不选择子分类（允许用户自己选择是看主分类还是子分类）
        this.currentSubTab = '';
      } else if (this.categories.length > 0) {
        // 备选方案：如果找不到书城，选择第一个
        this.currentMainTab = this.categories[0].key;
        this.currentSubTab = '';
      }
    },
    
    getCurrentPageId() {
      // 根据当前主分类和子分类获取对应的page_id
      const mainCategory = this.categories.find(cat => cat.key === this.currentMainTab);
      
      if (!mainCategory) {
        console.warn(`未找到主分类 ${this.currentMainTab}，返回默认index`);
        return 'index'; // 默认返回书城首页
      }
      
      // 特殊处理：夹子分类直接返回其ID，不需要子分类
      if (mainCategory.key === 'jiazi') {
        return 'jiazi';
      }
      
      // 简单分类（如书城、百合）直接返回其channel值
      if (mainCategory.type === 'simple') {
        return mainCategory.channel || mainCategory.id;
      }
      
      // 复杂分类处理
      if (mainCategory.type === 'complex') {
        // 如果有选中子分类，返回组合的page_id格式：主分类.子分类
        if (this.currentSubTab) {
          const subCategory = mainCategory.children?.find(sub => sub.key === this.currentSubTab);
          if (subCategory) {
            // 对于复杂分类的子分类，使用 主分类id.子分类id 的格式
            const pageId = `${mainCategory.id}.${subCategory.id}`;
            console.log(`复杂分类子分类: ${mainCategory.name} > ${subCategory.name}, page_id: ${pageId}`);
            return pageId;
          }
        }
        
        // 如果没有选中子分类，返回主分类的id（只看主分类的榜单）
        console.log(`复杂分类主分类: ${mainCategory.name}, page_id: ${mainCategory.id}`);
        return mainCategory.id;
      }
      
      // 其他情况：返回主分类的channel或id
      return mainCategory.channel || mainCategory.id;
    },

    /**
     * 确定数据加载策略
     * @returns {string} 'jiazi-books' | 'ranking-list'
     */
    determineLoadStrategy() {
      const pageId = this.getCurrentPageId();
      // 如果是夹子分类，直接加载书籍数据
      if (pageId === 'jiazi') {
        return 'jiazi-books';
      }
      // 其他情况加载榜单列表
      return 'ranking-list';
    },
    

    /**
     * 加载夹子榜单的书籍数据
     */
    async loadJiaziBooks() {
      const JIAZI_RANKING_ID = 1;
      console.log(`正在加载夹子榜单书籍数据: /rankingsdetail/day/${JIAZI_RANKING_ID}`);
      
      return await requestManager.getRankingDetail(JIAZI_RANKING_ID, {
        page: this.page,
        size: this.pageSize
      });
    },

    /**
     * 加载榜单列表数据
     */
    async loadRankingsList() {
      const apiParams = {
        page_id: this.getCurrentPageId(),
        page: this.page,
        size: this.pageSize
      };
      
      console.log(`正在请求榜单数据: /rankings/?page_id=${apiParams.page_id}&page=${apiParams.page}&size=${apiParams.size}`);
      
      return await requestManager.getRankingsList(apiParams);
    },
    
    /**
     * 主数据加载函数 - 根据策略选择不同的加载方式
     */
    async loadRankings() {
      if (this.loading || !this.hasMore) return;
      
      this.loading = true;
      
      try {
        const strategy = this.determineLoadStrategy();
        console.log(`使用加载策略: ${strategy}, 页面ID: ${this.getCurrentPageId()}`);
        
        // 根据策略选择加载方法
        const result = strategy === 'jiazi-books' 
          ? await this.loadJiaziBooks() 
          : await this.loadRankingsList();
        
        // 处理加载结果
        if (result.success && result.data && result.data.length > 0) {
          this.processLoadedData(result.data, result.totalPages);
          const itemType = strategy === 'jiazi-books' ? '书籍' : '榜单';
          console.log(`成功加载 ${result.data.length} 个${itemType}项目，当前第${this.page-1}页，共${result.totalPages}页`);
        } else {
          console.warn(`未获取到有效的数据 (策略: ${strategy})`);
        }
      } catch (error) {
        console.error('数据加载失败:', error);
      } finally {
        this.loading = false;
        this.refreshing = false;
      }
    },

    /**
     * 处理加载的数据（通用逻辑）
     */
    processLoadedData(data, totalPages) {
      if (this.page === 1) {
        this.allRankings = data;
      } else {
        this.allRankings.push(...data);
      }
      
      // 根据总页数判断是否还有更多数据
      this.hasMore = this.page < totalPages;
      this.page++;
      
      this.filterRankings();
    },


    filterRankings() {
      let filtered = [...this.allRankings];
      console.log(`开始过滤榜单，原始数据量: ${this.allRankings.length}`);
      
      // 只根据搜索关键词过滤，API已经返回了对应分类的榜单
      if (this.searchKeyword.trim()) {
        const keyword = this.searchKeyword.toLowerCase();
        filtered = filtered.filter(ranking => 
          ranking.name.toLowerCase().includes(keyword) ||
          (ranking.description && ranking.description.toLowerCase().includes(keyword))
        );
        console.log(`搜索关键词"${this.searchKeyword}"过滤后: ${filtered.length} 个榜单`);
      }
      
      this.filteredRankings = filtered;
      console.log(`最终显示榜单数量: ${this.filteredRankings.length}`);
    },
    
    onTabChange({ mainTab, subTab }) {
      console.log('Tab切换:', { mainTab, subTab});
      this.currentMainTab = mainTab;
      this.currentSubTab = subTab || ''; // 允许子分类为空
      
      const pageId = this.getCurrentPageId();
      console.log(`分类切换: ${mainTab}${subTab ? ` > ${subTab}` : ''}, page_id: ${pageId}`);
      
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
      console.log('点击项目:', ranking);
      
      if (ranking.isBook) {
        // 如果是书籍项，跳转到书籍详情页
        uni.navigateTo({
          url: `/pages/book/detail?id=${ranking.bookData?.id || ranking.id.replace('book_', '')}`
        });
      } else {
        // 如果是榜单项，跳转到榜单详情页
        uni.navigateTo({
          url: `/pages/ranking/detail?id=${ranking.id}&name=${encodeURIComponent(ranking.name)}`
        });
      }
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