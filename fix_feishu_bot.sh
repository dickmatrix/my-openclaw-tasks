#!/bin/bash
# 飞书Bot快速修复脚本

set -e

PROJECT_DIR="/Users/mac/Documents/龙虾相关/my_openclaw"
ENV_FILE="$PROJECT_DIR/.env"

echo "=========================================="
echo "飞书Bot快速修复脚本"
echo "=========================================="
echo ""

# 第一步：修复环境变量
echo "第一步：修复环境变量..."
echo "当前 FEISHU_MAC_APP_ID: $(grep FEISHU_MAC_APP_ID $ENV_FILE | head -1)"

# 备份原文件
cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%s)"
echo "✓ 已备份原文件"

# 修复主Bot配置（使用Auditor Bot作为主Bot）
sed -i '' 's/^FEISHU_MAC_APP_ID=.*/FEISHU_MAC_APP_ID=cli_a94d84f810f81ccd/' "$ENV_FILE"
sed -i '' 's/^FEISHU_MAC_APP_SECRET=.*/FEISHU_MAC_APP_SECRET=zBby54R3UKWJy0pn2shoWY6dRQKlq3B1/' "$ENV_FILE"

echo "✓ 环境变量已修复"
echo "新 FEISHU_MAC_APP_ID: $(grep FEISHU_MAC_APP_ID $ENV_FILE | head -1)"
echo ""

# 第二步：杀死Gateway进程
echo "第二步：重启Gateway服务..."
if pgrep -f "openclaw-gateway" > /dev/null; then
    echo "发现运行中的Gateway进程，正在停止..."
    pkill -9 openclaw-gateway || true
    echo "✓ Gateway进程已停止"
else
    echo "✓ 没有运行中的Gateway进程"
fi

sleep 2

# 第三步：重启Gateway
echo "第三步：启动Gateway..."
cd "$PROJECT_DIR"

# 检查是否安装了openclaw
if ! command -v openclaw &> /dev/null; then
    echo "✗ openclaw命令未找到，请先安装"
    exit 1
fi

# 后台启动Gateway（监听端口与 openclaw.json gateway.port 一致）
GATEWAY_LISTEN_PORT="$("$PROJECT_DIR/scripts/openclaw-gateway.sh" listen-port)"
nohup openclaw gateway --port "$GATEWAY_LISTEN_PORT" > /tmp/gateway.log 2>&1 &
GATEWAY_PID=$!
echo "✓ Gateway已启动 (PID: $GATEWAY_PID, port $GATEWAY_LISTEN_PORT)"

# 等待Gateway启动
echo "等待Gateway启动..."
sleep 3

# 第四步：验证Gateway
echo ""
echo "第四步：验证Gateway状态..."

# 检查进程
if pgrep -f "openclaw-gateway" > /dev/null; then
    echo "✓ Gateway进程运行中"
else
    echo "✗ Gateway进程未运行"
    echo "查看日志: tail -50 /tmp/gateway.log"
    exit 1
fi

# 检查端口
if lsof -i ":$GATEWAY_LISTEN_PORT" > /dev/null 2>&1; then
    echo "✓ 端口${GATEWAY_LISTEN_PORT}已监听"
else
    echo "✗ 端口${GATEWAY_LISTEN_PORT}未监听"
    exit 1
fi

# 尝试健康检查（带超时；本机访问端口见 scripts/openclaw-gateway.sh host-port）
GATEWAY_HOST_PORT="$("$PROJECT_DIR/scripts/openclaw-gateway.sh" host-port)"
echo "检查Gateway健康状态..."
if timeout 5 curl -s "http://127.0.0.1:${GATEWAY_HOST_PORT}/health" > /dev/null 2>&1; then
    echo "✓ Gateway健康检查通过"
else
    echo "⚠ Gateway健康检查超时（这可能是正常的）"
fi

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "后续步骤："
echo "1. 在飞书群中测试Bot命令："
echo "   @Scout 扫描 /app/workspace"
echo ""
echo "2. 查看Gateway日志："
echo "   tail -f /Users/mac/.openclaw/logs/gateway.log  # 宿主机日志"
echo ""
echo "3. 如果仍有问题，运行诊断："
echo "   bash $PROJECT_DIR/test_feishu_connection.sh"
echo ""
