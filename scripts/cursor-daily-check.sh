#!/bin/bash

# Cursor Daily Optimization Script
# 每日自动化优化检查和日志记录

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MEMORY_DIR="$PROJECT_ROOT/memory"
TODAY=$(date +%Y-%m-%d)
TODAY_LOG="$MEMORY_DIR/$TODAY.md"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Cursor Daily Optimization ===${NC}"
echo "Date: $TODAY"
echo ""

# 1. 检查 .cursorrules 和 .cursorignore
echo -e "${YELLOW}[1/5] Checking configuration files...${NC}"
if [ -f "$PROJECT_ROOT/.cursorrules" ]; then
    echo -e "${GREEN}✓ .cursorrules found${NC}"
else
    echo -e "${RED}✗ .cursorrules missing${NC}"
fi

if [ -f "$PROJECT_ROOT/.cursorignore" ]; then
    echo -e "${GREEN}✓ .cursorignore found${NC}"
else
    echo -e "${RED}✗ .cursorignore missing${NC}"
fi

# 2. 检查 Git 状态
echo ""
echo -e "${YELLOW}[2/5] Checking Git status...${NC}"
if [ -d "$PROJECT_ROOT/.git" ]; then
    UNCOMMITTED=$(cd "$PROJECT_ROOT" && git status --porcelain | wc -l)
    echo -e "${GREEN}✓ Git repo found${NC}"
    echo "  Uncommitted changes: $UNCOMMITTED"
else
    echo -e "${RED}✗ Git repo not found${NC}"
fi

# 3. 检查项目大小
echo ""
echo -e "${YELLOW}[3/5] Checking project size...${NC}"
PROJECT_SIZE=$(du -sh "$PROJECT_ROOT" 2>/dev/null | cut -f1)
echo "  Total size: $PROJECT_SIZE"

# 4. 检查 .cursor 索引大小
echo ""
echo -e "${YELLOW}[4/5] Checking Cursor index...${NC}"
CURSOR_DIR="$HOME/.cursor/projects"
if [ -d "$CURSOR_DIR" ]; then
    # 查找与项目相关的索引
    CURSOR_SIZE=$(du -sh "$CURSOR_DIR" 2>/dev/null | cut -f1)
    echo "  Cursor cache size: $CURSOR_SIZE"
else
    echo "  Cursor cache not found (normal on first run)"
fi

# 5. 生成或更新日志
echo ""
echo -e "${YELLOW}[5/5] Updating daily log...${NC}"

if [ ! -f "$TODAY_LOG" ]; then
    mkdir -p "$MEMORY_DIR"
    cat > "$TODAY_LOG" << 'EOF'
# Daily Cursor Optimization Log

## 自动检查结果

- Project size: [auto-filled]
- Git uncommitted: [auto-filled]
- Configuration: ✓ .cursorrules, ✓ .cursorignore

## 手动检查清单

- [ ] 是否需要重新索引？(Cmd+Shift+J)
- [ ] 是否有超过 50 条消息的 Chat 需要重置？(Cmd+N)
- [ ] 今日 Token 消耗是否超过预期？
- [ ] 是否有新的代码模式需要添加到 .cursorrules？

## 使用统计

| 指标 | 数值 |
|------|------|
| Chat 数量 | - |
| 平均消息数 | - |
| 使用模型 | - |
| 总 Token 消耗 | - |

## 优化发现

_待填充_

## 明日计划

_待填充_
EOF
    echo -e "${GREEN}✓ Created $TODAY_LOG${NC}"
else
    echo -e "${GREEN}✓ $TODAY_LOG already exists${NC}"
fi

# 6. 提示下一步
echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo "1. Run: Cmd+Shift+J (Rescan Cursor index)"
echo "2. Review: CURSOR_OPTIMIZATION.md"
echo "3. Update: memory/$TODAY.md with your usage stats"
echo "4. Weekly: Review memory/ files and update MEMORY.md"
echo ""
echo -e "${GREEN}✓ Daily optimization check complete!${NC}"
