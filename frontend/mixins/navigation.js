/**
 * 导航混入
 * 提供通用的页面跳转和导航方法
 */

export default {
  methods: {
    /**
     * 导航到指定页面
     * @param {string} url 页面路径
     * @param {object} params 参数对象
     * @param {string} method 导航方法：navigateTo, redirectTo, switchTab, reLaunch
     */
    navigateTo(url, params = {}, method = 'navigateTo') {
      // 构建完整的URL
      let fullUrl = url;
      
      // 添加参数
      if (Object.keys(params).length > 0) {
        const queryString = Object.entries(params)
          .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
          .join('&');
        fullUrl += (url.includes('?') ? '&' : '?') + queryString;
      }
      
      // 执行导航
      uni[method]({
        url: fullUrl,
        fail: (err) => {
          console.error(`导航失败 (${method}):`, err);
          
          // 如果switchTab失败，尝试navigateTo
          if (method === 'switchTab') {
            uni.navigateTo({
              url: fullUrl,
              fail: (navErr) => {
                console.error('导航备用方案失败:', navErr);
              }
            });
          }
        }
      });
    },
    
    /**
     * 跳转到书籍详情页
     * @param {object|string} book 书籍对象或书籍ID
     */
    goToBookDetail(book) {
      const bookId = typeof book === 'object' ? book.id : book;
      this.navigateTo('/pages/book/detail', { id: bookId });
    },
    
    /**
     * 跳转到榜单详情页
     * @param {object|string} ranking 榜单对象或榜单ID
     */
    goToRankingDetail(ranking) {
      const rankingId = typeof ranking === 'object' ? ranking.id : ranking;
      const rankingName = typeof ranking === 'object' ? ranking.name : '';
      
      this.navigateTo('/pages/ranking/detail', { 
        id: rankingId,
        name: rankingName
      });
    },
    
    /**
     * 跳转到用户页面
     * @param {object|string} user 用户对象或用户ID
     */
    goToUserProfile(user) {
      const userId = typeof user === 'object' ? user.id : user;
      this.navigateTo('/pages/user/profile', { id: userId });
    },
    
    /**
     * 跳转到搜索页面
     * @param {string} keyword 搜索关键词
     * @param {string} type 搜索类型
     */
    goToSearch(keyword = '', type = 'all') {
      this.navigateTo('/pages/search/index', { 
        keyword: keyword,
        type: type
      });
    },
    
    /**
     * 切换到主要标签页
     * @param {string} tab 标签页名称：index, ranking, follow, settings
     */
    switchMainTab(tab) {
      const tabUrls = {
        index: '/pages/index/index',
        ranking: '/pages/ranking/index', 
        follow: '/pages/follow/index',
        settings: '/pages/settings/index'
      };
      
      const url = tabUrls[tab];
      if (url) {
        this.navigateTo(url, {}, 'switchTab');
      } else {
        console.error('未知的标签页:', tab);
      }
    },
    
    /**
     * 返回上一页
     * @param {number} delta 返回的页面层数
     */
    goBack(delta = 1) {
      uni.navigateBack({
        delta: delta,
        fail: () => {
          // 如果返回失败，跳转到首页
          this.switchMainTab('index');
        }
      });
    },
    
    /**
     * 重新加载当前页面
     */
    relaunch() {
      const pages = getCurrentPages();
      if (pages.length > 0) {
        const currentPage = pages[pages.length - 1];
        const route = currentPage.route;
        const options = currentPage.options;
        
        // 构建URL
        let url = '/' + route;
        if (options && Object.keys(options).length > 0) {
          const queryString = Object.entries(options)
            .map(([key, value]) => `${key}=${value}`)
            .join('&');
          url += '?' + queryString;
        }
        
        this.navigateTo(url, {}, 'reLaunch');
      }
    },
    
    /**
     * 检查当前页面路由
     * @returns {string} 当前页面路由
     */
    getCurrentRoute() {
      const pages = getCurrentPages();
      if (pages.length > 0) {
        return pages[pages.length - 1].route;
      }
      return '';
    },
    
    /**
     * 检查是否在指定页面
     * @param {string} route 页面路由
     * @returns {boolean} 是否在指定页面
     */
    isCurrentPage(route) {
      return this.getCurrentRoute().includes(route);
    }
  }
};