"use strict";
const common_vendor = require("../common/vendor.js");
const _sfc_main = {
  name: "BookCard",
  props: {
    book: {
      type: Object,
      required: true,
      default: () => ({})
    },
    clickable: {
      type: Boolean,
      default: true
    },
    showDescription: {
      type: Boolean,
      default: false
    },
    showRankings: {
      type: Boolean,
      default: true
    },
    showActions: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    /**
     * 状态样式类
     */
    statusClass() {
      const status = this.book.status;
      if (status === "完结")
        return "status-completed";
      if (status === "连载")
        return "status-ongoing";
      return "status-default";
    }
  },
  methods: {
    /**
     * 格式化字数显示
     */
    formatWordCount(count) {
      if (typeof count !== "number")
        return count || "未知";
      if (count >= 1e4) {
        return (count / 1e4).toFixed(1) + "万字";
      } else if (count >= 1e3) {
        return (count / 1e3).toFixed(1) + "千字";
      }
      return count + "字";
    },
    /**
     * 格式化时间显示
     */
    formatTime(time) {
      if (!time)
        return "未知";
      const now = /* @__PURE__ */ new Date();
      const updateTime = new Date(time);
      const diff = now - updateTime;
      const minutes = Math.floor(diff / (1e3 * 60));
      const hours = Math.floor(diff / (1e3 * 60 * 60));
      const days = Math.floor(diff / (1e3 * 60 * 60 * 24));
      if (minutes < 60) {
        return `${minutes}分钟前`;
      } else if (hours < 24) {
        return `${hours}小时前`;
      } else if (days < 30) {
        return `${days}天前`;
      } else {
        return updateTime.toLocaleDateString();
      }
    },
    /**
     * 点击卡片事件
     */
    onClick() {
      if (this.clickable) {
        this.$emit("click", this.book);
      }
    },
    /**
     * 关注/取消关注
     */
    onFollow() {
      this.$emit("follow", {
        book: this.book,
        isFollowed: !this.book.isFollowed
      });
    },
    /**
     * 阅读书籍
     */
    onRead() {
      this.$emit("read", this.book);
    },
    /**
     * 分享书籍
     */
    onShare() {
      this.$emit("share", this.book);
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $props.book.cover
  }, $props.book.cover ? {
    b: $props.book.cover
  } : {}, {
    c: common_vendor.t($props.book.name || $props.book.title),
    d: $props.book.author
  }, $props.book.author ? {
    e: common_vendor.t($props.book.author)
  } : {}, {
    f: $props.book.category
  }, $props.book.category ? {
    g: common_vendor.t($props.book.category)
  } : {}, {
    h: $props.book.tags && $props.book.tags.length
  }, $props.book.tags && $props.book.tags.length ? {
    i: common_vendor.f($props.book.tags.slice(0, 3), (tag, k0, i0) => {
      return {
        a: common_vendor.t(tag),
        b: tag
      };
    })
  } : {}, {
    j: $props.book.rank
  }, $props.book.rank ? {
    k: common_vendor.t($props.book.rank)
  } : {}, {
    l: $props.book.description && $props.showDescription
  }, $props.book.description && $props.showDescription ? {
    m: common_vendor.t($props.book.description)
  } : {}, {
    n: $props.book.wordCount
  }, $props.book.wordCount ? {
    o: common_vendor.t($options.formatWordCount($props.book.wordCount))
  } : {}, {
    p: $props.book.updateTime
  }, $props.book.updateTime ? {
    q: common_vendor.t($options.formatTime($props.book.updateTime))
  } : {}, {
    r: $props.book.status
  }, $props.book.status ? {
    s: common_vendor.t($props.book.status),
    t: common_vendor.n($options.statusClass)
  } : {}, {
    v: $props.book.score
  }, $props.book.score ? {
    w: common_vendor.t($props.book.score)
  } : {}, {
    x: $props.showRankings && $props.book.rankings && $props.book.rankings.length
  }, $props.showRankings && $props.book.rankings && $props.book.rankings.length ? {
    y: common_vendor.f($props.book.rankings.slice(0, 2), (ranking, k0, i0) => {
      return {
        a: common_vendor.t(ranking.name),
        b: ranking.id
      };
    })
  } : {}, {
    z: $props.showActions
  }, $props.showActions ? {
    A: common_vendor.t($props.book.isFollowed ? "已关注" : "关注"),
    B: common_vendor.o((...args) => $options.onFollow && $options.onFollow(...args)),
    C: common_vendor.o((...args) => $options.onRead && $options.onRead(...args)),
    D: common_vendor.o((...args) => $options.onShare && $options.onShare(...args))
  } : {}, {
    E: $props.clickable ? 1 : "",
    F: common_vendor.o((...args) => $options.onClick && $options.onClick(...args))
  });
}
const Component = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-c553b042"]]);
wx.createComponent(Component);
//# sourceMappingURL=../../.sourcemap/mp-weixin/components/BookCard.js.map
