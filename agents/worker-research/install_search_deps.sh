#!/bin/bash
# 安装免费搜索方案依赖

echo "=== 安装 OpenClaw 免费搜索方案依赖 ==="

# 方案 A: DuckDuckGo (完全免费)
echo ""
echo "📦 安装 DuckDuckGo 搜索依赖..."
pip install duckduckgo-search

# 方案 B: Google Gemini Grounding (1000/day 免费)
echo ""
echo "📦 安装 Google Gemini 依赖..."
pip install google-generativeai

# 可选：httpx (用于异步 HTTP 请求)
echo ""
echo "📦 安装 httpx (异步 HTTP 客户端)..."
pip install httpx

echo ""
echo "✅ 依赖安装完成！"
echo ""
echo "=== 配置说明 ==="
echo ""
echo "方案 A - DuckDuckGo (推荐，完全免费):"
echo "  - 无需配置，开箱即用"
echo "  - 调用: search(query, provider='duckduckgo')"
echo ""
echo "方案 B - Google Gemini Grounding:"
echo "  - 需要 Gemini API Key (免费额度: 1000/day)"
echo "  - 获取: https://ai.google.dev"
echo "  - 配置: export GEMINI_API_KEY='your-key'"
echo "  - 调用: search(query, provider='gemini', gemini_api_key='your-key')"
echo ""
echo "方案 C - 自动降级 (推荐):"
echo "  - 优先使用 DuckDuckGo，失败时自动降级"
echo "  - 调用: search(query, provider='auto')"
echo ""
