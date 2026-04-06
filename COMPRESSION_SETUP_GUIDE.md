# OpenClaw 压缩功能启用指南

## 🚀 快速启用 (3 步)

### 1️⃣ 验证配置已更新

```bash
cd /Users/mac/Documents/龙虾相关/my_openclaw
cat .openclawrc.json | grep -A 5 '"compaction"'
```

**预期输出**:
```json
"compaction": {
  "mode": "safeguard",
  "reserveTokens": 2048,
  "model": "ollama/qwen2.5:7b",
  ...
}
```

### 2️⃣ 启用定期压缩任务

```bash
# 使脚本可执行
chmod +x /Users/mac/Documents/龙虾相关/my_openclaw/scripts/compress-sessions.sh

# 加载 LaunchAgent (每天 02:00 执行)
launchctl load ~/Library/LaunchAgents/com.openclaw.compression.daily.plist

# 验证已加载
launchctl list | grep openclaw.compression
```

### 3️⃣ 重启 OpenClaw Agent

```bash
# 停止当前 agent
openclaw stop --agent main

# 启动新 agent (使用新配置)
openclaw start --agent main

# 验证压缩已启用
openclaw config --agent main | grep compaction
```

---

## ✅ 验证清单

运行以下命令验证配置生效:

```bash
#!/bin/bash

echo "🔍 OpenClaw 压缩功能验证"
echo ""

# 1. 检查配置文件
echo "1️⃣  配置文件检查:"
if grep -q '"mode": "safeguard"' /Users/mac/Documents/龙虾相关/my_openclaw/.openclawrc.json; then
    echo "   ✅ 压缩模式已启用"
else
    echo "   ❌ 压缩模式未启用"
fi

# 2. 检查记忆配置
echo ""
echo "2️⃣  记忆系统检查:"
if grep -q '"autoCapture": true' /Users/mac/Documents/龙虾相关/my_openclaw/.openclawrc.json; then
    echo "   ✅ 自动捕获已启用"
else
    echo "   ❌ 自动捕获未启用"
fi

# 3. 检查 LaunchAgent
echo ""
echo "3️⃣  定期任务检查:"
if launchctl list | grep -q "openclaw.compression"; then
    echo "   ✅ 定期压缩任务已加载"
else
    echo "   ⚠️  定期压缩任务未加载"
fi

# 4. 检查会话文件
echo ""
echo "4️⃣  会话文件检查:"
SESSION_COUNT=$(find /Users/mac/Documents/龙虾相关/my_openclaw/agents/main/sessions -name "*.jsonl" 2>/dev/null | wc -l)
echo "   📊 活跃会话: $SESSION_COUNT 个"

# 5. 检查日志
echo ""
echo "5️⃣  日志检查:"
if [ -f /Users/mac/Documents/龙虾相关/my_openclaw/logs/compression.log ]; then
    echo "   ✅ 压缩日志已创建"
    echo "   📝 最近 3 条记录:"
    tail -3 /Users/mac/Documents/龙虾相关/my_openclaw/logs/compression.log | sed 's/^/      /'
else
    echo "   ⏳ 压缩日志待生成 (首次运行后创建)"
fi

echo ""
echo "✨ 验证完成"
```

---

## 📊 监控压缩效果

### 实时监控

```bash
# 监控会话文件大小变化
watch -n 5 'du -sh /Users/mac/Documents/龙虾相关/my_openclaw/agents/main/sessions/*.jsonl'

# 监控压缩日志
tail -f /Users/mac/Documents/龙虾相关/my_openclaw/logs/compression.log
```

### 性能指标

```bash
# 统计会话统计
for f in /Users/mac/Documents/龙虾相关/my_openclaw/agents/main/sessions/*.jsonl; do
    echo "$(basename $f): $(wc -l < $f) 行, $(du -h $f | cut -f1)"
done

# 计算平均会话大小
du -sh /Users/mac/Documents/龙虾相关/my_openclaw/agents/main/sessions | awk '{print "总大小: " $1}'
```

---

## 🔧 故障排查

### 问题 1: 压缩任务未执行

```bash
# 检查 LaunchAgent 状态
launchctl list com.openclaw.compression.daily

# 查看错误日志
cat /Users/mac/Documents/龙虾相关/my_openclaw/logs/compression-error.log

# 手动运行脚本测试
bash /Users/mac/Documents/龙虾相关/my_openclaw/scripts/compress-sessions.sh
```

### 问题 2: 压缩后会话丢失

```bash
# 恢复备份
BACKUP=$(ls -t /Users/mac/Documents/龙虾相关/my_openclaw/agents/main/sessions/*.backup.* | head -1)
cp "$BACKUP" "${BACKUP%.backup.*}"
echo "✅ 已从 $BACKUP 恢复"
```

### 问题 3: Agent 启动失败

```bash
# 检查配置语法
jq . /Users/mac/Documents/龙虾相关/my_openclaw/.openclawrc.json > /dev/null && echo "✅ 配置有效" || echo "❌ 配置错误"

# 查看 agent 日志
openclaw logs --agent main --tail 50
```

---

## 📈 预期改进时间表

| 时间 | 预期效果 |
|------|---------|
| **立即** | 压缩模式启用，新会话使用压缩 |
| **24 小时** | 首次定期压缩执行，日志生成 |
| **7 天** | 长对话性能明显改善 |
| **30 天** | 存储占用稳定在恒定水平 |

---

## 💡 高级配置

### 自定义压缩策略

编辑 `.openclawrc.json`:

```json
"compaction": {
  "mode": "safeguard",
  "reserveTokens": 3000,
  "model": "ollama/qwen2.5:7b",
  "compressionRatio": 0.2,
  "minMessagesToCompact": 30,
  "maxCompactionFrequency": "1h",
  "strategy": "semantic"
}
```

**参数说明**:
- `compressionRatio`: 压缩后保留比例 (0.2 = 保留 20%)
- `minMessagesToCompact`: 最少消息数才触发压缩
- `maxCompactionFrequency`: 最大压缩频率
- `strategy`: 压缩策略 (semantic/summarize/truncate)

### 启用智能摘要

```json
"compaction": {
  "strategy": "summarize",
  "summaryModel": "ollama/qwen2.5:7b",
  "summaryPrompt": "用 3-5 句话总结以下对话的关键点"
}
```

---

## 📞 支持

- 配置问题: 检查 `.openclawrc.json` 语法
- 性能问题: 查看 `logs/compression.log`
- 数据恢复: 使用 `.backup.*` 文件恢复

