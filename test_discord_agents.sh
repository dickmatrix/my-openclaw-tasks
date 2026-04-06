#!/bin/bash
# Discord Agent 连接测试脚本
# 使用方法: bash test_discord_agents.sh

echo "=========================================="
echo "Discord Agent 连接测试"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试目录
CONFIG_DIR="/Users/mac/Documents/龙虾相关/my_openclaw"

echo -e "${BLUE}[1/5] 检查 Docker 状态...${NC}"
if docker ps | grep -q openclaw-discord; then
    echo -e "${GREEN}✓ OpenClaw 容器正在运行${NC}"
else
    echo -e "${YELLOW}! OpenClaw 容器未运行，尝试启动...${NC}"
    cd "$CONFIG_DIR"
    docker-compose up -d
    echo -e "${GREEN}✓ 已启动容器${NC}"
fi
echo ""

echo -e "${BLUE}[2/5] 检查配置文件...${NC}"
if [ -f "$CONFIG_DIR/.env" ]; then
    echo -e "${GREEN}✓ .env 文件存在${NC}"
else
    echo -e "${RED}✗ .env 文件不存在${NC}"
    exit 1
fi

if [ -f "$CONFIG_DIR/openclaw.json" ]; then
    echo -e "${GREEN}✓ openclaw.json 文件存在${NC}"
else
    echo -e "${RED}✗ openclaw.json 文件不存在${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[3/5] 验证 Token 配置...${NC}"
# 检查主要 Token 是否配置
if grep -q "DISCORD_DA_FEI_TOKEN=" "$CONFIG_DIR/.env"; then
    TOKEN=$(grep "DISCORD_DA_FEI_TOKEN=" "$CONFIG_DIR/.env" | cut -d'=' -f2-)
    if [ -n "$TOKEN" ] && [ "${#TOKEN}" -ge 20 ]; then
        echo -e "${GREEN}✓ 大肥助手 Token 已配置${NC}"
    else
        echo -e "${YELLOW}! 大肥助手 Token 未填写或过短${NC}"
    fi
fi

if grep -q "DISCORD_ARCHITECT_TOKEN=" "$CONFIG_DIR/.env"; then
    echo -e "${GREEN}✓ 架构师 Token 已配置${NC}"
fi

if grep -q "DISCORD_RESEARCHER_TOKEN=" "$CONFIG_DIR/.env"; then
    echo -e "${GREEN}✓ 搜索员 Token 已配置${NC}"
fi

if grep -q "DISCORD_CODER_TOKEN=" "$CONFIG_DIR/.env"; then
    echo -e "${GREEN}✓ 程序员 Token 已配置${NC}"
fi

echo ""

echo -e "${BLUE}[4/5] 查看容器日志...${NC}"
echo -e "${YELLOW}最近 50 行日志:${NC}"
docker logs --tail 50 openclaw-discord 2>&1 | tail -20
echo ""

echo -e "${BLUE}[5/5] Agent 连接状态检查...${NC}"
# 检查容器是否正常运行
if docker ps | grep -q openclaw-discord; then
    echo -e "${GREEN}✓ 容器状态: 运行中${NC}"
    
    # 检查容器内部进程
    echo -e "${YELLOW}检查 Discord 连接...${NC}"
    docker exec openclaw-discord ps aux | grep -i node | head -3
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo -e "测试完成！"
    echo -e "==========================================${NC}"
    echo ""
    echo "下一步操作："
    echo "1. 检查 Discord 服务器，确认所有 Bot 机器人都已上线"
    echo "2. 在频道中 @提及 各机器人测试功能"
    echo "3. 查看完整日志: docker logs -f openclaw-discord"
    echo ""
    echo "测试指令示例："
    echo "  @大肥助手 你好！"
    echo "  @架构师 请分析需求"
    echo "  @搜索员 查询白银价格"
    echo "  @程序员 写Hello World"
    echo ""
else
    echo -e "${RED}✗ 容器未运行${NC}"
    echo ""
    echo "请手动启动容器："
    echo "  cd $CONFIG_DIR"
    echo "  docker-compose up -d"
    echo "  docker logs -f openclaw-discord"
fi
