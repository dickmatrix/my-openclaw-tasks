#!/bin/bash

# GitHub Integration & Automation Setup
# GitHub 集成和自动化设置

set -e

OPENCLAW_DIR="/Users/mac/Documents/龙虾相关/my_openclaw"
DATA_HUNTER_DIR="$OPENCLAW_DIR/data_hunter"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     GitHub Integration & Data Automation - GitHub 集成自动化    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. 检查 GitHub CLI
echo -e "${BLUE}[1/4] 检查 GitHub CLI...${NC}"

if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI 未安装，正在安装...${NC}"
    brew install gh
fi

echo -e "${GREEN}✓ GitHub CLI 已就绪${NC}"
echo ""

# 2. 验证 GitHub 认证
echo -e "${BLUE}[2/4] 验证 GitHub 认证...${NC}"

if gh auth status > /dev/null 2>&1; then
    echo -e "${GREEN}✓ GitHub 已认证${NC}"
else
    echo -e "${YELLOW}需要 GitHub 认证，请运行: gh auth login${NC}"
fi
echo ""

# 3. 创建 GitHub Actions 工作流
echo -e "${BLUE}[3/4] 创建 GitHub Actions 工作流...${NC}"

mkdir -p "$OPENCLAW_DIR/.github/workflows"

cat > "$OPENCLAW_DIR/.github/workflows/data_automation.yml" << 'GITHUBEOF'
name: Data Collection & Cleaning Automation

on:
  schedule:
    - cron: '0 9 * * *'  # 每天 9:00 运行
  workflow_dispatch:

jobs:
  data_hunting:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pandas polars requests beautifulsoup4
      
      - name: Run Data Hunter
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python data_hunter/scripts/data_hunter.py
      
      - name: Upload Scout Report
        uses: actions/upload-artifact@v3
        with:
          name: scout-reports
          path: data_hunter/results/scout_report_*.md
      
      - name: Commit results
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data_hunter/results/
          git commit -m "Data Hunter Report - $(date)" || true
          git push

GITHUBEOF

echo -e "${GREEN}✓ GitHub Actions 工作流已创建${NC}"
echo ""

# 4. 创建 GitHub Issue 模板
echo -e "${BLUE}[4/4] 创建 GitHub Issue 模板...${NC}"

mkdir -p "$OPENCLAW_DIR/.github/ISSUE_TEMPLATE"

cat > "$OPENCLAW_DIR/.github/ISSUE_TEMPLATE/data_cleaning.md" << 'ISSUEEOF'
---
name: Data Cleaning Task
about: 提交数据清洗任务
title: '[Data Cleaning] '
labels: data-cleaning
assignees: ''

---

## 任务描述
<!-- 描述需要清洗的数据 -->

## 数据源
<!-- 数据来自哪里？URL、文件路径等 -->

## 清洗需求
<!-- 需要进行哪些清洗操作？ -->

- [ ] 移除重复行
- [ ] 处理缺失值
- [ ] 文本规范化
- [ ] 异常值处理
- [ ] 其他: ___

## 预期输出格式
<!-- CSV、JSON、Parquet 等 -->

## 优先级
<!-- High / Medium / Low -->

ISSUEEOF

echo -e "${GREEN}✓ GitHub Issue 模板已创建${NC}"
echo ""

# 最终总结
echo "╔════════════════════════════════════════════════════════════════╗"
echo -e "║${GREEN}        ✅ GitHub 集成和自动化设置完成！              ${NC}║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${YELLOW}📋 已创建的文件：${NC}"
echo ""
echo "  1. GitHub Actions 工作流"
echo "     - 位置: .github/workflows/data_automation.yml"
echo "     - 触发: 每天 09:00 UTC"
echo ""
echo "  2. GitHub Issue 模板"
echo "     - 位置: .github/ISSUE_TEMPLATE/data_cleaning.md"
echo ""

echo -e "${YELLOW}🚀 后续步骤：${NC}"
echo ""
echo "1. 提交到 GitHub:"
echo "   cd $OPENCLAW_DIR"
echo "   git add .github/"
echo "   git commit -m 'Add data automation workflows'"
echo "   git push origin main"
echo ""
echo "2. 启用 GitHub Actions:"
echo "   - 访问 GitHub 仓库"
echo "   - 点击 Actions 标签"
echo "   - 启用工作流"
echo ""
echo "3. 创建数据清洗任务:"
echo "   - 访问 Issues"
echo "   - 点击 New Issue"
echo "   - 选择 Data Cleaning Task 模板"
echo ""
echo "4. 查看自动化结果:"
echo "   - 每天 09:00 自动运行"
echo "   - 结果保存在 Artifacts"
echo ""
