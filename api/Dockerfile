# 使用Debian 12的Python 3.12版本作为基础镜像，并用uv管理依赖
FROM python:3.12-slim-bookworm AS base

# 安装uv二进制
COPY --from=ghcr.io/astral-sh/uv:0.9.15 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app/api

# 优先复制依赖清单，让Docker缓存可以复用uv解析与安装结果
COPY pyproject.toml uv.lock ./

# 构建缓存并使用uv安装生产依赖
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# 二阶段生产环境构建
FROM base AS production

# 设置工作目录
WORKDIR /app/api

# 定义环境变量
ENV FLASK_APP=app/http/app.py
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV NLTK_DATA=/app/api/internal/core/unstructured/nltk_data
ENV HF_ENDPOINT=https://hf-mirror.com
ENV PATH="/app/api/.venv/bin:${PATH}"

# 设置容器时区为中国标准时间，避免时区错误
ENV TZ Asia/Shanghai

# 拷贝源码文件
COPY . /app/api

# 拷贝运行脚本并设置权限
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 暴露5001端口
EXPOSE 5001

# 运行脚本并启动项目
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
