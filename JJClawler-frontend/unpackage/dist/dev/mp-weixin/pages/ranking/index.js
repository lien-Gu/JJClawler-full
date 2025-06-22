"use strict";
const common_vendor = require("../../common/vendor.js");
const data_url = require("../../data/url.js");
const BookList = () => "../../components/BookList.js";
const _sfc_main = {
  name: "RankingPage",
  components: {
    BookList
  },
  data() {
    return {
      searchKeyword: "",
      sites: [],
      selectedSite: null,
      selectedChannel: null,
      currentChannels: [],
      currentRankings: [],
      books: [],
      level: 1,
      // 1: 分站选择, 2: 频道选择, 3: 内容显示
      currentRankingTitle: ""
    };
  },
  onLoad(options) {
    this.initData();
    if (options.site) {
      const site = data_url.getSiteById(options.site);
      if (site) {
        this.selectSite(site);
      }
    } else {
      this.restoreLastSelection();
    }
  },
  methods: {
    /**
     * 初始化数据
     */
    initData() {
      try {
        this.sites = data_url.getSitesList();
        common_vendor.index.__f__("log", "at pages/ranking/index.vue:133", "加载分站列表:", this.sites);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/index.vue:135", "加载分站数据失败:", error);
        this.sites = [
          { id: "jj", name: "夹子", type: "special" },
          { id: "shu", name: "书城", type: "simple" },
          { id: "yan", name: "言情", type: "complex" }
        ];
      }
    },
    /**
     * 恢复上次选择的tab
     */
    restoreLastSelection() {
      try {
        const lastSelection = common_vendor.index.getStorageSync("ranking_last_selection");
        if (lastSelection && lastSelection.siteId) {
          common_vendor.index.__f__("log", "at pages/ranking/index.vue:152", "恢复历史选择:", lastSelection);
          const site = data_url.getSiteById(lastSelection.siteId);
          if (site) {
            this.selectSite(site, false);
            if (lastSelection.channelId && site.type === "complex") {
              const channels = data_url.getChannelsBySiteId(site.id);
              const channel = channels.find((ch) => ch.id === lastSelection.channelId);
              if (channel) {
                setTimeout(() => {
                  this.selectChannel(channel, false);
                }, 100);
              }
            }
            return;
          }
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/index.vue:171", "恢复历史选择失败:", error);
      }
      const jiaziSite = this.sites.find((site) => site.id === "jj");
      if (jiaziSite) {
        this.selectSite(jiaziSite);
      }
    },
    /**
     * 保存当前选择到历史
     */
    saveCurrentSelection() {
      var _a, _b;
      try {
        const selection = {
          siteId: (_a = this.selectedSite) == null ? void 0 : _a.id,
          channelId: (_b = this.selectedChannel) == null ? void 0 : _b.id,
          timestamp: Date.now()
        };
        common_vendor.index.setStorageSync("ranking_last_selection", selection);
        common_vendor.index.__f__("log", "at pages/ranking/index.vue:192", "保存选择历史:", selection);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/index.vue:194", "保存选择历史失败:", error);
      }
    },
    /**
     * 选择分站
     */
    selectSite(site, saveHistory = true) {
      this.selectedSite = site;
      this.selectedChannel = null;
      common_vendor.index.__f__("log", "at pages/ranking/index.vue:205", "选择分站:", site);
      if (saveHistory) {
        this.saveCurrentSelection();
      }
      if (site.type === "special" && site.id === "jj") {
        this.level = 2;
        this.currentRankingTitle = "夹子榜单";
        this.loadJiaziBooks();
      } else if (site.type === "complex") {
        this.level = 2;
        this.currentChannels = data_url.getChannelsBySiteId(site.id);
        this.loadSiteRankings(site);
      } else {
        this.level = 2;
        this.loadSiteRankings(site);
      }
    },
    /**
     * 选择频道
     */
    selectChannel(channel, saveHistory = true) {
      this.selectedChannel = channel;
      this.level = 3;
      common_vendor.index.__f__("log", "at pages/ranking/index.vue:235", "选择频道:", channel);
      if (saveHistory) {
        this.saveCurrentSelection();
      }
      this.loadChannelRankings(this.selectedSite, channel);
    },
    /**
     * 加载分站榜单
     */
    loadSiteRankings(site) {
      const siteRankings = {
        jj: [
          { id: "jj_main", name: "夹子总榜", type: "books" },
          { id: "jj_rising", name: "夹子新星榜", type: "books" },
          { id: "jj_hot", name: "夹子热门榜", type: "books" }
        ],
        shu: [
          { id: "shu_hot", name: "热门榜" },
          { id: "shu_new", name: "新书榜" },
          { id: "shu_finish", name: "完结榜" }
        ],
        yan: [
          { id: "yan_monthly", name: "月榜" },
          { id: "yan_weekly", name: "周榜" },
          { id: "yan_daily", name: "日榜" }
        ],
        chun: [
          { id: "chun_popular", name: "人气榜" },
          { id: "chun_recommend", name: "推荐榜" }
        ]
      };
      this.currentRankings = siteRankings[site.id] || [
        { id: `${site.id}_default`, name: "默认榜单" }
      ];
    },
    /**
     * 加载频道榜单
     */
    loadChannelRankings(site, channel) {
      this.currentRankings = [
        { id: `${site.id}_${channel.id}_hot`, name: `${channel.name}热门榜` },
        { id: `${site.id}_${channel.id}_new`, name: `${channel.name}新作榜` }
      ];
    },
    /**
     * 加载夹子书籍列表
     */
    loadJiaziBooks() {
      this.books = Array.from({ length: 50 }, (_, index) => ({
        id: `book_${index + 1}`,
        title: `重生之农女${index + 1}`,
        collections: 193 + Math.floor(Math.random() * 1e3),
        collectionChange: Math.floor(Math.random() * 100) - 50,
        rankChange: Math.floor(Math.random() * 10) - 5
      }));
    },
    /**
     * 搜索输入
     */
    onSearchInput(e) {
      common_vendor.index.__f__("log", "at pages/ranking/index.vue:306", "搜索:", e.detail.value);
    },
    /**
     * 跳转到榜单详情
     */
    goToRankingDetail(ranking) {
      if (ranking.type === "books") {
        this.level = 3;
        this.currentRankingTitle = ranking.name;
        this.loadJiaziBooks();
        return;
      }
      common_vendor.index.navigateTo({
        url: `/pages/ranking/detail?id=${ranking.id}&name=${encodeURIComponent(ranking.name)}`
      });
    },
    /**
     * 处理书籍点击（BookList组件事件）
     */
    handleBookTap({ book, index }) {
      this.goToBookDetail(book);
    },
    /**
     * 跳转到书籍详情
     */
    goToBookDetail(book) {
      common_vendor.index.navigateTo({
        url: `/pages/book/detail?id=${book.id}`
      });
    }
  }
};
if (!Array) {
  const _component_BookList = common_vendor.resolveComponent("BookList");
  _component_BookList();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.o([($event) => $data.searchKeyword = $event.detail.value, (...args) => $options.onSearchInput && $options.onSearchInput(...args)]),
    b: $data.searchKeyword,
    c: common_vendor.f($data.sites, (site, k0, i0) => {
      return {
        a: common_vendor.t(site.name),
        b: $data.selectedSite && $data.selectedSite.id === site.id ? 1 : "",
        c: site.id,
        d: common_vendor.o(($event) => $options.selectSite(site), site.id)
      };
    }),
    d: $data.selectedSite && $data.selectedSite.type === "complex"
  }, $data.selectedSite && $data.selectedSite.type === "complex" ? {
    e: common_vendor.f($data.currentChannels, (channel, k0, i0) => {
      return {
        a: common_vendor.t(channel.name),
        b: $data.selectedChannel && $data.selectedChannel.id === channel.id ? 1 : "",
        c: channel.id,
        d: common_vendor.o(($event) => $options.selectChannel(channel), channel.id)
      };
    })
  } : {}, {
    f: $data.selectedSite && $data.selectedSite.id === "jj" && $data.level >= 2
  }, $data.selectedSite && $data.selectedSite.id === "jj" && $data.level >= 2 ? {
    g: common_vendor.o($options.handleBookTap),
    h: common_vendor.p({
      books: $data.books,
      title: $data.currentRankingTitle,
      ["show-count"]: true,
      ["show-rank"]: true,
      ["show-actions"]: false
    })
  } : $data.selectedSite && $data.level >= 2 ? {
    j: common_vendor.f($data.currentRankings, (ranking, k0, i0) => {
      return {
        a: common_vendor.t(ranking.name),
        b: ranking.id,
        c: common_vendor.o(($event) => $options.goToRankingDetail(ranking), ranking.id)
      };
    })
  } : {}, {
    i: $data.selectedSite && $data.level >= 2
  });
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-55d17871"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/ranking/index.js.map
