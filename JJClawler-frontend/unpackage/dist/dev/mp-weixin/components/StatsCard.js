"use strict";
const common_vendor = require("../common/vendor.js");
const _sfc_main = {
  name: "StatsCard",
  props: {
    title: {
      type: String,
      default: ""
    },
    subtitle: {
      type: String,
      default: ""
    },
    value: {
      type: [Number, String],
      default: 0
    },
    unit: {
      type: String,
      default: ""
    },
    trend: {
      type: Number,
      default: null
    },
    description: {
      type: String,
      default: ""
    },
    clickable: {
      type: Boolean,
      default: false
    },
    color: {
      type: String,
      default: "primary"
    }
  },
  computed: {
    /**
     * 趋势图标
     */
    trendIcon() {
      if (this.trend === null)
        return "";
      return this.trend > 0 ? "↗" : "↘";
    },
    /**
     * 趋势样式类
     */
    trendClass() {
      if (this.trend === null)
        return "";
      return this.trend > 0 ? "trend-up" : "trend-down";
    }
  },
  methods: {
    /**
     * 格式化数字显示
     */
    formatNumber(num) {
      if (typeof num !== "number")
        return num;
      if (num >= 1e4) {
        return (num / 1e4).toFixed(1) + "万";
      } else if (num >= 1e3) {
        return (num / 1e3).toFixed(1) + "k";
      }
      return num.toString();
    },
    /**
     * 点击事件
     */
    onClick() {
      if (this.clickable) {
        this.$emit("click");
      }
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $props.title
  }, $props.title ? common_vendor.e({
    b: common_vendor.t($props.title),
    c: $props.subtitle
  }, $props.subtitle ? {
    d: common_vendor.t($props.subtitle)
  } : {}) : {}, {
    e: common_vendor.t($options.formatNumber($props.value)),
    f: $props.unit
  }, $props.unit ? {
    g: common_vendor.t($props.unit)
  } : {}, {
    h: $props.trend !== null
  }, $props.trend !== null ? {
    i: common_vendor.t($options.trendIcon),
    j: common_vendor.n($options.trendClass),
    k: common_vendor.t(Math.abs($props.trend)),
    l: common_vendor.n($options.trendClass)
  } : {}, {
    m: $props.description
  }, $props.description ? {
    n: common_vendor.t($props.description)
  } : {}, {
    o: $props.clickable ? 1 : "",
    p: common_vendor.o((...args) => $options.onClick && $options.onClick(...args))
  });
}
const Component = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-8f8d3f18"]]);
wx.createComponent(Component);
//# sourceMappingURL=../../.sourcemap/mp-weixin/components/StatsCard.js.map
