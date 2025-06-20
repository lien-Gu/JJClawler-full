"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const utils_storage = require("../../utils/storage.js");
const BookCard = () => "../../components/BookCard.js";
const _sfc_main = {
  name: "RankingDetailPage",
  components: {
    BookCard
  },
  data() {
    return {
      // 榜单ID
      rankingId: "",
      // 榜单数据
      rankingData: {},
      // 书籍列表
      booksList: [],
      // 分页信息
      currentPage: 1,
      pageSize: 20,
      hasMore: true,
      // 筛选选项
      filterOptions: [
        { key: "all", name: "全部" },
        { key: "completed", name: "已完结" },
        { key: "ongoing", name: "连载中" },
        { key: "new", name: "新书" }
      ],
      currentFilter: "all",
      // 排序选项
      sortOptions: [
        { key: "rank", name: "榜单排名" },
        { key: "updateTime", name: "最近更新" },
        { key: "wordCount", name: "字数排序" },
        { key: "score", name: "评分排序" }
      ],
      currentSort: "rank",
      showSortPopup: false,
      // 加载状态
      loading: false,
      loadingMore: false
    };
  },
  computed: {
    /**
     * 当前排序名称
     */
    currentSortName() {
      const option = this.sortOptions.find((item) => item.key === this.currentSort);
      return option ? option.name : "榜单排名";
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
          this.fetchBooksList(true)
        ]);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/detail.vue:245", "初始化数据失败:", error);
        this.showError("数据加载失败");
      } finally {
        this.loading = false;
      }
    },
    /**
     * 加载缓存数据
     */
    loadCachedData() {
      const cachedRanking = utils_storage.getSync(`ranking_${this.rankingId}`);
      const cachedBooks = utils_storage.getSync(`ranking_books_${this.rankingId}`);
      if (cachedRanking) {
        this.rankingData = cachedRanking;
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
        const data = await utils_request.get(`/api/rankings/${this.rankingId}`);
        if (data) {
          this.rankingData = data;
          utils_storage.setSync(`ranking_${this.rankingId}`, data, 30 * 60 * 1e3);
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/detail.vue:279", "获取榜单信息失败:", error);
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
        const params = {
          page: this.currentPage,
          pageSize: this.pageSize,
          filter: this.currentFilter,
          sort: this.currentSort
        };
        const data = await utils_request.get(`/api/rankings/${this.rankingId}/books`, params);
        if (data && data.list) {
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
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/ranking/detail.vue:319", "获取书籍列表失败:", error);
        throw error;
      }
    },
    /**
     * 刷新数据
     */
    async refreshData() {
      try {
        await Promise.all([
          this.fetchRankingInfo(),
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
     * 切换筛选条件
     */
    changeFilter(filterKey) {
      if (this.currentFilter === filterKey)
        return;
      this.currentFilter = filterKey;
      this.fetchBooksList(true);
    },
    /**
     * 显示排序选项
     */
    showSortOptions() {
      this.showSortPopup = true;
    },
    /**
     * 隐藏排序选项
     */
    hideSortOptions() {
      this.showSortPopup = false;
    },
    /**
     * 切换排序方式
     */
    changeSort(sortKey) {
      if (this.currentSort === sortKey) {
        this.hideSortOptions();
        return;
      }
      this.currentSort = sortKey;
      this.hideSortOptions();
      this.fetchBooksList(true);
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
     * 书籍关注事件
     */
    async onBookFollow(event) {
      try {
        const { book, isFollowed } = event;
        const action = isFollowed ? "follow" : "unfollow";
        await utils_request.get(`/api/books/${book.id}/${action}`, {}, { method: "POST" });
        const bookIndex = this.booksList.findIndex((item) => item.id === book.id);
        if (bookIndex !== -1) {
          this.booksList[bookIndex].isFollowed = isFollowed;
        }
        common_vendor.index.showToast({
          title: isFollowed ? "关注成功" : "取消关注",
          icon: "success",
          duration: 1500
        });
      } catch (error) {
        this.showError("操作失败");
      }
    },
    /**
     * 书籍阅读事件
     */
    onBookRead(book) {
      common_vendor.index.__f__("log", "at pages/ranking/detail.vue:529", "阅读书籍:", book);
      common_vendor.index.showToast({
        title: "功能开发中",
        icon: "none"
      });
    },
    /**
     * 书籍分享事件
     */
    onBookShare(book) {
      common_vendor.index.share({
        provider: "weixin",
        scene: "WXSceneSession",
        type: 0,
        title: book.name || book.title,
        summary: `推荐一本好书：${book.author ? "作者 " + book.author : ""}`,
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
  const _component_BookCard = common_vendor.resolveComponent("BookCard");
  _component_BookCard();
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
    k: common_vendor.t($data.rankingData.bookCount || 0),
    l: common_vendor.t($options.formatNumber($data.rankingData.totalViews || 0)),
    m: common_vendor.t($data.rankingData.updateFrequency || "每日"),
    n: common_vendor.t($data.rankingData.followCount || 0),
    o: common_vendor.f($data.filterOptions, (filter, k0, i0) => {
      return {
        a: common_vendor.t(filter.name),
        b: $data.currentFilter === filter.key ? 1 : "",
        c: filter.key,
        d: common_vendor.o(($event) => $options.changeFilter(filter.key), filter.key)
      };
    }),
    p: common_vendor.t($options.currentSortName),
    q: common_vendor.o((...args) => $options.showSortOptions && $options.showSortOptions(...args)),
    r: common_vendor.f($data.booksList, (book, index, i0) => {
      return {
        a: book.id,
        b: common_vendor.o($options.goToBookDetail, book.id),
        c: common_vendor.o($options.onBookFollow, book.id),
        d: common_vendor.o($options.onBookRead, book.id),
        e: common_vendor.o($options.onBookShare, book.id),
        f: "919d4ad2-0-" + i0,
        g: common_vendor.p({
          book: {
            ...book,
            rank: index + 1 + ($data.currentPage - 1) * $data.pageSize
          },
          showRankings: false,
          showActions: true
        })
      };
    }),
    s: $data.hasMore
  }, $data.hasMore ? common_vendor.e({
    t: !$data.loadingMore
  }, !$data.loadingMore ? {
    v: common_vendor.o((...args) => $options.loadMore && $options.loadMore(...args))
  } : {}) : $data.booksList.length > 0 ? {} : {}, {
    w: $data.booksList.length > 0,
    x: !$data.loading && $data.booksList.length === 0
  }, !$data.loading && $data.booksList.length === 0 ? {
    y: common_vendor.o((...args) => $options.refreshData && $options.refreshData(...args))
  } : {}, {
    z: $data.showSortPopup
  }, $data.showSortPopup ? {
    A: common_vendor.o((...args) => $options.hideSortOptions && $options.hideSortOptions(...args)),
    B: common_vendor.f($data.sortOptions, (option, k0, i0) => {
      return common_vendor.e({
        a: common_vendor.t(option.name),
        b: $data.currentSort === option.key
      }, $data.currentSort === option.key ? {} : {}, {
        c: $data.currentSort === option.key ? 1 : "",
        d: option.key,
        e: common_vendor.o(($event) => $options.changeSort(option.key), option.key)
      });
    }),
    C: common_vendor.o(() => {
    }),
    D: common_vendor.o((...args) => $options.hideSortOptions && $options.hideSortOptions(...args))
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-919d4ad2"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/ranking/detail.js.map
