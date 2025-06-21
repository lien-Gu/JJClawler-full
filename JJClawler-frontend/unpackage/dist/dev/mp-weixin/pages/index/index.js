"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  name: "IndexPage",
  data() {
    return {
      // 可以在这里添加一些状态数据
    };
  },
  onLoad() {
    common_vendor.index.__f__("log", "at pages/index/index.vue:63", "首页加载完成");
  },
  // 下拉刷新
  onPullDownRefresh() {
    setTimeout(() => {
      common_vendor.index.stopPullDownRefresh();
      common_vendor.index.showToast({
        title: "刷新完成",
        icon: "success",
        duration: 1500
      });
    }, 1e3);
  },
  methods: {
    /**
     * 跳转到统计详情页面（后端接口）
     */
    goToStatisticsDetail() {
      this.openBackendUrl("/api/statistics/detail", "统计详情");
    },
    /**
     * 跳转到榜单统计（后端接口）
     */
    goToRankingStats() {
      this.openBackendUrl("/api/statistics/rankings", "榜单统计");
    },
    /**
     * 跳转到书籍统计（后端接口）
     */
    goToBookStats() {
      this.openBackendUrl("/api/statistics/books", "书籍统计");
    },
    /**
     * 跳转到频道统计（后端接口）
     */
    goToChannelStats() {
      this.openBackendUrl("/api/statistics/channels", "频道统计");
    },
    /**
     * 打开后端接口URL
     * @param {string} path - 接口路径
     * @param {string} title - 页面标题
     */
    openBackendUrl(path, title) {
      const baseUrl = this.getApiBaseUrl();
      const fullUrl = baseUrl + path;
      common_vendor.index.__f__("log", "at pages/index/index.vue:118", `准备打开${title}页面:`, fullUrl);
      common_vendor.index.navigateTo({
        url: `/pages/webview/index?url=${encodeURIComponent(fullUrl)}&title=${encodeURIComponent(title)}`
      });
    },
    /**
     * 获取API基础URL
     */
    getApiBaseUrl() {
      return "https://your-api-domain.com";
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_vendor.o((...args) => $options.goToStatisticsDetail && $options.goToStatisticsDetail(...args)),
    b: common_vendor.o((...args) => $options.goToStatisticsDetail && $options.goToStatisticsDetail(...args)),
    c: common_vendor.o((...args) => $options.goToRankingStats && $options.goToRankingStats(...args)),
    d: common_vendor.o((...args) => $options.goToBookStats && $options.goToBookStats(...args)),
    e: common_vendor.o((...args) => $options.goToChannelStats && $options.goToChannelStats(...args))
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-1cf27b2a"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/index/index.js.map
