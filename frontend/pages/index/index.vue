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
						<text class="ranking-name">{{ ranking.name }}</text>
						<text class="ranking-desc">{{ ranking.bookCount }}本书籍</text>
						<text class="ranking-update">{{ formatTime(ranking.updateTime) }}</text>
					</view>
				</view>
			</scroll-view>
		</view>
	</view>
</template>

<script>
import StatsCard from '@/components/StatsCard.vue'
import dataManager from '@/utils/data-manager.js'

export default {
	name: 'HomePage',
	components: {
		StatsCard
	},
	
	data() {
		return {
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
					icon: '📊',
					color: '#34C759'
				},
				{
					key: 'todayUpdates',
					title: '今日更新',
					value: 0,
					trend: 0,
					icon: '🔄',
					color: '#FF9500'
				}
			],
			siteStats: [],
			hotRankings: []
		}
	},
	
	onLoad() {
		this.loadData()
	},
	
	methods: {
		async loadData() {
			try {
				const [statsRes, rankingsRes] = await Promise.all([
					dataManager.getOverviewStats(),
					dataManager.getHotRankings({ limit: 6 })
				])
				
				if (statsRes) {
					this.updateCoreStats(statsRes)
				}
				
				if (rankingsRes) {
					this.hotRankings = rankingsRes.map(ranking => ({
						id: ranking.id,
						name: ranking.name,
						bookCount: ranking.total_books || ranking.book_count || 0,
						updateTime: ranking.last_updated || new Date().toISOString()
					}))
				}
				
				this.siteStats = [
					{ key: 'jiazi', name: '夹子', rankingCount: 1 },
					{ key: 'yanqing', name: '言情', rankingCount: 12 },
					{ key: 'chunai', name: '纯爱', rankingCount: 8 },
					{ key: 'yanshen', name: '衍生', rankingCount: 6 }
				]
				
			} catch (error) {
				console.error('数据加载失败:', error)
			}
		},
		
		updateCoreStats(data) {
			if (!data) return
			
			this.coreStats.forEach(stat => {
				switch(stat.key) {
					case 'totalBooks':
						stat.value = data.total_books || 0
						break
					case 'totalRankings':
						stat.value = data.total_rankings || 0
						break
					case 'todayUpdates':
						stat.value = data.recent_updates || 0
						break
				}
			})
		},
		
		async refreshData() {
			try {
				await this.loadData()
				uni.showToast({
					title: '刷新成功',
					icon: 'success',
					duration: 1500
				})
			} catch (error) {
				uni.showToast({
					title: '刷新失败',
					icon: 'none',
					duration: 2000
				})
			}
		},
		
		formatTime(time) {
			if (!time) return '未知'
			
			const now = new Date()
			const updateTime = new Date(time)
			const diff = now - updateTime
			
			const minutes = Math.floor(diff / (1000 * 60))
			const hours = Math.floor(diff / (1000 * 60 * 60))
			
			if (minutes < 60) {
				return `${minutes}分钟前`
			} else if (hours < 24) {
				return `${hours}小时前`
			} else {
				return updateTime.toLocaleDateString()
			}
		},
		
		goToRanking() {
			uni.switchTab({
				url: '/pages/ranking/index'
			})
		},
		
		goToSite(site) {
			uni.switchTab({
				url: `/pages/ranking/index?site=${site.key}`
			})
		},
		
		goToRankingDetail(ranking) {
			uni.navigateTo({
				url: `/pages/ranking/detail?id=${ranking.id}`
			})
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