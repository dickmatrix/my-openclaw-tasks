#!/bin/sh
# init-skills.sh — 容器启动时自动安装 Playwright MCP npm 包
# Chromium 浏览器通过卷挂载持久化，无需重新下载
# 用法：在 docker-compose command 中调用此脚本，最后 exec 原始进程

set -e

echo "[init-skills] 检查 playwright-mcp..."
if ! command -v playwright-mcp > /dev/null 2>&1; then
    echo "[init-skills] 安装系统依赖..."
    apt-get update -qq && apt-get install -y --no-install-recommends \
        libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libdbus-1-3 libxkbcommon0 \
        libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
        libgbm1 libasound2 libatspi2.0-0 \
        > /dev/null 2>&1
    echo "[init-skills] 安装 @playwright/mcp..."
    npm install -g @playwright/mcp @playwright/test --quiet
    echo "[init-skills] playwright-mcp 安装完成 (Chromium 从缓存卷加载)"
else
    echo "[init-skills] playwright-mcp $(playwright-mcp --version) 已就绪"
fi
