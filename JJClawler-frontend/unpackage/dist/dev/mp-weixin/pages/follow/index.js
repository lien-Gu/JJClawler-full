"use strict";
const common_vendor = require("../../common/vendor.js");
const BookList = () => "../../components/BookList.js";
const _sfc_main = {
  name: "FollowPage",
  components: {
    BookList
  },
  data() {
    return {
      searchKeyword: "",
      followedBooks: []
    };
  },
  onLoad() {
    this.loadFollowedBooks();
  },
  onShow() {
    this.loadFollowedBooks();
  },
  // 下拉刷新
  onPullDownRefresh() {
    this.loadFollowedBooks().finally(() => {
      common_vendor.index.stopPullDownRefresh();
    });
  },
  methods: {
    /**
     * 加载关注的书籍列表
     */
    async loadFollowedBooks() {
      try {
        this.followedBooks = Array.from({ length: 20 }, (_, index) => ({
          id: `book_${index + 1}`,
          title: "重生之农女",
          clicks: 193,
          collections: 34
        }));
        common_vendor.index.__f__("log", "at pages/follow/index.vue:98", "加载关注书籍列表:", this.followedBooks.length);
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/follow/index.vue:100", "加载关注书籍失败:", error);
        common_vendor.index.showToast({
          title: "加载失败",
          icon: "none",
          duration: 2e3
        });
      }
    },
    /**
     * 搜索输入
     */
    onSearchInput(e) {
      common_vendor.index.__f__("log", "at pages/follow/index.vue:113", "搜索关注书籍:", e.detail.value);
      this.searchKeyword = e.detail.value;
    },
    /**
     * 处理书籍点击（BookList组件事件）
     */
    handleBookTap({ book, index }) {
      this.goToBookDetail(book);
    },
    /**
     * 处理取消关注（BookList组件事件）
     */
    handleUnfollow({ book, index }) {
      this.unfollowBook(book);
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
     * 取消关注书籍
     */
    async unfollowBook(book) {
      try {
        const index = this.followedBooks.findIndex((item) => item.id === book.id);
        if (index > -1) {
          this.followedBooks.splice(index, 1);
        }
        common_vendor.index.showToast({
          title: "已取消关注",
          icon: "success",
          duration: 1500
        });
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/follow/index.vue:162", "取消关注失败:", error);
        common_vendor.index.showToast({
          title: "操作失败",
          icon: "none",
          duration: 2e3
        });
      }
    }
  }
};
if (!Array) {
  const _component_BookList = common_vendor.resolveComponent("BookList");
  _component_BookList();
}
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_vendor.o([($event) => $data.searchKeyword = $event.detail.value, (...args) => $options.onSearchInput && $options.onSearchInput(...args)]),
    b: $data.searchKeyword,
    c: common_vendor.o($options.handleBookTap),
    d: common_vendor.o($options.handleUnfollow),
    e: common_vendor.p({
      books: $data.followedBooks,
      ["show-count"]: false,
      ["show-rank"]: true,
      ["show-actions"]: true,
      ["action-type"]: "unfollow",
      ["empty-text"]: "暂无关注的书籍"
    })
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-ee081456"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/follow/index.js.map
