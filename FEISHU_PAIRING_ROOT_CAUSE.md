# 飞书Bot配对问题 - 根本原因分析与一了百了解决方案

**问题现象**：飞书Bot收到消息时，不断要求配对，即使底层逻辑已修正也无法解决。

**根本原因**：DM策略配置缺失 + 配对存储未清理

---

## 🔴 问题诊断

### 1. 配置缺失
在 `openclaw.json` 中，飞书频道配置**完全没有设置DM策略**：

```json
"channels": {
  "feishu": {
    "enabled": true,
    "useWebSocket": true,
    "accounts": { ... },
    "defaultAccount": "da_jie_tou_win"
    // ❌ 缺少 dmPolicy 配置！
  }
}
```

### 2. 代码逻辑
在 `bot.ts` 第1114行，当DM策略为 `"pairing"` 时：

```typescript
if (isDirect && dmPolicy !== "open" && !dmAllowed) {
  if (dmPolicy === "pairing") {
    await issuePairingChallenge({...});  // 发起配对挑战
  }
  return;  // 阻止消息处理
}
```

### 3. 配对存储状态
在 `.openclaw/credentials/feishu-pairing.json` 中：

```json
{
  "version": 1,
  "requests": [
    {
      "id": "ou_ad431611d6daf15ef9aa3e8ec023b46e",
      "code": "TF7JTLUU",
      "createdAt": "2026-03-21T06:17:55.243Z",
      "lastSeenAt": "2026-03-21T06:17:55.243Z",
      "meta": {
        "name": "luz",
        "accountId": "default"
      }
    }
  ]
}
```

**问题**：配对请求从未被批准（没有 `approvedAt` 字段），所以每次消息都被拒绝。

---

## ✅ 一了百了的解决方案

### 方案选择

有3种方案，选择最适合你的：

| 方案 | 难度 | 效果 | 适用场景 |
|------|------|------|---------|
| **A: 改为开放模式** | ⭐ 简单 | 立即生效 | 开发/测试环境 |
| **B: 批准现有配对** | ⭐⭐ 中等 | 立即生效 | 生产环境（单用户） |
| **C: 清理+重新配置** | ⭐⭐⭐ 复杂 | 最彻底 | 生产环境（多用户） |

---

## 方案 A：改为开放模式（推荐用于开发）

**优点**：最快，无需配对  
**缺点**：任何人都能访问

### 步骤1：修改 `openclaw.json`

```bash
cd /Users/mac/Documents/龙虾相关/my_openclaw
```

在 `channels.feishu` 中添加：

```json
"channels": {
  "feishu": {
    "enabled": true,
    "useWebSocket": true,
    "accounts": { ... },
    "defaultAccount": "da_jie_tou_win",
    "dmPolicy": "open"  // ✅ 添加这一行
  }
}
```

### 步骤2：重启Gateway

```bash
pkill -9 openclaw-gateway
sleep 2
openclaw gateway --port 18789
```

### 步骤3：测试

在飞书群中发送：
```
@Scout 扫描 /app/workspace
```

**预期**：立即响应，无需配对。

---

## 方案 B：批准现有配对（推荐用于生产）

**优点**：安全，只允许已配对用户  
**缺点**：需要手动批准

### 步骤1：批准配对请求

编辑 `.openclaw/credentials/feishu-pairing.json`，添加 `approvedAt` 字段：

```json
{
  "version": 1,
  "requests": [
    {
      "id": "ou_ad431611d6daf15ef9aa3e8ec023b46e",
      "code": "TF7JTLUU",
      "createdAt": "2026-03-21T06:17:55.243Z",
      "lastSeenAt": "2026-03-21T06:17:55.243Z",
      "approvedAt": "2026-03-29T00:00:00.000Z",  // ✅ 添加这一行
      "meta": {
        "name": "luz",
        "accountId": "default"
      }
    }
  ]
}
```

### 步骤2：修改 `openclaw.json`

```json
"channels": {
  "feishu": {
    "enabled": true,
    "useWebSocket": true,
    "accounts": { ... },
    "defaultAccount": "da_jie_tou_win",
    "dmPolicy": "pairing"  // ✅ 明确设置为 pairing
  }
}
```

### 步骤3：重启Gateway

```bash
pkill -9 openclaw-gateway
sleep 2
openclaw gateway --port 18789
```

### 步骤4：测试

在飞书群中发送：
```
@Scout 扫描 /app/workspace
```

**预期**：立即响应，因为用户已被批准。

---

## 方案 C：清理+重新配置（最彻底）

**优点**：完全清理，从零开始  
**缺点**：需要重新配对

### 步骤1：清理配对存储

```bash
# 备份原文件
cp .openclaw/credentials/feishu-pairing.json .openclaw/credentials/feishu-pairing.json.backup

# 清空配对请求
cat > .openclaw/credentials/feishu-pairing.json << 'EOF'
{
  "version": 1,
  "requests": []
}
EOF
```

### 步骤2：修改 `openclaw.json`

```json
"channels": {
  "feishu": {
    "enabled": true,
    "useWebSocket": true,
    "accounts": { ... },
    "defaultAccount": "da_jie_tou_win",
    "dmPolicy": "allowlist",  // ✅ 改为 allowlist
    "allowFrom": [
      "ou_ad431611d6daf15ef9aa3e8ec023b46e"  // 你的飞书用户ID
    ]
  }
}
```

### 步骤3：重启Gateway

```bash
pkill -9 openclaw-gateway
sleep 2
openclaw gateway --port 18789
```

### 步骤4：测试

在飞书群中发送：
```
@Scout 扫描 /app/workspace
```

**预期**：立即响应，因为用户在allowlist中。

---

## 🎯 我的建议

### 立即执行（5分钟）

**选择方案A**（开放模式）用于快速验证：

```bash
# 1. 修改配置
cat > openclaw.json << 'EOF'
{
  ...（保持其他内容不变）...
  "channels": {
    "feishu": {
      "enabled": true,
      "useWebSocket": true,
      "accounts": { ... },
      "defaultAccount": "da_jie_tou_win",
      "dmPolicy": "open"
    }
  }
  ...
}
EOF

# 2. 重启
pkill -9 openclaw-gateway && sleep 2 && openclaw gateway --port 18789

# 3. 测试
# 在飞书群中 @Scout 测试
```

### 长期方案（生产环境）

**选择方案B或C**，根据用户数量：
- **单用户**：方案B（批准现有配对）
- **多用户**：方案C（allowlist）

---

## 📋 DM策略详解

| 策略 | 含义 | 使用场景 |
|------|------|---------|
| `"open"` | 任何人都能发送DM | 开发/测试 |
| `"pairing"` | 需要配对码批准 | 生产环境（安全） |
| `"allowlist"` | 只允许指定用户 | 生产环境（最安全） |
| `"disabled"` | 禁用DM | 仅群聊 |

---

## 🔍 验证修复

执行以下命令验证：

```bash
# 1. 检查配置
cat openclaw.json | jq '.channels.feishu.dmPolicy'

# 2. 检查Gateway状态
ps aux | grep openclaw-gateway | grep -v grep

# 3. 查看日志
tail -20 /Users/mac/.openclaw/logs/gateway.log

# 4. 在飞书测试
# @Scout 扫描 /app/workspace
```

---

## 🚨 常见问题

### Q: 修改后还是要求配对？

**A**: 
1. 确保修改了 `openclaw.json`
2. 确保重启了Gateway（`pkill -9 openclaw-gateway`）
3. 检查日志：`tail -50 /Users/mac/.openclaw/logs/gateway.log | grep -i feishu`

### Q: 如何找到我的飞书用户ID？

**A**: 
1. 在飞书群中 @你自己
2. 查看消息中的 `open_id`（格式：`ou_xxxxxxxx`）
3. 或在飞书管理后台查看

### Q: 能同时配置多个用户吗？

**A**: 可以，使用方案C的allowlist：

```json
"allowFrom": [
  "ou_user1_id",
  "ou_user2_id",
  "ou_user3_id"
]
```

### Q: 如何从pairing切换到open？

**A**: 直接修改 `dmPolicy` 并重启Gateway即可。

---

## 📝 修改清单

- [ ] 选择合适的方案（A/B/C）
- [ ] 修改 `openclaw.json` 中的 `channels.feishu.dmPolicy`
- [ ] 如果选B，修改 `.openclaw/credentials/feishu-pairing.json`
- [ ] 重启Gateway：`pkill -9 openclaw-gateway && sleep 2 && openclaw gateway --port 18789`
- [ ] 在飞书测试：`@Scout 扫描 /app/workspace`
- [ ] 验证日志：`tail -20 /Users/mac/.openclaw/logs/gateway.log`

---

## 总结

**问题根源**：
1. `openclaw.json` 中没有设置 `dmPolicy`
2. 配对存储中的请求未被批准
3. 导致每条DM都被拒绝并要求配对

**一了百了的解决**：
- **快速**：方案A（改为open）
- **安全**：方案B（批准现有配对）
- **彻底**：方案C（清理+allowlist）

**立即行动**：选择方案A，5分钟内解决问题。

---

**最后更新**: 2026-03-29  
**状态**: ✅ 已诊断，提供完整解决方案
