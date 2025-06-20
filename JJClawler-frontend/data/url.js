/**
 * 分站和频道数据配置
 * @description 定义晋江文学城各分站和频道的层级结构
 * @source 基于 urls.json 文件生成
 */

export const sitesData = {
  sites: {
    jiazi: {
      name: "夹子",
      id: "jiazi",
      short_name: "jiazi",
      api: "favObservationByDate",
      type: "special", // 特殊榜单，直接显示书籍
      channels: []
    },
    index: {
      name: "书城",
      id: "index", 
      short_name: "index",
      channel: "index",
      type: "simple", // 简单榜单，无子频道
      channels: []
    },
    yq: {
      name: "言情",
      id: "yq",
      short_name: "yq",
      channel: "yq",
      type: "complex", // 复杂榜单，有子频道
      channels: [
        {
          name: "古言",
          id: "gy",
          short_name: "gy",
          channel: "gywx"
        },
        {
          name: "现言", 
          id: "xy",
          short_name: "xy",
          channel: "dsyq"
        },
        {
          name: "幻言",
          id: "hy",
          short_name: "hy",
          channel: "qqyq"
        },
        {
          name: "古穿",
          id: "gc",
          short_name: "gc",
          channel: "gdcy"
        },
        {
          name: "奇幻",
          id: "qh",
          short_name: "qh",
          channel: "xhqh"
        },
        {
          name: "未来",
          id: "wl",
          short_name: "wl",
          channel: "xywy"
        },
        {
          name: "衍生言情",
          id: "ysyq",
          short_name: "ysyq",
          channel: "trys"
        },
        {
          name: "二次元",
          id: "ecy",
          short_name: "ecy",
          channel: "trmd"
        }
      ]
    },
    ca: {
      name: "纯爱",
      id: "ca",
      short_name: "ca",
      channel: "noyq",
      type: "complex",
      channels: [
        {
          name: "都市",
          id: "ds",
          short_name: "ds",
          channel: "xddm"
        },
        {
          name: "现代幻想",
          id: "xdca",
          short_name: "xdca",
          channel: "xddm"
        },
        {
          name: "古代",
          id: "gd",
          short_name: "gd",
          channel: "gddm"
        },
        {
          name: "未来幻想",
          id: "wlhx",
          short_name: "wlhx",
          channel: "wlhxca"
        },
        {
          name: "衍生纯爱",
          id: "ysca",
          short_name: "ysca",
          channel: "trdm"
        }
      ]
    },
    ys: {
      name: "衍生",
      id: "ys",
      short_name: "ys",
      channel: "ys",
      type: "complex",
      channels: [
        {
          name: "无CP",
          id: "nocp",
          short_name: "nocp",
          channel: "=nocp_plus,yw"
        },
        {
          name: "纯爱",
          id: "ca_ys",
          short_name: "ca",
          channel: "=ca,ysca"
        },
        {
          name: "言情",
          id: "yq_ys",
          short_name: "yq",
          channel: "=yq,ysyq"
        },
        {
          name: "二次元",
          id: "ecy_ys",
          short_name: "ecy",
          channel: "=yq,ecy"
        }
      ]
    },
    nocp_plus: {
      name: "无CP+",
      id: "nocp_plus",
      short_name: "nocp_plus",
      channel: "nocp_plus",
      type: "complex",
      channels: [
        {
          name: "无CP",
          id: "nocp_main",
          short_name: "nocp",
          channel: "nocp"
        },
        {
          name: "衍无",
          id: "yw",
          short_name: "yw",
          channel: "ysnocp"
        },
        {
          name: "男主",
          id: "male",
          short_name: "male",
          channel: "nocp_male"
        },
        {
          name: "女主",
          id: "female",
          short_name: "female",
          channel: "nocp_female"
        },
        {
          name: "多元",
          id: "dy",
          short_name: "dy",
          channel: "dy"
        }
      ]
    },
    bh: {
      name: "百合",
      id: "bh",
      short_name: "bh",
      channel: "bh",
      type: "simple",
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