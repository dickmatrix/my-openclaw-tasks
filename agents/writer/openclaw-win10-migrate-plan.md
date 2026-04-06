# OpenClaw 本机打包迁移方案（→ Win10）

> 整理时间：2026-04-03  
> 用途：整机迁移到 Windows 10

---

## 一、打包清单（核心文件）

### 1. OpenClaw 配置目录
路径：`~/.openclaw/`（Mac）/ `%USERPROFILE%\.openclaw\`（Win）

| 文件/目录 | 说明 | 必要性 |
|---|---|---|
| `.env` | **所有 API Key**（飞书、Discord、LLM等） | ⭐ 必传 |
| `openclaw.json` | 主配置文件（模型、Agent、Channel、Gateway等） | ⭐ 必传 |
| `container.env` | NSCC/GLM/DeepSeek 等批量密钥 | ⭐ 必传 |
| `credentials/` | 飞书配对信息（feishu-pairing.json） | ⭐ 必传 |
| `devices/` | 设备绑定信息 | ⭐ 必传 |
| `identity/` | 设备认证（device-auth.json） | ⭐ 必传 |
| `plugins/` | 插件配置 | 建议 |
| `feishu/` | 飞书相关配置 | 建议 |
| `canvas/` | 画布数据 | 可选 |
| `logs/` | 日志 | 不需要 |

### 2. Agent 工作区
路径：`~/my_openclaw/agents/`

```
agents/
├── main/          (空，忽略)
├── director/      (SOUL/IDENTITY/BOOTSTRAP/HEARTBEAT/AGENTS/COMMANDS/TOOLS)
├── architect/     (AGENTS/BOOTSTRAP/HEARTBEAT/IDENTITY/SOUL/TOOLS/USER + docs/mock_data)
├── validator/     (agent.json + system_prompt.md)
├── tester/        (agent.json + system_prompt.md)
├── executor/      (agent.json + system_prompt.md)
├── creative/      (agent.json + system_prompt.md)
├── auditor/       (全套：SOUL/IDENTITY/HEARTBEAT/AGENTS/TOOLS/USER + memory/scripts/system_prompt.md)
├── auditor-code/  (agent.json + system_prompt.md)
├── ai_customer_service/ (agent.json + system_prompt.md)
├── censor/        (全套 + system_prompt.md)
├── writer/        (全套 + knowledge-base/ + memory/ + outputs/)
├── scout/         (全套 + automation/ + memory/)
├── worker-code/   (agent.json + memory/ + skills/ + system_prompt.md)
├── worker-doc/   (agent.json + memory/ + skills/ + system_prompt.md)
└── worker-research/ (全套 + test_free_search.py + install_search_deps.sh 等)
```

总大小：**28MB**

### 3. 全局 Skills（OpenClaw 官方技能）
路径：`~/.openclaw/skills/`

| Skill | 大小 |
|---|---|
| evolver-1.27.3 | 748KB |
| self-improving-1.2.10 | 52KB |
| agent-browser-0.2.0 | 20KB |
| tavily-search-1.0.0 | 16KB |
| desearch-web-search-1.0.1 | 12KB |
| find-skills-0.1.0 | 12KB |
| gog-1.0.0 | 8KB |
| ai-agent-helper-1.0.0 | 8KB |
| summarize-1.0.0 | 8KB |
| super-websearch-realtime-1.0.0 | 8KB |
| weather-1.0.0 | 8KB |

### 4. 全局 npm 包
```
openclaw@2026.3.28
安装路径：~/.npm-global/lib/node_modules/openclaw/
```

---

## 二、打包命令（Mac 端执行）

```bash
# 1. 创建打包目录
mkdir ~/openclaw-transfer
cd ~/openclaw-transfer

# 2. 打包配置
cp -r ~/.openclaw .env openclaw.json container.env credentials/ devices/ identity/ plugins/ feishu/ skills/ ./

# 3. 打包 Agent 工作区（28MB）
cp -r ~/my_openclaw/agents .

# 4. 打包 npm 全局包（openclaw）
cp -r ~/.npm-global/lib/node_modules/openclaw .

# 5. 打包成一个zip
zip -r openclaw-win10-migrate.zip .openclaw agents openclaw

# 6. 查看大小
du -sh ~/openclaw-transfer/
```

---

## 三、Win10 恢复步骤

### 1. 安装 Node.js
- 下载 LTS 版：https://nodejs.org/
- 验证：`node -v` + `npm -v`

### 2. 安装 OpenClaw
```bash
npm install -g openclaw@2026.3.28
```

### 3. 恢复配置
```powershell
# 创建配置目录
mkdir $env:USERPROFILE\.openclaw

# 解压并复制文件到对应位置
# .openclaw/ → $env:USERPROFILE\.openclaw\
# agents/ → $env:USERPROFILE\my_openclaw\agents\
```

### 4. 恢复 .env 环境变量
```powershell
# 将 .env 内容添加到系统环境变量或用户环境变量
# 或创建 $env:USERPROFILE\.openclaw\.env 文件
```

### 5. 启动验证
```bash
openclaw doctor
openclaw gateway start
```

---

## 四、⚠️ 注意事项

### API Key 变更
- `.env` 中的飞书 App Secret 等**直接写入配置文件**，在新机器上需重新填写
- Discord Bot Token 可直接迁移
- LLM API Key（DeepSeek/GLM/Moonshot）可直接迁移

### 飞书机器人
- 飞书企业自建应用（`FEISHU_*_APP_ID/APP_SECRET`）需要在新机器飞书开放平台重新注册
- **配对信息**（`credentials/feishu-pairing.json`）在新机器上需要重新配对

### Windows 路径差异
- Mac 的 `/Users/mac/Documents/龙虾相关/my_openclaw/agents/` 需要映射到 Windows 的 `C:\Users\<username>\my_openclaw\agents\`
- `openclaw.json` 中的 workspace 路径需要修改

### 设备认证
- `identity/device-auth.json` 与本机硬件绑定，**不能跨机器迁移**
- 新机器需要重新执行 `openclaw device pair`

---

## 五、openclaw.json workspace 路径适配

在新机器上，`openclaw.json` 中所有 agent 的 `workspace` 路径需要从：
```
/Users/mac/Documents/龙虾相关/my_openclaw/agents/xxx
```
改为：
```
C:\Users\<username>\my_openclaw\agents\xxx
```

建议在新机器上重新运行 `openclaw wizard` 或手动编辑 `openclaw.json` 的 `agents.list[].workspace` 字段。

---

## 六、最小化迁移（只迁移必要文件）

如果只想迁移核心配置，**最小集合**如下：

```
.openclaw/
├── .env                          # API密钥
├── openclaw.json                 # 主配置
├── container.env                 # 环境变量
├── credentials/                  # 飞书配对
├── devices/                      # 设备
├── identity/                     # 设备认证
└── skills/                       # 技能（可后续用clawhub重新安装）

agents/                           # 需要迁移的agent工作区
├── director/
├── architect/
├── validator/
├── tester/
├── executor/
├── creative/
├── auditor/
├── auditor-code/
├── ai_customer_service/
├── censor/
├── writer/
├── scout/
├── worker-code/
├── worker-doc/
└── worker-research/
```
