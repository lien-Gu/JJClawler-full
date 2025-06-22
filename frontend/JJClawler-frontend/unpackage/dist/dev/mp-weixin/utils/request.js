"use strict";
const common_vendor = require("../common/vendor.js");
const BASE_URL = "https://api.jjclawler.com";
const TIMEOUT = 1e4;
const HTTP_STATUS = {
  SUCCESS: 200,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500
};
const ERROR_MESSAGES = {
  [HTTP_STATUS.UNAUTHORIZED]: "未授权，请重新登录",
  [HTTP_STATUS.FORBIDDEN]: "拒绝访问",
  [HTTP_STATUS.NOT_FOUND]: "请求的资源不存在",
  [HTTP_STATUS.SERVER_ERROR]: "服务器内部错误",
  "NETWORK_ERROR": "网络连接异常",
  "TIMEOUT": "请求超时",
  "UNKNOWN": "未知错误"
};
function requestInterceptor(config) {
  if (!config.url.startsWith("http")) {
    config.url = BASE_URL + config.url;
  }
  config.header = {
    "Content-Type": "application/json",
    ...config.header
  };
  const token = common_vendor.index.getStorageSync("token");
  if (token) {
    config.header.Authorization = `Bearer ${token}`;
  }
  const systemInfo = common_vendor.index.getSystemInfoSync();
  config.header["User-Agent"] = `JJClawler/${systemInfo.platform} ${systemInfo.version}`;
  if (config.showLoading !== false) {
    common_vendor.index.showLoading({
      title: config.loadingText || "加载中...",
      mask: true
    });
  }
  common_vendor.index.__f__("log", "at utils/request.js:69", "请求发送:", config);
  return config;
}
function responseInterceptor(response, config) {
  if (config.showLoading !== false) {
    common_vendor.index.hideLoading();
  }
  common_vendor.index.__f__("log", "at utils/request.js:85", "响应接收:", response);
  const { statusCode, data } = response;
  if (statusCode === HTTP_STATUS.SUCCESS) {
    if (data.code === 0 || data.success === true) {
      return Promise.resolve(data.data || data);
    } else {
      const errorMsg = data.message || data.msg || "请求失败";
      return Promise.reject({
        type: "BUSINESS_ERROR",
        code: data.code,
        message: errorMsg,
        data
      });
    }
  } else {
    const errorMsg = ERROR_MESSAGES[statusCode] || ERROR_MESSAGES.UNKNOWN;
    return Promise.reject({
      type: "HTTP_ERROR",
      code: statusCode,
      message: errorMsg,
      data: response
    });
  }
}
function errorHandler(error, config) {
  if (config.showLoading !== false) {
    common_vendor.index.hideLoading();
  }
  common_vendor.index.__f__("error", "at utils/request.js:127", "请求错误:", error);
  let errorMessage = ERROR_MESSAGES.UNKNOWN;
  if (error.type === "BUSINESS_ERROR" || error.type === "HTTP_ERROR") {
    errorMessage = error.message;
  } else if (error.errMsg) {
    if (error.errMsg.includes("timeout")) {
      errorMessage = ERROR_MESSAGES.TIMEOUT;
    } else if (error.errMsg.includes("fail")) {
      errorMessage = ERROR_MESSAGES.NETWORK_ERROR;
    }
  }
  if (config.showError !== false) {
    common_vendor.index.showToast({
      title: errorMessage,
      icon: "none",
      duration: 2e3
    });
  }
  return Promise.reject({
    ...error,
    message: errorMessage
  });
}
function request(options = {}) {
  return new Promise((resolve, reject) => {
    const config = {
      method: "GET",
      timeout: TIMEOUT,
      showLoading: true,
      showError: true,
      ...options
    };
    const interceptedConfig = requestInterceptor(config);
    common_vendor.index.request({
      ...interceptedConfig,
      success: (response) => {
        responseInterceptor(response, config).then(resolve).catch(reject);
      },
      fail: (error) => {
        errorHandler(error, config).catch(reject);
      }
    });
  });
}
function get(url, params = {}, options = {}) {
  return request({
    url,
    method: "GET",
    data: params,
    ...options
  });
}
exports.get = get;
//# sourceMappingURL=../../.sourcemap/mp-weixin/utils/request.js.map
