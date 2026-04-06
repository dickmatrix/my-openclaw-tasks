# 飞书Bot配对问题 - 快速参考卡片

## 飞书插件未加载（所有 Bot 私信/群聊都不回）

若网关日志出现 **`feishu failed to load`** / **`Cannot find module '@larksuiteoapi/node-sdk'`**，与 `openclaw.json`、路由无关——**飞书插件根本没起来**。

1. 在本仓库执行（会往全局 `openclaw` 的 `node_modules` 合并依赖，仅本机修复）:
   ```bash
   bash scripts/repair-openclaw-feishu-deps.sh
   ```
2. 重启 Gateway（LaunchAgent 或 `launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway`）。
3. 再查日志应出现 `feishu[...]: WebSocket client started` 等行；可搜索: `grep feishu ~/.openclaw/logs/gateway.log | tail`.

升级全局 `npm install -g openclaw@...` 后若复发，再跑一次上述脚本。

## 网关端口（避免 18789 / 18889 搞混）

- **唯一配置源**：`openclaw.json` 里的 `gateway.port` = 进程监听端口（容器内或本机直连）。
- **宿主机访问**：多数脚本应使用 `scripts/openclaw-gateway.sh` 解析：
  - `listen-port`：`openclaw gateway --port` 应与此一致。
  - `host-port`：在本机执行 `curl .../health` 时用的端口（会读 `.env` 里 `OPENCLAW_GATEWAY_URL`，否则尝试 compose 映射）。
  - `docker-host-port`：**仅**在 `docker compose up` 后做健康检查时用（只认 compose 映射）。
- **辅助 JSON**：`feishu_bot_config.json` 里的 `gateway.url` 需与当前环境一致；拿不准时用 `scripts/openclaw-gateway.sh base-url` 对照。

## 问题
飞书Bot不断要求配对，即使底层逻辑已修正也无法解决。

## 根本原因
`openclaw.json` 中没有设置 `dmPolicy`，导致系统默认使用 `"pairing"` 模式。

## 一键修复
```bash
cd /Users/mac/Documents/龙虾相关/my_openclaw
bash fix_feishu_pairing.sh open
```

## 验证
```bash
# 诊断
bash diagnose_feishu_pairing.sh

# 在飞书群中测试
@Scout 扫描 /app/workspace
```

## 三种方案

### 方案A：开放模式（推荐开发）
```bash
bash fix_feishu_pairing.sh open
```
- 任何人都能访问
- 最快速
- 适合开发/测试

### 方案B：配对模式（推荐生产）
```bash
bash fix_feishu_pairing.sh pairing
```
- 需要配对码批准
- 安全
- 适合生产环境

### 方案C：白名单模式（最安全）
```bash
bash fix_feishu_pairing.sh allowlist
```
- 只允许指定用户
- 最安全
- 适合生产环境

## 手动修复

### 1. 编辑 `openclaw.json`
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

### 2. 重启Gateway（端口与 `gateway.port` 一致）
```bash
pkill -9 openclaw-gateway
sleep 2
P="$(./scripts/openclaw-gateway.sh listen-port)"
openclaw gateway --port "$P"
```

## 文件位置
- 配置：`/Users/mac/Documents/龙虾相关/my_openclaw/openclaw.json`
- 配对存储：`/Users/mac/Documents/龙虾相关/my_openclaw/.openclaw/credentials/feishu-pairing.json`
- 日志：`/Users/mac/.openclaw/logs/gateway.log`

## 诊断命令
```bash
# 检查dmPolicy
cat openclaw.json | jq '.channels.feishu.dmPolicy'

# 检查Gateway状态
ps aux | grep openclaw-gateway | grep -v grep

# 健康检查（本机应访问的端口）
curl -s "$(./scripts/openclaw-gateway.sh base-url)/health" | jq .

# 查看日志
tail -20 /Users/mac/.openclaw/logs/gateway.log

# 运行完整诊断
bash diagnose_feishu_pairing.sh
```

## 状态
✅ 已完全解决（2026-03-29）

---

**快速链接**：
- 详细分析：`FEISHU_PAIRING_ROOT_CAUSE.md`
- 完整方案：`FEISHU_PAIRING_SOLUTION.md`
- 修复脚本：`fix_feishu_pairing.sh`
- 诊断工具：`diagnose_feishu_pairing.sh`
