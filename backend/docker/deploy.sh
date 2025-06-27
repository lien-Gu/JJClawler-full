#!/bin/bash

# JJCrawler 部署脚本
# 用于自动化部署 JJCrawler 后端服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 帮助信息
show_help() {
    cat << EOF
JJCrawler 部署脚本

用法: ./deploy.sh [选项]

选项:
    -m, --mode MODE     部署模式: direct (直接) 或 nginx (反向代理)
    -h, --help          显示帮助信息
    -c, --check         检查部署环境
    -s, --status        查看服务状态
    -l, --logs          查看服务日志
    -r, --restart       重启服务
    -d, --down          停止服务

部署模式说明:
    direct: 直接暴露8000端口，适合开发环境和内网使用
    nginx:  使用Nginx反向代理，适合生产环境

示例:
    ./deploy.sh -m direct     # 直接部署模式
    ./deploy.sh -m nginx      # 使用Nginx反向代理
    ./deploy.sh -c            # 检查环境
    ./deploy.sh -s            # 查看状态
    ./deploy.sh -l            # 查看日志

EOF
}

# 检查环境
check_environment() {
    log_info "检查部署环境..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    log_success "Docker 已安装: $(docker --version)"
    
    # 检查Docker Compose (现在已集成到Docker中)
    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装或不可用，请确保 Docker 版本支持 Compose 插件"
        exit 1
    fi

    # 优先使用集成的 docker compose，回退到独立的 docker-compose
    if docker compose version &> /dev/null; then
        log_success "Docker Compose 已安装 (集成版本): $(docker compose version)"
        COMPOSE_CMD="docker compose"
    else
        log_success "Docker Compose 已安装 (独立版本): $(docker-compose --version)"
        COMPOSE_CMD="docker-compose"
    fi
    
    # 检查项目文件
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile 不存在，请确保在正确的目录中运行脚本"
        exit 1
    fi
    
    if [ ! -f "../pyproject.toml" ]; then
        log_error "pyproject.toml 不存在，请确保项目结构完整"
        exit 1
    fi
    
    # 检查数据目录
    if [ ! -d "../data" ]; then
        log_warning "数据目录不存在，将自动创建"
        mkdir -p ../data
    fi
    
    log_success "环境检查完成"
}

# 直接部署模式
deploy_direct() {
    log_info "开始直接部署模式..."
    
    # 检查端口占用
    if netstat -tlnp 2>/dev/null | grep :8000 > /dev/null; then
        log_warning "端口 8000 已被占用，请检查是否有其他服务运行"
    fi
    
    # 构建和启动
    log_info "构建和启动容器..."
    $COMPOSE_CMD up -d --build
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 健康检查
    if curl -f -s http://localhost:8000/health > /dev/null; then
        log_success "服务部署成功！"
        log_info "API文档访问地址: http://localhost:8000/docs"
        log_info "健康检查地址: http://localhost:8000/health"
        log_info "前端访问配置: http://服务器IP:8000"
    else
        log_error "服务启动失败，请检查日志"
        $COMPOSE_CMD logs --tail=20 jjcrawler
        exit 1
    fi
}

# Nginx反向代理模式
deploy_nginx() {
    log_info "开始Nginx反向代理模式部署..."
    
    # 检查端口占用
    if netstat -tlnp 2>/dev/null | grep :80 > /dev/null; then
        log_warning "端口 80 已被占用，请检查是否有其他服务运行"
    fi
    
    # 检查nginx配置
    if [ ! -f "nginx.conf" ]; then
        log_error "nginx.conf 不存在"
        exit 1
    fi
    
    # 构建和启动
    log_info "构建和启动容器..."
    $COMPOSE_CMD -f docker-compose.nginx.yml up -d --build
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 15
    
    # 健康检查
    if curl -f -s http://localhost/health > /dev/null; then
        log_success "服务部署成功！"
        log_info "API文档访问地址: http://localhost/docs"
        log_info "健康检查地址: http://localhost/health"
        log_info "前端访问配置: http://服务器IP"
    else
        log_error "服务启动失败，请检查日志"
        $COMPOSE_CMD -f docker-compose.nginx.yml logs --tail=20
        exit 1
    fi
}

# 查看服务状态
show_status() {
    log_info "查看服务状态..."
    
    # 检查直接模式
    if $COMPOSE_CMD ps | grep jjcrawler-backend > /dev/null; then
        log_info "直接模式服务状态:"
        $COMPOSE_CMD ps
        return
    fi

    # 检查nginx模式
    if $COMPOSE_CMD -f docker-compose.nginx.yml ps | grep jjcrawler > /dev/null; then
        log_info "Nginx代理模式服务状态:"
        $COMPOSE_CMD -f docker-compose.nginx.yml ps
        return
    fi
    
    log_warning "没有检测到运行中的服务"
}

# 查看服务日志
show_logs() {
    log_info "查看服务日志..."
    
    # 检查哪种模式在运行
    if $COMPOSE_CMD ps | grep jjcrawler-backend > /dev/null; then
        $COMPOSE_CMD logs -f --tail=50 jjcrawler
    elif $COMPOSE_CMD -f docker-compose.nginx.yml ps | grep jjcrawler > /dev/null; then
        echo "选择要查看的日志:"
        echo "1) JJCrawler 应用日志"
        echo "2) Nginx 日志"
        echo "3) 所有日志"
        read -p "请选择 (1-3): " choice

        case $choice in
            1) $COMPOSE_CMD -f docker-compose.nginx.yml logs -f --tail=50 jjcrawler ;;
            2) $COMPOSE_CMD -f docker-compose.nginx.yml logs -f --tail=50 nginx ;;
            3) $COMPOSE_CMD -f docker-compose.nginx.yml logs -f --tail=50 ;;
            *) log_error "无效选择" ;;
        esac
    else
        log_warning "没有检测到运行中的服务"
    fi
}

# 重启服务
restart_service() {
    log_info "重启服务..."
    
    if $COMPOSE_CMD ps | grep jjcrawler-backend > /dev/null; then
        $COMPOSE_CMD restart jjcrawler
        log_success "直接模式服务已重启"
    elif $COMPOSE_CMD -f docker-compose.nginx.yml ps | grep jjcrawler > /dev/null; then
        $COMPOSE_CMD -f docker-compose.nginx.yml restart
        log_success "Nginx代理模式服务已重启"
    else
        log_warning "没有检测到运行中的服务"
    fi
}

# 停止服务
stop_service() {
    log_info "停止服务..."
    
    if $COMPOSE_CMD ps | grep jjcrawler-backend > /dev/null; then
        $COMPOSE_CMD down
        log_success "直接模式服务已停止"
    fi

    if $COMPOSE_CMD -f docker-compose.nginx.yml ps | grep jjcrawler > /dev/null; then
        $COMPOSE_CMD -f docker-compose.nginx.yml down
        log_success "Nginx代理模式服务已停止"
    fi
    
    # 清理无用的镜像和容器
    read -p "是否清理无用的Docker镜像和容器? (y/N): " cleanup
    if [[ $cleanup == "y" || $cleanup == "Y" ]]; then
        docker system prune -f
        log_success "清理完成"
    fi
}

# 主函数
main() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--mode)
                MODE="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--check)
                check_environment
                exit 0
                ;;
            -s|--status)
                show_status
                exit 0
                ;;
            -l|--logs)
                show_logs
                exit 0
                ;;
            -r|--restart)
                restart_service
                exit 0
                ;;
            -d|--down)
                stop_service
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 如果没有指定模式，询问用户
    if [ -z "$MODE" ]; then
        echo "请选择部署模式:"
        echo "1) direct - 直接部署 (推荐用于开发/内网)"
        echo "2) nginx  - Nginx反向代理 (推荐用于生产)"
        read -p "请选择 (1-2): " choice
        
        case $choice in
            1) MODE="direct" ;;
            2) MODE="nginx" ;;
            *) log_error "无效选择"; exit 1 ;;
        esac
    fi
    
    # 检查环境
    check_environment
    
    # 根据模式部署
    case $MODE in
        direct)
            deploy_direct
            ;;
        nginx)
            deploy_nginx
            ;;
        *)
            log_error "无效的部署模式: $MODE"
            log_info "支持的模式: direct, nginx"
            exit 1
            ;;
    esac
}

# 确保脚本在正确的目录中运行
if [ ! -f "Dockerfile" ]; then
    log_error "请在包含 Dockerfile 的目录中运行此脚本"
    exit 1
fi

# 运行主函数
main "$@"