#!/bin/bash

# 飞书Bot配对问题 - 一键修复脚本
# 用法: bash fix_feishu_pairing.sh [方案]
# 方案: open (默认) | pairing | allowlist

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/openclaw.json"
PAIRING_FILE="$SCRIPT_DIR/.openclaw/credentials/feishu-pairing.json"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 方案选择
PLAN="${1:-open}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}飞书Bot配对问题 - 一键修复${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 验证文件存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ 错误: 找不到 openclaw.json${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 选择的方案: $PLAN${NC}"
echo ""

# 备份原配置
echo -e "${YELLOW}💾 备份原配置...${NC}"
cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%s)"
echo -e "${GREEN}✅ 备份完成${NC}"
echo ""

# 根据方案执行修复
case "$PLAN" in
    "open")
        echo -e "${YELLOW}🔓 方案A: 改为开放模式${NC}"
        echo "特点: 任何人都能访问，适合开发/测试"
        echo ""
        
        # 使用jq修改配置
        jq '.channels.feishu.dmPolicy = "open"' "$CONFIG_FILE" > "$CONFIG_FILE.tmp"
        mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
        
        echo -e "${GREEN}✅ 配置已修改: dmPolicy = \"open\"${NC}"
        ;;
        
    "pairing")
        echo -e "${YELLOW}🔐 方案B: 批准现有配对${NC}"
        echo "特点: 只允许已配对用户，安全"
        echo ""
        
        # 修改配置
        jq '.channels.feishu.dmPolicy = "pairing"' "$CONFIG_FILE" > "$CONFIG_FILE.tmp"
        mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
        
        # 批准配对请求
        if [ -f "$PAIRING_FILE" ]; then
            echo -e "${YELLOW}📝 批准配对请求...${NC}"
            jq '.requests[].approvedAt = now | todate' "$PAIRING_FILE" > "$PAIRING_FILE.tmp"
            mv "$PAIRING_FILE.tmp" "$PAIRING_FILE"
            echo -e "${GREEN}✅ 配对请求已批准${NC}"
        else
            echo -e "${YELLOW}⚠️  配对文件不存在，跳过批准步骤${NC}"
        fi
        
        echo -e "${GREEN}✅ 配置已修改: dmPolicy = \"pairing\"${NC}"
        ;;
        
    "allowlist")
        echo -e "${YELLOW}🛡️  方案C: 清理+allowlist${NC}"
        echo "特点: 最安全，只允许指定用户"
        echo ""
        
        # 获取用户ID
        read -p "请输入你的飞书用户ID (ou_xxxxxxxx): " USER_ID
        
        if [ -z "$USER_ID" ]; then
            echo -e "${RED}❌ 用户ID不能为空${NC}"
            exit 1
        fi
        
        # 修改配置
        jq ".channels.feishu.dmPolicy = \"allowlist\" | .channels.feishu.allowFrom = [\"$USER_ID\"]" "$CONFIG_FILE" > "$CONFIG_FILE.tmp"
        mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
        
        # 清理配对存储
        echo -e "${YELLOW}🧹 清理配对存储...${NC}"
        cat > "$PAIRING_FILE" << 'EOF'
{
  "version": 1,
  "requests": []
}
EOF
        echo -e "${GREEN}✅ 配对存储已清理${NC}"
        
        echo -e "${GREEN}✅ 配置已修改: dmPolicy = \"allowlist\", allowFrom = [\"$USER_ID\"]${NC}"
        ;;
        
    *)
        echo -e "${RED}❌ 未知方案: $PLAN${NC}"
        echo "支持的方案: open | pairing | allowlist"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}🔄 重启Gateway...${NC}"

# 杀死旧进程
if pgrep -f "openclaw-gateway" > /dev/null; then
    echo -e "${YELLOW}⏹️  停止旧Gateway进程...${NC}"
    pkill -9 openclaw-gateway || true
    sleep 2
    echo -e "${GREEN}✅ 旧进程已停止${NC}"
else
    echo -e "${YELLOW}ℹ️  Gateway进程未运行${NC}"
fi

echo ""
echo -e "${YELLOW}🚀 启动新Gateway...${NC}"
GATEWAY_LISTEN_PORT="$("$SCRIPT_DIR/scripts/openclaw-gateway.sh" listen-port)"
nohup openclaw gateway --port "$GATEWAY_LISTEN_PORT" > /dev/null 2>&1 &
sleep 3

# 验证Gateway状态
if pgrep -f "openclaw-gateway" > /dev/null; then
    echo -e "${GREEN}✅ Gateway已启动${NC}"
else
    echo -e "${RED}❌ Gateway启动失败${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ 修复完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 显示验证步骤
echo -e "${YELLOW}📋 验证步骤:${NC}"
echo "1. 检查配置:"
echo "   cat openclaw.json | jq '.channels.feishu.dmPolicy'"
echo ""
echo "2. 查看日志:"
echo "   tail -20 /Users/mac/.openclaw/logs/gateway.log  # 宿主机日志"
echo ""
echo "3. 在飞书测试:"
echo "   @Scout 扫描 /app/workspace"
echo ""

# 显示当前配置
echo -e "${YELLOW}📊 当前配置:${NC}"
jq '.channels.feishu | {dmPolicy, allowFrom}' "$CONFIG_FILE"
echo ""

echo -e "${GREEN}🎉 一切就绪！${NC}"
