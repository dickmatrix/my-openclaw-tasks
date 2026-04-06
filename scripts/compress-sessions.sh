#!/bin/bash
# OpenClaw 会话压缩维护脚本
# 用途: 定期压缩长对话会话，减少上下文占用
# 运行: 每天 02:00 执行

set -uo pipefail

PROJECT_ROOT="/Users/mac/Documents/龙虾相关/my_openclaw"
SESSIONS_DIR="$PROJECT_ROOT/agents/main/sessions"
LOG_FILE="$PROJECT_ROOT/logs/compression.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

log "========== 会话压缩任务开始 =========="

# 检查会话目录
if [ ! -d "$SESSIONS_DIR" ]; then
    log "❌ 会话目录不存在: $SESSIONS_DIR"
    exit 1
fi

# 统计会话文件（排除备份文件）
SESSION_COUNT=$(find "$SESSIONS_DIR" -maxdepth 1 -name "*.jsonl" ! -name '*.backup.*' | wc -l)
log "📊 发现 $SESSION_COUNT 个会话文件"

# 遍历每个会话文件（排除备份文件）
for session_file in "$SESSIONS_DIR"/*.jsonl; do
    # 跳过备份文件
    [[ "$session_file" == *.backup.* ]] && continue
    if [ ! -f "$session_file" ]; then
        continue
    fi
    
    filename=$(basename "$session_file")
    file_size=$(du -h "$session_file" | cut -f1)
    line_count=$(wc -l < "$session_file")
    
    log "📝 处理: $filename (大小: $file_size, 行数: $line_count)"
    
    # 获取文件大小（KB）
    file_size_kb=$(du -k "$session_file" | cut -f1)
    
    # 如果会话文件超过 20KB 或行数超过 20 行，执行压缩
    if [ "$file_size_kb" -gt 20 ] || [ "$line_count" -gt 20 ]; then
        log "  ⚙️  执行压缩 (大小: ${file_size_kb}KB, 行数: $line_count)..."
        
        # 备份原文件
        backup_file="${session_file}.backup.$(date +%s)"
        cp "$session_file" "$backup_file"
        log "  💾 备份: $backup_file"
        
        # 保留最后 5 行（最近的对话轮次）
        tail -5 "$session_file" > "${session_file}.tmp"
        mv "${session_file}.tmp" "$session_file"
        
        new_size=$(du -h "$session_file" | cut -f1)
        new_lines=$(wc -l < "$session_file")
        log "  ✅ 压缩完成: ${file_size_kb}KB/${line_count}行 → 新大小: $new_size/${new_lines}行"
    else
        log "  ⏭️  跳过 (${file_size_kb}KB / $line_count 行，未达阈值)"
    fi
done

# 清理旧备份（每个会话只保留最新一份备份）
log "🧹 清理旧备份文件..."
CLEANED=0
for base in $(find "$SESSIONS_DIR" -maxdepth 1 -name '*.backup.*' | sed 's/\.backup\.[0-9]*$//' | sort -u); do
    oldest=$(ls -t "${base}.backup."* 2>/dev/null | tail -n +2)
    for old in $oldest; do
        rm "$old"
        log "  🗑️  删除旧备份: $(basename "$old")"
        CLEANED=$((CLEANED + 1))
    done
done
log "  ✅ 清理完成，共删除 $CLEANED 个旧备份"

log "========== 会话压缩任务完成 =========="
log ""
