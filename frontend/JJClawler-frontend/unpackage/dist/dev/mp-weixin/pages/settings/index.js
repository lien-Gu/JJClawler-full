"use strict";
const common_vendor = require("../../common/vendor.js");
const utils_request = require("../../utils/request.js");
const utils_storage = require("../../utils/storage.js");
const _sfc_main = {
  name: "SettingsPage",
  data() {
    return {
      // 用户信息
      userInfo: {
        id: "",
        nickname: "",
        avatar: "",
        isLogin: false
      },
      // 用户统计
      userStats: {
        followRankings: 0,
        followBooks: 0,
        readHistory: 0
      },
      // 应用设置
      settings: {
        pushNotification: true,
        autoRefresh: true,
        enableCache: true,
        theme: "auto"
        // auto, light, dark
      },
      // 主题选项
      themeOptions: [
        { value: "auto", label: "跟随系统", icon: "🔄" },
        { value: "light", label: "浅色模式", icon: "☀️" },
        { value: "dark", label: "深色模式", icon: "🌙" }
      ],
      themeLabels: {
        auto: "跟随系统",
        light: "浅色模式",
        dark: "深色模式"
      },
      // 缓存信息
      cacheSize: 0,
      cacheInfo: {
        images: 0,
        data: 0
      },
      // 应用信息
      appVersion: "1.0.0",
      // 弹窗状态
      showThemePopup: false,
      showCachePopup: false,
      // 加载状态
      updateChecking: false
    };
  },
  onLoad() {
    this.initData();
  },
  onShow() {
    this.refreshUserStats();
  },
  methods: {
    /**
     * 初始化数据
     */
    async initData() {
      try {
        this.loadUserInfo();
        this.loadSettings();
        await this.getCacheInfo();
        await this.fetchUserStats();
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/settings/index.vue:351", "初始化设置页面失败:", error);
      }
    },
    /**
     * 加载用户信息
     */
    loadUserInfo() {
      const cachedUser = utils_storage.getSync("user_info");
      if (cachedUser) {
        this.userInfo = {
          ...this.userInfo,
          ...cachedUser,
          isLogin: true
        };
      }
    },
    /**
     * 加载应用设置
     */
    loadSettings() {
      const cachedSettings = utils_storage.getSync("app_settings");
      if (cachedSettings) {
        this.settings = {
          ...this.settings,
          ...cachedSettings
        };
      }
    },
    /**
     * 获取用户统计
     */
    async fetchUserStats() {
      try {
        const data = await utils_request.get("/api/user/stats");
        if (data) {
          this.userStats = data;
        }
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/settings/index.vue:392", "获取用户统计失败:", error);
        const followRankings = utils_storage.getSync("follow_rankings") || [];
        const followBooks = utils_storage.getSync("follow_books") || [];
        this.userStats = {
          followRankings: followRankings.length,
          followBooks: followBooks.length,
          readHistory: 0
        };
      }
    },
    /**
     * 刷新用户统计
     */
    async refreshUserStats() {
      await this.fetchUserStats();
    },
    /**
     * 获取缓存信息
     */
    async getCacheInfo() {
      try {
        const imageCache = Math.random() * 10 * 1024 * 1024;
        const dataCache = Math.random() * 5 * 1024 * 1024;
        this.cacheInfo = {
          images: imageCache,
          data: dataCache
        };
        this.cacheSize = imageCache + dataCache;
      } catch (error) {
        common_vendor.index.__f__("error", "at pages/settings/index.vue:429", "获取缓存信息失败:", error);
      }
    },
    /**
     * 切换设置项
     */
    toggleSetting(key, event) {
      this.settings[key] = event.detail.value;
      this.saveSettings();
    },
    /**
     * 保存设置
     */
    saveSettings() {
      utils_storage.setSync("app_settings", this.settings);
      common_vendor.index.showToast({
        title: "设置已保存",
        icon: "success",
        duration: 1500
      });
    },
    /**
     * 显示主题选择
     */
    showThemeOptions() {
      this.showThemePopup = true;
    },
    /**
     * 隐藏主题弹窗
     */
    hideThemePopup() {
      this.showThemePopup = false;
    },
    /**
     * 选择主题
     */
    selectTheme(theme) {
      this.settings.theme = theme;
      this.saveSettings();
      this.hideThemePopup();
      this.applyTheme(theme);
    },
    /**
     * 应用主题
     */
    applyTheme(theme) {
      common_vendor.index.__f__("log", "at pages/settings/index.vue:486", "应用主题:", theme);
    },
    /**
     * 显示缓存管理
     */
    showCacheManager() {
      this.getCacheInfo();
      this.showCachePopup = true;
    },
    /**
     * 隐藏缓存弹窗
     */
    hideCachePopup() {
      this.showCachePopup = false;
    },
    /**
     * 清理缓存
     */
    async clearCache(type) {
      try {
        common_vendor.index.showLoading({ title: "清理中..." });
        switch (type) {
          case "images":
            this.cacheInfo.images = 0;
            break;
          case "data":
            utils_storage.clearSync();
            this.cacheInfo.data = 0;
            break;
          case "all":
            utils_storage.clearSync();
            this.cacheInfo.images = 0;
            this.cacheInfo.data = 0;
            break;
        }
        this.cacheSize = this.cacheInfo.images + this.cacheInfo.data;
        common_vendor.index.showToast({
          title: "清理完成",
          icon: "success"
        });
      } catch (error) {
        common_vendor.index.showToast({
          title: "清理失败",
          icon: "none"
        });
      } finally {
        common_vendor.index.hideLoading();
      }
    },
    /**
     * 检查更新
     */
    async checkUpdate() {
      this.updateChecking = true;
      try {
        await new Promise((resolve) => setTimeout(resolve, 2e3));
        common_vendor.index.showToast({
          title: "已是最新版本",
          icon: "success"
        });
      } catch (error) {
        common_vendor.index.showToast({
          title: "检查更新失败",
          icon: "none"
        });
      } finally {
        this.updateChecking = false;
      }
    },
    /**
     * 显示登录
     */
    showLogin() {
      common_vendor.index.showToast({
        title: "登录功能开发中",
        icon: "none"
      });
    },
    /**
     * 显示个人资料
     */
    showProfile() {
      common_vendor.index.showToast({
        title: "个人资料功能开发中",
        icon: "none"
      });
    },
    /**
     * 跳转到反馈页面
     */
    goToFeedback() {
      common_vendor.index.showToast({
        title: "反馈功能开发中",
        icon: "none"
      });
    },
    /**
     * 显示关于我们
     */
    showAbout() {
      common_vendor.index.showModal({
        title: "关于 JJClawler",
        content: `JJClawler 是一个晋江文学城数据展示小程序

版本：${this.appVersion}
开发者：JJClawler Team`,
        showCancel: false,
        confirmText: "确定"
      });
    },
    /**
     * 显示退出登录确认
     */
    showLogoutConfirm() {
      common_vendor.index.showModal({
        title: "退出登录",
        content: "确定要退出登录吗？",
        success: (res) => {
          if (res.confirm) {
            this.logout();
          }
        }
      });
    },
    /**
     * 退出登录
     */
    logout() {
      utils_storage.removeSync("user_info");
      this.userInfo = {
        id: "",
        nickname: "",
        avatar: "",
        isLogin: false
      };
      this.userStats = {
        followRankings: 0,
        followBooks: 0,
        readHistory: 0
      };
      common_vendor.index.showToast({
        title: "已退出登录",
        icon: "success"
      });
    },
    /**
     * 格式化缓存大小
     */
    formatCacheSize(size) {
      if (typeof size !== "number")
        return "0B";
      const units = ["B", "KB", "MB", "GB"];
      let unitIndex = 0;
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
      }
      return `${size.toFixed(1)}${units[unitIndex]}`;
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: $data.userInfo.avatar
  }, $data.userInfo.avatar ? {
    b: $data.userInfo.avatar
  } : {}, {
    c: common_vendor.t($data.userInfo.nickname || "未设置昵称"),
    d: $data.userInfo.id
  }, $data.userInfo.id ? {
    e: common_vendor.t($data.userInfo.id)
  } : {}, {
    f: common_vendor.t($data.userInfo.isLogin ? "已登录" : "未登录"),
    g: !$data.userInfo.isLogin
  }, !$data.userInfo.isLogin ? {
    h: common_vendor.o((...args) => $options.showLogin && $options.showLogin(...args))
  } : {
    i: common_vendor.o((...args) => $options.showProfile && $options.showProfile(...args))
  }, {
    j: common_vendor.t($data.userStats.followRankings || 0),
    k: common_vendor.t($data.userStats.followBooks || 0),
    l: common_vendor.t($data.userStats.readHistory || 0),
    m: $data.settings.pushNotification,
    n: common_vendor.o(($event) => $options.toggleSetting("pushNotification", $event)),
    o: $data.settings.autoRefresh,
    p: common_vendor.o(($event) => $options.toggleSetting("autoRefresh", $event)),
    q: $data.settings.enableCache,
    r: common_vendor.o(($event) => $options.toggleSetting("enableCache", $event)),
    s: common_vendor.t($data.themeLabels[$data.settings.theme]),
    t: common_vendor.o((...args) => $options.showThemeOptions && $options.showThemeOptions(...args)),
    v: common_vendor.t($options.formatCacheSize($data.cacheSize)),
    w: common_vendor.o((...args) => $options.showCacheManager && $options.showCacheManager(...args)),
    x: common_vendor.t($data.appVersion),
    y: $data.updateChecking
  }, $data.updateChecking ? {} : {}, {
    z: common_vendor.o((...args) => $options.checkUpdate && $options.checkUpdate(...args)),
    A: common_vendor.o((...args) => $options.goToFeedback && $options.goToFeedback(...args)),
    B: common_vendor.o((...args) => $options.showAbout && $options.showAbout(...args)),
    C: $data.userInfo.isLogin
  }, $data.userInfo.isLogin ? {
    D: common_vendor.o((...args) => $options.showLogoutConfirm && $options.showLogoutConfirm(...args))
  } : {}, {
    E: $data.showThemePopup
  }, $data.showThemePopup ? {
    F: common_vendor.o((...args) => $options.hideThemePopup && $options.hideThemePopup(...args)),
    G: common_vendor.f($data.themeOptions, (theme, k0, i0) => {
      return common_vendor.e({
        a: common_vendor.t(theme.icon),
        b: common_vendor.t(theme.label),
        c: theme.value === $data.settings.theme
      }, theme.value === $data.settings.theme ? {} : {}, {
        d: theme.value === $data.settings.theme ? 1 : "",
        e: theme.value,
        f: common_vendor.o(($event) => $options.selectTheme(theme.value), theme.value)
      });
    }),
    H: common_vendor.o(() => {
    }),
    I: common_vendor.o((...args) => $options.hideThemePopup && $options.hideThemePopup(...args))
  } : {}, {
    J: $data.showCachePopup
  }, $data.showCachePopup ? {
    K: common_vendor.o((...args) => $options.hideCachePopup && $options.hideCachePopup(...args)),
    L: common_vendor.t($options.formatCacheSize($data.cacheInfo.images)),
    M: common_vendor.t($options.formatCacheSize($data.cacheInfo.data)),
    N: common_vendor.t($options.formatCacheSize($data.cacheSize)),
    O: common_vendor.o(($event) => $options.clearCache("images")),
    P: common_vendor.o(($event) => $options.clearCache("data")),
    Q: common_vendor.o(($event) => $options.clearCache("all")),
    R: common_vendor.o(() => {
    }),
    S: common_vendor.o((...args) => $options.hideCachePopup && $options.hideCachePopup(...args))
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-a11b3e9a"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/settings/index.js.map
