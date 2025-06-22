"use strict";
const common_vendor = require("../common/vendor.js");
const _sfc_main = {
  name: "RankingCard",
  props: {
    ranking: {
      type: Object,
      required: true,
      default: () => ({})
    },
    clickable: {
      type: Boolean,
      default: true
    },
    showPreview: {
      type: Boolean,
      default: true
    },
    showActions: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    /**
     * 格式化数字显示
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
      } else if (days < 7) {
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
        this.$emit("click", this.ranking);
      }
    },
    /**
     * 关注/取消关注
     */
    onFollow() {
      this.$emit("follow", {
        ranking: this.ranking,
        isFollowed: !this.ranking.isFollowed
      });
    },
    /**
     * 分享榜单
     */
    onShare() {
      this.$emit("share", this.ranking);
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.t($props.ranking.name || $props.ranking.title),
    b: $props.ranking.description
  }, $props.ranking.description ? {
    c: common_vendor.t($props.ranking.description)
  } : {}, {
    d: $props.ranking.isHot
  }, $props.ranking.isHot ? {} : {}, {
    e: common_vendor.t($options.formatNumber($props.ranking.bookCount || 0)),
    f: common_vendor.t($options.formatTime($props.ranking.updateTime)),
    g: $props.ranking.viewCount
  }, $props.ranking.viewCount ? {
    h: common_vendor.t($options.formatNumber($props.ranking.viewCount))
  } : {}, {
    i: $props.showPreview && $props.ranking.topBooks
  }, $props.showPreview && $props.ranking.topBooks ? {
    j: common_vendor.f($props.ranking.topBooks.slice(0, 3), (book, index, i0) => {
      return {
        a: common_vendor.t(book.name || book.title),
        b: book.id || index
      };
    })
  } : {}, {
    k: $props.showActions
  }, $props.showActions ? {
    l: common_vendor.t($props.ranking.isFollowed ? "已关注" : "关注"),
    m: common_vendor.o((...args) => $options.onFollow && $options.onFollow(...args)),
    n: common_vendor.o((...args) => $options.onShare && $options.onShare(...args))
  } : {}, {
    o: $props.clickable ? 1 : "",
    p: common_vendor.o((...args) => $options.onClick && $options.onClick(...args))
  });
}
const Component = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-d5c0b331"]]);
wx.createComponent(Component);
//# sourceMappingURL=../../.sourcemap/mp-weixin/components/RankingCard.js.map
