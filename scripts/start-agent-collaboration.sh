#!/bin/bash

# Agent 联动优化 - 启动脚本
# 用途: 启动 Gateway 和所有 Agent Bot，建立飞书群联动

set -e

PROJECT_ROOT="/Users/mac/Documents/龙虾相关/my_openclaw"
LOG_DIR="/Users/mac/.openclaw/logs"
GATEWAY_PORT=18789
GATEWAY_URL="http://127.0.0.1:${GATEWAY_PORT}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 检查环境变量
check_env() {
    log_info "检查环境变量..."
    
    local required_vars=(
        "FEISHU_MAC_APP_ID"
        "FEISHU_MAC_APP_SECRET"
        "FEISHU_SCOUT_APP_ID"
        "FEISHU_SCOUT_APP_SECRET"
        "FEISHU_CENSOR_APP_ID"
        "FEISHU_CENSOR_APP_SECRET"
        "FEISHU_WRITER_APP_ID"
        "FEISHU_WRITER_APP_SECRET"
        "FEISHU_AUDITOR_APP_ID"
        "FEISHU_AUDITOR_APP_SECRET"
        "GATEWAY_TOKEN"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "缺失环境变量: ${missing_vars[*]}"
        log_info "请在 .env 文件中配置这些变量"
        return 1
    fi
    
    log_success "所有环境变量已配置"
    return 0
}

# 检查 Gateway 状态
check_gateway() {
    log_info "检查 Gateway 状态..."
    
    if curl -s "${GATEWAY_URL}/health" > /dev/null 2>&1; then
        log_success "Gateway 已运行"
        return 0
    else
        log_warn "Gateway 未运行，准备启动..."
        return 1
    fi
}

# 启动 Gateway
start_gateway() {
    log_info "启动 Gateway..."
    
    # 检查是否已有进程在运行
    if pgrep -f "gateway --port ${GATEWAY_PORT}" > /dev/null; then
        log_warn "Gateway 进程已存在，跳过启动"
        return 0
    fi
    
    # 启动 Gateway
    openclaw gateway --port ${GATEWAY_PORT} > "${LOG_DIR}/gateway.log" 2>&1 &
    local gateway_pid=$!
    
    log_info "Gateway PID: $gateway_pid"
    
    # 等待 Gateway 启动
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "${GATEWAY_URL}/health" > /dev/null 2>&1; then
            log_success "Gateway 已启动"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    log_error "Gateway 启动超时"
    return 1
}

# 注册 Bot
register_bot() {
    local bot_name=$1
    local app_id=$2
    local app_secret=$3
    
    log_info "注册 Bot: $bot_name"
    
    local response=$(curl -s -X POST "${GATEWAY_URL}/bots/register" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${GATEWAY_TOKEN}" \
        -d "{
            \"name\": \"$bot_name\",
            \"app_id\": \"$app_id\",
            \"app_secret\": \"$app_secret\"
        }")
    
    if echo "$response" | grep -q "success"; then
        log_success "Bot 已注册: $bot_name"
        return 0
    else
        log_error "Bot 注册失败: $bot_name"
        log_info "响应: $response"
        return 1
    fi
}

# 注册所有 Bot
register_all_bots() {
    log_info "注册所有 Agent Bot..."
    
    register_bot "Scout" "$FEISHU_SCOUT_APP_ID" "$FEISHU_SCOUT_APP_SECRET" || true
    register_bot "Censor" "$FEISHU_CENSOR_APP_ID" "$FEISHU_CENSOR_APP_SECRET" || true
    register_bot "Writer" "$FEISHU_WRITER_APP_ID" "$FEISHU_WRITER_APP_SECRET" || true
    register_bot "Auditor" "$FEISHU_AUDITOR_APP_ID" "$FEISHU_AUDITOR_APP_SECRET" || true
    
    log_success "所有 Bot 已注册"
}

# 测试 Bot 连接
test_bot_connection() {
    log_info "测试 Bot 连接..."
    
    local response=$(curl -s "${GATEWAY_URL}/bots/status" \
        -H "Authorization: Bearer ${GATEWAY_TOKEN}")
    
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
}

# 启动 Agent 进程
start_agent() {
    local agent_name=$1
    local agent_dir="${PROJECT_ROOT}/agents/${agent_name}"
    
    if [ ! -d "$agent_dir" ]; then
        log_warn "Agent 目录不存在: $agent_dir"
        return 1
    fi
    
    log_info "启动 Agent: $agent_name"
    
    # 检查是否已有进程在运行
    if pgrep -f "agent.*${agent_name}" > /dev/null; then
        log_warn "Agent 进程已存在: $agent_name"
        return 0
    fi
    
    # 启动 Agent
    cd "$agent_dir"
    npm start > "${LOG_DIR}/${agent_name}.log" 2>&1 &
    local agent_pid=$!
    
    log_info "Agent PID: $agent_pid"
    log_success "Agent 已启动: $agent_name"
}

# 启动所有 Agent
start_all_agents() {
    log_info "启动所有 Agent..."
    
    start_agent "scout" || true
    start_agent "censor" || true
    start_agent "writer" || true
    start_agent "auditor" || true
    
    log_success "所有 Agent 已启动"
}

# 显示状态
show_status() {
    log_info "系统状态:"
    echo ""
    
    # Gateway 状态
    if curl -s "${GATEWAY_URL}/health" > /dev/null 2>&1; then
        log_success "Gateway: 运行中"
    else
        log_error "Gateway: 未运行"
    fi
    
    # Bot 状态
    log_info "Bot 状态:"
    curl -s "${GATEWAY_URL}/bots/status" \
        -H "Authorization: Bearer ${GATEWAY_TOKEN}" | jq '.bots[] | {name, status}' 2>/dev/null || true
    
    # Agent 进程
    log_info "Agent 进程:"
    pgrep -f "agent" | while read pid; do
        ps -p "$pid" -o comm= | grep -o "agent.*" || true
    done
    
    echo ""
    log_info "日志位置: $LOG_DIR"
    log_info "Gateway URL: $GATEWAY_URL"
}

# 主函数
main() {
    log_info "=========================================="
    log_info "Agent 联动优化 - 启动脚本"
    log_info "=========================================="
    echo ""
    
    # 创建日志目录
    mkdir -p "$LOG_DIR"
    
    # 检查环境变量
    if ! check_env; then
        exit 1
    fi
    
    echo ""
    
    # 启动 Gateway
    if ! check_gateway; then
        if ! start_gateway; then
            exit 1
        fi
    fi
    
    echo ""
    
    # 注册 Bot
    register_all_bots
    
    echo ""
    
    # 测试连接
    test_bot_connection
    
    echo ""
    
    # 启动 Agent
    start_all_agents
    
    echo ""
    
    # 显示状态
    show_status
    
    echo ""
    log_success "=========================================="
    log_success "Agent 联动系统已启动"
    log_success "=========================================="
    echo ""
    log_info "飞书群命令示例:"
    echo "  @Scout 扫描 https://github.com/user/repo"
    echo "  @Censor 检查"
    echo "  @Writer 优化 /path/to/file"
    echo "  @Auditor 审计"
    echo ""
}

# 执行主函数
main "$@"
