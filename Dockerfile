FROM python:3.10-slim

WORKDIR /app

# 权限解耦与环境对齐：
# 1. 废弃显式 mkdir /app，由 WORKDIR 处理
# 2. 仅安装必要的运行环境，不安装 git 以减小体积
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 卷挂载配置：生产环境下可保留 COPY，但开发环境建议通过 docker-compose 挂载
COPY . .
CMD ["python", "main.py"]