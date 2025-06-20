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
        return true;
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
        common_vendor.index.__f__("log", "at pages/ranking/index.vue:171", "分站数据加载成功:", this.sites);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/index.vue:173", "加载分站数据失败:", error);
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
      } else {
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
     * 加载榜单数据
     */
    async loadRankings(siteId, channelId = "") {
      try {
        common_vendor.index.__f__("log", "at pages/ranking/index.vue:220", "加载榜单数据:", siteId, channelId);
        this.rankingList = this.generateTestRankings(siteId, channelId);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/index.vue:225", "加载榜单数据失败:", error);
      }
    },
    /**
     * 生成测试榜单数据
     */
    generateTestRankings(siteId, channelId = "") {
      const baseRankings = {
        // 书城榜单
        index: [
          { id: "index_1", name: "书城热门榜", desc: "书城最受欢迎的作品", bookCount: 100, updateTime: "1小时前更新" },
          { id: "index_2", name: "书城新书榜", desc: "书城最新发布的作品", bookCount: 80, updateTime: "2小时前更新" },
          { id: "index_3", name: "书城完结榜", desc: "书城已完结的优质作品", bookCount: 60, updateTime: "3小时前更新" }
        ],
        // 言情分站榜单
        yq: [
          { id: "yq_1", name: "言情总榜", desc: "言情分站综合排行", bookCount: 200, updateTime: "30分钟前更新" },
          { id: "yq_2", name: "言情月榜", desc: "本月最受欢迎的言情作品", bookCount: 150, updateTime: "1小时前更新" },
          { id: "yq_3", name: "言情新作榜", desc: "最新发布的言情作品", bookCount: 120, updateTime: "2小时前更新" },
          { id: "yq_4", name: "言情完结榜", desc: "已完结的优质言情作品", bookCount: 90, updateTime: "4小时前更新" }
        ],
        // 纯爱分站榜单
        ca: [
          { id: "ca_1", name: "纯爱总榜", desc: "纯爱分站综合排行", bookCount: 180, updateTime: "45分钟前更新" },
          { id: "ca_2", name: "纯爱热门榜", desc: "最受欢迎的纯爱作品", bookCount: 140, updateTime: "1小时前更新" },
          { id: "ca_3", name: "纯爱新书榜", desc: "最新发布的纯爱作品", bookCount: 110, updateTime: "2小时前更新" },
          { id: "ca_4", name: "纯爱收藏榜", desc: "收藏量最高的纯爱作品", bookCount: 85, updateTime: "3小时前更新" }
        ],
        // 衍生分站榜单
        ys: [
          { id: "ys_1", name: "衍生总榜", desc: "衍生分站综合排行", bookCount: 160, updateTime: "20分钟前更新" },
          { id: "ys_2", name: "衍生热门榜", desc: "最受欢迎的衍生作品", bookCount: 130, updateTime: "1小时前更新" },
          { id: "ys_3", name: "衍生新作榜", desc: "最新发布的衍生作品", bookCount: 100, updateTime: "2小时前更新" }
        ],
        // 无CP+分站榜单
        nocp_plus: [
          { id: "nocp_1", name: "无CP+总榜", desc: "无CP+分站综合排行", bookCount: 140, updateTime: "35分钟前更新" },
          { id: "nocp_2", name: "无CP+热门榜", desc: "最受欢迎的无CP+作品", bookCount: 110, updateTime: "1小时前更新" },
          { id: "nocp_3", name: "无CP+新书榜", desc: "最新发布的无CP+作品", bookCount: 90, updateTime: "3小时前更新" }
        ],
        // 百合分站榜单
        bh: [
          { id: "bh_1", name: "百合热门榜", desc: "最受欢迎的百合作品", bookCount: 80, updateTime: "1小时前更新" },
          { id: "bh_2", name: "百合新书榜", desc: "最新发布的百合作品", bookCount: 60, updateTime: "2小时前更新" },
          { id: "bh_3", name: "百合完结榜", desc: "已完结的优质百合作品", bookCount: 45, updateTime: "4小时前更新" }
        ]
      };
      if (channelId) {
        const channelName = this.currentChannel.name || "频道";
        return [
          { id: `${channelId}_1`, name: `${channelName}热门榜`, desc: `${channelName}最受欢迎的作品`, bookCount: 80, updateTime: "30分钟前更新" },
          { id: `${channelId}_2`, name: `${channelName}新书榜`, desc: `${channelName}最新发布的作品`, bookCount: 60, updateTime: "1小时前更新" },
          { id: `${channelId}_3`, name: `${channelName}完结榜`, desc: `${channelName}已完结的优质作品`, bookCount: 40, updateTime: "2小时前更新" }
        ];
      }
      return baseRankings[siteId] || [
        { id: "default_1", name: "热门榜单", desc: "当前最受欢迎的作品", bookCount: 50, updateTime: "2小时前更新" },
        { id: "default_2", name: "新书榜单", desc: "最新发布的优质作品", bookCount: 30, updateTime: "1小时前更新" },
        { id: "default_3", name: "完结榜单", desc: "已完结的优质作品", bookCount: 25, updateTime: "6小时前更新" }
      ];
    },
    /**
     * 加载夹子书籍列表
     */
    async loadBookList(siteId) {
      try {
        common_vendor.index.__f__("log", "at pages/ranking/index.vue:306", "加载夹子书籍数据:", siteId);
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
        common_vendor.index.__f__("error", "at pages/ranking/index.vue:347", "加载夹子书籍数据失败:", error);
      }
    },
    /**
     * 搜索功能
     */
    onSearch() {
      common_vendor.index.__f__("log", "at pages/ranking/index.vue:356", "搜索关键词:", this.searchKeyword);
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
    c: common_vendor.f($data.sites, (site, k0, i0) => {
      return {
        a: common_vendor.t(site.name),
        b: $data.selectedSite === site.id ? 1 : "",
        c: site.id,
        d: common_vendor.o(($event) => $options.selectSite(site), site.id)
      };
    }),
    d: $options.showChannelLevel
  }, $options.showChannelLevel ? {
    e: common_vendor.f($data.currentSite.channels, (channel, k0, i0) => {
      return {
        a: common_vendor.t(channel.name),
        b: $data.selectedChannel === channel.id ? 1 : "",
        c: channel.id,
        d: common_vendor.o(($event) => $options.selectChannel(channel), channel.id)
      };
    })
  } : {}, {
    f: $options.showContentLevel
  }, $options.showContentLevel ? common_vendor.e({
    g: $data.currentSite.type === "special"
  }, $data.currentSite.type === "special" ? {
    h: common_vendor.o((...args) => $options.goToJiaziDetail && $options.goToJiaziDetail(...args)),
    i: common_vendor.f($data.bookList, (book, index, i0) => {
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
    j: common_vendor.f($data.rankingList, (ranking, k0, i0) => {
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
