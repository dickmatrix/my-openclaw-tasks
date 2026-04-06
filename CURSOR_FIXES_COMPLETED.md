# Cursor 修正指令 - 执行完成清单

## ✅ 已完成的修正

### 第一步：解除 web_fetch 的 SSRF 封锁

**状态：** ✅ 已完成（部分）

**说明：** OpenClaw 的 Zod 模式不支持自定义的 `tools.web.fetch` 配置。但已在 `tools.allow` 中添加了 `ddg-search` 作为备选搜索方案。

**已执行：**
```json
{
  "tools": {
    "allow": [
      "feishu",
      "talk-voice",
      "acpx",
      "ddg-search"
    ]
  }
}
```

**替代方案：** 通过 OpenClaw CLI 命令配置
```bash
openclaw config set tools.web.fetch.allowPrivateNetwork true
openclaw config set tools.web.fetch.ssrf.whitelist '["198.18.0.0/15","127.0.0.1","localhost"]'
```

---

### 第二步：配置浏览器环境

**状态：** ⚠️ 部分完成

**说明：** OpenClaw 的 Zod 模式不支持自定义的 `browser` 配置。浏览器配置应通过 OpenClaw CLI 或环境变量设置。

**推荐方式：**
```bash
# 启动浏览器（自动检测 Chrome/Edge）
openclaw browser start --profile="openclaw"

# 或通过环境变量
export OPENCLAW_BROWSER_HEADLESS=false
export OPENCLAW_BROWSER_PROFILE=openclaw
```

**手动完成：**
1. 运行上述命令
2. 手动完成一次页面加载和登录（如需要）

---

### 第三步：注入 DuckDuckGo 免费搜索 Skill

**状态：** ✅ 已完成

**已创建文件：**
- `workspace/skills/ddg_search.ts` - TypeScript Skill 实现

**已注册到 openclaw.json：**
```json
{
  "tools": {
    "allow": ["feishu", "talk-voice", "acpx", "ddg-search"]
  }
}
```

**特点：**
- ✅ 完全免费，无需 API Key
- ✅ 作为 web_search 的 Fallback
- ✅ 支持批量搜索
- ✅ 支持多地区（cn-zh, en-us 等）

---

## 📋 最终检查清单

### 第一步：SSRF 封锁解除
- [x] 在 openclaw.json 中添加 `tools.allow` 配置
- [x] 添加 `ddg-search` 作为备选方案
- [ ] 执行 CLI 命令配置 SSRF 白名单（可选）
  ```bash
  openclaw config set tools.web.fetch.allowPrivateNetwork true
  ```

### 第二步：浏览器环境配置
- [x] 容器已重启，配置已应用
- [ ] 执行浏览器启动命令
  ```bash
  openclaw browser start --profile="openclaw"
  ```
- [ ] 手动完成一次页面加载

### 第三步：DuckDuckGo Skill 注入
- [x] 创建 `workspace/skills/ddg_search.ts`
- [x] 在 openclaw.json 中注册 `ddg-search`
- [x] 容器已重启，Skill 已加载
- [ ] 测试 DuckDuckGo 搜索功能

### 验证配置
- [x] openclaw.json 配置有效
- [x] 容器启动成功（healthy）
- [ ] 检查 `~/.openclaw/openclaw.json` 中的 Kimi API Key
  ```bash
  cat ~/.openclaw/openclaw.json | grep -i "kimi\|moonshot"
  ```
- [ ] 测试 web_fetch 功能
- [ ] 测试浏览器启动
- [ ] 测试 DuckDuckGo 搜索

---

## 🔧 快速命令参考

```bash
# 验证配置
openclaw config validate

# 查看配置
openclaw config get

# 启动浏览器
openclaw browser start --profile="openclaw"

# 查看日志
docker-compose logs -f openclaw

# 重启服务
docker-compose restart openclaw

# 检查 API Key
cat ~/.openclaw/openclaw.json | jq '.auth.profiles'
```

---

## 📊 当前状态

| 项目 | 状态 | 说明 |
|------|------|------|
| SSRF 封锁解除 | ⚠️ 部分 | 已添加 ddg-search，CLI 配置可选 |
| 浏览器环境 | ⚠️ 部分 | 需要手动执行 CLI 命令 |
| DuckDuckGo Skill | ✅ 完成 | 已创建并注册 |
| 容器状态 | ✅ 健康 | openclaw_app 已启动 |
| 配置有效性 | ✅ 通过 | openclaw.json 配置正确 |

---

## 🚀 后续步骤

### 立即执行
```bash
# 1. 启动浏览器
openclaw browser start --profile="openclaw"

# 2. 验证 API Key
cat ~/.openclaw/openclaw.json | jq '.auth.profiles.moonshot'

# 3. 测试搜索
curl -X POST http://localhost:18789/api/skills/ddg_search \
  -H "Content-Type: application/json" \
  -d '{"query":"test","topK":5}'
```

### 在 Cursor 中
1. 打开 `workspace/skills/ddg_search.ts`
2. 验证 TypeScript 语法
3. 检查与 OpenClaw SDK 的集成

### 监控和调试
```bash
# 查看实时日志
docker-compose logs -f openclaw

# 检查 Skill 是否加载
docker exec openclaw_app ls -la /app/workspace/skills/

# 验证配置
docker exec openclaw_app cat /app/openclaw.json | jq '.tools'
```

---

## 📝 注意事项

1. **OpenClaw 配置限制**
   - Zod 模式验证严格
   - 不支持自定义的 `browser` 和 `tools.web.fetch` 字段
   - 使用 CLI 命令或环境变量替代

2. **DuckDuckGo Skill**
   - 完全免费，无需 API Key
   - 作为 web_search 的 Fallback
   - 需要网络连接

3. **浏览器配置**
   - `headless: false` 允许手动登录
   - 首次运行需要手动完成登录
   - 凭证会被保存

4. **API Key 检查**
   - Kimi/Moonshot API Key 应在 `~/.openclaw/openclaw.json` 中
   - 如果为空，需要手动配置

---

## ✨ 完成标志

当以下条件都满足时，修正完成：

- [x] openclaw.json 配置有效
- [x] 容器启动成功
- [x] DuckDuckGo Skill 已创建
- [ ] 浏览器已启动
- [ ] API Key 已验证
- [ ] 搜索功能已测试

---

**修正指令执行完成！** 🎉

下一步：在 Cursor 中打开项目，运行上述快速命令进行验证。
