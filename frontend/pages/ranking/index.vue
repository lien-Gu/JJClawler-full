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
    
    formatRankingName(channelName, subChannelName) {
      // 格式化榜单名称，智能组合 channel_name 和 sub_channel_name
      if (channelName && subChannelName) {
        // 两个都有，组合显示
        return `${channelName} - ${subChannelName}`;
      } else if (channelName) {
        // 只有主分类名
        return channelName;
      } else if (subChannelName) {
        // 只有子分类名
        return subChannelName;
      } else {
        // 都没有，返回默认名称
        return '未知榜单';
      }
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

        console.log('API响应数据:', response);
        
        // 解析真实的API响应格式
        let rankingsData = [];
        let totalPages = 0;
        
        if (response && response.success && response.data) {
          const responseData = response.data;
          
          // 获取榜单列表数据
          if (responseData.data_list && Array.isArray(responseData.data_list)) {
            rankingsData = responseData.data_list.map(item => ({
              id: item.id,
              name: this.formatRankingName(item.channel_name, item.sub_channel_name),
              channel_name: item.channel_name || '',
              sub_channel_name: item.sub_channel_name || '',
              page_id: item.page_id,
              rank_group_type: item.rank_group_type || '其他',
              description: `${item.rank_group_type || '其他'} - ${item.page_id}`
            }));
            
            // 获取分页信息
            totalPages = responseData.total_pages || 1;
          }
        }
        
        console.log('处理后的榜单数据:', rankingsData);
        console.log('总页数:', totalPages);
        
        // 检查是否获取到有效数据
        if (rankingsData && rankingsData.length > 0) {
          if (this.page === 1) {
            this.allRankings = rankingsData;
          } else {
            this.allRankings.push(...rankingsData);
          }
          
          // 根据总页数判断是否还有更多数据
          this.hasMore = this.page < totalPages;
          this.page++;
          
          this.filterRankings();
          console.log(`成功加载 ${rankingsData.length} 个榜单项目，当前第${this.page-1}页，共${totalPages}页`);
        } else {
          console.warn('未获取到有效的榜单数据，使用模拟数据');
          this.loadMockRankings();
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
      const mockRankingNames = [
        '完结榜', '收藏榜', '点击榜', '推荐榜', '评分榜', 
        '新书榜', '月度榜', '季度榜', '年度榜', '热门榜',
        '原创榜', '同人榜', '现代榜', '古代榜', '幻想榜',
        '都市榜', '校园榜', '职场榜', '军事榜', '历史榜'
      ];
      
      const mockRankings = Array.from({ length: this.pageSize }, (_, index) => ({
        id: `ranking_${pageId}_${this.page}_${index + 1}`,
        name: mockRankingNames[((this.page - 1) * this.pageSize + index) % mockRankingNames.length],
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
      console.log(`成功加载 ${mockRankings.length} 个模拟榜单项目，当前第${this.page-1}页`);
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