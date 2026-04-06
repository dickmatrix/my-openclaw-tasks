#!/bin/bash

# 飞书Bot审计员 - 知识库权限配置脚本
# 用途: 自动配置 Auditor Bot 的知识库读取权限

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 配置文件路径
PROJECT_ROOT="/Users/mac/Documents/龙虾相关/my_openclaw"
FEISHU_BOT_CONFIG="${PROJECT_ROOT}/feishu_bot_config.json"
AGENT_CONFIG="${PROJECT_ROOT}/config/agent_collaboration.json"
ENV_FILE="${PROJECT_ROOT}/.env"

# 主函数
main() {
    log_info "=========================================="
    log_info "飞书Bot审计员 - 知识库权限配置"
    log_info "=========================================="
    echo ""
    
    # 步骤 1: 获取知识库信息
    log_info "步骤 1: 获取知识库信息"
    echo ""
    
    read -p "请输入知识库 ID (从分享链接中获取): " WIKI_ID
    if [ -z "$WIKI_ID" ]; then
        log_error "知识库 ID 不能为空"
        exit 1
    fi
    log_success "知识库 ID: $WIKI_ID"
    
    read -p "请输入知识库名称 (如: 龙虾文档库): " WIKI_NAME
    if [ -z "$WIKI_NAME" ]; then
        log_error "知识库名称不能为空"
        exit 1
    fi
    log_success "知识库名称: $WIKI_NAME"
    
    echo ""
    
    # 步骤 2: 验证配置文件
    log_info "步骤 2: 验证配置文件"
    echo ""
    
    if [ ! -f "$FEISHU_BOT_CONFIG" ]; then
        log_error "配置文件不存在: $FEISHU_BOT_CONFIG"
        exit 1
    fi
    log_success "feishu_bot_config.json 存在"
    
    if [ ! -f "$AGENT_CONFIG" ]; then
        log_error "配置文件不存在: $AGENT_CONFIG"
        exit 1
    fi
    log_success "agent_collaboration.json 存在"
    
    if [ ! -f "$ENV_FILE" ]; then
        log_error "环境变量文件不存在: $ENV_FILE"
        exit 1
    fi
    log_success ".env 文件存在"
    
    echo ""
    
    # 步骤 3: 更新 feishu_bot_config.json
    log_info "步骤 3: 更新 feishu_bot_config.json"
    echo ""
    
    # 使用 Python 更新 JSON 文件
    python3 << PYTHON_SCRIPT
import json
import sys

config_file = "$FEISHU_BOT_CONFIG"

try:
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 找到 Auditor Bot 并更新知识库配置
    for bot in config.get('feishu_bots', []):
        if bot.get('name') == 'Auditor':
            bot['knowledge_base'] = {
                'enabled': True,
                'wiki_id': '$WIKI_ID',
                'wiki_name': '$WIKI_NAME',
                'permissions': ['read'],
                'cache_enabled': True,
                'cache_ttl': 3600
            }
            print(f"✓ 已更新 Auditor Bot 的知识库配置")
            break
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✓ feishu_bot_config.json 已更新")
except Exception as e:
    print(f"✗ 更新失败: {e}")
    sys.exit(1)
PYTHON_SCRIPT
    
    log_success "feishu_bot_config.json 已更新"
    echo ""
    
    # 步骤 4: 更新 .env 文件
    log_info "步骤 4: 更新 .env 文件"
    echo ""
    
    # 备份原文件
    cp "$ENV_FILE" "${ENV_FILE}.backup"
    log_success ".env 文件已备份"
    
    # 添加或更新环境变量
    if grep -q "FEISHU_WIKI_ID" "$ENV_FILE"; then
        sed -i '' "s/FEISHU_WIKI_ID=.*/FEISHU_WIKI_ID=$WIKI_ID/" "$ENV_FILE"
    else
        echo "FEISHU_WIKI_ID=$WIKI_ID" >> "$ENV_FILE"
    fi
    
    if grep -q "FEISHU_WIKI_NAME" "$ENV_FILE"; then
        sed -i '' "s/FEISHU_WIKI_NAME=.*/FEISHU_WIKI_NAME=$WIKI_NAME/" "$ENV_FILE"
    else
        echo "FEISHU_WIKI_NAME=$WIKI_NAME" >> "$ENV_FILE"
    fi
    
    if grep -q "FEISHU_AUDITOR_KB_READ" "$ENV_FILE"; then
        sed -i '' "s/FEISHU_AUDITOR_KB_READ=.*/FEISHU_AUDITOR_KB_READ=true/" "$ENV_FILE"
    else
        echo "FEISHU_AUDITOR_KB_READ=true" >> "$ENV_FILE"
    fi
    
    if grep -q "FEISHU_AUDITOR_KB_WRITE" "$ENV_FILE"; then
        sed -i '' "s/FEISHU_AUDITOR_KB_WRITE=.*/FEISHU_AUDITOR_KB_WRITE=false/" "$ENV_FILE"
    else
        echo "FEISHU_AUDITOR_KB_WRITE=false" >> "$ENV_FILE"
    fi
    
    log_success ".env 文件已更新"
    echo ""
    
    # 步骤 5: 显示配置摘要
    log_info "步骤 5: 配置摘要"
    echo ""
    
    echo "知识库配置:"
    echo "  知识库 ID: $WIKI_ID"
    echo "  知识库名称: $WIKI_NAME"
    echo "  读取权限: 已启用"
    echo "  写入权限: 已禁用"
    echo "  缓存: 已启用 (TTL: 3600秒)"
    echo ""
    
    # 步骤 6: 提示后续操作
    log_info "步骤 6: 后续操作"
    echo ""
    
    echo "请按照以下步骤完成配置:"
    echo ""
    echo "1. 在飞书开发者后台添加权限:"
    echo "   - 进入应用详情"
    echo "   - 添加以下权限:"
    echo "     * wiki:wiki:read"
    echo "     * wiki:space:read"
    echo "     * wiki:node:read"
    echo "     * docs:doc:read"
    echo "   - 点击保存"
    echo ""
    echo "2. 在飞书云文档中添加 Bot:"
    echo "   - 打开知识库"
    echo "   - 点击分享按钮"
    echo "   - 添加 Auditor Bot 为成员"
    echo "   - 设置权限为 '查看者'"
    echo ""
    echo "3. 重启 Bot 服务:"
    echo "   bash ${PROJECT_ROOT}/scripts/start-agent-collaboration.sh"
    echo ""
    echo "4. 在飞书群中测试:"
    echo "   @Auditor 读取知识库"
    echo ""
    
    log_success "=========================================="
    log_success "配置完成！"
    log_success "=========================================="
}

# 执行主函数
main "$@"
