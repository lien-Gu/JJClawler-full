<template>
  <view class="index-page">
    <!-- 主要内容区域 -->
    <view class="content-container">
      <!-- 问候语 -->
      <view class="greeting-section">
        <text class="greeting-text">嗨~</text>
      </view>
      
      <!-- 统计报告卡片 -->
      <view class="summary-card" @tap="goToStatisticsDetail">
        <view class="summary-content">
          <text class="summary-title">统计报告</text>
          <view class="summary-button" @tap.stop="goToStatisticsDetail">
            <text class="button-text">查看详情</text>
          </view>
        </view>
      </view>
      
      <!-- 分项统计 -->
      <view class="reports-section">
        <text class="section-title">分项</text>
        <scroll-view class="reports-scroll" scroll-x show-scrollbar="false">
          <view class="reports-container">
            <view class="report-card" @tap="goToRankingStats">
              <view class="report-icon">📊</view>
              <text class="report-title">榜单统计</text>
              <text class="report-desc">查看榜单数据</text>
            </view>
            <view class="report-card" @tap="goToBookStats">
              <view class="report-icon">📚</view>
              <text class="report-title">书籍统计</text>
              <text class="report-desc">查看书籍数据</text>
            </view>
            <view class="report-card" @tap="goToChannelStats">
              <view class="report-icon">📺</view>
              <text class="report-title">频道统计</text>
              <text class="report-desc">查看频道数据</text>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script>
/**
 * 首页
 * @description 展示统计报告和分项统计，按照Figma设计实现
 */
export default {
	name: 'IndexPage',
	
	data() {
		return {
			// 可以在这里添加一些状态数据
		}
	},
	
	onLoad() {
		// 页面加载时的初始化
		console.log('首页加载完成')
	},
	
	// 下拉刷新
	onPullDownRefresh() {
		// 这里可以添加刷新逻辑
		setTimeout(() => {
			uni.stopPullDownRefresh()
			uni.showToast({
				title: '刷新完成',
				icon: 'success',
				duration: 1500
			})
		}, 1000)
	},
	
	methods: {
		/**
		 * 跳转到统计详情页面（后端接口）
		 */
		goToStatisticsDetail() {
			this.openBackendUrl('/api/statistics/detail', '统计详情')
		},
		
		/**
		 * 跳转到榜单统计（后端接口）
		 */
		goToRankingStats() {
			this.openBackendUrl('/api/statistics/rankings', '榜单统计')
		},
		
		/**
		 * 跳转到书籍统计（后端接口）
		 */
		goToBookStats() {
			this.openBackendUrl('/api/statistics/books', '书籍统计')
		},
		
		/**
		 * 跳转到频道统计（后端接口）
		 */
		goToChannelStats() {
			this.openBackendUrl('/api/statistics/channels', '频道统计')
		},
		
		/**
		 * 打开后端接口URL
		 * @param {string} path - 接口路径
		 * @param {string} title - 页面标题
		 */
		openBackendUrl(path, title) {
			// 获取后端基础URL
			const baseUrl = this.getApiBaseUrl()
			const fullUrl = baseUrl + path
			
			console.log(`准备打开${title}页面:`, fullUrl)
			
			// 在小程序中打开网页
			// #ifdef MP-WEIXIN
			uni.navigateTo({
				url: `/pages/webview/index?url=${encodeURIComponent(fullUrl)}&title=${encodeURIComponent(title)}`
			})
			// #endif
			
			// 在其他平台中的处理
			// #ifndef MP-WEIXIN
			uni.showModal({
				title: title,
				content: `将要打开: ${fullUrl}`,
				confirmText: '打开',
				success: (res) => {
					if (res.confirm) {
						// 在H5或APP中可以直接打开链接
						// #ifdef H5
						window.open(fullUrl, '_blank')
						// #endif
						
						// #ifdef APP-PLUS
						plus.runtime.openURL(fullUrl)
						// #endif
					}
				}
			})
			// #endif
		},
		
		/**
		 * 获取API基础URL
		 */
		getApiBaseUrl() {
			// 开发环境
			// #ifdef MP-WEIXIN
			return 'https://your-api-domain.com'  // 小程序中需要使用HTTPS
			// #endif
			
			// #ifndef MP-WEIXIN
			return 'http://localhost:8000'  // 开发环境
			// #endif
		}
	}
}
</script>

<style lang="scss" scoped>
.index-page {
	min-height: 100vh;
	background-color: $background-color;
	padding: 0 $spacing-md;
	padding-bottom: calc(#{$safe-area-bottom} + #{$spacing-lg});
}

.content-container {
	padding: 49rpx 62rpx 0;  // 按照Figma设计的间距
	
	// 问候语部分
	.greeting-section {
		margin-bottom: 48rpx;  // 24px * 2
		
		.greeting-text {
			font-family: 'Inter', sans-serif;
			font-weight: 600;  // Semi Bold
			font-size: 64rpx;  // 32px * 2
			line-height: 80rpx;  // 40px * 2
			color: #454444;  // text secondary
		}
	}
	
	// 统计报告卡片
	.summary-card {
		width: 100%;
		height: 434rpx;
		background-color: $secondary-color;
		border-radius: $radius-lg;
		margin-bottom: $spacing-lg;
		position: relative;
		overflow: hidden;
		box-shadow: $shadow-md;
		transition: $transition-normal;
		
		.summary-content {
			padding: 116rpx 56rpx 0;  // 按照Figma设计调整
			
			.summary-title {
				font-family: 'Inter', sans-serif;
				font-weight: 600;  // Semi Bold
				font-size: 64rpx;  // 32px * 2
				line-height: 80rpx;  // 40px * 2
				color: #ffffff;  // 白色文字
				display: block;
				margin-bottom: 38rpx;  // 调整间距
			}
			
			.summary-button {
				background: linear-gradient(135deg, $primary-color 0%, $primary-light 100%);
				border-radius: 36rpx;
				padding: $spacing-sm $spacing-md;
				display: inline-block;
				box-shadow: $shadow-primary;
				transition: $transition-normal;
				
				.button-text {
					font-family: 'Inter', sans-serif;
					font-weight: 400;  // Regular
					font-size: 32rpx;  // 16px * 2
					line-height: 48rpx;  // 24px * 2
					color: #ffffff;  // 白色文字
				}
				
				&:active {
					opacity: 0.8;
				}
			}
		}
		
		&:active {
			opacity: 0.9;
		}
	}
	
	// 分项统计部分
	.reports-section {
		.section-title {
			font-family: 'Inter', sans-serif;
			font-weight: 600;  // Semi Bold
			font-size: 40rpx;  // 20px * 2
			line-height: 56rpx;  // 28px * 2
			color: #000000;  // 黑色
			display: block;
			margin-bottom: 32rpx;  // 16px * 2
		}
		
		.reports-scroll {
			white-space: nowrap;
			
			.reports-container {
				display: flex;
				gap: 16rpx;
				padding: 0 32rpx;
				
				.report-card {
					flex-shrink: 0;
					width: 240rpx;
					height: 180rpx;
					background: linear-gradient(135deg, #64a347 0%, #7bb354 100%);
					border-radius: 20rpx;
					padding: 24rpx;
					display: flex;
					flex-direction: column;
					justify-content: space-between;
					box-shadow: 0 8rpx 24rpx rgba(100, 163, 71, 0.2);
					
					.report-icon {
						font-size: 40rpx;
						line-height: 1;
					}
					
					.report-title {
						font-family: 'Inter', sans-serif;
						font-weight: 600;
						font-size: 28rpx;
						line-height: 36rpx;
						color: #ffffff;
						margin: 8rpx 0 4rpx 0;
					}
					
					.report-desc {
						font-family: 'Inter', sans-serif;
						font-weight: 400;
						font-size: 22rpx;
						line-height: 28rpx;
						color: rgba(255, 255, 255, 0.8);
					}
					
					&:active {
						opacity: 0.8;
						transform: scale(0.98);
						transition: all 0.2s ease;
					}
				}
			}
		}
	}
}
</style>
