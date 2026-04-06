#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_URL="$("$SCRIPT_DIR/scripts/openclaw-gateway.sh" base-url)"

echo "=== 飞书 Bot 连接测试 ==="
echo "Gateway base: $BASE_URL"
echo ""

# 测试 Gateway
echo "1. 测试 Gateway 连接..."
curl -s "${BASE_URL}/health" | jq . || echo "Gateway 未响应"
echo ""

# 测试各个 Bot
echo "2. 测试 Scout Bot..."
curl -s -X POST "${BASE_URL}/bot/scout/test" \
  -H "Content-Type: application/json" \
  -d '{"action":"ping"}' | jq . || echo "Scout Bot 未响应"
echo ""

echo "3. 测试 Censor Bot..."
curl -s -X POST "${BASE_URL}/bot/censor/test" \
  -H "Content-Type: application/json" \
  -d '{"action":"ping"}' | jq . || echo "Censor Bot 未响应"
echo ""

echo "4. 测试 Writer Bot..."
curl -s -X POST "${BASE_URL}/bot/writer/test" \
  -H "Content-Type: application/json" \
  -d '{"action":"ping"}' | jq . || echo "Writer Bot 未响应"
echo ""

echo "5. 测试 Auditor Bot..."
curl -s -X POST "${BASE_URL}/bot/auditor/test" \
  -H "Content-Type: application/json" \
  -d '{"action":"ping"}' | jq . || echo "Auditor Bot 未响应"
echo ""

echo "=== 测试完成 ==="
