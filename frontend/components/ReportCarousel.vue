<template>
  <view class="carousel-container" @click="handleClick">
    <view class="carousel-content">
      <view class="carousel-main">
        <view class="carousel-main-content">
          <!-- 报告图标/图表 -->
          <view class="report-icon">
            <image 
              v-if="report.icon" 
              :src="report.icon" 
              mode="aspectFit"
              class="icon-image"
            />
            <view v-else class="icon-placeholder">
              📊
            </view>
          </view>
          
          <!-- 报告信息 -->
          <view class="report-info">
            <text class="report-title">{{ report.title }}</text>
            <text class="report-description">{{ report.description }}</text>
            <text class="report-date">{{ formatDate(report.createdAt) }}</text>
          </view>
        </view>
      </view>
      
      <view class="carousel-action">
        <view class="action-button">
          <text class="action-icon">›</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'ReportCarousel',
  props: {
    report: {
      type: Object,
      required: true,
      default: () => ({
        id: '',
        title: '统计报告',
        description: '查看详细数据分析',
        createdAt: new Date(),
        icon: null
      })
    }
  },
  methods: {
    handleClick() {
      this.$emit('click', this.report);
      
      // 跳转到报告详情页
      uni.navigateTo({
        url: `/pages/reports/detail?id=${this.report.id}`
      });
    },
    
    formatDate(date) {
      if (!date) return '';
      
      const now = new Date();
      const reportDate = new Date(date);
      const diffTime = now - reportDate;
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) {
        return '今天';
      } else if (diffDays === 1) {
        return '昨天';
      } else if (diffDays < 7) {
        return `${diffDays}天前`;
      } else {
        return reportDate.toLocaleDateString('zh-CN', {
          month: 'short',
          day: 'numeric'
        });
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/design-tokens.scss';

.carousel-container {
  height: $carousel-height;
  margin-bottom: $spacing-sm;
  cursor: pointer;
  transition: transform $transition-fast;
  
  &:active {
    transform: scale(0.98);
  }
}

.carousel-content {
  height: 100%;
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-sm $spacing-md;
}

.carousel-main {
  flex: 1;
  background: $surface-container-high;
  border-radius: $radius-2xl;
  overflow: hidden;
  min-width: 0; // 防止flex项目收缩问题
}

.carousel-main-content {
  height: 100%;
  display: flex;
  align-items: center;
  padding: $spacing-md;
  gap: $spacing-md;
}

.report-icon {
  width: 120rpx; // 60px
  height: 120rpx; // 60px
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.3);
  border-radius: $radius-lg;
}

.icon-image {
  width: 80rpx; // 40px
  height: 80rpx; // 40px
}

.icon-placeholder {
  font-size: 48rpx; // 24px
  opacity: 0.6;
}

.report-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: $spacing-xs;
  min-width: 0; // 防止文本溢出
}

.report-title {
  font-family: $font-family-base;
  font-size: 32rpx; // 16px
  font-weight: 600;
  color: $text-primary;
  line-height: 1.3;
  
  // 单行省略
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.report-description {
  font-family: $font-family-base;
  font-size: $caption-font-size-rpx;
  font-weight: $caption-font-weight;
  color: $text-secondary;
  line-height: 1.4;
  
  // 两行省略
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.report-date {
  font-family: $font-family-base;
  font-size: 24rpx; // 12px
  color: $text-secondary;
  opacity: 0.7;
}

.carousel-action {
  width: 112rpx; // 56px
  flex-shrink: 0;
}

.action-button {
  width: 100%;
  height: 100%;
  background: $surface-container-high;
  border-radius: $radius-2xl;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color $transition-normal;
  
  &:active {
    background: darken($surface-container-high, 5%);
  }
}

.action-icon {
  font-size: 48rpx; // 24px
  color: $text-secondary;
  font-weight: 300;
}
</style>