FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，确保 Python 正常运行
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 配置国内镜像源以加速下载
RUN echo "deb http://mirrors.tencent.com/debian/ bookworm main" > /etc/apt/sources.list && \
    echo "deb http://mirrors.tencent.com/debian/ bookworm-updates main" >> /etc/apt/sources.list

# 1. 创建一个非 root 用户来运行应用，这是安全最佳实践
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser

# 2. 将工作目录的所有权交给新创建的 appuser
# 这样后续 appuser 才能在里面写入文件
RUN chown -R appuser:appuser /app

# 3. 切换到新创建的 appuser
# 从现在开始，所有后续的 RUN, CMD, ENTRYPOINT 指令都将以 appuser 的身份执行
USER appuser

# 4. 以 appuser 的身份，将用户自己的 bin 目录添加到 PATH 中
# 这是关键一步，确保后续安装的可执行文件能被找到
ENV PATH="/home/appuser/.local/bin:${PATH}"

# --- 依赖安装 ---

# 5. 复制依赖管理文件
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# 6. 以 appuser 的身份安装 uv 和项目依赖
# 配置 pip 使用国内镜像源并增加超时时间
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.cloud.tencent.com && \
    pip config set global.timeout 300 && \
    pip install --user uv --timeout=300 && \
    uv sync --no-dev --frozen

# --- 拷贝代码并设置权限 ---

# 7. 复制应用代码
# 使用 --chown 确保复制进来的文件也属于 appuser
COPY --chown=appuser:appuser app/ ./app/

# 8. 创建应用所需的目录
# 因为我们已经是 appuser，并且拥有 /app 目录的权限，所以可以直接创建
RUN mkdir -p /app/data /app/logs

# 暴露端口
EXPOSE 8000

# 健康检查 (保持不变，这是一个很好的设计)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
# 现在 appuser 可以在自己的 PATH 中找到 uvicorn
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]