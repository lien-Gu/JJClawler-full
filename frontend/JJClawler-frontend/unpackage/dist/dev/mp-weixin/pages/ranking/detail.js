"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const utils_storage = require("../../utils/storage.js");
const _sfc_main = {
  name: "RankingDetailPage",
  data() {
    return {
      // 榜单ID
      rankingId: "",
      // 榜单数据
      rankingData: {
        name: "",
        description: "",
        siteName: "",
        channelName: "",
        updateTime: ""
      },
      // 当前选中的tab
      activeTab: "totalClicks",
      // 'totalClicks' | 'avgClicks' | 'totalCollects' | 'avgCollects'
      // 图表数据
      chartStats: {
        dates: [],
        totalClicksData: [],
        // 点击量增量总和
        avgClicksData: [],
        // 点击量增量平均值
        totalCollectsData: [],
        // 收藏量增量总和
        avgCollectsData: []
        // 收藏量增量平均值
      },
      // 书籍列表
      booksList: [],
      // 分页信息
      currentPage: 1,
      pageSize: 20,
      hasMore: true,
      // 加载状态
      loading: false,
      loadingMore: false
    };
  },
  computed: {
    /**
     * 当前显示的图表数据
     */
    chartData() {
      switch (this.activeTab) {
        case "totalClicks":
          return this.chartStats.totalClicksData || [];
        case "avgClicks":
          return this.chartStats.avgClicksData || [];
        case "totalCollects":
          return this.chartStats.totalCollectsData || [];
        case "avgCollects":
          return this.chartStats.avgCollectsData || [];
        default:
          return [];
      }
    },
    /**
     * 图表点位数据
     */
    chartPoints() {
      if (this.chartData.length === 0)
        return [];
      const maxValue = Math.max(...this.chartData);
      const minValue = Math.min(...this.chartData);
      const range = maxValue - minValue || 1;
      return this.chartData.map((value, index) => ({
        x: index / (this.chartData.length - 1) * 100,
        y: (value - minValue) / range * 80 + 10,
        value: this.formatNumber(value)
      }));
    },
    /**
     * 图表连接线点位
     */
    chartLinePoints() {
      return this.chartPoints.map((point) => `${point.x},${100 - point.y}`).join(" ");
    }
  },
  onLoad(options) {
    if (options.id) {
      this.rankingId = options.id;
      this.initData();
    }
  },
  // 下拉刷新
  onPullDownRefresh() {
    this.refreshData().finally(() => {
      common_vendor.index.stopPullDownRefresh();
    });
  },
  // 上拉加载更多
  onReachBottom() {
    if (this.hasMore && !this.loadingMore) {
      this.loadMore();
    }
  },
  methods: {
    /**
     * 初始化数据
     */
    async initData() {
      this.loading = true;
      try {
        this.loadCachedData();
        await Promise.all([
          this.fetchRankingInfo(),
          this.fetchChartStats(),
          this.fetchBooksList(true)
        ]);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/detail.vue:319", "初始化数据失败:", error);
        this.showError("数据加载失败");
      } finally {
        this.loading = false;
      }
    },
    /**
     * 加载缓存数据
     */
    loadCachedData() {
      const cachedRanking = utils_storage.getSync(`ranking_detail_${this.rankingId}`);
      const cachedChart = utils_storage.getSync(`ranking_chart_${this.rankingId}`);
      const cachedBooks = utils_storage.getSync(`ranking_books_${this.rankingId}`);
      if (cachedRanking) {
        this.rankingData = { ...this.rankingData, ...cachedRanking };
      }
      if (cachedChart) {
        this.chartStats = cachedChart;
      }
      if (cachedBooks) {
        this.booksList = cachedBooks;
      }
    },
    /**
     * 获取榜单信息
     */
    async fetchRankingInfo() {
      try {
        const data = await this.getMockRankingData();
        this.rankingData = { ...this.rankingData, ...data };
        utils_storage.setSync(`ranking_detail_${this.rankingId}`, data, 30 * 60 * 1e3);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/detail.vue:358", "获取榜单信息失败:", error);
        throw error;
      }
    },
    /**
     * 获取图表统计数据
     */
    async fetchChartStats() {
      try {
        const data = await this.getMockChartData();
        this.chartStats = data;
        utils_storage.setSync(`ranking_chart_${this.rankingId}`, data, 15 * 60 * 1e3);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/detail.vue:374", "获取图表数据失败:", error);
        throw error;
      }
    },
    /**
     * 获取书籍列表
     */
    async fetchBooksList(reset = false) {
      try {
        if (reset) {
          this.currentPage = 1;
          this.hasMore = true;
        }
        const data = await this.getMockBooksData(this.currentPage);
        if (reset) {
          this.booksList = data.list;
        } else {
          this.booksList.push(...data.list);
        }
        this.hasMore = data.hasMore || false;
        this.currentPage++;
        if (reset) {
          utils_storage.setSync(`ranking_books_${this.rankingId}`, data.list, 15 * 60 * 1e3);
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/detail.vue:406", "获取书籍列表失败:", error);
        throw error;
      }
    },
    /**
     * 获取模拟榜单数据
     */
    async getMockRankingData() {
      await new Promise((resolve) => setTimeout(resolve, 500));
      return {
        name: "言情总榜",
        description: "言情分站综合排行榜单",
        siteName: "言情",
        channelName: "总榜",
        updateTime: "2024-01-15T10:30:00"
      };
    },
    /**
     * 获取模拟图表数据
     */
    async getMockChartData() {
      await new Promise((resolve) => setTimeout(resolve, 300));
      const dates = [];
      const totalClicksData = [];
      const avgClicksData = [];
      const totalCollectsData = [];
      const avgCollectsData = [];
      const now = /* @__PURE__ */ new Date();
      for (let i = 29; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        dates.push(date.toISOString().split("T")[0]);
        const baseTotalClicks = 5e4 + i * 1e3;
        const totalClicksVariation = Math.random() * 1e4 - 5e3;
        totalClicksData.push(Math.max(0, Math.floor(baseTotalClicks + totalClicksVariation)));
        const baseAvgClicks = 250 + i * 5;
        const avgClicksVariation = Math.random() * 50 - 25;
        avgClicksData.push(Math.max(0, Math.floor(baseAvgClicks + avgClicksVariation)));
        const baseTotalCollects = 5e3 + i * 100;
        const totalCollectsVariation = Math.random() * 1e3 - 500;
        totalCollectsData.push(Math.max(0, Math.floor(baseTotalCollects + totalCollectsVariation)));
        const baseAvgCollects = 25 + i * 0.5;
        const avgCollectsVariation = Math.random() * 5 - 2.5;
        avgCollectsData.push(Math.max(0, Math.floor(baseAvgCollects + avgCollectsVariation)));
      }
      return {
        dates,
        totalClicksData,
        avgClicksData,
        totalCollectsData,
        avgCollectsData
      };
    },
    /**
     * 获取模拟书籍数据
     */
    async getMockBooksData(page = 1) {
      await new Promise((resolve) => setTimeout(resolve, 200));
      const pageSize = 20;
      const totalBooks = 100;
      const startIndex = (page - 1) * pageSize;
      const books = [];
      for (let i = 0; i < pageSize && startIndex + i < totalBooks; i++) {
        const index = startIndex + i;
        books.push({
          id: `book_${index + 1}`,
          title: `榜单书籍${index + 1}`,
          collections: Math.floor(Math.random() * 5e4) + 1e4,
          collectionChange: Math.floor(Math.random() * 1e3) - 500,
          rankChange: Math.floor(Math.random() * 10) - 5
        });
      }
      return {
        list: books,
        hasMore: startIndex + pageSize < totalBooks
      };
    },
    /**
     * 刷新数据
     */
    async refreshData() {
      try {
        await Promise.all([
          this.fetchRankingInfo(),
          this.fetchChartStats(),
          this.fetchBooksList(true)
        ]);
        common_vendor.index.showToast({
          title: "刷新成功",
          icon: "success",
          duration: 1500
        });
      } catch (error) {
        this.showError("刷新失败");
      }
    },
    /**
     * 加载更多
     */
    async loadMore() {
      if (this.loadingMore || !this.hasMore)
        return;
      this.loadingMore = true;
      try {
        await this.fetchBooksList();
      } catch (error) {
        this.showError("加载失败");
      } finally {
        this.loadingMore = false;
      }
    },
    /**
     * 切换图表Tab
     */
    switchTab(tab) {
      this.activeTab = tab;
    },
    /**
     * 获取最大值
     */
    getMaxValue() {
      return Math.max(...this.chartData);
    },
    /**
     * 获取最小值
     */
    getMinValue() {
      return Math.min(...this.chartData);
    },
    /**
     * 获取总变化
     */
    getTotalChange() {
      if (this.chartData.length < 2)
        return "0%";
      const first = this.chartData[0];
      const last = this.chartData[this.chartData.length - 1];
      const change = ((last - first) / first * 100).toFixed(1);
      return change > 0 ? `+${change}%` : `${change}%`;
    },
    /**
     * 格式化数字
     */
    formatNumber(num) {
      if (typeof num !== "number")
        return num || "0";
      if (num >= 1e4) {
        return (num / 1e4).toFixed(1) + "万";
      } else if (num >= 1e3) {
        return (num / 1e3).toFixed(1) + "k";
      }
      return num.toString();
    },
    /**
     * 格式化时间
     */
    formatTime(time) {
      if (!time)
        return "未知";
      const now = /* @__PURE__ */ new Date();
      const updateTime = new Date(time);
      const diff = now - updateTime;
      const hours = Math.floor(diff / (1e3 * 60 * 60));
      const days = Math.floor(diff / (1e3 * 60 * 60 * 24));
      if (hours < 24) {
        return `${hours}小时前`;
      } else if (days < 7) {
        return `${days}天前`;
      } else {
        return updateTime.toLocaleDateString();
      }
    },
    /**
     * 显示错误提示
     */
    showError(message) {
      common_vendor.index.showToast({
        title: message,
        icon: "none",
        duration: 2e3
      });
    },
    /**
     * 跳转到书籍详情
     */
    goToBookDetail(book) {
      common_vendor.index.navigateTo({
        url: `/pages/book/detail?id=${book.id}`
      });
    },
    /**
     * 切换关注状态
     */
    async toggleFollow() {
      try {
        const action = this.rankingData.isFollowed ? "unfollow" : "follow";
        await utils_request.get(`/api/rankings/${this.rankingId}/${action}`, {}, { method: "POST" });
        this.rankingData.isFollowed = !this.rankingData.isFollowed;
        common_vendor.index.showToast({
          title: this.rankingData.isFollowed ? "关注成功" : "取消关注",
          icon: "success",
          duration: 1500
        });
      } catch (error) {
        this.showError("操作失败");
      }
    },
    /**
     * 分享榜单
     */
    shareRanking() {
      common_vendor.index.share({
        provider: "weixin",
        scene: "WXSceneSession",
        type: 0,
        title: this.rankingData.name,
        summary: this.rankingData.description || "来看看这个热门榜单",
        success: () => {
          common_vendor.index.showToast({
            title: "分享成功",
            icon: "success"
          });
        },
        fail: () => {
          this.showError("分享失败");
        }
      });
    }
  }
};
if (!Array) {
  const _component_polyline = common_vendor.resolveComponent("polyline");
  const _component_svg = common_vendor.resolveComponent("svg");
  (_component_polyline + _component_svg)();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.t($data.rankingData.name || "榜单详情"),
    b: $data.rankingData.description
  }, $data.rankingData.description ? {
    c: common_vendor.t($data.rankingData.description)
  } : {}, {
    d: common_vendor.t($data.rankingData.siteName),
    e: common_vendor.t($data.rankingData.channelName),
    f: common_vendor.t($options.formatTime($data.rankingData.updateTime)),
    g: common_vendor.t($data.rankingData.isFollowed ? "已关注" : "关注"),
    h: $data.rankingData.isFollowed ? 1 : "",
    i: common_vendor.o((...args) => $options.toggleFollow && $options.toggleFollow(...args)),
    j: common_vendor.o((...args) => $options.shareRanking && $options.shareRanking(...args)),
    k: $data.activeTab === "totalClicks" ? 1 : "",
    l: common_vendor.o(($event) => $options.switchTab("totalClicks")),
    m: $data.activeTab === "avgClicks" ? 1 : "",
    n: common_vendor.o(($event) => $options.switchTab("avgClicks")),
    o: $data.activeTab === "totalCollects" ? 1 : "",
    p: common_vendor.o(($event) => $options.switchTab("totalCollects")),
    q: $data.activeTab === "avgCollects" ? 1 : "",
    r: common_vendor.o(($event) => $options.switchTab("avgCollects")),
    s: $options.chartData.length > 0
  }, $options.chartData.length > 0 ? {
    t: common_vendor.f(5, (i, k0, i0) => {
      return {
        a: i
      };
    }),
    v: common_vendor.f($options.chartPoints, (point, index, i0) => {
      return {
        a: common_vendor.t(point.value),
        b: index,
        c: point.x + "%",
        d: point.y + "%"
      };
    }),
    w: common_vendor.p({
      points: $options.chartLinePoints,
      fill: "none",
      stroke: "#007aff",
      ["stroke-width"]: "0.5"
    }),
    x: common_vendor.p({
      viewBox: "0 0 100 100",
      preserveAspectRatio: "none"
    })
  } : {}, {
    y: $options.chartData.length > 0
  }, $options.chartData.length > 0 ? {
    z: common_vendor.t($options.formatNumber($options.getMaxValue())),
    A: common_vendor.t($options.formatNumber($options.getMinValue())),
    B: common_vendor.t($options.getTotalChange())
  } : {}, {
    C: common_vendor.t($data.booksList.length),
    D: $data.booksList.length > 0
  }, $data.booksList.length > 0 ? {
    E: common_vendor.f($data.booksList, (book, index, i0) => {
      return {
        a: common_vendor.t(index + 1),
        b: common_vendor.t(book.title),
        c: common_vendor.t($options.formatNumber(book.collections)),
        d: common_vendor.t(book.collectionChange > 0 ? "↑" : "↓"),
        e: common_vendor.t(Math.abs(book.collectionChange)),
        f: common_vendor.n(book.collectionChange > 0 ? "up" : "down"),
        g: common_vendor.t(book.rankChange === 0 ? "—" : book.rankChange > 0 ? "↓" : "↑"),
        h: common_vendor.t(Math.abs(book.rankChange)),
        i: common_vendor.n(book.rankChange > 0 ? "down" : "up"),
        j: book.id,
        k: common_vendor.o(($event) => $options.goToBookDetail(book), book.id)
      };
    })
  } : {}, {
    F: $data.hasMore
  }, $data.hasMore ? common_vendor.e({
    G: !$data.loadingMore
  }, !$data.loadingMore ? {
    H: common_vendor.o((...args) => $options.loadMore && $options.loadMore(...args))
  } : {}) : $data.booksList.length > 0 ? {} : {}, {
    I: $data.booksList.length > 0,
    J: !$data.loading && $data.booksList.length === 0
  }, !$data.loading && $data.booksList.length === 0 ? {
    K: common_vendor.o((...args) => $options.refreshData && $options.refreshData(...args))
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-919d4ad2"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/ranking/detail.js.map
