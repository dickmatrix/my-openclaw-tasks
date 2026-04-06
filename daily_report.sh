#!/bin/bash
# =============================================================
# 飞书巡逻日报自动生成脚本
# Scout 侦察员自主巡逻日报 - 每天 09:00 定时触发
# 数据源：OpenClaw 本地知识库 (openclaw_app 容器)
# =============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/memory/daily_report.log"
DATE_TODAY="$(date +%Y-%m-%d)"
DATE_LABEL="$(date '+%Y年%m月%d日')"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

log "===== 飞书巡逻日报触发 ===== 日期: ${DATE_TODAY}"

# ------------------------------------------------------------------
# 1. 从 openclaw_app 容器内检索昨日 #AUDIT_PASS 成果摘要
# ------------------------------------------------------------------
log "[1/3] 检索昨日 AUDIT_PASS 记录..."

REPORT_DATA=$(docker exec openclaw_app \
  node /usr/local/lib/node_modules/openclaw/dist/index.js \
  memory query \
  "总结昨日所有标记为 #AUDIT_PASS 的任务摘要，包括 Issue 编号、任务名称和完成状态" \
  --limit 10 2>/dev/null) || {
  log "[WARN] memory query 失败，使用默认占位文本"
  REPORT_DATA="暂无昨日 AUDIT_PASS 记录，请检查流水线状态。"
}

log "[1/3] 检索完成。摘要长度: ${#REPORT_DATA} 字符"

# ------------------------------------------------------------------
# 2. 构造飞书卡片 JSON（直接通过 feishu webhook 发送）
#    使用 Scout 的飞书账号 (zhen_cha_yuan) 发消息到群组
# ------------------------------------------------------------------
log "[2/3] 构造飞书巡逻日报卡片..."

CARD_JSON=$(cat <<EOF
{
  "config": { "wide_screen_mode": true },
  "header": {
    "title": { "tag": "plain_text", "content": "🤖 侦察员自主巡逻日报 · ${DATE_LABEL}" },
    "template": "blue"
  },
  "elements": [
    {
      "tag": "div",
      "fields": [
        { "is_short": true, "text": { "tag": "lark_md", "content": "**🗓 报告日期:**\n${DATE_LABEL}" } },
        { "is_short": true, "text": { "tag": "lark_md", "content": "**📡 数据来源:**\nOpenClaw 本地知识库" } }
      ]
    },
    { "tag": "hr" },
    {
      "tag": "div",
      "text": {
        "tag": "lark_md",
        "content": "📂 **进化成果摘要 (Audit Pass):**\n${REPORT_DATA}"
      }
    },
    { "tag": "hr" },
    {
      "tag": "note",
      "elements": [{
        "tag": "plain_text",
        "content": "数据来源：OpenClaw 本地知识库 (Ollama-BGE-M3) · 自动生成于 $(date '+%Y-%m-%d %H:%M:%S')"
      }]
    }
  ]
}
EOF
)

# ------------------------------------------------------------------
# 3. 通过 OpenClaw Gateway Hook 触发 Scout 发送飞书卡片日报
#    Scout (zhen_cha_yuan) 绑定 feishu 账号，直接发消息
# ------------------------------------------------------------------
log "[3/3] 通过 OpenClaw hook 触发 Scout 发送日报..."

# 加载环境变量
if [ -f "${SCRIPT_DIR}/.env" ]; then
  set -o allexport
  source "${SCRIPT_DIR}/.env"
  set +o allexport
fi

GATEWAY_URL="${OPENCLAW_GATEWAY_URL:-http://127.0.0.1:18789}"
HOOK_TOKEN="${GATEWAY_HOOK_TOKEN:-feishu-gateway-hook-secret-2026-03-25}"

# 通过 hook 端点向 Scout agent 发送日报生成指令
HOOK_PAYLOAD=$(cat <<HOOKEOF
@Scout 请根据以下巡逻数据，以飞书卡片格式发送今日巡逻日报：

${REPORT_DATA}

日报卡片 JSON 参考模板已在系统中配置，请直接发送到当前群组。发送完成后输出 #SCOUT_READY。
HOOKEOF
)

HTTP_STATUS=$(curl -s -o /tmp/daily_report_resp.json -w "%{http_code}" \
  -X POST "${GATEWAY_URL}/hooks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${HOOK_TOKEN}" \
  -d "{
    \"agentId\": \"scout\",
    \"sessionKey\": \"hook:feishu-daily-report\",
    \"message\": $(echo "${HOOK_PAYLOAD}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
  }" 2>/dev/null) || HTTP_STATUS="000"

if [ "${HTTP_STATUS}" = "200" ] || [ "${HTTP_STATUS}" = "201" ] || [ "${HTTP_STATUS}" = "202" ]; then
  log "[3/3] ✅ Scout 日报触发成功 (HTTP ${HTTP_STATUS})"
else
  log "[3/3] ⚠️  Scout hook 返回 HTTP ${HTTP_STATUS}，响应: $(cat /tmp/daily_report_resp.json 2>/dev/null | head -c 200)"
  log "[FALLBACK] 尝试直接通过 openclaw CLI 发送..."

  docker exec openclaw_app \
    node /usr/local/lib/node_modules/openclaw/dist/index.js \
    chat --agent scout \
    "@Scout 请生成今日飞书巡逻日报。数据摘要：${REPORT_DATA}" 2>/dev/null \
  && log "[FALLBACK] ✅ CLI fallback 发送成功" \
  || log "[FALLBACK] ❌ CLI fallback 也失败，请人工检查"
fi

log "===== 日报流程结束 ====="
exit 0
