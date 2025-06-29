FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 配置国内镜像源以加速下载
RUN echo "deb http://mirrors.tencent.com/debian/ bookworm main" > /etc/apt/sources.list && \
    echo "deb http://mirrors.tencent.com/debian/ bookworm-updates main" >> /etc/apt/sources.list

# 安装系统依赖（简化版）
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 配置 pip 国内镜像源
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple/

# 复制依赖文件
COPY pyproject.toml poetry.lock* requirements.txt ./

# 尝试使用 Poetry，失败则使用 pip
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi || \
    pip install -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY data/ ./data/

# 创建数据目录
RUN mkdir -p /app/data/failures /app/data/tasks/history

# 设置数据目录权限
RUN chmod -R 755 /app/data

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]