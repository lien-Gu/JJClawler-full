"use strict";
const common_vendor = require("../../common/vendor.js");
const data_url = require("../../data/url.js");
const _sfc_main = {
  data() {
    return {
      searchKeyword: "",
      currentLevel: 1,
      // 1: 分站选择, 2: 频道选择, 3: 榜单列表
      selectedSite: "",
      selectedChannel: "",
      currentSite: {},
      currentChannel: {},
      sites: [],
      rankingList: []
    };
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
        common_vendor.index.__f__("log", "at pages/ranking/index.vue:112", "分站数据加载成功:", this.sites);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/index.vue:114", "加载分站数据失败:", error);
      }
    },
    /**
     * 选择分站
     */
    selectSite(site) {
      this.selectedSite = site.id;
      this.currentSite = site;
      if (site.channels && site.channels.length > 0) {
        this.currentLevel = 2;
      } else {
        this.currentLevel = 3;
        this.loadRankings(site.id);
      }
    },
    /**
     * 选择频道
     */
    selectChannel(channel) {
      this.selectedChannel = channel.id;
      this.currentChannel = channel;
      this.currentLevel = 3;
      this.loadRankings(this.selectedSite, channel.id);
    },
    /**
     * 返回指定层级
     */
    goToLevel(level) {
      this.currentLevel = level;
      if (level === 1) {
        this.selectedSite = "";
        this.selectedChannel = "";
        this.currentSite = {};
        this.currentChannel = {};
      }
    },
    /**
     * 加载榜单数据
     */
    async loadRankings(siteId, channelId = "") {
      try {
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
          }
        ];
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/index.vue:183", "加载榜单数据失败:", error);
      }
    },
    /**
     * 搜索功能
     */
    onSearch() {
      common_vendor.index.__f__("log", "at pages/ranking/index.vue:192", "搜索关键词:", this.searchKeyword);
    },
    /**
     * 跳转到榜单详情
     */
    goToRankingDetail(ranking) {
      common_vendor.index.navigateTo({
        url: `/pages/ranking/detail?id=${ranking.id}`
      });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.t($data.currentLevel),
    b: common_vendor.t($data.sites.length),
    c: common_vendor.t($data.selectedSite),
    d: common_vendor.t($data.rankingList.length),
    e: common_vendor.o([($event) => $data.searchKeyword = $event.detail.value, (...args) => $options.onSearch && $options.onSearch(...args)]),
    f: $data.searchKeyword,
    g: $data.currentLevel > 1
  }, $data.currentLevel > 1 ? common_vendor.e({
    h: common_vendor.t($data.currentSite.name),
    i: common_vendor.o(($event) => $options.goToLevel(1)),
    j: $data.currentLevel > 2
  }, $data.currentLevel > 2 ? {} : {}, {
    k: $data.currentLevel > 2
  }, $data.currentLevel > 2 ? {
    l: common_vendor.t($data.currentChannel.name)
  } : {}) : {}, {
    m: $data.currentLevel === 1
  }, $data.currentLevel === 1 ? {
    n: common_vendor.f($data.sites, (site, k0, i0) => {
      return {
        a: common_vendor.t(site.name),
        b: $data.selectedSite === site.id ? 1 : "",
        c: site.id,
        d: common_vendor.o(($event) => $options.selectSite(site), site.id)
      };
    })
  } : {}, {
    o: $data.currentLevel === 2 && $data.currentSite.channels.length > 0
  }, $data.currentLevel === 2 && $data.currentSite.channels.length > 0 ? {
    p: common_vendor.f($data.currentSite.channels, (channel, k0, i0) => {
      return {
        a: common_vendor.t(channel.name),
        b: $data.selectedChannel === channel.id ? 1 : "",
        c: channel.id,
        d: common_vendor.o(($event) => $options.selectChannel(channel), channel.id)
      };
    })
  } : {}, {
    q: $data.currentLevel === 3
  }, $data.currentLevel === 3 ? {
    r: common_vendor.f($data.rankingList, (ranking, k0, i0) => {
      return {
        a: common_vendor.t(ranking.name),
        b: common_vendor.t(ranking.desc),
        c: common_vendor.t(ranking.bookCount),
        d: common_vendor.t(ranking.updateTime),
        e: ranking.id,
        f: common_vendor.o(($event) => $options.goToRankingDetail(ranking), ranking.id)
      };
    })
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-55d17871"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/ranking/index.js.map
