"use strict";
const sitesData = {
  sites: {
    jiazi: {
      name: "夹子",
      id: "jiazi",
      channels: []
    },
    shucheng: {
      name: "书城",
      id: "shucheng",
      channels: []
    },
    yanqing: {
      name: "言情",
      id: "yanqing",
      channels: [
        {
          name: "古言",
          id: "guyan"
        },
        {
          name: "现言",
          id: "xianyan"
        },
        {
          name: "幻言",
          id: "huanyan"
        },
        {
          name: "古穿",
          id: "guchuan"
        },
        {
          name: "未来",
          id: "weilai"
        }
      ]
    },
    chunai: {
      name: "纯爱",
      id: "chunai",
      channels: []
    },
    yansheng: {
      name: "衍生",
      id: "yansheng",
      channels: []
    },
    erciyuan: {
      name: "二次元",
      id: "erciyuan",
      channels: []
    },
    wucp: {
      name: "无CP+",
      id: "wucp",
      channels: []
    },
    baihe: {
      name: "百合",
      id: "baihe",
      channels: []
    }
  }
};
function getSitesList() {
  return Object.values(sitesData.sites);
}
exports.getSitesList = getSitesList;
//# sourceMappingURL=../../.sourcemap/mp-weixin/data/url.js.map
