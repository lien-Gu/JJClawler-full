"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  name: "SettingsPage",
  data() {
    return {
      // 用户登录状态
      isLoggedIn: false,
      userInfo: null,
      // 设置选项
      autoRefresh: true,
      dataCache: true,
      autoSubscribe: false
    };
  },
  onLoad() {
    this.loadSettings();
  },
  methods: {
    /**
     * 加载设置
     */
    loadSettings() {
      try {
        this.autoRefresh = common_vendor.index.getStorageSync("autoRefresh") !== false;
        this.dataCache = common_vendor.index.getStorageSync("dataCache") !== false;
        this.autoSubscribe = common_vendor.index.getStorageSync("autoSubscribe") === true;
        const userInfo = common_vendor.index.getStorageSync("userInfo");
        if (userInfo) {
          this.isLoggedIn = true;
          this.userInfo = userInfo;
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/settings/index.vue:86", "加载设置失败:", error);
      }
    },
    /**
     * 处理登录
     */
    handleLogin() {
      if (this.isLoggedIn) {
        this.showUserMenu();
      } else {
        this.goToLogin();
      }
    },
    /**
     * 跳转到登录页面
     */
    goToLogin() {
      common_vendor.index.showModal({
        title: "登录",
        content: "是否要进行登录？",
        confirmText: "登录",
        success: (res) => {
          if (res.confirm) {
            this.mockLogin();
          }
        }
      });
    },
    /**
     * 模拟登录
     */
    mockLogin() {
      const userInfo = {
        id: "12345",
        username: "user123",
        avatar: "",
        loginTime: (/* @__PURE__ */ new Date()).toISOString()
      };
      this.isLoggedIn = true;
      this.userInfo = userInfo;
      common_vendor.index.setStorageSync("userInfo", userInfo);
      common_vendor.index.showToast({
        title: "登录成功",
        icon: "success",
        duration: 1500
      });
    },
    /**
     * 显示用户菜单
     */
    showUserMenu() {
      common_vendor.index.showActionSheet({
        itemList: ["退出登录"],
        success: (res) => {
          if (res.tapIndex === 0) {
            this.logout();
          }
        }
      });
    },
    /**
     * 退出登录
     */
    logout() {
      common_vendor.index.showModal({
        title: "确认退出",
        content: "是否要退出登录？",
        confirmText: "退出",
        success: (res) => {
          if (res.confirm) {
            this.isLoggedIn = false;
            this.userInfo = null;
            common_vendor.index.removeStorageSync("userInfo");
            common_vendor.index.showToast({
              title: "已退出登录",
              icon: "success",
              duration: 1500
            });
          }
        }
      });
    },
    /**
     * 切换自动刷新
     */
    toggleAutoRefresh() {
      this.autoRefresh = !this.autoRefresh;
      common_vendor.index.setStorageSync("autoRefresh", this.autoRefresh);
      common_vendor.index.showToast({
        title: this.autoRefresh ? "已开启自动刷新" : "已关闭自动刷新",
        icon: "none",
        duration: 1500
      });
    },
    /**
     * 切换数据缓存
     */
    toggleDataCache() {
      this.dataCache = !this.dataCache;
      common_vendor.index.setStorageSync("dataCache", this.dataCache);
      common_vendor.index.showToast({
        title: this.dataCache ? "已开启数据缓存" : "已关闭数据缓存",
        icon: "none",
        duration: 1500
      });
    },
    /**
     * 切换自动订阅
     */
    toggleAutoSubscribe() {
      this.autoSubscribe = !this.autoSubscribe;
      common_vendor.index.setStorageSync("autoSubscribe", this.autoSubscribe);
      common_vendor.index.showToast({
        title: this.autoSubscribe ? "已开启自动订阅" : "已关闭自动订阅",
        icon: "none",
        duration: 1500
      });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return {
    a: common_vendor.o((...args) => $options.handleLogin && $options.handleLogin(...args)),
    b: $data.autoRefresh ? 1 : "",
    c: common_vendor.o((...args) => $options.toggleAutoRefresh && $options.toggleAutoRefresh(...args)),
    d: $data.dataCache ? 1 : "",
    e: common_vendor.o((...args) => $options.toggleDataCache && $options.toggleDataCache(...args)),
    f: $data.autoSubscribe ? 1 : "",
    g: common_vendor.o((...args) => $options.toggleAutoSubscribe && $options.toggleAutoSubscribe(...args))
  };
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-a11b3e9a"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/settings/index.js.map
