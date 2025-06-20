"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const utils_storage = require("../../utils/storage.js");
const RankingCard = () => "../../components/RankingCard.js";
const BookCard = () => "../../components/BookCard.js";
const _sfc_main = {
  name: "FollowPage",
  components: {
    RankingCard,
    BookCard
  },
  data() {
    return {
      // 当前激活的标签页
      activeTab: "rankings",
      // 关注的榜单列表
      followRankings: [],
      // 关注的书籍列表
      followBooks: [],
      // 筛选条件
      selectedSite: "",
      selectedCategory: "",
      // 排序方式
      sortBy: "followTime",
      bookSortBy: "followTime",
      // 排序标签映射
      sortLabels: {
        followTime: "关注时间",
        updateTime: "更新时间",
        name: "名称"
      },
      bookSortLabels: {
        followTime: "关注时间",
        updateTime: "更新时间",
        name: "书名",
        author: "作者"
      },
      // 批量操作模式
      batchMode: false,
      bookBatchMode: false,
      // 选中的项目
      selectedRankings: [],
      selectedBooks: [],
      // 筛选弹窗
      showFilterPopup: false,
      filterTitle: "",
      filterOptions: [],
      filterSelectedValue: "",
      filterType: "",
      // 加载状态
      loadingRankings: false,
      loadingBooks: false
    };
  },
  computed: {
    /**
     * 筛选后的榜单列表
     */
    filteredRankings() {
      let list = [...this.followRankings];
      if (this.selectedSite) {
        list = list.filter((ranking) => ranking.site === this.selectedSite);
      }
      list.sort((a, b) => {
        switch (this.sortBy) {
          case "followTime":
            return new Date(b.followTime) - new Date(a.followTime);
          case "updateTime":
            return new Date(b.updateTime || 0) - new Date(a.updateTime || 0);
          case "name":
            return (a.name || "").localeCompare(b.name || "");
          default:
            return 0;
        }
      });
      return list;
    },
    /**
     * 筛选后的书籍列表
     */
    filteredBooks() {
      let list = [...this.followBooks];
      if (this.selectedCategory) {
        list = list.filter((book) => book.category === this.selectedCategory);
      }
      list.sort((a, b) => {
        switch (this.bookSortBy) {
          case "followTime":
            return new Date(b.followTime) - new Date(a.followTime);
          case "updateTime":
            return new Date(b.updateTime || 0) - new Date(a.updateTime || 0);
          case "name":
            return (a.name || a.title || "").localeCompare(b.name || b.title || "");
          case "author":
            return (a.author || "").localeCompare(b.author || "");
          default:
            return 0;
        }
      });
      return list;
    }
  },
  onLoad() {
    this.initData();
  },
  // 页面显示时刷新数据
  onShow() {
    this.refreshData();
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
      try {
        this.loadCachedData();
        await this.fetchFollowData();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/follow/index.vue:373", "初始化数据失败:", error);
        this.showError("数据加载失败");
      }
    },
    /**
     * 加载缓存数据
     */
    loadCachedData() {
      const cachedRankings = utils_storage.getSync("follow_rankings");
      const cachedBooks = utils_storage.getSync("follow_books");
      if (cachedRankings) {
        this.followRankings = cachedRankings;
      }
      if (cachedBooks) {
        this.followBooks = cachedBooks;
      }
    },
    /**
     * 获取关注数据
     */
    async fetchFollowData() {
      this.loadingRankings = true;
      this.loadingBooks = true;
      try {
        const [rankingsData, booksData] = await Promise.all([
          utils_request.get("/api/user/follows/rankings"),
          utils_request.get("/api/user/follows/books")
        ]);
        if (rankingsData && rankingsData.list) {
          this.followRankings = rankingsData.list;
          utils_storage.setSync("follow_rankings", rankingsData.list, 15 * 60 * 1e3);
        }
        if (booksData && booksData.list) {
          this.followBooks = booksData.list;
          utils_storage.setSync("follow_books", booksData.list, 15 * 60 * 1e3);
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/follow/index.vue:417", "获取关注数据失败:", error);
        throw error;
      } finally {
        this.loadingRankings = false;
        this.loadingBooks = false;
      }
    },
    /**
     * 刷新数据
     */
    async refreshData() {
      try {
        await this.fetchFollowData();
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
     * 切换标签页
     */
    switchTab(tab) {
      this.activeTab = tab;
      this.batchMode = false;
      this.bookBatchMode = false;
      this.selectedRankings = [];
      this.selectedBooks = [];
    },
    /**
     * 显示分站筛选
     */
    showSiteFilter() {
      const sites = [...new Set(this.followRankings.map((r) => r.site).filter(Boolean))];
      this.filterTitle = "选择分站";
      this.filterOptions = [
        { label: "全部分站", value: "" },
        ...sites.map((site) => ({ label: site, value: site }))
      ];
      this.filterSelectedValue = this.selectedSite;
      this.filterType = "site";
      this.showFilterPopup = true;
    },
    /**
     * 显示分类筛选
     */
    showCategoryFilter() {
      const categories = [...new Set(this.followBooks.map((b) => b.category).filter(Boolean))];
      this.filterTitle = "选择分类";
      this.filterOptions = [
        { label: "全部分类", value: "" },
        ...categories.map((category) => ({ label: category, value: category }))
      ];
      this.filterSelectedValue = this.selectedCategory;
      this.filterType = "category";
      this.showFilterPopup = true;
    },
    /**
     * 显示排序选项
     */
    showSortOptions() {
      this.filterTitle = "排序方式";
      this.filterOptions = Object.entries(this.sortLabels).map(([value, label]) => ({
        label,
        value
      }));
      this.filterSelectedValue = this.sortBy;
      this.filterType = "sort";
      this.showFilterPopup = true;
    },
    /**
     * 显示书籍排序选项
     */
    showBookSortOptions() {
      this.filterTitle = "排序方式";
      this.filterOptions = Object.entries(this.bookSortLabels).map(([value, label]) => ({
        label,
        value
      }));
      this.filterSelectedValue = this.bookSortBy;
      this.filterType = "bookSort";
      this.showFilterPopup = true;
    },
    /**
     * 选择筛选选项
     */
    selectFilterOption(option) {
      switch (this.filterType) {
        case "site":
          this.selectedSite = option.value;
          break;
        case "category":
          this.selectedCategory = option.value;
          break;
        case "sort":
          this.sortBy = option.value;
          break;
        case "bookSort":
          this.bookSortBy = option.value;
          break;
      }
      this.hideFilterPopup();
    },
    /**
     * 隐藏筛选弹窗
     */
    hideFilterPopup() {
      this.showFilterPopup = false;
    },
    /**
     * 切换批量操作模式
     */
    toggleBatchMode() {
      this.batchMode = !this.batchMode;
      if (!this.batchMode) {
        this.selectedRankings = [];
      }
    },
    /**
     * 切换书籍批量操作模式
     */
    toggleBookBatchMode() {
      this.bookBatchMode = !this.bookBatchMode;
      if (!this.bookBatchMode) {
        this.selectedBooks = [];
      }
    },
    /**
     * 切换榜单选择状态
     */
    toggleRankingSelection(id) {
      const index = this.selectedRankings.indexOf(id);
      if (index > -1) {
        this.selectedRankings.splice(index, 1);
      } else {
        this.selectedRankings.push(id);
      }
    },
    /**
     * 切换书籍选择状态
     */
    toggleBookSelection(id) {
      const index = this.selectedBooks.indexOf(id);
      if (index > -1) {
        this.selectedBooks.splice(index, 1);
      } else {
        this.selectedBooks.push(id);
      }
    },
    /**
     * 处理榜单点击
     */
    handleRankingTap(ranking) {
      if (this.batchMode) {
        this.toggleRankingSelection(ranking.id);
      } else {
        this.goToRankingDetail(ranking);
      }
    },
    /**
     * 处理书籍点击
     */
    handleBookTap(book) {
      if (this.bookBatchMode) {
        this.toggleBookSelection(book.id);
      } else {
        this.goToBookDetail(book);
      }
    },
    /**
     * 清除选择
     */
    clearSelection() {
      this.selectedRankings = [];
      this.selectedBooks = [];
    },
    /**
     * 批量取消关注
     */
    async batchUnfollow() {
      const items = this.batchMode ? this.selectedRankings : this.selectedBooks;
      const type = this.batchMode ? "rankings" : "books";
      if (items.length === 0)
        return;
      try {
        common_vendor.index.showLoading({ title: "处理中..." });
        await utils_request.get(`/api/user/follows/${type}/batch`, {
          ids: items,
          action: "unfollow"
        }, { method: "POST" });
        if (this.batchMode) {
          this.followRankings = this.followRankings.filter((r) => !items.includes(r.id));
        } else {
          this.followBooks = this.followBooks.filter((b) => !items.includes(b.id));
        }
        this.clearSelection();
        this.batchMode = false;
        this.bookBatchMode = false;
        common_vendor.index.showToast({
          title: "取消关注成功",
          icon: "success"
        });
      } catch (error) {
        this.showError("操作失败");
      } finally {
        common_vendor.index.hideLoading();
      }
    },
    /**
     * 取消关注榜单
     */
    async unfollowRanking(ranking) {
      try {
        await utils_request.get(`/api/rankings/${ranking.id}/unfollow`, {}, { method: "POST" });
        const index = this.followRankings.findIndex((r) => r.id === ranking.id);
        if (index > -1) {
          this.followRankings.splice(index, 1);
        }
        common_vendor.index.showToast({
          title: "取消关注成功",
          icon: "success"
        });
      } catch (error) {
        this.showError("操作失败");
      }
    },
    /**
     * 取消关注书籍
     */
    async unfollowBook(book) {
      try {
        await utils_request.get(`/api/books/${book.id}/unfollow`, {}, { method: "POST" });
        const index = this.followBooks.findIndex((b) => b.id === book.id);
        if (index > -1) {
          this.followBooks.splice(index, 1);
        }
        common_vendor.index.showToast({
          title: "取消关注成功",
          icon: "success"
        });
      } catch (error) {
        this.showError("操作失败");
      }
    },
    /**
     * 格式化关注时间
     */
    formatFollowTime(time) {
      if (!time)
        return "未知";
      const followTime = new Date(time);
      const now = /* @__PURE__ */ new Date();
      const diff = now - followTime;
      const days = Math.floor(diff / (1e3 * 60 * 60 * 24));
      const hours = Math.floor(diff / (1e3 * 60 * 60));
      if (days > 30) {
        return followTime.toLocaleDateString();
      } else if (days > 0) {
        return `${days}天前`;
      } else if (hours > 0) {
        return `${hours}小时前`;
      } else {
        return "刚刚";
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
      common_vendor.index.navigateTo({
        url: `/pages/book/detail?id=${book.id}`
      });
    },
    /**
     * 跳转到榜单页面
     */
    goToRankings() {
      common_vendor.index.switchTab({
        url: "/pages/ranking/index"
      });
    }
  }
};
if (!Array) {
  const _component_RankingCard = common_vendor.resolveComponent("RankingCard");
  const _component_BookCard = common_vendor.resolveComponent("BookCard");
  (_component_RankingCard + _component_BookCard)();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.t($data.followRankings.length),
    b: common_vendor.t($data.followBooks.length),
    c: $data.followRankings.length > 0
  }, $data.followRankings.length > 0 ? {
    d: common_vendor.t($data.followRankings.length)
  } : {}, {
    e: $data.activeTab === "rankings" ? 1 : "",
    f: common_vendor.o(($event) => $options.switchTab("rankings")),
    g: $data.followBooks.length > 0
  }, $data.followBooks.length > 0 ? {
    h: common_vendor.t($data.followBooks.length)
  } : {}, {
    i: $data.activeTab === "books" ? 1 : "",
    j: common_vendor.o(($event) => $options.switchTab("books")),
    k: $data.activeTab === "rankings"
  }, $data.activeTab === "rankings" ? common_vendor.e({
    l: common_vendor.t($data.selectedSite || "全部分站"),
    m: common_vendor.o((...args) => $options.showSiteFilter && $options.showSiteFilter(...args)),
    n: common_vendor.t($data.sortLabels[$data.sortBy]),
    o: common_vendor.o((...args) => $options.showSortOptions && $options.showSortOptions(...args)),
    p: common_vendor.t($data.batchMode ? "完成" : "管理"),
    q: common_vendor.o((...args) => $options.toggleBatchMode && $options.toggleBatchMode(...args)),
    r: $data.batchMode ? 1 : "",
    s: $options.filteredRankings.length > 0
  }, $options.filteredRankings.length > 0 ? {
    t: common_vendor.f($options.filteredRankings, (ranking, k0, i0) => {
      return common_vendor.e($data.batchMode ? common_vendor.e({
        a: $data.selectedRankings.includes(ranking.id)
      }, $data.selectedRankings.includes(ranking.id) ? {} : {}, {
        b: $data.selectedRankings.includes(ranking.id) ? 1 : "",
        c: common_vendor.o(($event) => $options.toggleRankingSelection(ranking.id), ranking.id)
      }) : {}, {
        d: common_vendor.o($options.goToRankingDetail, ranking.id),
        e: common_vendor.o($options.unfollowRanking, ranking.id),
        f: "ee081456-0-" + i0,
        g: common_vendor.p({
          ranking,
          showActions: !$data.batchMode,
          showPreview: true
        }),
        h: common_vendor.t($options.formatFollowTime(ranking.followTime)),
        i: ranking.hasUpdate
      }, ranking.hasUpdate ? {} : {}, {
        j: $data.selectedRankings.includes(ranking.id) ? 1 : "",
        k: ranking.id,
        l: common_vendor.o(($event) => $options.handleRankingTap(ranking), ranking.id)
      });
    }),
    v: $data.batchMode,
    w: $data.batchMode ? 1 : ""
  } : !$data.loadingRankings ? {
    y: common_vendor.o((...args) => $options.goToRankings && $options.goToRankings(...args))
  } : {}, {
    x: !$data.loadingRankings
  }) : {}, {
    z: $data.activeTab === "books"
  }, $data.activeTab === "books" ? common_vendor.e({
    A: common_vendor.t($data.selectedCategory || "全部分类"),
    B: common_vendor.o((...args) => $options.showCategoryFilter && $options.showCategoryFilter(...args)),
    C: common_vendor.t($data.bookSortLabels[$data.bookSortBy]),
    D: common_vendor.o((...args) => $options.showBookSortOptions && $options.showBookSortOptions(...args)),
    E: common_vendor.t($data.bookBatchMode ? "完成" : "管理"),
    F: common_vendor.o((...args) => $options.toggleBookBatchMode && $options.toggleBookBatchMode(...args)),
    G: $data.bookBatchMode ? 1 : "",
    H: $options.filteredBooks.length > 0
  }, $options.filteredBooks.length > 0 ? {
    I: common_vendor.f($options.filteredBooks, (book, k0, i0) => {
      return common_vendor.e($data.bookBatchMode ? common_vendor.e({
        a: $data.selectedBooks.includes(book.id)
      }, $data.selectedBooks.includes(book.id) ? {} : {}, {
        b: $data.selectedBooks.includes(book.id) ? 1 : "",
        c: common_vendor.o(($event) => $options.toggleBookSelection(book.id), book.id)
      }) : {}, {
        d: common_vendor.o($options.goToBookDetail, book.id),
        e: common_vendor.o($options.unfollowBook, book.id),
        f: "ee081456-1-" + i0,
        g: common_vendor.p({
          book,
          showActions: !$data.bookBatchMode
        }),
        h: common_vendor.t($options.formatFollowTime(book.followTime)),
        i: book.hasUpdate
      }, book.hasUpdate ? {} : {}, {
        j: $data.selectedBooks.includes(book.id) ? 1 : "",
        k: book.id,
        l: common_vendor.o(($event) => $options.handleBookTap(book), book.id)
      });
    }),
    J: $data.bookBatchMode,
    K: $data.bookBatchMode ? 1 : ""
  } : !$data.loadingBooks ? {
    M: common_vendor.o((...args) => $options.goToRankings && $options.goToRankings(...args))
  } : {}, {
    L: !$data.loadingBooks
  }) : {}, {
    N: $data.batchMode && $data.selectedRankings.length > 0 || $data.bookBatchMode && $data.selectedBooks.length > 0
  }, $data.batchMode && $data.selectedRankings.length > 0 || $data.bookBatchMode && $data.selectedBooks.length > 0 ? {
    O: common_vendor.t($data.batchMode ? $data.selectedRankings.length : $data.selectedBooks.length),
    P: common_vendor.o((...args) => $options.clearSelection && $options.clearSelection(...args)),
    Q: common_vendor.o((...args) => $options.batchUnfollow && $options.batchUnfollow(...args))
  } : {}, {
    R: $data.loadingRankings || $data.loadingBooks
  }, $data.loadingRankings || $data.loadingBooks ? {} : {}, {
    S: $data.showFilterPopup
  }, $data.showFilterPopup ? {
    T: common_vendor.t($data.filterTitle),
    U: common_vendor.o((...args) => $options.hideFilterPopup && $options.hideFilterPopup(...args)),
    V: common_vendor.f($data.filterOptions, (option, k0, i0) => {
      return common_vendor.e({
        a: common_vendor.t(option.label),
        b: option.value === $data.filterSelectedValue
      }, option.value === $data.filterSelectedValue ? {} : {}, {
        c: option.value === $data.filterSelectedValue ? 1 : "",
        d: option.value,
        e: common_vendor.o(($event) => $options.selectFilterOption(option), option.value)
      });
    }),
    W: common_vendor.o(() => {
    }),
    X: common_vendor.o((...args) => $options.hideFilterPopup && $options.hideFilterPopup(...args))
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-ee081456"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/follow/index.js.map
