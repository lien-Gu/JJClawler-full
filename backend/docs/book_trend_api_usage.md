# 书籍趋势数据API使用说明

## 概述

书籍趋势数据API提供了两种获取趋势数据的方式：
1. **原始趋势数据** - 获取原始快照数据
2. **聚合趋势数据** - 按时间间隔聚合的统计数据

## API端点

### 1. 获取原始趋势数据

```
GET /api/v1/books/{book_id}/trend
```

**参数:**
- `book_id`: 书籍ID（路径参数）
- `days`: 统计天数，范围1-365（查询参数，默认7天）

**响应:**
返回指定天数内的所有快照数据，包含确切的时间点和数据值。

**示例请求:**
```
GET /api/v1/books/123/trend?days=30
```

### 2. 独立的时间间隔聚合端点

#### 2.1 按小时聚合
```
GET /api/v1/books/{book_id}/trend/hourly
```

**参数:**
- `book_id`: 书籍ID（路径参数）
- `hours`: 统计小时数，范围1-168（查询参数，默认24小时）

**适用场景:** 分析一天内的变化模式

**示例请求:**
```
GET /api/v1/books/123/trend/hourly?hours=48
```

#### 2.2 按天聚合
```
GET /api/v1/books/{book_id}/trend/daily
```

**参数:**
- `book_id`: 书籍ID（路径参数）
- `days`: 统计天数，范围1-90（查询参数，默认7天）

**适用场景:** 周/月级别的趋势分析

**示例请求:**
```
GET /api/v1/books/123/trend/daily?days=30
```

#### 2.3 按周聚合
```
GET /api/v1/books/{book_id}/trend/weekly
```

**参数:**
- `book_id`: 书籍ID（路径参数）
- `weeks`: 统计周数，范围1-52（查询参数，默认4周）

**适用场景:** 季度级别的趋势分析

**示例请求:**
```
GET /api/v1/books/123/trend/weekly?weeks=12
```

#### 2.4 按月聚合
```
GET /api/v1/books/{book_id}/trend/monthly
```

**参数:**
- `book_id`: 书籍ID（路径参数）
- `months`: 统计月数，范围1-24（查询参数，默认3个月）

**适用场景:** 年度级别的趋势分析

**示例请求:**
```
GET /api/v1/books/123/trend/monthly?months=12
```

### 3. 通用聚合端点（向后兼容）

```
GET /api/v1/books/{book_id}/trend/aggregated
```

**参数:**
- `book_id`: 书籍ID（路径参数）
- `period_count`: 统计周期数（查询参数，默认7）
- `interval`: 时间间隔（查询参数，默认"day"）
  - `hour`: 按小时聚合
  - `day`: 按天聚合
  - `week`: 按周聚合
  - `month`: 按月聚合

**示例请求:**
```
GET /api/v1/books/123/trend/aggregated?period_count=30&interval=day
```

### 聚合数据响应格式

所有聚合端点都返回相同的响应格式：

```json
{
  "success": true,
  "code": 200,
  "message": "获取30天的趋势数据成功",
  "data": [
    {
      "time_period": "2024-01-15",
      "avg_favorites": 3245.67,
      "avg_clicks": 15432.12,
      "avg_comments": 158.34,
      "avg_recommendations": 89.45,
      "max_favorites": 3280,
      "max_clicks": 15500,
      "min_favorites": 3210,
      "min_clicks": 15300,
      "snapshot_count": 24,
      "period_start": "2024-01-15T00:00:00Z",
      "period_end": "2024-01-15T23:59:59Z"
    }
  ],
  "count": 30
}
```

## 使用场景

### 1. 原始趋势数据适用于：
- 需要精确时间点数据的场景
- 绘制详细的时间序列图表
- 分析短期内的细粒度变化
- 数据导出和进一步分析

### 2. 聚合趋势数据适用于：
- 长期趋势分析
- 性能优化（数据量更小）
- 统计报表生成
- 不同时间粒度的对比分析

## 时间间隔说明

### Hour（小时聚合）
- 适用场景：分析一天内的变化模式
- 建议周期数：1-7天
- 数据粒度：每小时一个聚合点
- 示例：`/trend/aggregated?days=3&interval=hour`

### Day（天聚合）
- 适用场景：周/月级别的趋势分析
- 建议周期数：7-90天
- 数据粒度：每天一个聚合点
- 示例：`/trend/aggregated?days=30&interval=day`

### Week（周聚合）
- 适用场景：季度级别的趋势分析
- 建议周期数：4-52周
- 数据粒度：每周一个聚合点
- 示例：`/trend/aggregated?days=12&interval=week`

### Month（月聚合）
- 适用场景：年度级别的趋势分析
- 建议周期数：3-24个月
- 数据粒度：每月一个聚合点
- 示例：`/trend/aggregated?days=12&interval=month`

## 前端使用建议

### 使用独立端点的Chart.js示例
```javascript
// 按天获取趋势数据（推荐使用独立端点）
async function fetchDailyTrend(bookId, days = 30) {
  const response = await fetch(`/api/v1/books/${bookId}/trend/daily?days=${days}`);
  const data = await response.json();
  
  return {
    labels: data.data.map(point => point.time_period),
    datasets: [
      {
        label: '平均收藏数',
        data: data.data.map(point => point.avg_favorites),
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
      },
      {
        label: '平均点击数',
        data: data.data.map(point => point.avg_clicks),
        borderColor: 'rgb(255, 99, 132)',
        tension: 0.1
      }
    ]
  };
}

// 按小时获取趋势数据
async function fetchHourlyTrend(bookId, hours = 24) {
  const response = await fetch(`/api/v1/books/${bookId}/trend/hourly?hours=${hours}`);
  return response.json();
}

// 按周获取趋势数据
async function fetchWeeklyTrend(bookId, weeks = 4) {
  const response = await fetch(`/api/v1/books/${bookId}/trend/weekly?weeks=${weeks}`);
  return response.json();
}

// 按月获取趋势数据
async function fetchMonthlyTrend(bookId, months = 3) {
  const response = await fetch(`/api/v1/books/${bookId}/trend/monthly?months=${months}`);
  return response.json();
}
```

### Vue.js组件示例（使用独立端点）
```vue
<template>
  <div>
    <div class="trend-controls">
      <button @click="fetchHourlyData" :class="{active: activeInterval === 'hourly'}">
        按小时
      </button>
      <button @click="fetchDailyData" :class="{active: activeInterval === 'daily'}">
        按天
      </button>
      <button @click="fetchWeeklyData" :class="{active: activeInterval === 'weekly'}">
        按周
      </button>
      <button @click="fetchMonthlyData" :class="{active: activeInterval === 'monthly'}">
        按月
      </button>
    </div>
    
    <div class="period-input">
      <label>{{ periodLabel }}:</label>
      <input v-model="periodCount" type="number" :min="1" :max="maxPeriod" @change="fetchCurrentData">
    </div>
    
    <canvas ref="chart"></canvas>
  </div>
</template>

<script>
export default {
  data() {
    return {
      activeInterval: 'daily',
      periodCount: 7,
      bookId: this.$route.params.id,
      chart: null
    };
  },
  computed: {
    periodLabel() {
      const labels = {
        hourly: '小时数',
        daily: '天数',
        weekly: '周数',
        monthly: '月数'
      };
      return labels[this.activeInterval] || '周期数';
    },
    maxPeriod() {
      const maxValues = {
        hourly: 168,
        daily: 90,
        weekly: 52,
        monthly: 24
      };
      return maxValues[this.activeInterval] || 365;
    }
  },
  methods: {
    async fetchHourlyData() {
      this.activeInterval = 'hourly';
      this.periodCount = 24;
      const response = await this.$http.get(`/books/${this.bookId}/trend/hourly`, {
        params: { hours: this.periodCount }
      });
      this.updateChart(response.data.data, '小时级趋势');
    },
    
    async fetchDailyData() {
      this.activeInterval = 'daily';
      this.periodCount = 7;
      const response = await this.$http.get(`/books/${this.bookId}/trend/daily`, {
        params: { days: this.periodCount }
      });
      this.updateChart(response.data.data, '日级趋势');
    },
    
    async fetchWeeklyData() {
      this.activeInterval = 'weekly';
      this.periodCount = 4;
      const response = await this.$http.get(`/books/${this.bookId}/trend/weekly`, {
        params: { weeks: this.periodCount }
      });
      this.updateChart(response.data.data, '周级趋势');
    },
    
    async fetchMonthlyData() {
      this.activeInterval = 'monthly';
      this.periodCount = 3;
      const response = await this.$http.get(`/books/${this.bookId}/trend/monthly`, {
        params: { months: this.periodCount }
      });
      this.updateChart(response.data.data, '月级趋势');
    },
    
    async fetchCurrentData() {
      const methods = {
        hourly: this.fetchHourlyData,
        daily: this.fetchDailyData,
        weekly: this.fetchWeeklyData,
        monthly: this.fetchMonthlyData
      };
      
      if (methods[this.activeInterval]) {
        await methods[this.activeInterval]();
      }
    },
    
    updateChart(data, title) {
      // Chart.js更新逻辑
      if (this.chart) {
        this.chart.destroy();
      }
      
      const ctx = this.$refs.chart.getContext('2d');
      this.chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.map(point => point.time_period),
          datasets: [
            {
              label: '平均收藏数',
              data: data.map(point => point.avg_favorites),
              borderColor: 'rgb(75, 192, 192)',
              tension: 0.1
            }
          ]
        },
        options: {
          plugins: {
            title: {
              display: true,
              text: title
            }
          }
        }
      });
    }
  },
  
  mounted() {
    this.fetchDailyData(); // 默认加载日级数据
  }
};
</script>

<style scoped>
.trend-controls button {
  margin: 0 5px;
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
}

.trend-controls button.active {
  background: #007bff;
  color: white;
}

.period-input {
  margin: 10px 0;
}
</style>
```

### React Hook示例
```jsx
import { useState, useEffect, useCallback } from 'react';

const useBookTrend = (bookId) => {
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeInterval, setActiveInterval] = useState('daily');
  
  const fetchHourlyTrend = useCallback(async (hours = 24) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/books/${bookId}/trend/hourly?hours=${hours}`);
      const data = await response.json();
      setTrendData(data.data);
      setActiveInterval('hourly');
    } catch (error) {
      console.error('Failed to fetch hourly trend:', error);
    } finally {
      setLoading(false);
    }
  }, [bookId]);
  
  const fetchDailyTrend = useCallback(async (days = 7) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/books/${bookId}/trend/daily?days=${days}`);
      const data = await response.json();
      setTrendData(data.data);
      setActiveInterval('daily');
    } catch (error) {
      console.error('Failed to fetch daily trend:', error);
    } finally {
      setLoading(false);
    }
  }, [bookId]);
  
  const fetchWeeklyTrend = useCallback(async (weeks = 4) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/books/${bookId}/trend/weekly?weeks=${weeks}`);
      const data = await response.json();
      setTrendData(data.data);
      setActiveInterval('weekly');
    } catch (error) {
      console.error('Failed to fetch weekly trend:', error);
    } finally {
      setLoading(false);
    }
  }, [bookId]);
  
  const fetchMonthlyTrend = useCallback(async (months = 3) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/books/${bookId}/trend/monthly?months=${months}`);
      const data = await response.json();
      setTrendData(data.data);
      setActiveInterval('monthly');
    } catch (error) {
      console.error('Failed to fetch monthly trend:', error);
    } finally {
      setLoading(false);
    }
  }, [bookId]);
  
  return {
    trendData,
    loading,
    activeInterval,
    fetchHourlyTrend,
    fetchDailyTrend,
    fetchWeeklyTrend,
    fetchMonthlyTrend
  };
};

export default useBookTrend;
```

## 性能考虑

1. **聚合数据查询更高效**：对于长期趋势分析，优先使用聚合API
2. **合理的时间范围**：避免请求过长时间范围的原始数据
3. **缓存策略**：前端可以缓存聚合数据，减少重复请求
4. **分页处理**：对于大量数据，考虑使用分页参数

## 错误处理

常见错误码：
- `404`: 书籍不存在
- `400`: 参数错误（如不支持的interval值）
- `500`: 服务器内部错误

示例错误响应：
```json
{
  "success": false,
  "code": 400,
  "message": "不支持的时间间隔: invalid_interval",
  "timestamp": "2024-01-15T12:00:00Z"
}
```