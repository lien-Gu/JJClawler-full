<template>
	<view class="home-page">
		<!-- 顶部欢迎区域 -->
		<view class="welcome-section">
			<view class="welcome-content">
				<text class="welcome-title">晋江数据中心</text>
				<text class="welcome-subtitle">实时掌握最新榜单动态</text>
			</view>
			<view class="refresh-btn" @tap="refreshData">
				<text class="refresh-text">刷新</text>
			</view>
		</view>
		
		<!-- 核心统计数据 -->
		<view class="stats-section">
			<text class="section-title">数据概览</text>
			<view class="stats-grid">
				<StatsCard 
					v-for="stat in coreStats" 
					:key="stat.key"
					:title="stat.title"
					:value="stat.value"
					:trend="stat.trend"
					:icon="stat.icon"
					:color="stat.color"
					@click="onStatClick(stat)"
				/>
			</view>
		</view>
		
		<!-- 分站数据统计 -->
		<view class="sites-section">
			<view class="section-header">
				<text class="section-title">分站统计</text>
				<text class="section-more" @tap="goToRanking">查看更多</text>
			</view>
			<view class="sites-grid">
				<view 
					class="site-card" 
					v-for="site in siteStats" 
					:key="site.key"
					@tap="goToSite(site)"
				>
					<view class="site-info">
						<text class="site-name">{{ site.name }}</text>
						<text class="site-count">{{ site.rankingCount }}个榜单</text>
					</view>
					<view class="site-trend">
						<text class="trend-value" :class="site.trend > 0 ? 'trend-up' : 'trend-down'">
							{{ site.trend > 0 ? '+' : '' }}{{ site.trend }}
						</text>
						<text class="trend-label">本周</text>
					</view>
				</view>
			</view>
		</view>
		
		<!-- 热门榜单 -->
		<view class="hot-rankings-section">
			<view class="section-header">
				<text class="section-title">热门榜单</text>
				<text class="section-more" @tap="goToRanking">查看全部</text>
			</view>
			<scroll-view class="rankings-scroll" scroll-x>
				<view class="rankings-list">
					<view 
						class="ranking-item" 
						v-for="ranking in hotRankings" 
						:key="ranking.id"
						@tap="goToRankingDetail(ranking)"
					>
						<view class="ranking-badge" v-if="ranking.isHot">HOT</view>
						<text class="ranking-name">{{ ranking.name }}</text>
						<text class="ranking-desc">{{ ranking.bookCount }}本书籍</text>
						<text class="ranking-update">{{ formatTime(ranking.updateTime) }}</text>
					</view>
				</view>
			</scroll-view>
		</view>
		
		<!-- 最近更新 -->
		<view class="recent-section">
			<text class="section-title">最近更新</text>
			<view class="recent-list">
				<view 
					class="recent-item" 
					v-for="item in recentUpdates" 
					:key="item.id"
					@tap="goToDetail(item)"
				>
					<view class="recent-info">
						<text class="recent-title">{{ item.title }}</text>
						<text class="recent-subtitle">{{ item.subtitle }}</text>
					</view>
					<view class="recent-time">
						<text class="time-text">{{ formatTime(item.updateTime) }}</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
import StatsCard from '@/components/StatsCard.vue'
import dataManager from '@/utils/data-manager.js'
import { getSync, setSync } from '@/utils/storage.js'

/**
 * 首页组件
 * @description 展示统计数据概览、热门榜单、最近更新等信息
 */
export default {
	name: 'HomePage',
	components: {
		StatsCard
	},
	
	data() {
		return {
			// 核心统计数据
			coreStats: [
				{
					key: 'totalBooks',
					title: '总书籍数',
					value: 0,
					trend: 0,
					icon: '📚',
					color: '#007AFF'
				},
				{
					key: 'totalRankings',
					title: '总榜单数',
					value: 0,
					trend: 0,
					icon: '��',
					color: '#34C759'
				},
				{
					key: 'todayUpdates',
					title: '今日更新',
					value: 0,
					trend: 0,
					icon: '🔄',
					color: '#FF9500'
				},
				{
					key: 'activeUsers',
					title: '活跃用户',
					value: 0,
					trend: 0,
					icon: '👥',
					color: '#AF52DE'
				}
			],
			
			// 分站统计数据
			siteStats: [],
			
			// 热门榜单
			hotRankings: [],
			
			// 最近更新
			recentUpdates: [],
			
			// 加载状态
			loading: false,
			
			// 刷新状态
			refreshing: false
		}
	},
	
	onLoad() {
		this.initData()
	},
	
	onShow() {
		// 每次显示页面时检查是否需要刷新数据
		this.checkDataFreshness()
	},
	
	// 下拉刷新
	onPullDownRefresh() {
		this.refreshData().finally(() => {
			uni.stopPullDownRefresh()
		})
	},
	
	methods: {
		/**
		 * 初始化数据
		 */
		async initData() {
			this.loading = true
			
			try {
				// 先加载缓存数据
				this.loadCachedData()
				
				// 再获取最新数据
				await this.fetchData()
			} catch (error) {
				console.error('初始化数据失败:', error)
				this.showError('数据加载失败')
			} finally {
				this.loading = false
			}
		},
		
		/**
		 * 加载缓存数据
		 */
		loadCachedData() {
			const cachedStats = getSync('homeStats')
			const cachedSiteStats = getSync('homeSiteStats')
			const cachedHotRankings = getSync('homeHotRankings')
			const cachedRecentUpdates = getSync('homeRecentUpdates')
			
			if (cachedStats) {
				this.updateCoreStats(cachedStats)
			}
			
			if (cachedSiteStats) {
				this.siteStats = cachedSiteStats
			}
			
			if (cachedHotRankings) {
				this.hotRankings = cachedHotRankings
			}
			
			if (cachedRecentUpdates) {
				this.recentUpdates = cachedRecentUpdates
			}
		},
		
		/**
		 * 获取最新数据
		 */
		async fetchData() {
			try {
				// 显示当前数据源信息
				if (dataManager.getEnvironmentInfo().debug) {
					const envInfo = dataManager.getEnvironmentInfo()
					console.log('首页数据源:', envInfo)
				}
				
				// 并行请求所有数据 - 使用数据管理器
				const [statsRes, sitesRes, rankingsRes] = await Promise.all([
					dataManager.getOverviewStats(),
					dataManager.getPageStatistics(),
					dataManager.getHotRankings({ limit: 6 })
				])
				
				// 更新核心统计
				if (statsRes) {
					this.updateCoreStats(statsRes)
					setSync('homeStats', statsRes, 5 * 60 * 1000) // 缓存5分钟
				}
				
				// 更新分站统计 - 从页面统计中提取
				if (sitesRes) {
					this.siteStats = this.buildSiteStats(sitesRes)
					setSync('homeSiteStats', this.siteStats, 10 * 60 * 1000) // 缓存10分钟
				}
				
				// 更新热门榜单
				if (rankingsRes) {
					this.hotRankings = this.formatHotRankings(rankingsRes)
					setSync('homeHotRankings', this.hotRankings, 15 * 60 * 1000) // 缓存15分钟
				}
				
				// 构建最近更新数据
				this.recentUpdates = this.buildRecentUpdates(statsRes)
				setSync('homeRecentUpdates', this.recentUpdates, 5 * 60 * 1000) // 缓存5分钟
				
			} catch (error) {
				console.error('获取数据失败:', error)
				throw error
			}
		},
		
		/**
		 * 更新核心统计数据
		 */
		updateCoreStats(data) {
			if (!data) return
			
			// 映射后端数据字段到前端显示字段
			const fieldMapping = {
				'totalBooks': 'total_books',
				'totalRankings': 'total_rankings', 
				'todayUpdates': 'recent_updates',
				'activeUsers': 'active_users'
			}
			
			this.coreStats.forEach(stat => {
				const backendField = fieldMapping[stat.key] || stat.key
				if (data[backendField] !== undefined) {
					stat.value = data[backendField]
					// 假设趋势数据（实际项目中应该从后端获取）
					stat.trend = Math.floor(Math.random() * 20) - 10
				}
			})
		},

		/**
		 * 构建分站统计数据
		 */
		buildSiteStats(sitesData) {
			if (!sitesData) return []
			
			// 模拟分站数据（基于页面统计）
			const sites = [
				{ key: 'jiazi', name: '夹子', rankingCount: 1, trend: 8 },
				{ key: 'yanqing', name: '言情', rankingCount: 12, trend: 5 },
				{ key: 'chunai', name: '纯爱', rankingCount: 8, trend: -2 },
				{ key: 'yanshen', name: '衍生', rankingCount: 6, trend: 3 },
				{ key: 'erciyuan', name: '二次元', rankingCount: 4, trend: 1 },
				{ key: 'wucp', name: '无CP+', rankingCount: 3, trend: -1 },
				{ key: 'baihe', name: '百合', rankingCount: 2, trend: 2 }
			]
			
			return sites
		},

		/**
		 * 格式化热门榜单数据
		 */
		formatHotRankings(rankingsData) {
			if (!Array.isArray(rankingsData)) return []
			
			return rankingsData.map(ranking => ({
				id: ranking.id,
				name: ranking.name,
				bookCount: ranking.total_books || ranking.book_count || 0,
				updateTime: ranking.last_updated || new Date().toISOString(),
				isHot: ranking.activity_score > 90
			}))
		},

		/**
		 * 构建最近更新数据
		 */
		buildRecentUpdates(statsData) {
			const updates = [
				{
					id: 'update_1',
					title: '夹子榜更新',
					subtitle: `新增 ${statsData?.recent_updates || 0} 条数据`,
					updateTime: new Date(Date.now() - 1000 * 60 * 30).toISOString() // 30分钟前
				},
				{
					id: 'update_2', 
					title: '言情榜单更新',
					subtitle: '排名发生变化',
					updateTime: new Date(Date.now() - 1000 * 60 * 60).toISOString() // 1小时前
				},
				{
					id: 'update_3',
					title: '系统维护',
					subtitle: '数据同步完成',
					updateTime: new Date(Date.now() - 1000 * 60 * 120).toISOString() // 2小时前
				}
			]
			
			return updates
		},
		
		/**
		 * 检查数据新鲜度
		 */
		checkDataFreshness() {
			const lastUpdate = getSync('homeLastUpdate', 0)
			const now = Date.now()
			
			// 如果超过10分钟，静默刷新数据
			if (now - lastUpdate > 10 * 60 * 1000) {
				this.fetchData().catch(() => {
					// 静默失败
				}).finally(() => {
					setSync('homeLastUpdate', now)
				})
			}
		},
		
		/**
		 * 刷新数据
		 */
		async refreshData() {
			if (this.refreshing) return
			
			this.refreshing = true
			
			try {
				await this.fetchData()
				setSync('homeLastUpdate', Date.now())
				
				uni.showToast({
					title: '刷新成功',
					icon: 'success',
					duration: 1500
				})
			} catch (error) {
				this.showError('刷新失败')
			} finally {
				this.refreshing = false
			}
		},
		
		/**
		 * 格式化时间显示
		 */
		formatTime(time) {
			if (!time) return '未知'
			
			const now = new Date()
			const updateTime = new Date(time)
			const diff = now - updateTime
			
			const minutes = Math.floor(diff / (1000 * 60))
			const hours = Math.floor(diff / (1000 * 60 * 60))
			const days = Math.floor(diff / (1000 * 60 * 60 * 24))
			
			if (minutes < 60) {
				return `${minutes}分钟前`
			} else if (hours < 24) {
				return `${hours}小时前`
			} else if (days < 7) {
				return `${days}天前`
			} else {
				return updateTime.toLocaleDateString()
			}
		},
		
		/**
		 * 显示错误提示
		 */
		showError(message) {
			uni.showToast({
				title: message,
				icon: 'none',
				duration: 2000
			})
		},
		
		/**
		 * 统计卡片点击事件
		 */
		onStatClick(stat) {
			console.log('点击统计卡片:', stat)
			// 可以跳转到对应的详情页面
		},
		
		/**
		 * 跳转到榜单页面
		 */
		goToRanking() {
			uni.switchTab({
				url: '/pages/ranking/index'
			})
		},
		
		/**
		 * 跳转到分站页面
		 */
		goToSite(site) {
			uni.switchTab({
				url: `/pages/ranking/index?site=${site.key}`
			})
		},
		
		/**
		 * 跳转到榜单详情
		 */
		goToRankingDetail(ranking) {
			uni.navigateTo({
				url: `/pages/ranking/detail?id=${ranking.id}`
			})
		},
		
		/**
		 * 跳转到详情页面
		 */
		goToDetail(item) {
			if (item.type === 'ranking') {
				this.goToRankingDetail(item)
			} else if (item.type === 'book') {
				uni.navigateTo({
					url: `/pages/book/detail?id=${item.id}`
				})
			}
		}
	}
}
</script>

<style lang="scss" scoped>
.home-page {
	min-height: 100vh;
	background-color: $page-background;
	padding-bottom: $safe-area-bottom;
}

.welcome-section {
	@include flex-between;
	align-items: center;
	padding: $spacing-lg;
	background: linear-gradient(135deg, $primary-color, $secondary-color);
	color: white;
	
	.welcome-content {
		flex: 1;
		
		.welcome-title {
			display: block;
			font-size: $font-size-xl;
			font-weight: bold;
			margin-bottom: $spacing-xs;
		}
		
		.welcome-subtitle {
			font-size: $font-size-sm;
			opacity: 0.9;
		}
	}
	
	.refresh-btn {
		@include flex-center;
		padding: $spacing-xs $spacing-md;
		background-color: rgba(255, 255, 255, 0.2);
		border-radius: $border-radius-medium;
		
		.refresh-text {
			color: white;
			font-size: $font-size-sm;
		}
		
		&:active {
			opacity: 0.7;
		}
	}
}

.stats-section {
	padding: $spacing-lg;
	
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: $spacing-md;
		margin-top: $spacing-md;
	}
}

.sites-section {
	padding: 0 $spacing-lg $spacing-lg;
	
	.sites-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: $spacing-sm;
		margin-top: $spacing-md;
	}
	
	.site-card {
		@include card-style;
		@include flex-between;
		align-items: center;
		padding: $spacing-md;
		transition: all 0.3s ease;
		
		&:active {
			transform: scale(0.98);
		}
	}
	
	.site-info {
		flex: 1;
		
		.site-name {
			display: block;
			font-size: $font-size-md;
			font-weight: bold;
			color: $text-primary;
			margin-bottom: 4rpx;
		}
		
		.site-count {
			font-size: $font-size-xs;
			color: $text-secondary;
		}
	}
	
	.site-trend {
		@include flex-column-center;
		
		.trend-value {
			font-size: $font-size-sm;
			font-weight: bold;
			margin-bottom: 2rpx;
			
			&.trend-up {
				color: #34C759;
			}
			
			&.trend-down {
				color: #FF3B30;
			}
		}
		
		.trend-label {
			font-size: $font-size-xs;
			color: $text-placeholder;
		}
	}
}

.hot-rankings-section {
	padding: 0 $spacing-lg $spacing-lg;
	
	.rankings-scroll {
		margin-top: $spacing-md;
		white-space: nowrap;
	}
	
	.rankings-list {
		@include flex-center;
		gap: $spacing-sm;
		padding-bottom: $spacing-xs;
	}
	
	.ranking-item {
		@include card-style;
		position: relative;
		padding: $spacing-md;
		min-width: 200rpx;
		transition: all 0.3s ease;
		
		&:active {
			transform: scale(0.98);
		}
		
		.ranking-badge {
			position: absolute;
			top: -8rpx;
			right: -8rpx;
			background-color: $accent-color;
			color: white;
			font-size: $font-size-xs;
			padding: 2rpx 8rpx;
			border-radius: $border-radius-small;
		}
		
		.ranking-name {
			display: block;
			font-size: $font-size-md;
			font-weight: bold;
			color: $text-primary;
			margin-bottom: $spacing-xs;
			@include text-ellipsis;
		}
		
		.ranking-desc {
			display: block;
			font-size: $font-size-sm;
			color: $text-secondary;
			margin-bottom: 4rpx;
		}
		
		.ranking-update {
			font-size: $font-size-xs;
			color: $text-placeholder;
		}
	}
}

.recent-section {
	padding: 0 $spacing-lg $spacing-lg;
	
	.recent-list {
		margin-top: $spacing-md;
	}
	
	.recent-item {
		@include flex-between;
		align-items: center;
		padding: $spacing-md;
		background-color: white;
		border-radius: $border-radius-medium;
		margin-bottom: $spacing-sm;
		transition: all 0.3s ease;
		
		&:active {
			background-color: $background-color;
		}
		
		&:last-child {
			margin-bottom: 0;
		}
	}
	
	.recent-info {
		flex: 1;
		
		.recent-title {
			display: block;
			font-size: $font-size-md;
			color: $text-primary;
			margin-bottom: 4rpx;
			@include text-ellipsis;
		}
		
		.recent-subtitle {
			font-size: $font-size-sm;
			color: $text-secondary;
			@include text-ellipsis;
		}
	}
	
	.recent-time {
		margin-left: $spacing-sm;
		
		.time-text {
			font-size: $font-size-xs;
			color: $text-placeholder;
		}
	}
}

.section-title {
	font-size: $font-size-lg;
	font-weight: bold;
	color: $text-primary;
}

.section-header {
	@include flex-between;
	align-items: center;
	margin-bottom: $spacing-md;
	
	.section-more {
		font-size: $font-size-sm;
		color: $primary-color;
		
		&:active {
			opacity: 0.7;
		}
	}
}
</style>
