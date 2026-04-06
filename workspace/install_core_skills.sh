#!/bin/bash

echo "=== OpenClaw核心skill安装脚本 ==="
echo "开始时间: $(date)"
echo ""

# 创建日志目录
LOG_DIR="/tmp/openclaw_skill_install"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/install_$(date +%Y%m%d_%H%M%S).log"

# 记录日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查skill是否已安装
check_skill() {
    local skill_name="$1"
    if [ -d "$HOME/.npm-global/lib/node_modules/openclaw/skills/$skill_name" ]; then
        return 0  # 已安装
    else
        return 1  # 未安装
    fi
}

# 安装skill函数
install_skill() {
    local skill_name="$1"
    local skill_desc="$2"
    
    log "检查skill: $skill_name ($skill_desc)"
    
    if check_skill "$skill_name"; then
        log "✓ $skill_name 已安装"
        return 0
    fi
    
    log "正在安装 $skill_name..."
    
    # 尝试不同的安装方法
    if command -v clawhub &> /dev/null; then
        log "使用clawhub安装 $skill_name..."
        if clawhub install "$skill_name" --no-input --force 2>&1 | tee -a "$LOG_FILE"; then
            log "✓ $skill_name 安装成功 (通过clawhub)"
            return 0
        else
            log "⚠️ clawhub安装失败，尝试其他方法"
        fi
    fi
    
    # 检查是否在npm包中
    if [ -d "/usr/local/lib/node_modules/openclaw/skills/$skill_name" ]; then
        log "找到系统skill: $skill_name"
        # 创建符号链接到用户目录
        ln -sf "/usr/local/lib/node_modules/openclaw/skills/$skill_name" \
               "$HOME/.npm-global/lib/node_modules/openclaw/skills/$skill_name" 2>/dev/null
        if [ $? -eq 0 ]; then
            log "✓ $skill_name 链接创建成功"
            return 0
        fi
    fi
    
    log "❌ $skill_name 安装失败"
    return 1
}

# 主安装流程
log "开始安装核心skill..."

# 第一阶段：基础工具类skill
log "=== 第一阶段：安装基础工具类skill ==="
install_skill "coding-agent" "编码助手"
install_skill "github" "GitHub集成"
install_skill "summarize" "摘要生成"
install_skill "tmux" "终端会话管理"

# 第二阶段：生产力类skill
log "=== 第二阶段：安装生产力类skill ==="
install_skill "notion" "Notion集成"
install_skill "obsidian" "Obsidian集成"
install_skill "1password" "密码管理"

# 第三阶段：通信类skill
log "=== 第三阶段：安装通信类skill ==="
install_skill "discord" "Discord集成"
install_skill "slack" "Slack集成"

# 第四阶段：多媒体类skill
log "=== 第四阶段：安装多媒体类skill ==="
install_skill "sag" "ElevenLabs TTS"
install_skill "spotify-player" "Spotify播放控制"

# 第五阶段：其他实用skill
log "=== 第五阶段：安装其他实用skill ==="
install_skill "weather" "天气查询"
install_skill "healthcheck" "健康检查"
install_skill "video-frames" "视频帧提取"
install_skill "skill-creator" "skill创建工具"

# 安装结果统计
log ""
log "=== 安装完成 ==="
log "安装日志: $LOG_FILE"

# 列出已安装的skill
log "已安装skill列表:"
find "$HOME/.npm-global/lib/node_modules/openclaw/skills" -type d -maxdepth 1 -mindepth 1 | \
    while read dir; do basename "$dir"; done | sort | while read skill; do
    echo "  - $skill"
done | tee -a "$LOG_FILE"

log ""
log "安装脚本执行完成"
echo "安装完成！详细日志请查看: $LOG_FILE"