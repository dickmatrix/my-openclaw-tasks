#!/bin/bash

# 飞书Bot配对问题 - 快速诊断工具

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/openclaw.json"
PAIRING_FILE="$SCRIPT_DIR/.openclaw/credentials/feishu-pairing.json"
GATEWAY_LOG="/Users/mac/.openclaw/logs/gateway.log"  # 宿主机日志
GW_HELPER="$SCRIPT_DIR/scripts/openclaw-gateway.sh"
if [ -f "$GW_HELPER" ]; then
  GATEWAY_PORT="$("$GW_HELPER" host-port)"
else
  GATEWAY_PORT="$(jq -r '.gateway.port // 18889' "$CONFIG_FILE" 2>/dev/null || echo 18889)"
fi
PENDING_COUNT=0

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}飞书Bot配对问题 - 快速诊断${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 检查配置文件
echo -e "${YELLOW}1️⃣  检查配置文件...${NC}"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ openclaw.json 不存在${NC}"
else
    echo -e "${GREEN}✅ openclaw.json 存在${NC}"
    
    # 检查dmPolicy
    DM_POLICY=$(jq -r '.channels.feishu.dmPolicy // "未设置"' "$CONFIG_FILE" 2>/dev/null)
    echo "   dmPolicy: $DM_POLICY"
    
    # 检查allowFrom
    ALLOW_FROM=$(jq -r '.channels.feishu.allowFrom // []' "$CONFIG_FILE" 2>/dev/null)
    echo "   allowFrom: $ALLOW_FROM"
fi
echo ""

# 2. 检查配对存储
echo -e "${YELLOW}2️⃣  检查配对存储...${NC}"
if [ ! -f "$PAIRING_FILE" ]; then
    echo -e "${RED}❌ 配对文件不存在${NC}"
else
    echo -e "${GREEN}✅ 配对文件存在${NC}"
    
    # 统计配对请求
    REQUEST_COUNT=$(jq '.requests | length' "$PAIRING_FILE" 2>/dev/null || echo 0)
    echo "   配对请求数: $REQUEST_COUNT"
    
    if [ "$REQUEST_COUNT" -gt 0 ]; then
        # 检查是否有批准的请求
        APPROVED_COUNT=$(jq '[.requests[] | select(.approvedAt != null)] | length' "$PAIRING_FILE" 2>/dev/null || echo 0)
        PENDING_COUNT=$((REQUEST_COUNT - APPROVED_COUNT))
        
        echo "   已批准: $APPROVED_COUNT"
        echo "   待批准: $PENDING_COUNT"
        
        if [ "$PENDING_COUNT" -gt 0 ]; then
            echo -e "${RED}   ⚠️  有 $PENDING_COUNT 个待批准的请求${NC}"
        fi
    fi
fi
echo ""

# 3. 检查Gateway进程
echo -e "${YELLOW}3️⃣  检查Gateway进程...${NC}"
if pgrep -f "openclaw-gateway" > /dev/null; then
    echo -e "${GREEN}✅ Gateway 正在运行${NC}"
    
    # 获取进程信息
    PID=$(pgrep -f "openclaw-gateway" | head -1)
    CPU=$(ps aux | grep $PID | grep -v grep | awk '{print $3}')
    MEM=$(ps aux | grep $PID | grep -v grep | awk '{print $4}')
    echo "   PID: $PID"
    echo "   CPU: ${CPU}%"
    echo "   内存: ${MEM}%"
else
    echo -e "${RED}❌ Gateway 未运行${NC}"
fi
echo ""

# 4. 检查端口（与 openclaw.json gateway.port 一致）
echo -e "${YELLOW}4️⃣  检查 Gateway 端口 ${GATEWAY_PORT}...${NC}"
if lsof -i ":${GATEWAY_PORT}" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 端口 ${GATEWAY_PORT} 已监听${NC}"
else
    echo -e "${RED}❌ 端口 ${GATEWAY_PORT} 未监听${NC}"
fi
if command -v curl >/dev/null 2>&1; then
  HEALTH=$(curl -s -m 3 "http://127.0.0.1:${GATEWAY_PORT}/health" 2>/dev/null || true)
  if echo "$HEALTH" | grep -q '"ok"'; then
    echo -e "${GREEN}✅ /health 响应正常${NC}"
  else
    echo -e "${YELLOW}⚠️  /health 无正常 JSON（可能未启动或路径不同）${NC}"
  fi
fi
echo ""

# 5. 检查日志
echo -e "${YELLOW}5️⃣  检查最近的日志...${NC}"
if [ ! -f "$GATEWAY_LOG" ]; then
    echo -e "${YELLOW}⚠️  日志文件不存在${NC}"
else
    echo -e "${GREEN}✅ 日志文件存在${NC}"
    
    # 检查最近的错误
    ERROR_COUNT=$(tail -100 "$GATEWAY_LOG" 2>/dev/null | grep -i "error\|pairing" | wc -l)
    echo "   最近100行中的错误/配对相关: $ERROR_COUNT"
    
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}   最近的相关日志:${NC}"
        tail -100 "$GATEWAY_LOG" 2>/dev/null | grep -i "error\|pairing" | tail -5 | sed 's/^/   /'
    fi
fi
echo ""

# 6. 诊断总结
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}📊 诊断总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 判断问题
ISSUES=0

if [ "$DM_POLICY" = "未设置" ]; then
    echo -e "${RED}❌ 问题1: dmPolicy 未设置${NC}"
    echo "   解决: bash fix_feishu_pairing.sh open"
    ISSUES=$((ISSUES + 1))
elif [ "$DM_POLICY" = "pairing" ]; then
    if [ "$PENDING_COUNT" -gt 0 ]; then
        echo -e "${RED}❌ 问题2: 有待批准的配对请求${NC}"
        echo "   解决: bash fix_feishu_pairing.sh pairing"
        ISSUES=$((ISSUES + 1))
    fi
fi

if ! pgrep -f "openclaw-gateway" > /dev/null; then
    echo -e "${RED}❌ 问题3: Gateway 未运行${NC}"
    echo "   解决: openclaw gateway --port ${GATEWAY_PORT}"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ 没有发现问题！${NC}"
    echo ""
    echo "如果Bot仍然要求配对，请:"
    echo "1. 检查飞书群中的消息"
    echo "2. 查看完整日志: tail -50 $GATEWAY_LOG"
    echo "3. 重启Gateway: pkill -9 openclaw-gateway && sleep 2 && openclaw gateway --port ${GATEWAY_PORT}"
else
    echo ""
    echo -e "${YELLOW}发现 $ISSUES 个问题，请按上述建议修复${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
