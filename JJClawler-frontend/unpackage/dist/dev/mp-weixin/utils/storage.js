"use strict";
const common_vendor = require("../common/vendor.js");
const STORAGE_PREFIX = "jjclawler_";
function getFullKey(key) {
  return STORAGE_PREFIX + key;
}
function isExpired(data) {
  if (!data || !data.expire || data.expire === 0) {
    return false;
  }
  return Date.now() > data.expire;
}
function wrapData(value, expireTime = 0) {
  const now = Date.now();
  return {
    value,
    timestamp: now,
    expire: expireTime > 0 ? now + expireTime : 0,
    type: typeof value
  };
}
function unwrapData(data) {
  if (!data || typeof data !== "object" || !data.hasOwnProperty("value")) {
    return data;
  }
  if (isExpired(data)) {
    return null;
  }
  return data.value;
}
function setSync(key, value, expireTime = 0) {
  try {
    const fullKey = getFullKey(key);
    const wrappedData = wrapData(value, expireTime);
    common_vendor.index.setStorageSync(fullKey, wrappedData);
    return true;
  } catch (error) {
    common_vendor.index.__f__("error", "at utils/storage.js:94", "Storage setSync error:", error);
    return false;
  }
}
function getSync(key, defaultValue = null) {
  try {
    const fullKey = getFullKey(key);
    const data = common_vendor.index.getStorageSync(fullKey);
    const value = unwrapData(data);
    if (value === null && data && isExpired(data)) {
      removeSync(key);
      return defaultValue;
    }
    return value !== null ? value : defaultValue;
  } catch (error) {
    common_vendor.index.__f__("error", "at utils/storage.js:148", "Storage getSync error:", error);
    return defaultValue;
  }
}
function removeSync(key) {
  try {
    const fullKey = getFullKey(key);
    common_vendor.index.removeStorageSync(fullKey);
    return true;
  } catch (error) {
    common_vendor.index.__f__("error", "at utils/storage.js:201", "Storage removeSync error:", error);
    return false;
  }
}
exports.getSync = getSync;
exports.setSync = setSync;
//# sourceMappingURL=../../.sourcemap/mp-weixin/utils/storage.js.map
