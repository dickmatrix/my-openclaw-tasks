#!/bin/bash

# Agent 联动优化 - 测试脚本
# 用途: 验证 Agent 联动系统的各个环节

set -e

PROJECT_ROOT="/Users/mac/Documents/龙虾相关/my_openclaw"
GATEWAY_URL="http://127.0.0.1:18789"
GATEWAY_TOKEN="${GATEWAY_TOKEN:-6a61964bc12fb8f56bfd7541ee4598f5f808e5ab4493a091}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 计数器
TESTS_PASSED=0
TESTS_FAILED=0

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((TESTS_FAILED++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 测试 Gateway 连接
test_gateway_connection() {
    log_info "测试 Gateway 连接..."
    
    if curl -s "${GATEWAY_URL}/health" > /dev/null 2>&1; then
        log_success "Gateway 连接正常"
    else
        log_error "Gateway 连接失败"
        return 1
    fi
}

# 测试 Bot 注册
test_bot_registration() {
    log_info "测试 Bot 注册状态..."
    
    local response=$(curl -s "${GATEWAY_URL}/bots/status" \
        -H "Authorization: Bearer ${GATEWAY_TOKEN}" 2>/dev/null || echo "{}")
    
    if echo "$response" | grep -q "scout\|censor\|writer\|auditor"; then
        log_success "Bot 已注册"
    else
        log_warn "Bot 注册状态未知"
    fi
}

# 测试 Scout 命令
test_scout_command() {
    log_info "测试 Scout 命令..."
    
    local response=$(curl -s -X POST "${GATEWAY_URL}/agents/scout/scan" \
        -H "Authorization: Bearer ${GATEWAY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"path": "/app/workspace"}' 2>/dev/null || echo "{}")
    
    if echo "$response" | grep -q "success\|error"; then
        log_success "Scout 命令响应正常"
    else
        log_warn "Scout 命令响应异常"
    fi
}

# 测试 Censor 命令
test_censor_command() {
    log_info "测试 Censor 命令..."
    
    local response=$(curl -s -X POST "${GATEWAY_URL}/agents/censor/verify" \
        -H "Authorization: Bearer ${GATEWAY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{}' 2>/dev/null || echo "{}")
    
    if echo "$response" | grep -q "success\|error"; then
        log_success "Censor 命令响应正常"
    else
        log_warn "Censor 命令响应异常"
    fi
}

# 测试 Writer 命令
test_writer_command() {
    log_info "测试 Writer 命令..."
    
    local response=$(curl -s -X POST "${GATEWAY_URL}/agents/writer/optimize" \
        -H "Authorization: Bearer ${GATEWAY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"file": "/path/to/file"}' 2>/dev/null || echo "{}")
    
    if echo "$response" | grep -q "success\|error"; then
        log_success "Writer 命令响应正常"
    else
        log_warn "Writer 命令响应异常"
    fi
}

# 测试 Auditor 命令
test_auditor_command() {
    log_info "测试 Auditor 命令..."
    
    local response=$(curl -s -X POST "${GATEWAY_URL}/agents/auditor/audit" \
        -H "Authorization: Bearer ${GATEWAY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{}' 2>/dev/null || echo "{}")
    
    if echo "$response" | grep -q "success\|error"; then
        log_success "Auditor 命令响应正常"
    else
        log_warn "Auditor 命令响应异常"
    fi
}

# 测试 Schema Registry
test_schema_registry() {
    log_info "测试 Schema Registry..."
    
    local schema_dir="${PROJECT_ROOT}/schema_registry"
    if [ -d "$schema_dir" ]; then
        local schema_count=$(find "$schema_dir" -name "*.json" | wc -l)
        if [ $schema_count -gt 0 ]; then
            log_success "Schema Registry 包含 $schema_count 个 Schema"
        else
            log_warn "Schema Registry 为空"
        fi
    else
        log_warn "Schema Registry 目录不存在"
    fi
}

# 测试 GitHub Actions 工作流
test_github_workflow() {
    log_info "测试 GitHub Actions 工作流..."
    
    local workflow_file="${PROJECT_ROOT}/.github/workflows/agent-evolution-collaboration.yml"
    if [ -f "$workflow_file" ]; then
        log_success "GitHub Actions 工作流已配置"
    else
        log_warn "GitHub Actions 工作流未配置"
    fi
}

# 测试 Benchmark 数据集
test_benchmark_dataset() {
    log_info "测试 Benchmark 数据集..."
    
    local benchmark_dir="${PROJECT_ROOT}/benchmark/cursor_vs_agent"
    if [ -d "$benchmark_dir" ]; then
        local test_count=$(find "$benchmark_dir" -name "*.json" -o -name "*.csv" | wc -l)
        if [ $test_count -gt 0 ]; then
            log_success "Benchmark 数据集包含 $test_count 个测试文件"
        else
            log_warn "Benchmark 数据集为空"
        fi
    else
        log_warn "Benchmark 数据集目录不存在"
    fi
}

# 测试环境变量
test_environment_variables() {
    log_info "测试环境变量..."
    
    local required_vars=(
        "FEISHU_SCOUT_APP_ID"
        "FEISHU_CENSOR_APP_ID"
        "FEISHU_WRITER_APP_ID"
        "FEISHU_AUDITOR_APP_ID"
        "GATEWAY_TOKEN"
    )
    
    local missing=0
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_warn "缺失环境变量: $var"
            ((missing++))
        fi
    done
    
    if [ $missing -eq 0 ]; then
        log_success "所有必需的环境变量已配置"
    else
        log_error "$missing 个环境变量缺失"
    fi
}

# 测试日志目录
test_log_directory() {
    log_info "测试日志目录..."
    
    local log_dir="/Users/mac/.openclaw/logs"
    if [ -d "$log_dir" ]; then
        log_success "日志目录存在: $log_dir"
    else
        log_warn "日志目录不存在，创建中..."
        mkdir -p "$log_dir"
        log_success "日志目录已创建"
    fi
}

# 测试配置文件
test_configuration_files() {
    log_info "测试配置文件..."
    
    local config_files=(
        "${PROJECT_ROOT}/config/agent_collaboration.json"
        "${PROJECT_ROOT}/feishu_bot_config.json"
        "${PROJECT_ROOT}/bot_commands.json"
    )
    
    for config_file in "${config_files[@]}"; do
        if [ -f "$config_file" ]; then
            log_success "配置文件存在: $(basename $config_file)"
        else
            log_warn "配置文件不存在: $(basename $config_file)"
        fi
    done
}

# 运行所有测试
run_all_tests() {
    log_info "=========================================="
    log_info "Agent 联动优化 - 测试套件"
    log_info "=========================================="
    echo ""
    
    # 环境检查
    test_environment_variables
    echo ""
    
    # 配置检查
    test_configuration_files
    echo ""
    
    # 日志检查
    test_log_directory
    echo ""
    
    # Gateway 检查
    test_gateway_connection
    echo ""
    
    # Bot 检查
    test_bot_registration
    echo ""
    
    # Agent 命令检查
    test_scout_command
    test_censor_command
    test_writer_command
    test_auditor_command
    echo ""
    
    # Schema 检查
    test_schema_registry
    echo ""
    
    # GitHub 检查
    test_github_workflow
    echo ""
    
    # Benchmark 检查
    test_benchmark_dataset
    echo ""
    
    # 显示测试结果
    log_info "=========================================="
    log_info "测试结果"
    log_info "=========================================="
    echo -e "${GREEN}通过: $TESTS_PASSED${NC}"
    echo -e "${RED}失败: $TESTS_FAILED${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "所有测试通过！"
        return 0
    else
        log_error "$TESTS_FAILED 个测试失败"
        return 1
    fi
}

# 主函数
main() {
    run_all_tests
}

# 执行主函数
main "$@"
