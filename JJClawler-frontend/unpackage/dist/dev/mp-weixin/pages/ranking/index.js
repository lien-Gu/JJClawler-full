"use strict";
const common_vendor = require("../../common/vendor.js");
const data_url = require("../../data/url.js");
const _sfc_main = {
  data() {
    return {
      searchKeyword: "",
      selectedSite: "",
      selectedChannel: "",
      currentSite: {},
      currentChannel: {},
      sites: [],
      rankingList: [],
      bookList: []
      // 夹子榜单的书籍列表
    };
  },
  computed: {
    // 是否显示频道选择层级
    showChannelLevel() {
      return this.selectedSite && this.currentSite.type === "complex" && this.currentSite.channels && this.currentSite.channels.length > 0;
    },
    // 是否显示内容层级
    showContentLevel() {
      if (!this.selectedSite)
        return false;
      if (this.currentSite.type === "special") {
        return true;
      }
      if (this.currentSite.type === "simple") {
        return true;
      }
      if (this.currentSite.type === "complex") {
        return this.selectedChannel !== "";
      }
      return false;
    }
  },
  onLoad() {
    this.loadSites();
  },
  methods: {
    /**
     * 加载分站数据
     */
    loadSites() {
      try {
        this.sites = data_url.getSitesList();
        common_vendor.index.__f__("log", "at pages/ranking/index.vue:176", "分站数据加载成功:", this.sites);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/index.vue:178", "加载分站数据失败:", error);
      }
    },
    /**
     * 选择分站
     */
    selectSite(site) {
      this.selectedSite = site.id;
      this.currentSite = site;
      this.selectedChannel = "";
      this.currentChannel = {};
      if (site.type === "special") {
        this.loadBookList(site.id);
      } else if (site.type === "simple") {
        this.loadRankings(site.id);
      }
    },
    /**
     * 选择频道
     */
    selectChannel(channel) {
      this.selectedChannel = channel.id;
      this.currentChannel = channel;
      this.loadRankings(this.selectedSite, channel.id);
    },
    /**
     * 重置到分站层级
     */
    resetToSiteLevel() {
      this.selectedChannel = "";
      this.currentChannel = {};
      if (this.currentSite.type === "special") {
        this.loadBookList(this.selectedSite);
      } else if (this.currentSite.type === "simple") {
        this.loadRankings(this.selectedSite);
      }
    },
    /**
     * 重置到频道层级
     */
    resetToChannelLevel() {
      this.loadRankings(this.selectedSite, this.selectedChannel);
    },
    /**
     * 加载榜单数据
     */
    async loadRankings(siteId, channelId = "") {
      try {
        common_vendor.index.__f__("log", "at pages/ranking/index.vue:247", "加载榜单数据:", siteId, channelId);
        this.rankingList = [
          {
            id: "1",
            name: "热门榜单",
            desc: "当前最受欢迎的作品",
            bookCount: 50,
            updateTime: "2小时前更新"
          },
          {
            id: "2",
            name: "新书榜单",
            desc: "最新发布的优质作品",
            bookCount: 30,
            updateTime: "1小时前更新"
          },
          {
            id: "3",
            name: "完结榜单",
            desc: "已完结的优质作品",
            bookCount: 25,
            updateTime: "6小时前更新"
          }
        ];
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/index.vue:274", "加载榜单数据失败:", error);
      }
    },
    /**
     * 加载夹子书籍列表
     */
    async loadBookList(siteId) {
      try {
        common_vendor.index.__f__("log", "at pages/ranking/index.vue:287", "加载夹子书籍数据:", siteId);
        this.bookList = [
          {
            id: "1",
            title: "重生之商业帝国",
            collections: 15680,
            collectionChange: 245,
            // 正数表示增加
            rankChange: -2
            // 负数表示排名上升，正数表示排名下降
          },
          {
            id: "2",
            title: "穿越古代当皇后",
            collections: 12450,
            collectionChange: -89,
            rankChange: 1
          },
          {
            id: "3",
            title: "现代都市修仙录",
            collections: 11230,
            collectionChange: 156,
            rankChange: 0
          },
          {
            id: "4",
            title: "娱乐圈的那些事",
            collections: 9870,
            collectionChange: 78,
            rankChange: -1
          },
          {
            id: "5",
            title: "末世重生女配逆袭",
            collections: 8950,
            collectionChange: -23,
            rankChange: 3
          }
        ];
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/index.vue:328", "加载夹子书籍数据失败:", error);
      }
    },
    /**
     * 搜索功能
     */
    onSearch() {
      common_vendor.index.__f__("log", "at pages/ranking/index.vue:337", "搜索关键词:", this.searchKeyword);
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
     * 跳转到夹子榜单详情
     */
    goToJiaziDetail() {
      common_vendor.index.navigateTo({
        url: `/pages/ranking/detail?id=jiazi&type=special`
      });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.o([($event) => $data.searchKeyword = $event.detail.value, (...args) => $options.onSearch && $options.onSearch(...args)]),
    b: $data.searchKeyword,
    c: $data.selectedSite
  }, $data.selectedSite ? common_vendor.e({
    d: common_vendor.t($data.currentSite.name),
    e: common_vendor.o((...args) => $options.resetToSiteLevel && $options.resetToSiteLevel(...args)),
    f: $data.selectedChannel
  }, $data.selectedChannel ? {} : {}, {
    g: $data.selectedChannel
  }, $data.selectedChannel ? {
    h: common_vendor.t($data.currentChannel.name),
    i: common_vendor.o((...args) => $options.resetToChannelLevel && $options.resetToChannelLevel(...args))
  } : {}) : {}, {
    j: common_vendor.f($data.sites, (site, k0, i0) => {
      return {
        a: common_vendor.t(site.name),
        b: $data.selectedSite === site.id ? 1 : "",
        c: site.id,
        d: common_vendor.o(($event) => $options.selectSite(site), site.id)
      };
    }),
    k: $options.showChannelLevel
  }, $options.showChannelLevel ? {
    l: common_vendor.f($data.currentSite.channels, (channel, k0, i0) => {
      return {
        a: common_vendor.t(channel.name),
        b: $data.selectedChannel === channel.id ? 1 : "",
        c: channel.id,
        d: common_vendor.o(($event) => $options.selectChannel(channel), channel.id)
      };
    })
  } : {}, {
    m: $options.showContentLevel
  }, $options.showContentLevel ? common_vendor.e({
    n: $data.currentSite.type === "special"
  }, $data.currentSite.type === "special" ? {
    o: common_vendor.o((...args) => $options.goToJiaziDetail && $options.goToJiaziDetail(...args)),
    p: common_vendor.f($data.bookList, (book, index, i0) => {
      return {
        a: common_vendor.t(index + 1),
        b: common_vendor.t(book.title),
        c: common_vendor.t(book.collections),
        d: common_vendor.t(book.collectionChange > 0 ? "↑" : "↓"),
        e: common_vendor.t(Math.abs(book.collectionChange)),
        f: common_vendor.n(book.collectionChange > 0 ? "up" : "down"),
        g: common_vendor.t(book.rankChange > 0 ? "↓" : "↑"),
        h: common_vendor.t(Math.abs(book.rankChange)),
        i: common_vendor.n(book.rankChange > 0 ? "down" : "up"),
        j: book.id
      };
    })
  } : {
    q: common_vendor.f($data.rankingList, (ranking, k0, i0) => {
      return {
        a: common_vendor.t(ranking.name),
        b: common_vendor.t(ranking.desc),
        c: common_vendor.t(ranking.bookCount),
        d: common_vendor.t(ranking.updateTime),
        e: ranking.id,
        f: common_vendor.o(($event) => $options.goToRankingDetail(ranking), ranking.id)
      };
    })
  }) : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-55d17871"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/ranking/index.js.map
