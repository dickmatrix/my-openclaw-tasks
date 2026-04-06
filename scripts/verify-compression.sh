#!/bin/bash
# OpenClaw 压缩功能验证脚本
# 用途: 验证所有压缩相关配置是否正确

set -e

PROJECT_ROOT="/Users/mac/Documents/龙虾相关/my_openclaw"
CONFIG_FILE="$PROJECT_ROOT/.openclawrc.json"
SESSIONS_DIR="$PROJECT_ROOT/agents/main/sessions"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========== OpenClaw 压缩功能验证 ==========${NC}\n"

# 1. 检查配置文件
echo -e "${BLUE}1️⃣  配置文件检查${NC}"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ 配置文件不存在: $CONFIG_FILE${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 配置文件存在${NC}"

# 验证 JSON 语法
if jq . "$CONFIG_FILE" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ JSON 语法有效${NC}"
else
    echo -e "${RED}❌ JSON 语法错误${NC}"
    exit 1
fi

# 2. 检查压缩模式
echo -e "\n${BLUE}2️⃣  压缩模式检查${NC}"
COMPACTION_MODE=$(jq -r '.agents.defaults.compaction.mode' "$CONFIG_FILE")
if [ "$COMPACTION_MODE" = "safeguard" ]; then
    echo -e "${GREEN}✅ 压缩模式: $COMPACTION_MODE${NC}"
else
    echo -e "${YELLOW}⚠️  压缩模式: $COMPACTION_MODE (建议: safeguard)${NC}"
fi

RESERVE_TOKENS=$(jq -r '.agents.defaults.compaction.reserveTokens' "$CONFIG_FILE")
echo -e "${GREEN}✅ 预留 tokens: $RESERVE_TOKENS${NC}"

COMPRESSION_MODEL=$(jq -r '.agents.defaults.compaction.model' "$CONFIG_FILE")
echo -e "${GREEN}✅ 压缩模型: $COMPRESSION_MODEL${NC}"

# 3. 检查记忆系统
echo -e "\n${BLUE}3️⃣  记忆系统检查${NC}"
MEMORY_ENABLED=$(jq -r '.plugins.entries."memory-lancedb".enabled' "$CONFIG_FILE")
if [ "$MEMORY_ENABLED" = "true" ]; then
    echo -e "${GREEN}✅ 记忆系统已启用${NC}"
else
    echo -e "${RED}❌ 记忆系统未启用${NC}"
fi

AUTO_CAPTURE=$(jq -r '.plugins.entries."memory-lancedb".config.autoCapture' "$CONFIG_FILE")
AUTO_RECALL=$(jq -r '.plugins.entries."memory-lancedb".config.autoRecall' "$CONFIG_FILE")
echo -e "${GREEN}✅ 自动捕获: $AUTO_CAPTURE, 自动回忆: $AUTO_RECALL${NC}"

CAPTURE_MAX=$(jq -r '.plugins.entries."memory-lancedb".config.captureMaxChars' "$CONFIG_FILE")
echo -e "${GREEN}✅ 捕获最大字符: $CAPTURE_MAX${NC}"

EMBEDDING_MODEL=$(jq -r '.plugins.entries."memory-lancedb".config.embedding.model' "$CONFIG_FILE")
echo -e "${GREEN}✅ 嵌入模型: $EMBEDDING_MODEL${NC}"

# 4. 检查会话目录
echo -e "\n${BLUE}4️⃣  会话目录检查${NC}"
if [ -d "$SESSIONS_DIR" ]; then
    echo -e "${GREEN}✅ 会话目录存在${NC}"
    SESSION_COUNT=$(find "$SESSIONS_DIR" -name "*.jsonl" 2>/dev/null | wc -l)
    echo -e "${GREEN}✅ 活跃会话数: $SESSION_COUNT${NC}"
    
    # 统计会话大小
    TOTAL_SIZE=$(du -sh "$SESSIONS_DIR" 2>/dev/null | cut -f1)
    echo -e "${GREEN}✅ 总大小: $TOTAL_SIZE${NC}"
    
    # 显示最大的会话
    echo -e "\n   📊 会话大小分布:"
    du -h "$SESSIONS_DIR"/*.jsonl 2>/dev/null | sort -rh | head -5 | while read size file; do
        lines=$(wc -l < "$file" 2>/dev/null || echo "0")
        echo -e "      $(basename $file): $size ($lines 行)"
    done
else
    echo -e "${YELLOW}⚠️  会话目录不存在: $SESSIONS_DIR${NC}"
fi

# 5. 检查脚本
echo -e "\n${BLUE}5️⃣  压缩脚本检查${NC}"
SCRIPT_PATH="$PROJECT_ROOT/scripts/compress-sessions.sh"
if [ -f "$SCRIPT_PATH" ]; then
    echo -e "${GREEN}✅ 压缩脚本存在${NC}"
    if [ -x "$SCRIPT_PATH" ]; then
        echo -e "${GREEN}✅ 脚本可执行${NC}"
    else
        echo -e "${YELLOW}⚠️  脚本不可执行，运行: chmod +x $SCRIPT_PATH${NC}"
    fi
else
    echo -e "${RED}❌ 压缩脚本不存在${NC}"
fi

# 6. 检查 LaunchAgent
echo -e "\n${BLUE}6️⃣  定期任务检查${NC}"
PLIST_PATH="$HOME/Library/LaunchAgents/com.openclaw.compression.daily.plist"
if [ -f "$PLIST_PATH" ]; then
    echo -e "${GREEN}✅ LaunchAgent 配置存在${NC}"
    
    if launchctl list | grep -q "com.openclaw.compression.daily"; then
        echo -e "${GREEN}✅ 定期任务已加载${NC}"
    else
        echo -e "${YELLOW}⚠️  定期任务未加载，运行: launchctl load $PLIST_PATH${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  LaunchAgent 配置不存在${NC}"
fi

# 7. 检查日志
echo -e "\n${BLUE}7️⃣  日志检查${NC}"
LOG_DIR="$PROJECT_ROOT/logs"
if [ -d "$LOG_DIR" ]; then
    echo -e "${GREEN}✅ 日志目录存在${NC}"
    
    if [ -f "$LOG_DIR/compression.log" ]; then
        echo -e "${GREEN}✅ 压缩日志存在${NC}"
        echo -e "\n   📝 最近 5 条记录:"
        tail -5 "$LOG_DIR/compression.log" | sed 's/^/      /'
    else
        echo -e "${YELLOW}⏳ 压缩日志待生成 (首次运行后创建)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  日志目录不存在，将在首次运行时创建${NC}"
fi

# 8. 检查 Ollama 连接
echo -e "\n${BLUE}8️⃣  Ollama 连接检查${NC}"
OLLAMA_URL=$(jq -r '.plugins.entries."memory-lancedb".config.embedding.baseUrl' "$CONFIG_FILE")
if curl -s "$OLLAMA_URL/models" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama 服务可访问: $OLLAMA_URL${NC}"
    
    # 检查嵌入模型
    EMBED_MODEL=$(jq -r '.plugins.entries."memory-lancedb".config.embedding.model' "$CONFIG_FILE")
    if curl -s "$OLLAMA_URL/models" | grep -q "$EMBED_MODEL"; then
        echo -e "${GREEN}✅ 嵌入模型已加载: $EMBED_MODEL${NC}"
    else
        echo -e "${YELLOW}⚠️  嵌入模型未加载: $EMBED_MODEL${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Ollama 服务不可访问: $OLLAMA_URL${NC}"
fi

# 9. 总体评分
echo -e "\n${BLUE}========== 总体评分 ==========${NC}"
CHECKS_PASSED=0
CHECKS_TOTAL=8

[ "$COMPACTION_MODE" = "safeguard" ] && ((CHECKS_PASSED++))
[ "$MEMORY_ENABLED" = "true" ] && ((CHECKS_PASSED++))
[ -f "$SCRIPT_PATH" ] && ((CHECKS_PASSED++))
[ -f "$PLIST_PATH" ] && ((CHECKS_PASSED++))
[ -d "$LOG_DIR" ] && ((CHECKS_PASSED++))
[ -d "$SESSIONS_DIR" ] && ((CHECKS_PASSED++))
[ "$AUTO_CAPTURE" = "true" ] && ((CHECKS_PASSED++))
[ "$AUTO_RECALL" = "true" ] && ((CHECKS_PASSED++))

SCORE=$((CHECKS_PASSED * 100 / CHECKS_TOTAL))

if [ $SCORE -ge 90 ]; then
    echo -e "${GREEN}✅ 配置完整度: $SCORE% (优秀)${NC}"
elif [ $SCORE -ge 70 ]; then
    echo -e "${YELLOW}⚠️  配置完整度: $SCORE% (良好)${NC}"
else
    echo -e "${RED}❌ 配置完整度: $SCORE% (需要改进)${NC}"
fi

echo -e "\n${BLUE}========== 建议操作 ==========${NC}"

if [ "$COMPACTION_MODE" != "safeguard" ]; then
    echo -e "${YELLOW}1. 启用压缩模式:${NC}"
    echo "   编辑 .openclawrc.json，设置 compaction.mode = 'safeguard'"
fi

if [ ! -x "$SCRIPT_PATH" ]; then
    echo -e "${YELLOW}2. 使脚本可执行:${NC}"
    echo "   chmod +x $SCRIPT_PATH"
fi

if ! launchctl list | grep -q "com.openclaw.compression.daily"; then
    echo -e "${YELLOW}3. 加载定期任务:${NC}"
    echo "   launchctl load $PLIST_PATH"
fi

echo -e "\n${GREEN}✨ 验证完成${NC}\n"
