<template>
  <view class="stats-card" :class="{ 'clickable': clickable }" @tap="onClick">
    <view class="stats-header" v-if="title">
      <text class="stats-title">{{ title }}</text>
      <text class="stats-subtitle" v-if="subtitle">{{ subtitle }}</text>
    </view>
    
    <view class="stats-content">
      <view class="stats-main">
        <text class="stats-number">{{ formatNumber(value) }}</text>
        <text class="stats-unit" v-if="unit">{{ unit }}</text>
      </view>
      
      <view class="stats-trend" v-if="trend !== null">
        <text class="trend-icon" :class="trendClass">{{ trendIcon }}</text>
        <text class="trend-text" :class="trendClass">{{ Math.abs(trend) }}%</text>
      </view>
    </view>
    
    <view class="stats-footer" v-if="description">
      <text class="stats-description">{{ description }}</text>
    </view>
  </view>
</template>

<script>
/**
 * 统计卡片组件
 * @description 用于展示统计数据的卡片组件，支持标题、数值、趋势、描述等
 * @property {String} title 卡片标题
 * @property {String} subtitle 卡片副标题
 * @property {Number|String} value 统计数值
 * @property {String} unit 数值单位
 * @property {Number} trend 趋势百分比（正数为上升，负数为下降）
 * @property {String} description 描述文本
 * @property {Boolean} clickable 是否可点击
 * @property {String} color 主题色彩
 * @event {Function} click 点击事件
 */
export default {
  name: 'StatsCard',
  props: {
    title: {
      type: String,
      default: ''
    },
    subtitle: {
      type: String,
      default: ''
    },
    value: {
      type: [Number, String],
      default: 0
    },
    unit: {
      type: String,
      default: ''
    },
    trend: {
      type: Number,
      default: null
    },
    description: {
      type: String,
      default: ''
    },
    clickable: {
      type: Boolean,
      default: false
    },
    color: {
      type: String,
      default: 'primary'
    }
  },
  
  computed: {
    /**
     * 趋势图标
     */
    trendIcon() {
      if (this.trend === null) return ''
      return this.trend > 0 ? '↗' : '↘'
    },
    
    /**
     * 趋势样式类
     */
    trendClass() {
      if (this.trend === null) return ''
      return this.trend > 0 ? 'trend-up' : 'trend-down'
    }
  },
  
  methods: {
    /**
     * 格式化数字显示
     */
    formatNumber(num) {
      if (typeof num !== 'number') return num
      
      if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k'
      }
      
      return num.toString()
    },
    
    /**
     * 点击事件
     */
    onClick() {
      if (this.clickable) {
        this.$emit('click')
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.stats-card {
  @include card-style;
  padding: $spacing-lg;
  margin-bottom: $spacing-sm;
  transition: all 0.3s ease;
  
  &.clickable {
    cursor: pointer;
    
    &:hover {
      transform: translateY(-2rpx);
      box-shadow: $shadow-dark;
    }
    
    &:active {
      transform: translateY(0);
    }
  }
}

.stats-header {
  margin-bottom: $spacing-md;
  
  .stats-title {
    display: block;
    font-size: $font-size-lg;
    font-weight: bold;
    color: $text-primary;
    margin-bottom: $spacing-xs;
  }
  
  .stats-subtitle {
    font-size: $font-size-sm;
    color: $text-secondary;
  }
}

.stats-content {
  @include flex-between;
  align-items: flex-end;
  margin-bottom: $spacing-sm;
}

.stats-main {
  @include flex-center;
  align-items: baseline;
  
  .stats-number {
    font-size: $font-size-xxl;
    font-weight: bold;
    color: $primary-color;
    margin-right: $spacing-xs;
  }
  
  .stats-unit {
    font-size: $font-size-md;
    color: $text-secondary;
  }
}

.stats-trend {
  @include flex-center;
  
  .trend-icon,
  .trend-text {
    font-size: $font-size-sm;
    font-weight: bold;
  }
  
  .trend-icon {
    margin-right: 4rpx;
  }
  
  &.trend-up {
    .trend-icon,
    .trend-text {
      color: #4cd964;
    }
  }
  
  &.trend-down {
    .trend-icon,
    .trend-text {
      color: #dd524d;
    }
  }
}

.stats-footer {
  .stats-description {
    font-size: $font-size-sm;
    color: $text-placeholder;
    line-height: 1.4;
  }
}

// 主题色彩变体
.stats-card.color-success {
  .stats-number {
    color: #4cd964;
  }
}

.stats-card.color-warning {
  .stats-number {
    color: #f0ad4e;
  }
}

.stats-card.color-error {
  .stats-number {
    color: #dd524d;
  }
}

.stats-card.color-info {
  .stats-number {
    color: #5bc0de;
  }
}
</style> 