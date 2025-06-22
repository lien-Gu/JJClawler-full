"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const utils_storage = require("../../utils/storage.js");
const StatsCard = () => "../../components/StatsCard.js";
const _sfc_main = {
  name: "HomePage",
  components: {
    StatsCard
  },
  data() {
    return {
      // 核心统计数据
      coreStats: [
        {
          key: "totalBooks",
          title: "总书籍数",
          value: 0,
          trend: 0,
          icon: "📚",
          color: "#007AFF"
        },
        {
          key: "totalRankings",
          title: "总榜单数",
          value: 0,
          trend: 0,
          icon: "��",
          color: "#34C759"
        },
        {
          key: "todayUpdates",
          title: "今日更新",
          value: 0,
          trend: 0,
          icon: "🔄",
          color: "#FF9500"
        },
        {
          key: "activeUsers",
          title: "活跃用户",
          value: 0,
          trend: 0,
          icon: "👥",
          color: "#AF52DE"
        }
      ],
      // 分站统计数据
      siteStats: [],
      // 热门榜单
      hotRankings: [],
      // 最近更新
      recentUpdates: [],
      // 加载状态
      loading: false,
      // 刷新状态
      refreshing: false
    };
  },
  onLoad() {
    this.initData();
  },
  onShow() {
    this.checkDataFreshness();
  },
  // 下拉刷新
  onPullDownRefresh() {
    this.refreshData().finally(() => {
      common_vendor.index.stopPullDownRefresh();
    });
  },
  methods: {
    /**
     * 初始化数据
     */
    async initData() {
      this.loading = true;
      try {
        this.loadCachedData();
        await this.fetchData();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/index/index.vue:204", "初始化数据失败:", error);
        this.showError("数据加载失败");
      } finally {
        this.loading = false;
      }
    },
    /**
     * 加载缓存数据
     */
    loadCachedData() {
      const cachedStats = utils_storage.getSync("homeStats");
      const cachedSiteStats = utils_storage.getSync("homeSiteStats");
      const cachedHotRankings = utils_storage.getSync("homeHotRankings");
      const cachedRecentUpdates = utils_storage.getSync("homeRecentUpdates");
      if (cachedStats) {
        this.updateCoreStats(cachedStats);
      }
      if (cachedSiteStats) {
        this.siteStats = cachedSiteStats;
      }
      if (cachedHotRankings) {
        this.hotRankings = cachedHotRankings;
      }
      if (cachedRecentUpdates) {
        this.recentUpdates = cachedRecentUpdates;
      }
    },
    /**
     * 获取最新数据
     */
    async fetchData() {
      try {
        const [statsRes, sitesRes, rankingsRes, updatesRes] = await Promise.all([
          utils_request.get("/api/stats/overview"),
          utils_request.get("/api/sites/stats"),
          utils_request.get("/api/rankings/hot", { limit: 6 }),
          utils_request.get("/api/recent/updates", { limit: 8 })
        ]);
        if (statsRes) {
          this.updateCoreStats(statsRes);
          utils_storage.setSync("homeStats", statsRes, 5 * 60 * 1e3);
        }
        if (sitesRes) {
          this.siteStats = sitesRes;
          utils_storage.setSync("homeSiteStats", sitesRes, 10 * 60 * 1e3);
        }
        if (rankingsRes) {
          this.hotRankings = rankingsRes;
          utils_storage.setSync("homeHotRankings", rankingsRes, 15 * 60 * 1e3);
        }
        if (updatesRes) {
          this.recentUpdates = updatesRes;
          utils_storage.setSync("homeRecentUpdates", updatesRes, 5 * 60 * 1e3);
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/index/index.vue:275", "获取数据失败:", error);
        throw error;
      }
    },
    /**
     * 更新核心统计数据
     */
    updateCoreStats(data) {
      this.coreStats.forEach((stat) => {
        if (data[stat.key] !== void 0) {
          stat.value = data[stat.key];
          stat.trend = data[`${stat.key}Trend`] || 0;
        }
      });
    },
    /**
     * 检查数据新鲜度
     */
    checkDataFreshness() {
      const lastUpdate = utils_storage.getSync("homeLastUpdate", 0);
      const now = Date.now();
      if (now - lastUpdate > 10 * 60 * 1e3) {
        this.fetchData().catch(() => {
        }).finally(() => {
          utils_storage.setSync("homeLastUpdate", now);
        });
      }
    },
    /**
     * 刷新数据
     */
    async refreshData() {
      if (this.refreshing)
        return;
      this.refreshing = true;
      try {
        await this.fetchData();
        utils_storage.setSync("homeLastUpdate", Date.now());
        common_vendor.index.showToast({
          title: "刷新成功",
          icon: "success",
          duration: 1500
        });
      } catch (error) {
        this.showError("刷新失败");
      } finally {
        this.refreshing = false;
      }
    },
    /**
     * 格式化时间显示
     */
    formatTime(time) {
      if (!time)
        return "未知";
      const now = /* @__PURE__ */ new Date();
      const updateTime = new Date(time);
      const diff = now - updateTime;
      const minutes = Math.floor(diff / (1e3 * 60));
      const hours = Math.floor(diff / (1e3 * 60 * 60));
      const days = Math.floor(diff / (1e3 * 60 * 60 * 24));
      if (minutes < 60) {
        return `${minutes}分钟前`;
      } else if (hours < 24) {
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
     * 统计卡片点击事件
     */
    onStatClick(stat) {
      common_vendor.index.__f__("log", "at pages/index/index.vue:373", "点击统计卡片:", stat);
    },
    /**
     * 跳转到榜单页面
     */
    goToRanking() {
      common_vendor.index.switchTab({
        url: "/pages/ranking/index"
      });
    },
    /**
     * 跳转到分站页面
     */
    goToSite(site) {
      common_vendor.index.switchTab({
        url: `/pages/ranking/index?site=${site.key}`
      });
    },
    /**
     * 跳转到榜单详情
     */
    goToRankingDetail(ranking) {
      common_vendor.index.navigateTo({
        url: `/pages/ranking/detail?id=${ranking.id}`
      });
    },
    /**
     * 跳转到详情页面
     */
    goToDetail(item) {
      if (item.type === "ranking") {
        this.goToRankingDetail(item);
      } else if (item.type === "book") {
        common_vendor.index.navigateTo({
          url: `/pages/book/detail?id=${item.id}`
        });
      }
    }
  }
};
if (!Array) {
  const _component_StatsCard = common_vendor.resolveComponent("StatsCard");
  _component_StatsCard();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_vendor.o((...args) => $options.refreshData && $options.refreshData(...args)),
    b: common_vendor.f($data.coreStats, (stat, k0, i0) => {
      return {
        a: stat.key,
        b: common_vendor.o(($event) => $options.onStatClick(stat), stat.key),
        c: "1cf27b2a-0-" + i0,
        d: common_vendor.p({
          title: stat.title,
          value: stat.value,
          trend: stat.trend,
          icon: stat.icon,
          color: stat.color
        })
      };
    }),
    c: common_vendor.o((...args) => $options.goToRanking && $options.goToRanking(...args)),
    d: common_vendor.f($data.siteStats, (site, k0, i0) => {
      return {
        a: common_vendor.t(site.name),
        b: common_vendor.t(site.rankingCount),
        c: common_vendor.t(site.trend > 0 ? "+" : ""),
        d: common_vendor.t(site.trend),
        e: common_vendor.n(site.trend > 0 ? "trend-up" : "trend-down"),
        f: site.key,
        g: common_vendor.o(($event) => $options.goToSite(site), site.key)
      };
    }),
    e: common_vendor.o((...args) => $options.goToRanking && $options.goToRanking(...args)),
    f: common_vendor.f($data.hotRankings, (ranking, k0, i0) => {
      return common_vendor.e({
        a: ranking.isHot
      }, ranking.isHot ? {} : {}, {
        b: common_vendor.t(ranking.name),
        c: common_vendor.t(ranking.bookCount),
        d: common_vendor.t($options.formatTime(ranking.updateTime)),
        e: ranking.id,
        f: common_vendor.o(($event) => $options.goToRankingDetail(ranking), ranking.id)
      });
    }),
    g: common_vendor.f($data.recentUpdates, (item, k0, i0) => {
      return {
        a: common_vendor.t(item.title),
        b: common_vendor.t(item.subtitle),
        c: common_vendor.t($options.formatTime(item.updateTime)),
        d: item.id,
        e: common_vendor.o(($event) => $options.goToDetail(item), item.id)
      };
    })
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-1cf27b2a"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/index/index.js.map
