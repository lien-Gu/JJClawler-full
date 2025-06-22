<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style lang="scss">
	/*每个页面公共css */
	@import 'uni.scss';
	@import 'styles/variables.scss';
	@import 'styles/mixins.scss';
	@import 'styles/common.scss';

	/* 全局样式 */
	page {
		background-color: $background-color;
		font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}

	/* 自定义tabBar样式 */
	.uni-tabbar {
		.uni-tabbar__item {
			.uni-tabbar__bd {
				.uni-tabbar__icon {
					filter: hue-rotate(90deg) saturate(1.2) brightness(0.8) !important;
				}
				
				.uni-tabbar__label {
					font-family: 'Inter', sans-serif !important;
					font-size: 14px !important;
					
					&.uni-tabbar__label--active {
						font-weight: 600 !important;
					}
				}
			}
		}
	}

	/* 针对微信小程序的tabBar样式 */
	/* #ifdef MP-WEIXIN */
	.wx-tabbar {
		.wx-tabbar-item {
			.wx-tabbar-icon {
				filter: hue-rotate(90deg) saturate(1.2) brightness(0.8) !important;
			}
			
			.wx-tabbar-label {
				font-family: 'Inter', sans-serif !important;
				font-size: 14px !important;
				
				&.wx-tabbar-label-active {
					font-weight: 600 !important;
				}
			}
		}
	}
	/* #endif */
</style>
