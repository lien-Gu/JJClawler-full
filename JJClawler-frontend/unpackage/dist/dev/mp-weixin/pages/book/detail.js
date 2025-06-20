"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_storage = require("../../utils/storage.js");
const _sfc_main = {
  name: "BookDetailPage",
  data() {
    return {
      // 书籍ID
      bookId: "",
      // 书籍数据
      bookData: {
        title: "",
        author: "",
        cover: "",
        category: "",
        status: "",
        currentStats: {
          collectCount: 0,
          avgClickPerChapter: 0
        },
        rankings: []
      },
      // 当前选中的tab
      activeTab: "collect",
      // 'collect' | 'click'
      // 历史数据
      historyStats: {
        dates: [],
        collectHistory: [],
        clickHistory: []
      },
      // 加载状态
      loading: false
    };
  },
  computed: {
    /**
     * 当前显示的历史数据
     */
    historyData() {
      if (this.activeTab === "collect") {
        return this.historyStats.collectHistory || [];
      } else {
        return this.historyStats.clickHistory || [];
      }
    },
    /**
     * 图表点位数据
     */
    chartPoints() {
      if (this.historyData.length === 0)
        return [];
      const maxValue = Math.max(...this.historyData);
      const minValue = Math.min(...this.historyData);
      const range = maxValue - minValue || 1;
      return this.historyData.map((value, index) => ({
        x: index / (this.historyData.length - 1) * 100,
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
      this.bookId = options.id;
      this.initData();
    }
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
        await Promise.all([
          this.fetchBookInfo(),
          this.fetchHistoryStats()
        ]);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/book/detail.vue:264", "初始化数据失败:", error);
        this.showError("数据加载失败");
      } finally {
        this.loading = false;
      }
    },
    /**
     * 加载缓存数据
     */
    loadCachedData() {
      const cachedBook = utils_storage.getSync(`book_detail_${this.bookId}`);
      const cachedHistory = utils_storage.getSync(`book_history_${this.bookId}`);
      if (cachedBook) {
        this.bookData = { ...this.bookData, ...cachedBook };
      }
      if (cachedHistory) {
        this.historyStats = cachedHistory;
      }
    },
    /**
     * 获取书籍详细信息
     */
    async fetchBookInfo() {
      try {
        const data = await this.getMockBookData();
        this.bookData = { ...this.bookData, ...data };
        utils_storage.setSync(`book_detail_${this.bookId}`, data, 30 * 60 * 1e3);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/book/detail.vue:298", "获取书籍信息失败:", error);
        throw error;
      }
    },
    /**
     * 获取历史统计数据
     */
    async fetchHistoryStats() {
      try {
        const data = await this.getMockHistoryData();
        this.historyStats = data;
        utils_storage.setSync(`book_history_${this.bookId}`, data, 15 * 60 * 1e3);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/book/detail.vue:314", "获取历史数据失败:", error);
        throw error;
      }
    },
    /**
     * 获取模拟书籍数据
     */
    async getMockBookData() {
      await new Promise((resolve) => setTimeout(resolve, 500));
      return {
        title: "霸道总裁的小娇妻",
        author: "言情作家",
        cover: "",
        category: "现代言情",
        status: "连载中",
        currentStats: {
          collectCount: 125847,
          avgClickPerChapter: 2156
        },
        rankings: [
          {
            id: "ranking1",
            name: "言情总榜",
            currentRank: 15,
            rankChange: -2,
            updateTime: "2024-01-15T10:30:00"
          },
          {
            id: "ranking2",
            name: "新书榜",
            currentRank: 8,
            rankChange: 3,
            updateTime: "2024-01-15T10:30:00"
          },
          {
            id: "ranking3",
            name: "收藏榜",
            currentRank: 22,
            rankChange: 0,
            updateTime: "2024-01-15T10:30:00"
          }
        ]
      };
    },
    /**
     * 获取模拟历史数据
     */
    async getMockHistoryData() {
      await new Promise((resolve) => setTimeout(resolve, 300));
      const dates = [];
      const collectHistory = [];
      const clickHistory = [];
      const now = /* @__PURE__ */ new Date();
      for (let i = 29; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        dates.push(date.toISOString().split("T")[0]);
        const baseCollect = 12e4 + i * 200;
        const collectVariation = Math.random() * 1e3 - 500;
        collectHistory.push(Math.max(0, Math.floor(baseCollect + collectVariation)));
        const baseClick = 2e6 + i * 5e3;
        const clickVariation = Math.random() * 1e4 - 5e3;
        clickHistory.push(Math.max(0, Math.floor(baseClick + clickVariation)));
      }
      return {
        dates,
        collectHistory,
        clickHistory
      };
    },
    /**
     * 刷新数据
     */
    async refreshData() {
      try {
        await Promise.all([
          this.fetchBookInfo(),
          this.fetchHistoryStats()
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
     * 切换统计Tab
     */
    switchTab(tab) {
      this.activeTab = tab;
    },
    /**
     * 获取排名变化样式类
     */
    getRankChangeClass(change) {
      if (!change || change === 0)
        return "no-change";
      return change > 0 ? "rank-up" : "rank-down";
    },
    /**
     * 获取排名变化图标
     */
    getRankChangeIcon(change) {
      if (!change || change === 0)
        return "—";
      return change > 0 ? "↗" : "↘";
    },
    /**
     * 获取最大值
     */
    getMaxValue() {
      return Math.max(...this.historyData);
    },
    /**
     * 获取最小值
     */
    getMinValue() {
      return Math.min(...this.historyData);
    },
    /**
     * 获取平均增长
     */
    getAverageGrowth() {
      if (this.historyData.length < 2)
        return "0%";
      const first = this.historyData[0];
      const last = this.historyData[this.historyData.length - 1];
      const growth = ((last - first) / first * 100).toFixed(1);
      return growth > 0 ? `+${growth}%` : `${growth}%`;
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
    }
  }
};
if (!Array) {
  const _component_polyline = common_vendor.resolveComponent("polyline");
  const _component_svg = common_vendor.resolveComponent("svg");
  (_component_polyline + _component_svg)();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  var _a, _b;
  return common_vendor.e({
    a: $data.bookData.cover
  }, $data.bookData.cover ? {
    b: $data.bookData.cover
  } : {}, {
    c: common_vendor.t($data.bookData.title || $data.bookData.name || "书籍详情"),
    d: $data.bookData.author
  }, $data.bookData.author ? {
    e: common_vendor.t($data.bookData.author)
  } : {}, {
    f: $data.bookData.category || $data.bookData.status
  }, $data.bookData.category || $data.bookData.status ? common_vendor.e({
    g: $data.bookData.category
  }, $data.bookData.category ? {
    h: common_vendor.t($data.bookData.category)
  } : {}, {
    i: $data.bookData.category && $data.bookData.status
  }, $data.bookData.category && $data.bookData.status ? {} : {}, {
    j: $data.bookData.status
  }, $data.bookData.status ? {
    k: common_vendor.t($data.bookData.status)
  } : {}) : {}, {
    l: common_vendor.t($options.formatNumber(((_a = $data.bookData.currentStats) == null ? void 0 : _a.collectCount) || 0)),
    m: common_vendor.t($options.formatNumber(((_b = $data.bookData.currentStats) == null ? void 0 : _b.avgClickPerChapter) || 0)),
    n: $data.bookData.rankings && $data.bookData.rankings.length > 0
  }, $data.bookData.rankings && $data.bookData.rankings.length > 0 ? {
    o: common_vendor.f($data.bookData.rankings, (ranking, k0, i0) => {
      return {
        a: common_vendor.t(ranking.name),
        b: common_vendor.t(ranking.currentRank),
        c: common_vendor.t($options.getRankChangeIcon(ranking.rankChange)),
        d: common_vendor.t(Math.abs(ranking.rankChange || 0)),
        e: common_vendor.n($options.getRankChangeClass(ranking.rankChange)),
        f: common_vendor.t($options.formatTime(ranking.updateTime)),
        g: ranking.id
      };
    })
  } : {}, {
    p: $data.activeTab === "collect" ? 1 : "",
    q: common_vendor.o(($event) => $options.switchTab("collect")),
    r: $data.activeTab === "click" ? 1 : "",
    s: common_vendor.o(($event) => $options.switchTab("click")),
    t: $options.historyData.length > 0
  }, $options.historyData.length > 0 ? {
    v: common_vendor.f(5, (i, k0, i0) => {
      return {
        a: i
      };
    }),
    w: common_vendor.f($options.chartPoints, (point, index, i0) => {
      return {
        a: common_vendor.t(point.value),
        b: index,
        c: point.x + "%",
        d: point.y + "%"
      };
    }),
    x: common_vendor.p({
      points: $options.chartLinePoints,
      fill: "none",
      stroke: "#007aff",
      ["stroke-width"]: "0.5"
    }),
    y: common_vendor.p({
      viewBox: "0 0 100 100",
      preserveAspectRatio: "none"
    })
  } : {}, {
    z: $options.historyData.length > 0
  }, $options.historyData.length > 0 ? {
    A: common_vendor.t($options.formatNumber($options.getMaxValue())),
    B: common_vendor.t($options.formatNumber($options.getMinValue())),
    C: common_vendor.t($options.getAverageGrowth())
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-f3085b2f"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/book/detail.js.map
