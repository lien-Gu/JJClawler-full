# 生产环境运维指南

## 概述

本文档提供 JJCrawler3 生产环境的完整运维指南，包括应用监控、日志管理、数据备份、系统维护和故障处理等关键运维操作。

## 目录

1. [应用监控](#应用监控)
2. [日志管理](#日志管理)
3. [数据备份与恢复](#数据备份与恢复)
4. [系统维护](#系统维护)
5. [性能优化](#性能优化)
6. [安全管理](#安全管理)
7. [故障处理](#故障处理)
8. [升级部署](#升级部署)

## 应用监控

### 1. 健康检查监控

#### 基础健康检查

```bash
#!/bin/bash
# health_check.sh - 基础健康检查脚本

# 配置参数
SERVICE_URL="http://localhost:8000"
ALERT_EMAIL="admin@example.com"
LOG_FILE="/var/log/jjcrawler/health.log"

# 健康检查函数
check_service_health() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # API 健康检查
    if curl -s -f "${SERVICE_URL}/health" > /dev/null; then
        echo "[$timestamp] ✅ API 服务正常" | tee -a $LOG_FILE
        return 0
    else
        echo "[$timestamp] ❌ API 服务异常" | tee -a $LOG_FILE
        return 1
    fi
}

# 详细状态检查
check_detailed_status() {
    local response=$(curl -s "${SERVICE_URL}/stats")
    local status=$(echo $response | jq -r '.status')
    
    if [ "$status" = "ok" ]; then
        # 检查关键指标
        local crawler_stats=$(echo $response | jq -r '.crawler_stats')
        local scheduler_stats=$(echo $response | jq -r '.scheduler_stats')
        
        echo "爬虫统计: $crawler_stats"
        echo "调度器统计: $scheduler_stats"
    else
        echo "服务状态异常: $status"
        return 1
    fi
}

# 执行检查
if check_service_health; then
    check_detailed_status
else
    # 发送告警
    echo "JJCrawler3 服务异常，请立即检查" | mail -s "服务告警" $ALERT_EMAIL
    exit 1
fi
```

#### 高级监控指标

```bash
#!/bin/bash
# advanced_monitor.sh - 高级监控脚本

# 监控配置
THRESHOLDS=(
    "memory_usage:80"      # 内存使用率阈值 80%
    "cpu_usage:70"         # CPU使用率阈值 70%
    "disk_usage:85"        # 磁盘使用率阈值 85%
    "response_time:5000"   # 响应时间阈值 5秒
    "error_rate:5"         # 错误率阈值 5%
)

# 获取容器资源使用情况
get_container_stats() {
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" jjcrawler
}

# 检查响应时间
check_response_time() {
    local start_time=$(date +%s%3N)
    curl -s "${SERVICE_URL}/health" > /dev/null
    local end_time=$(date +%s%3N)
    local response_time=$((end_time - start_time))
    
    echo "响应时间: ${response_time}ms"
    
    if [ $response_time -gt 5000 ]; then
        echo "⚠️  响应时间过长: ${response_time}ms"
        return 1
    fi
    return 0
}

# 检查错误率
check_error_rate() {
    local stats=$(curl -s "${SERVICE_URL}/api/v1/crawl/scheduler/stats")
    local total_executed=$(echo $stats | jq -r '.total_executed // 0')
    local total_failed=$(echo $stats | jq -r '.total_failed // 0')
    
    if [ $total_executed -gt 0 ]; then
        local error_rate=$(echo "scale=2; $total_failed * 100 / $total_executed" | bc)
        echo "错误率: ${error_rate}%"
        
        if (( $(echo "$error_rate > 5" | bc -l) )); then
            echo "⚠️  错误率过高: ${error_rate}%"
            return 1
        fi
    fi
    return 0
}

# 检查磁盘空间
check_disk_space() {
    local usage=$(df -h /app/data | awk 'NR==2 {print $5}' | sed 's/%//')
    echo "数据目录磁盘使用率: ${usage}%"
    
    if [ $usage -gt 85 ]; then
        echo "⚠️  磁盘空间不足: ${usage}%"
        return 1
    fi
    return 0
}

# 执行全面监控
main() {
    echo "=== JJCrawler3 高级监控 $(date) ==="
    
    local issues=0
    
    echo "📊 容器资源使用:"
    get_container_stats
    
    echo -e "\n🕐 响应时间检查:"
    check_response_time || ((issues++))
    
    echo -e "\n📈 错误率检查:"
    check_error_rate || ((issues++))
    
    echo -e "\n💾 磁盘空间检查:"
    check_disk_space || ((issues++))
    
    echo -e "\n📋 总结:"
    if [ $issues -eq 0 ]; then
        echo "✅ 所有监控指标正常"
    else
        echo "❌ 发现 $issues 个监控告警"
        # 发送告警通知
        send_alert "发现 $issues 个监控告警，需要检查"
    fi
}

# 告警通知函数
send_alert() {
    local message="$1"
    # 钉钉机器人通知
    curl -H "Content-Type: application/json" \
         -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"JJCrawler3告警: $message\"}}" \
         "$DINGTALK_WEBHOOK"
}

main
```

### 2. 自动化监控部署

#### Prometheus + Grafana 监控

创建 `docker-compose.monitoring.yml`：

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: jjcrawler-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    container_name: jjcrawler-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml:ro
      - ./monitoring/grafana-dashboards.yml:/etc/grafana/provisioning/dashboards/dashboards.yml:ro
      - ./monitoring/dashboards:/var/lib/grafana/dashboards:ro
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false

  node-exporter:
    image: prom/node-exporter:latest
    container_name: jjcrawler-node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

volumes:
  prometheus_data:
  grafana_data:
```

#### Prometheus 配置

`monitoring/prometheus.yml`：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "jjcrawler_rules.yml"

scrape_configs:
  - job_name: 'jjcrawler'
    static_configs:
      - targets: ['jjcrawler:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 3. 实时监控面板

#### 自定义监控端点

在 FastAPI 应用中添加监控端点：

```python
# app/api/monitoring.py
from fastapi import APIRouter
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import psutil
import time

router = APIRouter()

# Prometheus 指标
REQUEST_COUNT = Counter('jjcrawler_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('jjcrawler_request_duration_seconds', 'Request duration')
TASK_COUNT = Counter('jjcrawler_tasks_total', 'Total tasks', ['type', 'status'])
MEMORY_USAGE = Gauge('jjcrawler_memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('jjcrawler_cpu_usage_percent', 'CPU usage percentage')

@router.get("/metrics")
async def get_metrics():
    """Prometheus 指标端点"""
    # 更新系统指标
    MEMORY_USAGE.set(psutil.virtual_memory().used)
    CPU_USAGE.set(psutil.cpu_percent())
    
    return Response(generate_latest(), media_type="text/plain")

@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard():
    """监控面板数据"""
    from app.modules.service.scheduler_service import get_scheduler_service
    from app.modules.service.task_service import get_task_manager
    
    scheduler_service = get_scheduler_service()
    task_manager = get_task_manager()
    
    return {
        "timestamp": time.time(),
        "system": {
            "memory_usage": psutil.virtual_memory()._asdict(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "disk_usage": psutil.disk_usage('/app/data')._asdict()
        },
        "scheduler": scheduler_service.get_job_statistics(),
        "tasks": task_manager.get_task_summary(),
        "active_jobs": len(scheduler_service.get_scheduled_jobs()) if scheduler_service.scheduler else 0
    }
```

## 日志管理

### 1. 日志配置和收集

#### 结构化日志配置

```python
# app/utils/log_utils.py 增强版
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any

class StructuredFormatter(logging.Formatter):
    """结构化日志格式器"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加自定义字段
        if hasattr(record, 'task_id'):
            log_data["task_id"] = record.task_id
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
            
        return json.dumps(log_data, ensure_ascii=False)

def setup_production_logging():
    """生产环境日志配置"""
    
    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 控制台处理器 (结构化输出)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # 文件处理器 (按大小滚动)
    file_handler = logging.handlers.RotatingFileHandler(
        filename="/app/logs/jjcrawler.log",
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)
    
    # 错误日志处理器
    error_handler = logging.handlers.RotatingFileHandler(
        filename="/app/logs/jjcrawler-error.log",
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)
    
    # 任务专用日志
    task_logger = logging.getLogger('jjcrawler.tasks')
    task_handler = logging.handlers.TimedRotatingFileHandler(
        filename="/app/logs/tasks.log",
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    task_handler.setFormatter(StructuredFormatter())
    task_logger.addHandler(task_handler)
```

#### Docker 日志配置

```yaml
# docker-compose.yml 日志配置
services:
  jjcrawler:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
        labels: "service=jjcrawler,environment=production"
    
    # 或使用 syslog 驱动
    # logging:
    #   driver: "syslog"
    #   options:
    #     syslog-address: "tcp://logstash:5000"
    #     tag: "jjcrawler"
```

### 2. 日志聚合和分析

#### ELK Stack 集成

```yaml
# docker-compose.elk.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    container_name: jjcrawler-elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:7.15.0
    container_name: jjcrawler-logstash
    volumes:
      - ./elk/logstash.conf:/usr/share/logstash/pipeline/logstash.conf:ro
    ports:
      - "5000:5000"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    container_name: jjcrawler-kibana
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

#### Logstash 配置

```ruby
# elk/logstash.conf
input {
  tcp {
    port => 5000
    codec => json_lines
  }
  
  beats {
    port => 5044
  }
}

filter {
  if [message] =~ /^{.*}$/ {
    json {
      source => "message"
    }
  }
  
  # 解析 JJCrawler 特定字段
  if [logger] =~ /jjcrawler/ {
    mutate {
      add_field => { "service" => "jjcrawler" }
    }
  }
  
  # 添加时间戳
  date {
    match => [ "timestamp", "ISO8601" ]
    target => "@timestamp"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "jjcrawler-logs-%{+YYYY.MM.dd}"
  }
  
  # 输出到控制台用于调试
  stdout { 
    codec => rubydebug 
  }
}
```

### 3. 日志运维脚本

#### 日志分析脚本

```bash
#!/bin/bash
# log_analysis.sh - 日志分析工具

LOG_DIR="/app/logs"
REPORT_FILE="/tmp/log_report_$(date +%Y%m%d).txt"

analyze_error_patterns() {
    echo "=== 错误模式分析 ===" > $REPORT_FILE
    echo "时间范围: $(date)" >> $REPORT_FILE
    echo "" >> $REPORT_FILE
    
    # 分析最近24小时的错误
    find $LOG_DIR -name "*.log" -mtime -1 -exec grep -h "ERROR" {} \; | \
    awk -F'"message":"' '{print $2}' | \
    awk -F'"' '{print $1}' | \
    sort | uniq -c | sort -nr | head -10 >> $REPORT_FILE
    
    echo "" >> $REPORT_FILE
}

analyze_performance() {
    echo "=== 性能分析 ===" >> $REPORT_FILE
    
    # 分析任务执行时间
    grep "任务执行完成" $LOG_DIR/tasks.log | \
    grep -o "耗时: [0-9.]*秒" | \
    awk '{print $2}' | sort -n | \
    awk '
    {
        values[NR] = $1
        sum += $1
    }
    END {
        avg = sum / NR
        median = values[int(NR/2)]
        print "平均执行时间: " avg "秒"
        print "中位数执行时间: " median "秒"
        print "最长执行时间: " values[NR] "秒"
    }' >> $REPORT_FILE
    
    echo "" >> $REPORT_FILE
}

check_disk_usage() {
    echo "=== 日志磁盘使用情况 ===" >> $REPORT_FILE
    du -sh $LOG_DIR/* | sort -hr >> $REPORT_FILE
    echo "" >> $REPORT_FILE
}

cleanup_old_logs() {
    echo "=== 清理旧日志 ===" >> $REPORT_FILE
    
    # 删除30天前的日志文件
    deleted_files=$(find $LOG_DIR -name "*.log.*" -mtime +30 -delete -print | wc -l)
    echo "已删除 $deleted_files 个旧日志文件" >> $REPORT_FILE
    
    # 压缩7天前的日志文件
    find $LOG_DIR -name "*.log" -mtime +7 ! -name "*.gz" -exec gzip {} \;
    compressed_files=$(find $LOG_DIR -name "*.log.gz" -mtime -1 | wc -l)
    echo "已压缩 $compressed_files 个日志文件" >> $REPORT_FILE
}

# 执行分析
analyze_error_patterns
analyze_performance
check_disk_usage
cleanup_old_logs

# 发送报告
echo "日志分析报告已生成: $REPORT_FILE"
cat $REPORT_FILE

# 如果有严重错误，发送告警
error_count=$(grep -c "ERROR" $LOG_DIR/jjcrawler-error.log 2>/dev/null || echo 0)
if [ $error_count -gt 10 ]; then
    echo "检测到大量错误 ($error_count 个)，请立即检查" | \
    mail -s "JJCrawler3 错误告警" admin@example.com
fi
```

## 数据备份与恢复

### 1. 数据备份策略

#### 自动备份脚本

```bash
#!/bin/bash
# backup.sh - 数据备份脚本

# 配置参数
BACKUP_DIR="/backup/jjcrawler"
DATA_DIR="/app/data"
RETENTION_DAYS=30
REMOTE_BACKUP_HOST="backup-server.example.com"
REMOTE_BACKUP_USER="backup"

# 创建备份目录
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
CURRENT_BACKUP_DIR="$BACKUP_DIR/$BACKUP_DATE"
mkdir -p "$CURRENT_BACKUP_DIR"

# 数据库备份
backup_database() {
    echo "开始备份数据库..."
    
    # SQLite 数据库备份
    if [ -f "$DATA_DIR/jjcrawler.db" ]; then
        # 创建数据库备份
        sqlite3 "$DATA_DIR/jjcrawler.db" ".backup $CURRENT_BACKUP_DIR/jjcrawler.db"
        
        # 导出 SQL 文件
        sqlite3 "$DATA_DIR/jjcrawler.db" ".dump" > "$CURRENT_BACKUP_DIR/jjcrawler.sql"
        
        # 验证备份完整性
        if sqlite3 "$CURRENT_BACKUP_DIR/jjcrawler.db" "PRAGMA integrity_check;" | grep -q "ok"; then
            echo "✅ 数据库备份成功"
        else
            echo "❌ 数据库备份验证失败"
            return 1
        fi
    fi
}

# 配置文件备份
backup_config() {
    echo "备份配置文件..."
    
    cp -r "$DATA_DIR/urls.json" "$CURRENT_BACKUP_DIR/"
    cp -r "$DATA_DIR/tasks/" "$CURRENT_BACKUP_DIR/"
    
    # 备份应用配置
    if [ -f "/app/.env" ]; then
        cp "/app/.env" "$CURRENT_BACKUP_DIR/"
    fi
    
    echo "✅ 配置文件备份完成"
}

# 日志备份
backup_logs() {
    echo "备份关键日志..."
    
    # 只备份最近7天的日志
    find /app/logs -name "*.log" -mtime -7 -exec cp {} "$CURRENT_BACKUP_DIR/" \;
    
    echo "✅ 日志备份完成"
}

# 压缩备份
compress_backup() {
    echo "压缩备份文件..."
    
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_DATE}.tar.gz" "$BACKUP_DATE/"
    
    if [ $? -eq 0 ]; then
        rm -rf "$CURRENT_BACKUP_DIR"
        echo "✅ 备份压缩完成: ${BACKUP_DATE}.tar.gz"
    else
        echo "❌ 备份压缩失败"
        return 1
    fi
}

# 清理旧备份
cleanup_old_backups() {
    echo "清理旧备份文件..."
    
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
    
    local remaining_backups=$(find "$BACKUP_DIR" -name "*.tar.gz" | wc -l)
    echo "✅ 清理完成，保留 $remaining_backups 个备份文件"
}

# 远程备份同步
sync_remote_backup() {
    echo "同步到远程备份服务器..."
    
    rsync -avz --delete "$BACKUP_DIR/" \
          "$REMOTE_BACKUP_USER@$REMOTE_BACKUP_HOST:/backup/jjcrawler/"
    
    if [ $? -eq 0 ]; then
        echo "✅ 远程备份同步完成"
    else
        echo "⚠️  远程备份同步失败"
    fi
}

# 备份验证
verify_backup() {
    local backup_file="$BACKUP_DIR/${BACKUP_DATE}.tar.gz"
    
    echo "验证备份文件完整性..."
    
    if tar -tzf "$backup_file" > /dev/null 2>&1; then
        echo "✅ 备份文件完整性验证通过"
        
        # 获取备份大小
        local backup_size=$(du -h "$backup_file" | cut -f1)
        echo "备份文件大小: $backup_size"
        
        return 0
    else
        echo "❌ 备份文件损坏"
        return 1
    fi
}

# 发送备份报告
send_backup_report() {
    local status=$1
    local report_file="/tmp/backup_report_$(date +%Y%m%d).txt"
    
    {
        echo "JJCrawler3 备份报告"
        echo "====================="
        echo "备份时间: $(date)"
        echo "备份状态: $status"
        echo "备份位置: $BACKUP_DIR"
        echo ""
        echo "备份内容:"
        echo "- 数据库文件"
        echo "- 配置文件"
        echo "- 任务记录"
        echo "- 关键日志"
        echo ""
        echo "磁盘使用情况:"
        df -h "$BACKUP_DIR"
    } > "$report_file"
    
    # 发送邮件报告
    mail -s "JJCrawler3 备份报告 - $status" admin@example.com < "$report_file"
}

# 主备份流程
main() {
    echo "开始 JJCrawler3 数据备份..."
    echo "备份时间: $(date)"
    echo "备份目录: $CURRENT_BACKUP_DIR"
    
    # 停止应用写入 (可选)
    # docker-compose pause jjcrawler
    
    if backup_database && backup_config && backup_logs; then
        if compress_backup && verify_backup; then
            cleanup_old_backups
            sync_remote_backup
            send_backup_report "成功"
            echo "✅ 备份流程完成"
        else
            send_backup_report "失败 - 压缩或验证错误"
            exit 1
        fi
    else
        send_backup_report "失败 - 数据备份错误"
        exit 1
    fi
    
    # 恢复应用 (可选)
    # docker-compose unpause jjcrawler
}

# 执行备份
main
```

### 2. 数据恢复流程

#### 数据恢复脚本

```bash
#!/bin/bash
# restore.sh - 数据恢复脚本

BACKUP_DIR="/backup/jjcrawler"
DATA_DIR="/app/data"
RESTORE_LOG="/tmp/restore_$(date +%Y%m%d_%H%M%S).log"

# 列出可用备份
list_backups() {
    echo "可用备份列表:"
    ls -lht "$BACKUP_DIR"/*.tar.gz | head -10
}

# 恢复数据库
restore_database() {
    local backup_path="$1"
    
    echo "恢复数据库..." | tee -a $RESTORE_LOG
    
    # 备份当前数据库
    if [ -f "$DATA_DIR/jjcrawler.db" ]; then
        cp "$DATA_DIR/jjcrawler.db" "$DATA_DIR/jjcrawler.db.bak.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # 恢复数据库文件
    if [ -f "$backup_path/jjcrawler.db" ]; then
        cp "$backup_path/jjcrawler.db" "$DATA_DIR/"
        echo "✅ 数据库文件恢复完成" | tee -a $RESTORE_LOG
    else
        echo "❌ 备份中未找到数据库文件" | tee -a $RESTORE_LOG
        return 1
    fi
    
    # 验证数据库完整性
    if sqlite3 "$DATA_DIR/jjcrawler.db" "PRAGMA integrity_check;" | grep -q "ok"; then
        echo "✅ 数据库完整性验证通过" | tee -a $RESTORE_LOG
    else
        echo "❌ 数据库完整性验证失败" | tee -a $RESTORE_LOG
        return 1
    fi
}

# 恢复配置文件
restore_config() {
    local backup_path="$1"
    
    echo "恢复配置文件..." | tee -a $RESTORE_LOG
    
    # 恢复 URLs 配置
    if [ -f "$backup_path/urls.json" ]; then
        cp "$backup_path/urls.json" "$DATA_DIR/"
        echo "✅ URLs 配置恢复完成" | tee -a $RESTORE_LOG
    fi
    
    # 恢复任务配置
    if [ -d "$backup_path/tasks" ]; then
        cp -r "$backup_path/tasks" "$DATA_DIR/"
        echo "✅ 任务配置恢复完成" | tee -a $RESTORE_LOG
    fi
    
    # 恢复环境配置
    if [ -f "$backup_path/.env" ]; then
        cp "$backup_path/.env" "/app/"
        echo "✅ 环境配置恢复完成" | tee -a $RESTORE_LOG
    fi
}

# 验证恢复结果
verify_restore() {
    echo "验证恢复结果..." | tee -a $RESTORE_LOG
    
    # 检查关键文件
    local files=("$DATA_DIR/jjcrawler.db" "$DATA_DIR/urls.json")
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            echo "✅ $file 存在" | tee -a $RESTORE_LOG
        else
            echo "❌ $file 缺失" | tee -a $RESTORE_LOG
            return 1
        fi
    done
    
    # 测试数据库连接
    if sqlite3 "$DATA_DIR/jjcrawler.db" "SELECT COUNT(*) FROM books;" > /dev/null 2>&1; then
        echo "✅ 数据库连接测试通过" | tee -a $RESTORE_LOG
    else
        echo "❌ 数据库连接测试失败" | tee -a $RESTORE_LOG
        return 1
    fi
}

# 主恢复流程
restore_from_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        echo "错误: 备份文件不存在: $backup_file"
        return 1
    fi
    
    echo "开始从备份恢复: $backup_file" | tee -a $RESTORE_LOG
    
    # 停止应用
    echo "停止应用服务..." | tee -a $RESTORE_LOG
    docker-compose stop jjcrawler
    
    # 解压备份
    local temp_dir="/tmp/restore_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$temp_dir"
    
    echo "解压备份文件..." | tee -a $RESTORE_LOG
    tar -xzf "$backup_file" -C "$temp_dir"
    
    local backup_path="$temp_dir/$(basename "$backup_file" .tar.gz)"
    
    # 执行恢复
    if restore_database "$backup_path" && restore_config "$backup_path"; then
        if verify_restore; then
            echo "✅ 数据恢复完成" | tee -a $RESTORE_LOG
            
            # 重启应用
            echo "重启应用服务..." | tee -a $RESTORE_LOG
            docker-compose start jjcrawler
            
            # 等待服务启动
            sleep 30
            
            # 验证服务
            if curl -s -f http://localhost:8000/health > /dev/null; then
                echo "✅ 服务恢复成功" | tee -a $RESTORE_LOG
            else
                echo "⚠️  服务启动异常，请检查" | tee -a $RESTORE_LOG
            fi
        else
            echo "❌ 恢复验证失败" | tee -a $RESTORE_LOG
            return 1
        fi
    else
        echo "❌ 数据恢复失败" | tee -a $RESTORE_LOG
        return 1
    fi
    
    # 清理临时文件
    rm -rf "$temp_dir"
}

# 脚本使用说明
usage() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -l, --list              列出可用备份"
    echo "  -r, --restore <file>    从指定备份恢复"
    echo "  -h, --help              显示帮助信息"
}

# 主函数
main() {
    case "$1" in
        -l|--list)
            list_backups
            ;;
        -r|--restore)
            if [ -z "$2" ]; then
                echo "错误: 请指定备份文件"
                usage
                exit 1
            fi
            restore_from_backup "$2"
            ;;
        -h|--help)
            usage
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "$@"
```

## 系统维护

### 1. 定期维护任务

#### 数据库维护

```bash
#!/bin/bash
# db_maintenance.sh - 数据库维护脚本

DB_PATH="/app/data/jjcrawler.db"
MAINTENANCE_LOG="/var/log/jjcrawler/maintenance.log"

# 数据库优化
optimize_database() {
    echo "执行数据库优化..." | tee -a $MAINTENANCE_LOG
    
    # VACUUM 操作
    sqlite3 "$DB_PATH" "VACUUM;" 2>&1 | tee -a $MAINTENANCE_LOG
    
    # 重新分析统计信息
    sqlite3 "$DB_PATH" "ANALYZE;" 2>&1 | tee -a $MAINTENANCE_LOG
    
    # 检查完整性
    local integrity_check=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;")
    if [ "$integrity_check" = "ok" ]; then
        echo "✅ 数据库完整性检查通过" | tee -a $MAINTENANCE_LOG
    else
        echo "❌ 数据库完整性检查失败: $integrity_check" | tee -a $MAINTENANCE_LOG
        return 1
    fi
    
    # 获取数据库大小
    local db_size=$(du -h "$DB_PATH" | cut -f1)
    echo "数据库当前大小: $db_size" | tee -a $MAINTENANCE_LOG
}

# 清理过期数据
cleanup_expired_data() {
    echo "清理过期数据..." | tee -a $MAINTENANCE_LOG
    
    # 清理90天前的快照数据
    local deleted_snapshots=$(sqlite3 "$DB_PATH" "
        DELETE FROM book_snapshots 
        WHERE created_at < datetime('now', '-90 days');
        SELECT changes();
    ")
    
    echo "已清理 $deleted_snapshots 条过期书籍快照" | tee -a $MAINTENANCE_LOG
    
    # 清理90天前的排行榜快照
    local deleted_rankings=$(sqlite3 "$DB_PATH" "
        DELETE FROM ranking_snapshots 
        WHERE created_at < datetime('now', '-90 days');
        SELECT changes();
    ")
    
    echo "已清理 $deleted_rankings 条过期排行榜快照" | tee -a $MAINTENANCE_LOG
}

# 更新数据库统计
update_statistics() {
    echo "更新数据库统计信息..." | tee -a $MAINTENANCE_LOG
    
    local total_books=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM books;")
    local total_snapshots=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM book_snapshots;")
    local total_rankings=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM ranking_snapshots;")
    
    echo "数据统计:" | tee -a $MAINTENANCE_LOG
    echo "- 总书籍数: $total_books" | tee -a $MAINTENANCE_LOG
    echo "- 总快照数: $total_snapshots" | tee -a $MAINTENANCE_LOG
    echo "- 总排行榜快照数: $total_rankings" | tee -a $MAINTENANCE_LOG
}

# 主维护流程
main() {
    echo "开始数据库维护 - $(date)" | tee -a $MAINTENANCE_LOG
    
    # 停止写入操作 (可选)
    # docker-compose exec jjcrawler curl -X POST http://localhost:8000/api/v1/maintenance/enable
    
    if optimize_database && cleanup_expired_data; then
        update_statistics
        echo "✅ 数据库维护完成" | tee -a $MAINTENANCE_LOG
    else
        echo "❌ 数据库维护失败" | tee -a $MAINTENANCE_LOG
        exit 1
    fi
    
    # 恢复写入操作 (可选)
    # docker-compose exec jjcrawler curl -X POST http://localhost:8000/api/v1/maintenance/disable
}

main
```

#### 系统清理脚本

```bash
#!/bin/bash
# system_cleanup.sh - 系统清理脚本

# Docker 清理
cleanup_docker() {
    echo "清理 Docker 资源..."
    
    # 清理未使用的镜像
    docker image prune -f
    
    # 清理未使用的容器
    docker container prune -f
    
    # 清理未使用的网络
    docker network prune -f
    
    # 清理未使用的卷
    docker volume prune -f
    
    echo "✅ Docker 清理完成"
}

# 日志清理
cleanup_logs() {
    echo "清理系统日志..."
    
    # 清理 journal 日志
    journalctl --vacuum-time=30d
    
    # 清理应用日志
    find /app/logs -name "*.log.*" -mtime +30 -delete
    
    echo "✅ 日志清理完成"
}

# 临时文件清理
cleanup_temp_files() {
    echo "清理临时文件..."
    
    # 清理系统临时文件
    find /tmp -type f -mtime +7 -delete 2>/dev/null
    
    # 清理应用临时文件
    find /app -name "*.tmp" -mtime +1 -delete 2>/dev/null
    
    echo "✅ 临时文件清理完成"
}

# 主清理流程
main() {
    echo "开始系统清理 - $(date)"
    
    cleanup_docker
    cleanup_logs
    cleanup_temp_files
    
    echo "✅ 系统清理完成"
    
    # 显示清理后的磁盘使用情况
    echo "磁盘使用情况:"
    df -h
}

main
```

### 2. 系统更新和升级

#### 应用升级脚本

```bash
#!/bin/bash
# upgrade.sh - 应用升级脚本

# 配置参数
BACKUP_DIR="/backup/jjcrawler/upgrades"
SERVICE_NAME="jjcrawler"
HEALTH_CHECK_URL="http://localhost:8000/health"
ROLLBACK_TIMEOUT=300

# 预升级检查
pre_upgrade_check() {
    echo "执行预升级检查..."
    
    # 检查当前服务状态
    if ! curl -s -f "$HEALTH_CHECK_URL" > /dev/null; then
        echo "❌ 当前服务状态异常，升级中止"
        return 1
    fi
    
    # 检查磁盘空间
    local disk_usage=$(df /app | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $disk_usage -gt 80 ]; then
        echo "❌ 磁盘空间不足 ($disk_usage%)，升级中止"
        return 1
    fi
    
    # 检查内存使用
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ $mem_usage -gt 90 ]; then
        echo "❌ 内存使用过高 ($mem_usage%)，升级中止"
        return 1
    fi
    
    echo "✅ 预升级检查通过"
}

# 创建升级备份
create_upgrade_backup() {
    echo "创建升级备份..."
    
    local backup_path="$BACKUP_DIR/upgrade_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_path"
    
    # 备份当前版本
    docker save jjcrawler:latest > "$backup_path/jjcrawler_current.tar"
    
    # 备份数据和配置
    cp -r /app/data "$backup_path/"
    cp /app/.env "$backup_path/" 2>/dev/null || true
    cp docker-compose.yml "$backup_path/"
    
    echo "upgrade_backup_path=$backup_path" > /tmp/upgrade_vars.env
    echo "✅ 升级备份创建完成: $backup_path"
}

# 执行升级
perform_upgrade() {
    echo "开始执行升级..."
    
    # 拉取新镜像
    echo "拉取新镜像..."
    docker-compose pull
    
    # 停止当前服务
    echo "停止当前服务..."
    docker-compose down
    
    # 启动新版本
    echo "启动新版本..."
    docker-compose up -d
    
    echo "✅ 升级部署完成"
}

# 升级后验证
post_upgrade_verification() {
    echo "执行升级后验证..."
    
    local retry_count=0
    local max_retries=30
    
    # 等待服务启动
    while [ $retry_count -lt $max_retries ]; do
        if curl -s -f "$HEALTH_CHECK_URL" > /dev/null; then
            echo "✅ 服务健康检查通过"
            break
        else
            echo "等待服务启动... ($((retry_count + 1))/$max_retries)"
            sleep 10
            ((retry_count++))
        fi
    done
    
    if [ $retry_count -ge $max_retries ]; then
        echo "❌ 服务启动超时，需要回滚"
        return 1
    fi
    
    # 功能测试
    echo "执行功能测试..."
    
    # 测试 API 端点
    local test_endpoints=(
        "/health"
        "/api/v1/pages"
        "/stats"
    )
    
    for endpoint in "${test_endpoints[@]}"; do
        if curl -s -f "http://localhost:8000$endpoint" > /dev/null; then
            echo "✅ $endpoint 测试通过"
        else
            echo "❌ $endpoint 测试失败"
            return 1
        fi
    done
    
    echo "✅ 升级后验证完成"
}

# 回滚操作
rollback() {
    echo "执行回滚操作..."
    
    source /tmp/upgrade_vars.env 2>/dev/null || {
        echo "❌ 无法找到备份路径，回滚失败"
        return 1
    }
    
    # 停止当前服务
    docker-compose down
    
    # 恢复镜像
    if [ -f "$upgrade_backup_path/jjcrawler_current.tar" ]; then
        docker load < "$upgrade_backup_path/jjcrawler_current.tar"
    fi
    
    # 恢复配置和数据
    cp -r "$upgrade_backup_path/data"/* /app/data/
    cp "$upgrade_backup_path/.env" /app/ 2>/dev/null || true
    cp "$upgrade_backup_path/docker-compose.yml" ./
    
    # 启动服务
    docker-compose up -d
    
    # 验证回滚
    sleep 30
    if curl -s -f "$HEALTH_CHECK_URL" > /dev/null; then
        echo "✅ 回滚成功"
    else
        echo "❌ 回滚验证失败"
        return 1
    fi
}

# 主升级流程
main() {
    echo "开始 JJCrawler3 升级流程..."
    echo "升级时间: $(date)"
    
    # 创建日志文件
    local upgrade_log="/var/log/jjcrawler/upgrade_$(date +%Y%m%d_%H%M%S).log"
    exec > >(tee -a "$upgrade_log") 2>&1
    
    if pre_upgrade_check && create_upgrade_backup; then
        if perform_upgrade; then
            if post_upgrade_verification; then
                echo "✅ 升级成功完成"
                
                # 发送成功通知
                echo "JJCrawler3 升级成功完成" | \
                mail -s "升级成功通知" admin@example.com
                
                # 清理旧备份 (保留最近5次)
                find "$BACKUP_DIR" -maxdepth 1 -type d -name "upgrade_*" | \
                sort -r | tail -n +6 | xargs rm -rf
                
            else
                echo "❌ 升级后验证失败，执行回滚"
                if rollback; then
                    echo "✅ 回滚成功"
                else
                    echo "❌ 回滚失败，需要人工干预"
                    exit 1
                fi
            fi
        else
            echo "❌ 升级部署失败，执行回滚"
            rollback
        fi
    else
        echo "❌ 预升级检查或备份失败，升级中止"
        exit 1
    fi
}

# 处理命令行参数
case "$1" in
    --check)
        pre_upgrade_check
        ;;
    --rollback)
        rollback
        ;;
    *)
        main
        ;;
esac
```

## 性能优化

### 1. 应用性能优化

#### 数据库性能调优

```python
# app/modules/database/optimization.py
import sqlite3
from typing import List, Dict
from app.utils.log_utils import get_logger

logger = get_logger(__name__)

class DatabaseOptimizer:
    """数据库性能优化器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def optimize_sqlite_settings(self):
        """优化 SQLite 设置"""
        with sqlite3.connect(self.db_path) as conn:
            # 启用 WAL 模式
            conn.execute("PRAGMA journal_mode = WAL")
            
            # 增加缓存大小
            conn.execute("PRAGMA cache_size = -65536")  # 64MB
            
            # 设置同步模式
            conn.execute("PRAGMA synchronous = NORMAL")
            
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            
            # 设置内存临时存储
            conn.execute("PRAGMA temp_store = MEMORY")
            
            # 优化页面大小
            conn.execute("PRAGMA page_size = 4096")
            
            logger.info("SQLite 性能优化设置已应用")
    
    def create_optimized_indexes(self):
        """创建优化索引"""
        indexes = [
            # 书籍表索引
            "CREATE INDEX IF NOT EXISTS idx_books_novel_id ON books(novel_id)",
            "CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)",
            "CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)",
            "CREATE INDEX IF NOT EXISTS idx_books_status ON books(status)",
            
            # 书籍快照表索引
            "CREATE INDEX IF NOT EXISTS idx_book_snapshots_book_id ON book_snapshots(book_id)",
            "CREATE INDEX IF NOT EXISTS idx_book_snapshots_created_at ON book_snapshots(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_book_snapshots_book_created ON book_snapshots(book_id, created_at)",
            
            # 排行榜快照表索引
            "CREATE INDEX IF NOT EXISTS idx_ranking_snapshots_ranking_id ON ranking_snapshots(ranking_id)",
            "CREATE INDEX IF NOT EXISTS idx_ranking_snapshots_created_at ON ranking_snapshots(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_ranking_snapshots_ranking_created ON ranking_snapshots(ranking_id, created_at)",
            
            # 复合索引
            "CREATE INDEX IF NOT EXISTS idx_books_compound ON books(status, genre, updated_at)",
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            for index_sql in indexes:
                try:
                    conn.execute(index_sql)
                    logger.debug(f"创建索引: {index_sql}")
                except sqlite3.Error as e:
                    logger.warning(f"索引创建失败: {e}")
        
        logger.info("数据库索引优化完成")
    
    def analyze_query_performance(self) -> Dict:
        """分析查询性能"""
        with sqlite3.connect(self.db_path) as conn:
            # 启用查询计划分析
            conn.execute("PRAGMA optimize")
            
            # 收集统计信息
            conn.execute("ANALYZE")
            
            # 获取数据库统计
            cursor = conn.execute("""
                SELECT 
                    name as table_name,
                    COUNT(*) as row_count
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            table_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 获取索引使用情况
            cursor = conn.execute("""
                SELECT name as index_name, tbl_name as table_name 
                FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            
            index_stats = [{"index": row[0], "table": row[1]} for row in cursor.fetchall()]
            
            return {
                "table_stats": table_stats,
                "index_stats": index_stats,
                "total_tables": len(table_stats),
                "total_indexes": len(index_stats)
            }
```

#### 爬虫性能优化

```python
# app/modules/crawler/performance.py
import asyncio
import time
from typing import List, Dict, Optional
from app.utils.log_utils import get_logger

logger = get_logger(__name__)

class CrawlerPerformanceOptimizer:
    """爬虫性能优化器"""
    
    def __init__(self):
        self.request_stats = []
        self.error_stats = []
    
    async def optimized_batch_crawl(self, urls: List[str], batch_size: int = 5) -> List[Dict]:
        """优化的批量爬取"""
        results = []
        
        # 将 URLs 分批处理
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            
            # 并发执行批次
            batch_results = await asyncio.gather(
                *[self._crawl_single_url(url) for url in batch],
                return_exceptions=True
            )
            
            # 处理结果
            for url, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"爬取失败 {url}: {result}")
                    self.error_stats.append({"url": url, "error": str(result)})
                else:
                    results.append(result)
            
            # 批次间延迟
            if i + batch_size < len(urls):
                await asyncio.sleep(1)
        
        return results
    
    async def _crawl_single_url(self, url: str) -> Dict:
        """单个 URL 爬取"""
        start_time = time.time()
        
        try:
            # 实际爬取逻辑
            result = await self._perform_crawl(url)
            
            # 记录性能统计
            duration = time.time() - start_time
            self.request_stats.append({
                "url": url,
                "duration": duration,
                "success": True
            })
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.request_stats.append({
                "url": url,
                "duration": duration,
                "success": False,
                "error": str(e)
            })
            raise
    
    def get_performance_report(self) -> Dict:
        """获取性能报告"""
        if not self.request_stats:
            return {"message": "无性能数据"}
        
        successful_requests = [r for r in self.request_stats if r["success"]]
        failed_requests = [r for r in self.request_stats if not r["success"]]
        
        if successful_requests:
            durations = [r["duration"] for r in successful_requests]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
        else:
            avg_duration = max_duration = min_duration = 0
        
        return {
            "total_requests": len(self.request_stats),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": len(successful_requests) / len(self.request_stats) * 100,
            "avg_duration": avg_duration,
            "max_duration": max_duration,
            "min_duration": min_duration,
            "errors": self.error_stats[-10:]  # 最近10个错误
        }
```

### 2. 系统性能监控

#### 性能监控脚本

```bash
#!/bin/bash
# performance_monitor.sh - 性能监控脚本

MONITOR_LOG="/var/log/jjcrawler/performance.log"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=85
ALERT_THRESHOLD_DISK=90

# 收集系统性能指标
collect_system_metrics() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # CPU 使用率
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    
    # 内存使用率
    local memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
    
    # 磁盘使用率
    local disk_usage=$(df -h /app | awk 'NR==2 {print $5}' | sed 's/%//')
    
    # 网络连接数
    local tcp_connections=$(netstat -an | grep ESTABLISHED | wc -l)
    
    # Docker 容器统计
    local container_stats=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" jjcrawler 2>/dev/null)
    
    # 记录指标
    echo "[$timestamp] CPU:${cpu_usage}% MEM:${memory_usage}% DISK:${disk_usage}% TCP:${tcp_connections} CONTAINER:${container_stats}" >> $MONITOR_LOG
    
    # 检查告警阈值
    check_performance_alerts "$cpu_usage" "$memory_usage" "$disk_usage"
}

# 检查性能告警
check_performance_alerts() {
    local cpu=$1
    local memory=$2
    local disk=$3
    
    local alerts=()
    
    if (( $(echo "$cpu > $ALERT_THRESHOLD_CPU" | bc -l) )); then
        alerts+=("CPU使用率过高: ${cpu}%")
    fi
    
    if (( $(echo "$memory > $ALERT_THRESHOLD_MEMORY" | bc -l) )); then
        alerts+=("内存使用率过高: ${memory}%")
    fi
    
    if [ "$disk" -gt "$ALERT_THRESHOLD_DISK" ]; then
        alerts+=("磁盘使用率过高: ${disk}%")
    fi
    
    # 发送告警
    if [ ${#alerts[@]} -gt 0 ]; then
        local alert_message="JJCrawler3 性能告警:\n$(printf '%s\n' "${alerts[@]}")"
        echo -e "$alert_message" | mail -s "性能告警" admin@example.com
    fi
}

# 应用性能分析
analyze_application_performance() {
    local response_time=$(curl -w "%{time_total}" -s -o /dev/null http://localhost:8000/health)
    local status_code=$(curl -w "%{http_code}" -s -o /dev/null http://localhost:8000/health)
    
    echo "API响应时间: ${response_time}s, 状态码: $status_code" >> $MONITOR_LOG
    
    # 检查响应时间告警
    if (( $(echo "$response_time > 5" | bc -l) )); then
        echo "API响应时间过长: ${response_time}s" | \
        mail -s "API性能告警" admin@example.com
    fi
}

# 生成性能报告
generate_performance_report() {
    local report_file="/tmp/performance_report_$(date +%Y%m%d).txt"
    
    {
        echo "JJCrawler3 性能报告"
        echo "==================="
        echo "报告时间: $(date)"
        echo ""
        
        echo "系统资源使用情况:"
        echo "---------------"
        echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')%"
        echo "内存: $(free | awk 'NR==2{printf "%.1f", $3*100/$2}')%"
        echo "磁盘: $(df -h /app | awk 'NR==2 {print $5}')"
        echo ""
        
        echo "最近24小时性能趋势:"
        echo "----------------"
        tail -n 288 $MONITOR_LOG | awk -F'[][]' '{print $2}' | \
        awk '{cpu+=$2; mem+=$3; disk+=$4; count++} END {
            printf "平均CPU: %.1f%%\n", cpu/count
            printf "平均内存: %.1f%%\n", mem/count  
            printf "平均磁盘: %.1f%%\n", disk/count
        }'
        echo ""
        
        echo "应用性能指标:"
        echo "----------"
        curl -s http://localhost:8000/api/v1/stats | jq -r '
            "任务成功率: " + (.scheduler_stats.total_succeeded / .scheduler_stats.total_executed * 100 | tostring) + "%",
            "活跃任务数: " + (.scheduler_stats.active_jobs | tostring),
            "最后执行时间: " + (.scheduler_stats.last_execution // "无")
        '
        
    } > "$report_file"
    
    echo "性能报告已生成: $report_file"
}

# 主监控流程
main() {
    case "$1" in
        "collect")
            collect_system_metrics
            analyze_application_performance
            ;;
        "report")
            generate_performance_report
            ;;
        *)
            echo "用法: $0 {collect|report}"
            exit 1
            ;;
    esac
}

main "$@"
```

通过这个完整的生产环境运维指南，您可以有效地监控、维护和优化 JJCrawler3 系统，确保其在生产环境中的稳定运行和高性能表现。建议根据实际部署环境和需求，调整相关配置参数和监控阈值。