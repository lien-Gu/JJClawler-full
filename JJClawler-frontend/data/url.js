/**
 * 分站和频道数据配置
 * @description 定义晋江文学城各分站和频道的层级结构
 */

export const sitesData = {
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
}

// 获取所有分站列表
export function getSitesList() {
  return Object.values(sitesData.sites)
}

// 根据分站ID获取分站信息
export function getSiteById(siteId) {
  return sitesData.sites[siteId] || null
}

// 根据分站ID获取频道列表
export function getChannelsBySiteId(siteId) {
  const site = getSiteById(siteId)
  return site ? site.channels : []
}

// 默认导出
export default sitesData 