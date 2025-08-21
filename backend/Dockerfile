FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 配置国内镜像源以加速下载
RUN echo "deb http://mirrors.tencent.com/debian/ bookworm main" > /etc/apt/sources.list && \
    echo "deb http://mirrors.tencent.com/debian/ bookworm-updates main" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 配置 pip 国内镜像源
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.cloud.tencent.com && \
    pip config set global.timeout 300

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装 uv 和项目依赖
RUN pip install uv --timeout=300 && \
    uv sync --no-dev --frozen

# 复制应用代码
COPY app/ ./app/

# 创建必要目录（root权限，无权限问题）
RUN mkdir -p /app/data /app/logs

# 暴露端口
EXPOSE 8000

# 健康检查 (保持不变，这是一个很好的设计)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令（以root用户运行，无权限问题）
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]