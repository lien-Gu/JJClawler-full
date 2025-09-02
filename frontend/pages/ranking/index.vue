<template>
  <view class="ranking-page">
    <!-- 搜索栏 -->
    <SearchBar
        :value="searchKeyword"
        placeholder="Hinted search text"
        @input="onSearchInput"
        @search="onSearch"
    />

    <!-- 分类标签 -->
    <CategoryTabs
        :categories="categories"
        :current-main-tab="currentMainTab"
        :current-sub-tab="currentSubTab"
        @change="onTabChange"
    />

    <!-- 夹子榜单使用书籍列表 -->
    <ScrollableList
        v-if="isJiaziStrategy" class="jiazi-section"
        :items="jiaziBooks"
        :loading="jiaziLoading"
        :refreshing="jiaziRefreshing"
        :has-more="jiaziHasMore"
        :height="'calc(100vh - 300rpx - env(safe-area-inset-top) - env(safe-area-inset-bottom))'"
        empty-icon="📚"
        empty-title="暂无书籍数据"
        no-more-text="没有更多书籍了"
        @refresh="onJiaziRefresh"
        @load-more="onJiaziLoadMore"
    >
      <BookListItem
          v-for="(book, index) in jiaziBooks"
          :key="book.id"
          :book="book"
          :index="index"
          @click="handleBookClick"
          @follow="handleBookFollow"
      />
    </ScrollableList>

    <!-- 普通榜单列表 -->
    <ScrollableList
        v-else
        :items="filteredRankings"
        :loading="loading"
        :refreshing="refreshing"
        :has-more="hasMore"
        :height="'calc(100vh - 300rpx - env(safe-area-inset-top) - env(safe-area-inset-bottom))'"
        empty-icon="📋"
        empty-title="暂无榜单数据"
        no-more-text="没有更多榜单了"
        @refresh="onRefresh"
        @load-more="onLoadMore"
    >
      <RankingListItem
          v-for="(ranking, index) in filteredRankings"
          :key="ranking.id"
          :ranking="ranking"
          :index="index"
          @click="handleRankingClick"
      />
    </ScrollableList>
  </view>
</template>

<script>
import SearchBar from '@/components/SearchBar.vue'
import CategoryTabs from '@/components/CategoryTabs.vue'
import RankingListItem from '@/components/RankingListItem.vue'
import BookListItem from '@/components/BookListItem.vue'
import ScrollableList from '@/components/ScrollableList.vue'
import requestManager from '@/api/request.js'
import {getSitesList} from '@/data/url.js'

export default {
  name: 'RankingPage',
  components: {
    SearchBar,
    CategoryTabs,
    RankingListItem,
    BookListItem,
    ScrollableList
  },
  data() {
    return {
      searchKeyword: '',
      currentMainTab: '',
      currentSubTab: '',
      categories: [],
      allRankings: [],
      filteredRankings: [],
      loading: false,
      refreshing: false,
      hasMore: true,
      page: 1,
      pageSize: 20,
      // 夹子榜单相关数据
      jiaziBooks: [],
      jiaziLoading: false,
      jiaziRefreshing: false,
      jiaziHasMore: true,
      jiaziPage: 1
    }
  },

  computed: {
    isJiaziStrategy() {
      return this.currentMainTab === 'jiazi';
    }
  },

  onLoad(options) {
    this.initCategories()
    this.initData()
    if (this.isJiaziStrategy) {
      this.loadJiaziBooks(true)
    } else {
      this.loadRankings()
    }
  },

  onShow() {
    if (this.isJiaziStrategy) {
      this.refreshJiaziBooks()
    } else {
      this.refreshRankings()
    }
  },

  methods: {
    initCategories() {
      // 从 url.js 加载分类数据
      const sites = getSitesList();
      this.categories = sites.map(site => ({
        key: site.id,
        name: site.name,
        id: site.id,
        type: site.type,
        channel: site.channel,
        children: site.channels.map(channel => ({
          key: channel.id,
          name: channel.name,
          id: channel.id,
          channel: channel.channel
        }))
      }));
    },

    initData() {
      // 默认选择书城分类（index），而不是第一个分类
      const defaultCategory = this.categories.find(cat => cat.key === 'index');
      if (defaultCategory) {
        this.currentMainTab = defaultCategory.key;
        this.currentSubTab = '';
      }
    },

    getCurrentPageId() {
      // 根据当前主分类和子分类获取对应的page_id
      const mainCategory = this.categories.find(cat => cat.key === this.currentMainTab);

      if (!mainCategory) {
        console.warn(`未找到主分类 ${this.currentMainTab}，返回默认index`);
        return 'index'
      }

      // 特殊处理：夹子分类直接返回其ID，不需要子分类
      if (mainCategory.key === 'jiazi') {
        return 'jiazi'
      }

      // 简单分类（如书城、百合）直接返回其channel值
      if (mainCategory.type === 'simple') {
        return mainCategory.channel || mainCategory.id
      }

      // 复杂分类处理
      if (mainCategory.type === 'complex') {
        // 如果有选中子分类，返回组合的page_id格式：主分类.子分类
        if (this.currentSubTab) {
          const subCategory = mainCategory.children?.find(sub => sub.key === this.currentSubTab);
          if (subCategory) {
            // 对于复杂分类的子分类，使用 主分类id.子分类id 的格式
            const pageId = `${mainCategory.id}.${subCategory.id}`;
            console.log(`复杂分类子分类: ${mainCategory.name} > ${subCategory.name}, page_id: ${pageId}`);
            return pageId;
          }
        }

        // 如果没有选中子分类，返回主分类的id（只看主分类的榜单）
        console.log(`复杂分类主分类: ${mainCategory.name}, page_id: ${mainCategory.id}`);
        return mainCategory.id
      }

      // 其他情况：返回主分类的channel或id
      return mainCategory.channel || mainCategory.id
    },


    /**
     * 加载榜单列表数据
     */
    async loadRankingsList() {
      const apiParams = {
        page_id: this.getCurrentPageId(),
        page: this.page,
        size: this.pageSize
      };

      console.log(`正在请求榜单数据: /rankings/?page_id=${apiParams.page_id}&page=${apiParams.page}&size=${apiParams.size}`);

      return await requestManager.getRankingsList(apiParams)
    },

    /**
     * 主数据加载函数 - 根据策略选择不同的加载方式
     */
    async loadRankings() {
      if (this.loading || !this.hasMore) return

      this.loading = true

      try {
        const result = await this.loadRankingsList()
        if (result.success && result.data && result.data.length > 0) {
          this.processLoadedData(result.data, result.totalPages)
        }
      } catch (error) {
        console.error('数据加载失败:', error)
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },

    /**
     * 处理加载的数据（通用逻辑）
     */
    processLoadedData(data, totalPages) {
      if (this.page === 1) {
        this.allRankings = data
      } else {
        this.allRankings.push(...data)
      }

      this.hasMore = this.page < totalPages
      this.page++
      this.filterRankings()
    },


    filterRankings() {
      let filtered = [...this.allRankings]
      console.log(`开始过滤榜单，原始数据量: ${this.allRankings.length}`)

      // 只根据搜索关键词过滤，API已经返回了对应分类的榜单
      if (this.searchKeyword.trim()) {
        const keyword = this.searchKeyword.toLowerCase()
        filtered = filtered.filter(ranking =>
            ranking.name.toLowerCase().includes(keyword) ||
            (ranking.description && ranking.description.toLowerCase().includes(keyword))
        )
        console.log(`搜索关键词"${this.searchKeyword}"过滤后: ${filtered.length} 个榜单`)
      }

      this.filteredRankings = filtered
      console.log(`最终显示榜单数量: ${this.filteredRankings.length}`)
    },

    onTabChange({mainTab, subTab}) {
      console.log('Tab切换:', {mainTab, subTab})
      this.currentMainTab = mainTab
      this.currentSubTab = subTab || ''

      const pageId = this.getCurrentPageId()
      console.log(`分类切换: ${mainTab}${subTab ? ` > ${subTab}` : ''}, page_id: ${pageId}`)

      // 根据策略重新加载对应数据
      if (this.isJiaziStrategy) {
        this.refreshJiaziBooks()
      } else {
        this.refreshRankings()
      }
    },

    onSearchInput(value) {
      this.searchKeyword = value
      // 延迟搜索，避免频繁请求
      clearTimeout(this.searchTimeout)
      this.searchTimeout = setTimeout(() => {
        this.filterRankings()
      }, 300)
    },

    onSearch(value) {
      this.searchKeyword = value
      this.filterRankings()
    },

    onRefresh() {
      this.refreshing = true
      this.refreshRankings()
    },

    refreshRankings() {
      this.page = 1
      this.hasMore = true
      this.allRankings = []
      this.filteredRankings = []
      this.loadRankings()
    },

    onLoadMore() {
      this.loadRankings()
    },

    handleRankingClick(ranking) {
      console.log('点击项目:', ranking)

      if (ranking.isBook || this.isJiaziStrategy) {
        // 如果是书籍项，跳转到书籍详情页
        const bookId = ranking.id || ranking.bookData?.novel_id || ranking.bookData?.id || ranking.novel_id
        if (bookId) {
          uni.navigateTo({
            url: `/pages/book/detail?id=${bookId}`
          })
        } else {
          console.warn('无法获取书籍ID:', ranking)
          uni.showToast({
            title: '无法打开书籍详情',
            icon: 'none'
          })
        }
      } else {
        // 如果是榜单项，跳转到榜单详情页
        uni.navigateTo({
          url: `/pages/ranking/detail?id=${ranking.id}&name=${encodeURIComponent(ranking.name)}`
        })
      }
    },

    // 夹子榜单相关方法
    async loadJiaziBooks(reset = false) {
      if (this.jiaziLoading) return

      this.jiaziLoading = true
      try {
        if (reset) {
          this.jiaziPage = 1
          this.jiaziBooks = []
          this.jiaziHasMore = true
        }

        const params = {
          page: this.jiaziPage,
          limit: this.pageSize
        }

        const response = await requestManager.getRankingBooksDetail(1, params) // 夹子榜单ID为1

        if (response && response.success && response.data && Array.isArray(response.data.books)) {
          const books = response.data.books

          if (reset) {
            this.jiaziBooks = books
          } else {
            this.jiaziBooks.push(...books)
          }

          const totalPages = Math.ceil(response.data.total / this.pageSize)
          this.jiaziHasMore = this.jiaziPage < totalPages
          this.jiaziPage++

          this.checkJiaziFollowStatus()
        } else {
          this.jiaziHasMore = false
        }
      } catch (error) {
        console.error('加载夹子榜单失败:', error)
        if (reset) {
          uni.showToast({
            title: '加载失败',
            icon: 'none'
          })
        }
      } finally {
        this.jiaziLoading = false
        this.jiaziRefreshing = false
      }
    },

    checkJiaziFollowStatus() {
      try {
        const followList = uni.getStorageSync('followList') || []
        this.jiaziBooks.forEach(book => {
          book.isFollowed = followList.some(item => item.id === book.id)
        })
      } catch (error) {
        console.error('检查关注状态失败:', error)
      }
    },

    onJiaziRefresh() {
      this.jiaziRefreshing = true
      this.refreshJiaziBooks()
    },

    refreshJiaziBooks() {
      this.jiaziPage = 1
      this.jiaziHasMore = true
      this.jiaziBooks = []
      this.loadJiaziBooks(true)
    },

    onJiaziLoadMore() {
      if (this.jiaziHasMore && !this.jiaziLoading) {
        this.loadJiaziBooks()
      }
    },

    handleBookClick(book) {
      console.log('点击书籍:', book)
      const bookId = book.id || book.novel_id
      if (bookId) {
        uni.navigateTo({
          url: `/pages/book/detail?id=${bookId}`
        })
      } else {
        console.warn('无法获取书籍ID:', book)
        uni.showToast({
          title: '无法打开书籍详情',
          icon: 'none'
        })
      }
    },

    handleBookFollow(book) {
      try {
        const followList = uni.getStorageSync('followList') || []
        const existingIndex = followList.findIndex(item => item.id === book.id)

        if (existingIndex === -1) {
          // 添加关注
          const followItem = {
            id: book.id,
            type: 'book',
            name: book.title || book.name,
            author: book.author || '未知作者',
            category: '夹子榜单',
            isOnList: true,
            followDate: new Date().toISOString()
          }

          followList.push(followItem)
          uni.setStorageSync('followList', followList)
          book.isFollowed = true

          uni.showToast({
            title: '已关注',
            icon: 'success',
            duration: 1000
          })
        } else {
          // 取消关注
          followList.splice(existingIndex, 1)
          uni.setStorageSync('followList', followList)
          book.isFollowed = false

          uni.showToast({
            title: '已取消关注',
            icon: 'success',
            duration: 1000
          })
        }

        // 更新状态
        this.checkJiaziFollowStatus()
      } catch (error) {
        console.error('关注操作失败:', error)
        uni.showToast({
          title: '操作失败',
          icon: 'none'
        })
      }
    }

  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.ranking-page {
  min-height: 100vh;
  background: $surface-default;
  padding-bottom: env(safe-area-inset-bottom);
}

.jiazi-section {
  padding: 0 $spacing-lg;
}
</style>