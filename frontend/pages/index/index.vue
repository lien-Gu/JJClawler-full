<template>
  <view class="index-page">
    <!-- 问候语 -->
    <view class="greeting-section">
      <text class="greeting-text">嗨~</text>
    </view>
    
    <!-- 报告列表 -->
    <ScrollableList
      :items="reportsList"
      :loading="loading"
      :refreshing="refreshing"
      :has-more="hasMore"
      :height="'calc(100vh - 200rpx - env(safe-area-inset-top) - env(safe-area-inset-bottom))'"
      empty-icon="📊"
      empty-title="暂无统计报告"
      no-more-text="没有更多报告了"
      @refresh="onRefresh"
      @load-more="onLoadMore"
    >
      <ReportCarousel
        v-for="report in reportsList"
        :key="report.id"
        :report="report"
        @click="handleReportClick"
      />
    </ScrollableList>
    
  </view>
</template>

<script>
import ReportCarousel from '@/components/ReportCarousel.vue';
import ScrollableList from '@/components/ScrollableList.vue';
import dataManager from '@/utils/data-manager.js';

export default {
  name: 'IndexPage',
  components: {
    ReportCarousel,
    ScrollableList
  },
  data() {
    return {
      reportsList: [],
      loading: false,
      refreshing: false,
      hasMore: true,
      page: 1,
      pageSize: 10
    };
  },
  
  onLoad() {
    this.loadReports();
  },
  
  onShow() {
    // 页面显示时刷新数据
    this.refreshReports();
  },
  
  methods: {
    async loadReports() {
      if (this.loading || !this.hasMore) return;
      
      this.loading = true;
      
      try {
        // 调用真实API获取统计报告
        const response = await this.fetchReports(this.page, this.pageSize);
        
        if (response.success) {
          if (this.page === 1) {
            this.reportsList = response.data;
          } else {
            this.reportsList.push(...response.data);
          }
          
          this.hasMore = response.data.length === this.pageSize;
          this.page++;
        }
      } catch (error) {
        console.error('加载报告失败:', error);
        uni.showToast({
          title: '加载失败',
          icon: 'error'
        });
      } finally {
        this.loading = false;
        this.refreshing = false;
      }
    },
    
    async fetchReports(page, pageSize) {
      try {
        // 获取统计概览数据
        const overviewStats = await dataManager.getOverviewStats();
        const hotRankings = await dataManager.getHotRankings({ limit: 5 });
        
        // 构造报告数据
        const reports = [
          {
            id: 'overview',
            title: '数据概览',
            description: `总计 ${overviewStats.total_books || 0} 本书籍，${overviewStats.total_rankings || 0} 个榜单`,
            createdAt: new Date(),
            type: 'overview',
            data: overviewStats
          },
          {
            id: 'hot_rankings',
            title: '热门榜单',
            description: '最活跃的书籍排行榜单',
            createdAt: new Date(),
            type: 'rankings',
            data: hotRankings
          }
        ];
        
        return {
          success: true,
          data: page === 1 ? reports : [] // 暂时只返回第一页
        };
      } catch (error) {
        console.error('获取报告数据失败:', error);
        return {
          success: false,
          data: []
        };
      }
    },
    
    onRefresh() {
      this.refreshing = true;
      this.refreshReports();
    },
    
    refreshReports() {
      this.page = 1;
      this.hasMore = true;
      this.reportsList = [];
      this.loadReports();
    },
    
    onLoadMore() {
      this.loadReports();
    },
    
    handleReportClick(report) {
      console.log('点击报告:', report);
      
      // 跳转到报告详情页面
      uni.navigateTo({
        url: `/pages/report/detail?type=${report.type}&title=${encodeURIComponent(report.title)}`
      });
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.index-page {
  min-height: 100vh;
  background: $surface-default;
  padding-bottom: env(safe-area-inset-bottom);
}

.greeting-section {
  padding: $spacing-lg $spacing-lg $spacing-md;
  margin-top: env(safe-area-inset-top);
}

.greeting-text {
  font-family: $font-family-base;
  font-size: $h1-font-size-rpx;
  font-weight: $h1-font-weight;
  line-height: $h1-line-height-rpx;
  color: $text-primary;
}

</style>