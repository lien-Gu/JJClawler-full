<template>
  <BaseCard
    :title="title"
    :subtitle="subtitle"
    :clickable="clickable"
    :class="`color-${color}`"
    @click="onClick"
  >
    <!-- 统计内容 -->
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
    
    <!-- 描述信息 -->
    <template #footer v-if="description">
      <view class="stats-footer">
        <text class="stats-description">{{ description }}</text>
      </view>
    </template>
  </BaseCard>
</template>

<script>
import BaseCard from '@/components/BaseCard/BaseCard.vue'
import { formatNumber } from '@/utils/format.js'

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
  components: {
    BaseCard
  },
  mixins: [formatterMixin],
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
      default: 'primary',
      validator: (value) => ['primary', 'success', 'warning', 'error', 'info'].includes(value)
    }
  },
  emits: ['click'],
  
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
@import '@/styles/design-tokens.scss';

.stats-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: $spacing-sm;
}

.stats-main {
  display: flex;
  align-items: baseline;
  gap: $spacing-xs;
  
  .stats-number {
    font-size: 48rpx;
    font-weight: 700;
    color: $brand-primary;
  }
  
  .stats-unit {
    font-size: 28rpx;
    color: $text-secondary;
  }
}

.stats-trend {
  display: flex;
  align-items: center;
  gap: 4rpx;
  
  .trend-icon,
  .trend-text {
    font-size: 24rpx;
    font-weight: 600;
  }
  
  &.trend-up {
    .trend-icon,
    .trend-text {
      color: #34c759;
    }
  }
  
  &.trend-down {
    .trend-icon,
    .trend-text {
      color: #ff3b30;
    }
  }
}

.stats-footer {
  .stats-description {
    font-size: 24rpx;
    color: rgba($text-secondary, 0.7);
    line-height: 1.4;
  }
}

// 主题色彩变体
:deep(.color-success) {
  .stats-number {
    color: #34c759;
  }
}

:deep(.color-warning) {
  .stats-number {
    color: #ff9500;
  }
}

:deep(.color-error) {
  .stats-number {
    color: #ff3b30;
  }
}

:deep(.color-info) {
  .stats-number {
    color: #007aff;
  }
}

:deep(.color-primary) {
  .stats-number {
    color: $brand-primary;
  }
}
</style> 