"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const utils_storage = require("../../utils/storage.js");
const RankingCard = () => "../../components/RankingCard.js";
const _sfc_main = {
  name: "BookDetailPage",
  components: {
    RankingCard
  },
  data() {
    return {
      // 书籍ID
      bookId: "",
      // 书籍数据
      bookData: {},
      // 榜单历史列表
      rankingsList: [],
      // 相关推荐书籍
      recommendedBooks: [],
      // 简介展开状态
      descriptionExpanded: false,
      // 榜单弹窗显示状态
      showRankingsPopup: false,
      // 加载状态
      loading: false,
      loadingRankings: false
    };
  },
  computed: {
    /**
     * 显示的榜单列表（前3个）
     */
    displayRankings() {
      return this.rankingsList.slice(0, 3);
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
          this.fetchRankingsHistory(),
          this.fetchRecommendations()
        ]);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/book/detail.vue:251", "初始化数据失败:", error);
        this.showError("数据加载失败");
      } finally {
        this.loading = false;
      }
    },
    /**
     * 加载缓存数据
     */
    loadCachedData() {
      const cachedBook = utils_storage.getSync(`book_${this.bookId}`);
      const cachedRankings = utils_storage.getSync(`book_rankings_${this.bookId}`);
      const cachedRecommendations = utils_storage.getSync(`book_recommendations_${this.bookId}`);
      if (cachedBook) {
        this.bookData = cachedBook;
      }
      if (cachedRankings) {
        this.rankingsList = cachedRankings;
      }
      if (cachedRecommendations) {
        this.recommendedBooks = cachedRecommendations;
      }
    },
    /**
     * 获取书籍信息
     */
    async fetchBookInfo() {
      try {
        const data = await utils_request.get(`/api/books/${this.bookId}`);
        if (data) {
          this.bookData = data;
          utils_storage.setSync(`book_${this.bookId}`, data, 30 * 60 * 1e3);
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/book/detail.vue:290", "获取书籍信息失败:", error);
        throw error;
      }
    },
    /**
     * 获取榜单历史
     */
    async fetchRankingsHistory() {
      this.loadingRankings = true;
      try {
        const data = await utils_request.get(`/api/books/${this.bookId}/rankings`);
        if (data && data.list) {
          this.rankingsList = data.list;
          utils_storage.setSync(`book_rankings_${this.bookId}`, data.list, 15 * 60 * 1e3);
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/book/detail.vue:308", "获取榜单历史失败:", error);
        throw error;
      } finally {
        this.loadingRankings = false;
      }
    },
    /**
     * 获取相关推荐
     */
    async fetchRecommendations() {
      try {
        const data = await utils_request.get(`/api/books/${this.bookId}/recommendations`, { limit: 8 });
        if (data && data.list) {
          this.recommendedBooks = data.list;
          utils_storage.setSync(`book_recommendations_${this.bookId}`, data.list, 60 * 60 * 1e3);
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/book/detail.vue:326", "获取相关推荐失败:", error);
      }
    },
    /**
     * 刷新数据
     */
    async refreshData() {
      try {
        await Promise.all([
          this.fetchBookInfo(),
          this.fetchRankingsHistory(),
          this.fetchRecommendations()
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
     * 切换关注状态
     */
    async toggleFollow() {
      try {
        const action = this.bookData.isFollowed ? "unfollow" : "follow";
        await utils_request.get(`/api/books/${this.bookId}/${action}`, {}, { method: "POST" });
        this.bookData.isFollowed = !this.bookData.isFollowed;
        common_vendor.index.showToast({
          title: this.bookData.isFollowed ? "关注成功" : "取消关注",
          icon: "success",
          duration: 1500
        });
      } catch (error) {
        this.showError("操作失败");
      }
    },
    /**
     * 阅读书籍
     */
    readBook() {
      if (this.bookData.readUrl) {
        common_vendor.index.navigateTo({
          url: `/pages/reader/index?bookId=${this.bookId}`
        });
      } else {
        common_vendor.index.showToast({
          title: "阅读功能开发中",
          icon: "none"
        });
      }
    },
    /**
     * 分享书籍
     */
    shareBook() {
      common_vendor.index.share({
        provider: "weixin",
        scene: "WXSceneSession",
        type: 0,
        title: this.bookData.name || this.bookData.title,
        summary: `推荐一本好书：${this.bookData.author ? "作者 " + this.bookData.author : ""}`,
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
    },
    /**
     * 切换简介展开状态
     */
    toggleDescription() {
      this.descriptionExpanded = !this.descriptionExpanded;
    },
    /**
     * 显示全部榜单
     */
    showAllRankings() {
      this.showRankingsPopup = true;
    },
    /**
     * 隐藏榜单弹窗
     */
    hideRankingsPopup() {
      this.showRankingsPopup = false;
    },
    /**
     * 格式化字数
     */
    formatWordCount(count) {
      if (typeof count !== "number")
        return count || "0";
      if (count >= 1e4) {
        return (count / 1e4).toFixed(1) + "万";
      } else if (count >= 1e3) {
        return (count / 1e3).toFixed(1) + "k";
      }
      return count.toString();
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
     * 跳转到榜单详情
     */
    goToRankingDetail(ranking) {
      common_vendor.index.navigateTo({
        url: `/pages/ranking/detail?id=${ranking.id}`
      });
    },
    /**
     * 跳转到书籍详情
     */
    goToBookDetail(book) {
      if (book.id === this.bookId)
        return;
      common_vendor.index.redirectTo({
        url: `/pages/book/detail?id=${book.id}`
      });
    }
  }
};
if (!Array) {
  const _component_RankingCard = common_vendor.resolveComponent("RankingCard");
  _component_RankingCard();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $data.bookData.cover
  }, $data.bookData.cover ? {
    b: $data.bookData.cover
  } : {}, {
    c: common_vendor.t($data.bookData.name || $data.bookData.title || "书籍详情"),
    d: $data.bookData.author
  }, $data.bookData.author ? {
    e: common_vendor.t($data.bookData.author)
  } : {}, {
    f: $data.bookData.category
  }, $data.bookData.category ? {
    g: common_vendor.t($data.bookData.category)
  } : {}, {
    h: $data.bookData.category && $data.bookData.status
  }, $data.bookData.category && $data.bookData.status ? {} : {}, {
    i: $data.bookData.status
  }, $data.bookData.status ? {
    j: common_vendor.t($data.bookData.status)
  } : {}, {
    k: $data.bookData.status && $data.bookData.wordCount
  }, $data.bookData.status && $data.bookData.wordCount ? {} : {}, {
    l: $data.bookData.wordCount
  }, $data.bookData.wordCount ? {
    m: common_vendor.t($options.formatWordCount($data.bookData.wordCount))
  } : {}, {
    n: common_vendor.t($data.bookData.isFollowed ? "已关注" : "关注"),
    o: $data.bookData.isFollowed ? 1 : "",
    p: common_vendor.o((...args) => $options.toggleFollow && $options.toggleFollow(...args)),
    q: common_vendor.o((...args) => $options.readBook && $options.readBook(...args)),
    r: common_vendor.o((...args) => $options.shareBook && $options.shareBook(...args)),
    s: common_vendor.t($options.formatNumber($data.bookData.readCount || 0)),
    t: common_vendor.t($options.formatNumber($data.bookData.collectCount || 0)),
    v: common_vendor.t($data.bookData.score || "暂无"),
    w: common_vendor.t($options.formatTime($data.bookData.updateTime)),
    x: $data.bookData.description
  }, $data.bookData.description ? common_vendor.e({
    y: common_vendor.t($data.bookData.description),
    z: $data.descriptionExpanded ? 1 : "",
    A: $data.bookData.description && $data.bookData.description.length > 100
  }, $data.bookData.description && $data.bookData.description.length > 100 ? {
    B: common_vendor.t($data.descriptionExpanded ? "收起" : "展开"),
    C: common_vendor.o((...args) => $options.toggleDescription && $options.toggleDescription(...args))
  } : {}) : {}, {
    D: $data.bookData.tags && $data.bookData.tags.length
  }, $data.bookData.tags && $data.bookData.tags.length ? {
    E: common_vendor.f($data.bookData.tags, (tag, k0, i0) => {
      return {
        a: common_vendor.t(tag),
        b: tag
      };
    })
  } : {}, {
    F: $data.rankingsList.length > 3
  }, $data.rankingsList.length > 3 ? {
    G: common_vendor.o((...args) => $options.showAllRankings && $options.showAllRankings(...args))
  } : {}, {
    H: $data.rankingsList.length > 0
  }, $data.rankingsList.length > 0 ? {
    I: common_vendor.f($options.displayRankings, (ranking, k0, i0) => {
      return {
        a: ranking.id,
        b: common_vendor.o($options.goToRankingDetail, ranking.id),
        c: "f3085b2f-0-" + i0,
        d: common_vendor.p({
          ranking,
          showActions: false,
          showPreview: false
        })
      };
    })
  } : !$data.loadingRankings ? {} : {}, {
    J: !$data.loadingRankings,
    K: $data.loadingRankings
  }, $data.loadingRankings ? {} : {}, {
    L: $data.recommendedBooks.length > 0
  }, $data.recommendedBooks.length > 0 ? {
    M: common_vendor.f($data.recommendedBooks, (book, k0, i0) => {
      return common_vendor.e({
        a: book.cover
      }, book.cover ? {
        b: book.cover
      } : {}, {
        c: common_vendor.t(book.name || book.title),
        d: book.author
      }, book.author ? {
        e: common_vendor.t(book.author)
      } : {}, {
        f: book.id,
        g: common_vendor.o(($event) => $options.goToBookDetail(book), book.id)
      });
    })
  } : {}, {
    N: $data.showRankingsPopup
  }, $data.showRankingsPopup ? {
    O: common_vendor.o((...args) => $options.hideRankingsPopup && $options.hideRankingsPopup(...args)),
    P: common_vendor.f($data.rankingsList, (ranking, k0, i0) => {
      return {
        a: ranking.id,
        b: common_vendor.o($options.goToRankingDetail, ranking.id),
        c: "f3085b2f-1-" + i0,
        d: common_vendor.p({
          ranking,
          showActions: false,
          showPreview: false
        })
      };
    }),
    Q: common_vendor.o(() => {
    }),
    R: common_vendor.o((...args) => $options.hideRankingsPopup && $options.hideRankingsPopup(...args))
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-f3085b2f"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/book/detail.js.map
