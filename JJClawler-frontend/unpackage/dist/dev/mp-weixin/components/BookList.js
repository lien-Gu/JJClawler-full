"use strict";
const common_vendor = require("../common/vendor.js");
const _sfc_main = {
  name: "BookList",
  props: {
    // 书籍列表数据
    books: {
      type: Array,
      default: () => []
    },
    // 列表标题
    title: {
      type: String,
      default: ""
    },
    // 是否显示数量
    showCount: {
      type: Boolean,
      default: false
    },
    // 是否显示排名
    showRank: {
      type: Boolean,
      default: true
    },
    // 是否显示操作按钮
    showActions: {
      type: Boolean,
      default: false
    },
    // 操作类型 unfollow-取消关注
    actionType: {
      type: String,
      default: "unfollow"
    },
    // 空状态文本
    emptyText: {
      type: String,
      default: "暂无数据"
    }
  },
  methods: {
    /**
     * 处理书籍点击
     */
    handleBookTap(book, index) {
      this.$emit("book-tap", { book, index });
    },
    /**
     * 处理取消关注
     */
    handleUnfollow(book, index) {
      this.$emit("unfollow", { book, index });
    },
    /**
     * 格式化数字
     */
    formatNumber(num) {
      if (num >= 1e4) {
        return (num / 1e4).toFixed(1) + "万";
      }
      return num.toString();
    },
    /**
     * 格式化变化值
     */
    formatChange(change) {
      if (change > 0) {
        return `+${change}`;
      } else if (change < 0) {
        return change.toString();
      } else {
        return "0";
      }
    },
    /**
     * 格式化排名变化
     */
    formatRankChange(change) {
      if (change > 0) {
        return `↗ +${change}`;
      } else if (change < 0) {
        return `↘ ${change}`;
      } else {
        return `— 0`;
      }
    },
    /**
     * 获取变化样式类名
     */
    getChangeClass(change) {
      if (change > 0) {
        return "positive";
      } else if (change < 0) {
        return "negative";
      } else {
        return "neutral";
      }
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $props.title
  }, $props.title ? common_vendor.e({
    b: common_vendor.t($props.title),
    c: $props.showCount
  }, $props.showCount ? {
    d: common_vendor.t($props.books.length)
  } : {}) : {}, {
    e: common_vendor.f($props.books, (book, index, i0) => {
      return common_vendor.e($props.showRank ? {
        a: common_vendor.t(index + 1)
      } : {}, {
        b: common_vendor.t(book.title),
        c: book.clicks !== void 0
      }, book.clicks !== void 0 ? {
        d: common_vendor.t($options.formatNumber(book.clicks))
      } : {}, {
        e: book.collections !== void 0
      }, book.collections !== void 0 ? {
        f: common_vendor.t($options.formatNumber(book.collections))
      } : {}, {
        g: book.collectionChange !== void 0
      }, book.collectionChange !== void 0 ? {
        h: common_vendor.t($options.formatChange(book.collectionChange)),
        i: common_vendor.n($options.getChangeClass(book.collectionChange))
      } : {}, {
        j: book.rankChange !== void 0
      }, book.rankChange !== void 0 ? {
        k: common_vendor.t($options.formatRankChange(book.rankChange)),
        l: common_vendor.n($options.getChangeClass(book.rankChange))
      } : {}, $props.showActions ? common_vendor.e({
        m: $props.actionType === "unfollow"
      }, $props.actionType === "unfollow" ? {
        n: common_vendor.o(($event) => $options.handleUnfollow(book, index), book.id)
      } : {}) : {}, {
        o: book.id,
        p: common_vendor.o(($event) => $options.handleBookTap(book, index), book.id)
      });
    }),
    f: $props.showRank,
    g: $props.showActions,
    h: $props.books.length === 0
  }, $props.books.length === 0 ? {
    i: common_vendor.t($props.emptyText || "暂无数据")
  } : {});
}
const Component = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-49050182"]]);
wx.createComponent(Component);
//# sourceMappingURL=../../.sourcemap/mp-weixin/components/BookList.js.map
