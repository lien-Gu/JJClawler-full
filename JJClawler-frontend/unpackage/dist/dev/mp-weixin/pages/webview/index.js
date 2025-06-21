"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  name: "WebViewPage",
  data() {
    return {
      targetUrl: "",
      pageTitle: "加载中...",
      loading: true,
      error: "",
      // 平台检测
      isH5: false,
      isMiniProgram: false,
      isApp: false
    };
  },
  onLoad(options) {
    this.detectPlatform();
    if (options.url) {
      this.targetUrl = decodeURIComponent(options.url);
    }
    if (options.title) {
      this.pageTitle = decodeURIComponent(options.title);
    }
    this.loadContent();
  },
  methods: {
    /**
     * 检测当前平台
     */
    detectPlatform() {
      this.isMiniProgram = true;
    },
    /**
     * 加载内容
     */
    async loadContent() {
      if (!this.targetUrl) {
        this.error = "缺少URL参数";
        this.loading = false;
        return;
      }
      try {
        this.loading = true;
        this.error = "";
        await new Promise((resolve) => setTimeout(resolve, 1e3));
        await this.handleUrlByPlatform();
        this.loading = false;
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/webview/index.vue:134", "加载内容失败:", err);
        this.error = err.message || "加载失败";
        this.loading = false;
      }
    },
    /**
     * 根据平台处理URL
     */
    async handleUrlByPlatform() {
      if (this.isH5) {
        common_vendor.index.__f__("log", "at pages/webview/index.vue:146", "H5环境，使用iframe加载:", this.targetUrl);
      } else if (this.isMiniProgram) {
        common_vendor.index.__f__("log", "at pages/webview/index.vue:149", "小程序环境，使用web-view加载:", this.targetUrl);
        if (!this.isValidMiniProgramUrl(this.targetUrl)) {
          throw new Error("URL不在小程序业务域名白名单中");
        }
      } else if (this.isApp) {
        common_vendor.index.__f__("log", "at pages/webview/index.vue:157", "APP环境，准备在系统浏览器中打开:", this.targetUrl);
      }
    },
    /**
     * 检查URL是否适用于小程序
     */
    isValidMiniProgramUrl(url) {
      return true;
    },
    /**
     * 重试加载
     */
    retryLoad() {
      this.loadContent();
    },
    /**
     * 返回上一页
     */
    goBack() {
      common_vendor.index.navigateBack({
        fail: () => {
          common_vendor.index.switchTab({
            url: "/pages/index/index"
          });
        }
      });
    },
    /**
     * 在浏览器中打开
     */
    openInBrowser() {
      common_vendor.index.showModal({
        title: "提示",
        content: "请复制链接到浏览器中打开",
        showCancel: true,
        cancelText: "取消",
        confirmText: "复制链接",
        success: (res) => {
          if (res.confirm) {
            common_vendor.index.setClipboardData({
              data: this.targetUrl,
              success: () => {
                common_vendor.index.showToast({
                  title: "链接已复制",
                  icon: "success"
                });
              }
            });
          }
        }
      });
    },
    /**
     * Web-view消息处理
     */
    onWebViewMessage(event) {
      common_vendor.index.__f__("log", "at pages/webview/index.vue:231", "收到web-view消息:", event.detail.data);
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.o((...args) => $options.goBack && $options.goBack(...args)),
    b: common_vendor.t($data.pageTitle),
    c: $data.loading
  }, $data.loading ? {} : $data.error ? {
    e: common_vendor.t($data.error),
    f: common_vendor.o((...args) => $options.retryLoad && $options.retryLoad(...args))
  } : common_vendor.e({
    g: $data.isH5
  }, $data.isH5 ? {
    h: $data.targetUrl
  } : $data.isMiniProgram ? {
    j: $data.targetUrl,
    k: common_vendor.o((...args) => $options.onWebViewMessage && $options.onWebViewMessage(...args))
  } : {
    l: common_vendor.t($data.targetUrl),
    m: common_vendor.o((...args) => $options.openInBrowser && $options.openInBrowser(...args))
  }, {
    i: $data.isMiniProgram
  }), {
    d: $data.error
  });
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-a96d96f3"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/webview/index.js.map
