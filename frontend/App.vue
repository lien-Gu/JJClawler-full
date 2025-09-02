<script>
import { initializeApp } from '@/utils/init.js'

export default {
	onLaunch() {
		console.log('App Launch')
		
		// 延迟初始化，确保应用实例完全初始化
		this.$nextTick(() => {
			this.initializeAppSafely()
		})
	},
	
	methods: {
		async initializeAppSafely() {
			try {
				console.log('开始安全初始化应用...')
				const result = await initializeApp()
				if (result.success) {
					console.log('✅ 应用初始化成功')
				} else {
					console.error('❌ 应用初始化失败:', result.message)
				}
			} catch (error) {
				console.error('❌ 应用初始化异常:', error)
			}
		}
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

	/* 全局样式 */
	page {
		background-color: $background-color;
		font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}
</style>
