# Cursor 修正指令 - OpenClaw 配置优化

## 📋 执行清单

### 第一步：解除 web_fetch 的 SSRF 封锁

**当前状态：** openclaw.json 中没有 `tools.web.fetch` 配置

**修正方案：**

在 openclaw.json 的根级别添加 `tools` 配置段：

```json
{
  "tools": {
    "web": {
      "fetch": {
        "allowPrivateNetwork": true,
        "ssrf": {
          "whitelist": [
            "198.18.0.0/15",
            "127.0.0.1",
            "localhost",
            "192.168.0.0/16",
            "10.0.0.0/8",
            "172.16.0.0/12"
          ]
        }
      }
    }
  }
}
```

**执行步骤：**

1. 在 Cursor 中打开 `/Users/mac/Documents/龙虾相关/my_openclaw/openclaw.json`
2. 在 `"plugins"` 部分之后添加上述 `tools` 配置
3. 保存文件
4. 在终端执行：
   ```bash
   openclaw config validate
   ```

---

### 第二步：配置浏览器环境

**当前状态：** 需要检查 browser 配置

**修正方案：**

在 openclaw.json 中添加或更新 `browser` 配置：

```json
{
  "browser": {
    "headless": false,
    "profile": "openclaw",
    "executablePath": "",
    "autoDetect": true,
    "launchArgs": [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage"
    ]
  }
}
```

**执行步骤：**

1. 在 Cursor 中打开 openclaw.json
2. 添加或更新 `browser` 配置段
3. 保存文件
4. 在终端执行：
   ```bash
   openclaw browser start --profile="openclaw"
   ```
5. 手动完成一次页面加载和登录（如需要）

---

### 第三步：注入 DuckDuckGo 免费搜索 Skill

**当前状态：** 已在 Python 中实现，需要在 TypeScript 中创建

**修正方案：**

1. **创建 TypeScript Skill 文件**

在 `workspace/skills/` 目录下创建 `ddg_search.ts`：

```typescript
import { Tool, ToolSchema } from '@openclaw/sdk';

export const ddgSearchSchema: ToolSchema = {
  name: 'ddg_search',
  description: 'Free DuckDuckGo search without API key',
  parameters: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Search query'
      },
      topK: {
        type: 'number',
        description: 'Number of results to return',
        default: 10
      },
      region: {
        type: 'string',
        description: 'Region code (cn-zh, en-us, etc)',
        default: 'cn-zh'
      }
    },
    required: ['query']
  }
};

export async function ddgSearch(params: {
  query: string;
  topK?: number;
  region?: string;
}): Promise<any> {
  try {
    // 调用 Python skill 或直接实现
    const response = await fetch('http://localhost:18789/api/skills/ddg_search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    
    return await response.json();
  } catch (error) {
    return {
      status: 'error',
      message: `DuckDuckGo search failed: ${error.message}`
    };
  }
}

export default {
  schema: ddgSearchSchema,
  execute: ddgSearch
};
```

2. **注册到 openclaw.json**

在 `plugins.entries` 中添加：

```json
{
  "plugins": {
    "entries": {
      "ddg-search": {
        "enabled": true,
        "path": "./workspace/skills/ddg_search.ts"
      }
    }
  }
}
```

3. **在 tools.allow 中添加**

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

---

## ✅ 最终检查清单

- [ ] **第一步完成**
  - [ ] 在 openclaw.json 中添加 `tools.web.fetch.allowPrivateNetwork: true`
  - [ ] 添加 SSRF 白名单（RFC 2544 范围）
  - [ ] 执行 `openclaw config validate` 验证

- [ ] **第二步完成**
  - [ ] 在 openclaw.json 中配置 `browser` 部分
  - [ ] 设置 `headless: false`
  - [ ] 执行 `openclaw browser start --profile="openclaw"`
  - [ ] 手动完成一次页面加载

- [ ] **第三步完成**
  - [ ] 创建 `workspace/skills/ddg_search.ts`
  - [ ] 在 openclaw.json 中注册 skill
  - [ ] 在 `tools.allow` 中添加 `ddg-search`
  - [ ] 重启 OpenClaw 服务

- [ ] **验证配置**
  - [ ] 检查 `~/.openclaw/openclaw.json` 中的 Kimi API Key
  - [ ] 验证所有配置项有效
  - [ ] 测试 web_fetch 功能
  - [ ] 测试浏览器启动
  - [ ] 测试 DuckDuckGo 搜索

---

## 🔧 快速命令

```bash
# 验证配置
openclaw config validate

# 启动浏览器
openclaw browser start --profile="openclaw"

# 查看配置
openclaw config get

# 重启服务
docker-compose restart openclaw_app

# 查看日志
docker-compose logs -f openclaw_app
```

---

## 📝 注意事项

1. **SSRF 白名单**
   - RFC 2544: 198.18.0.0/15 (Fake-IP 范围)
   - RFC 1918: 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12 (私网)
   - 本地: 127.0.0.1, localhost

2. **浏览器配置**
   - `headless: false` 允许手动登录
   - `autoDetect: true` 自动查找 Chrome/Edge
   - 如果 `executablePath` 为空，OpenClaw 会自动定位

3. **DuckDuckGo Skill**
   - 完全免费，无需 API Key
   - 作为 web_search 的 Fallback
   - 支持批量搜索

---

## 🚀 执行顺序

1. 修改 openclaw.json（第一、二、三步）
2. 验证配置：`openclaw config validate`
3. 重启服务：`docker-compose restart openclaw_app`
4. 启动浏览器：`openclaw browser start --profile="openclaw"`
5. 测试功能

---

**准备好在 Cursor 中执行了吗？** 🎯
