#!/bin/bash

# JJCrawler Debian12 部署脚本

set -e

echo "=== JJCrawler 部署脚本 ==="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    echo "安装命令: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# 检查文件
if [ ! -f "Dockerfile" ]; then
    echo "错误: 请在 backend 目录中运行此脚本"
    echo "确保 Dockerfile 文件存在"
    exit 1
fi

# 确保数据目录存在
mkdir -p ./data/tasks/history ./data/failures

# 构建和启动
echo "构建和启动服务..."
docker compose up -d --build

# 等待启动
echo "等待服务启动..."
sleep 10

# 检查服务
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ 部署成功!"
    echo "API 文档: http://localhost:8000/docs"
    echo "健康检查: http://localhost:8000/health"
else
    echo "❌ 部署失败，查看日志:"
    docker compose logs jjcrawler
fi

echo ""
echo "管理命令:"
echo "  查看状态: docker compose ps"
echo "  查看日志: docker compose logs -f jjcrawler"
echo "  停止服务: docker compose down"