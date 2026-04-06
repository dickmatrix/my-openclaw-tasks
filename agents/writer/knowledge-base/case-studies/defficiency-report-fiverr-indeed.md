# 能力缺陷报告 — Branch 3C

> **日期**: 2026-03-30T03:53:00Z
> **任务ID**: GIG-FIVERR-INDEED-2026
> **状态**: PENDING — 等待系统级补充

---

## 缺陷概述

尝试对 Fiverr 和 Indeed 执行数据采集任务，触发反爬机制后，无法完成绕过。

---

## 错误特征分析

### 测试记录

| 目标 | 方法 | 状态 | 拦截类型 |
|------|------|------|---------|
| Fiverr HTML 页面 | curl (直接) | ✅ 200 | 无 |
| Fiverr 搜索 API | requests + CSRF | ❌ 403 | PerimeterX CAPTCHA |
| Fiverr 搜索页面 | requests | ❌ 403 | PerimeterX |
| Indeed 职位页 | requests | ❌ 403 | Cloudflare |
| bypass_scraper (API模式) | 商业API | ❌ 失败 | 无 SCRAPER_API_KEY |
| bypass_scraper (浏览器模式) | Playwright | ❌ 失败 | 容器缺系统库 |

### 错误签名

```
HTTP_403 | PerimeterX CAPTCHA (px-captcha.px-cloud.net)
HTTP_403 | Cloudflare JS Challenge ("Just a moment...")
Browser launch failure: Host system is missing dependencies to run browsers
```

### 根因定位

| 环节 | 状态 | 说明 |
|------|------|------|
| 反爬检测（分支1C） | ✅ 正确触发 | HTTP 403 / Cloudflare 正确识别 |
| 商业 API 绕过 | ❌ 未激活 | 容器无 SCRAPER_API_KEY 环境变量 |
| 浏览器备选绕过 | ❌ 系统限制 | 容器缺少 libnspr4/nss/atk 等 Playwright 依赖 |
| 直接请求绕过 | ❌ 部分有效 | Fiverr HTML 返回 200，但 API 调用触发 CAPTCHA |

### 阻断节点

**节点 1**: 容器缺少 Playwright 浏览器系统依赖
- 影响：浏览器备选模式（分支1C 最终兜底）完全失效
- 发生概率：**100%**（容器级限制）
- 修复路径：安装 Playwright 系统依赖（需 root 权限或 Docker 镜像预装）

**节点 2**：无商业 API Key
- 影响：无法使用 ScrapingBee / ScrapingNinja 等绕过服务
- 发生概率：**100%**（配置缺失）
- 修复路径：配置 SCRAPER_API_KEY 环境变量

---

## 能力缺口分级

| 级别 | 缺口类型 | 描述 |
|------|---------|------|
| 🔴 P0 | 容器系统限制 | Playwright 浏览器依赖缺失，无法执行 JS 渲染绕过 |
| 🔴 P0 | 配置缺失 | 无 SCRAPER_API_KEY，商业 API 绕过不可用 |
| 🟡 P1 | 反爬绕过能力 | 仅能处理 HTTP 403，无法处理 Cloudflare PerimeterX JS 挑战 |
| 🟡 P2 | SPA 数据提取 | Fiverr 等 React SPA 的数据需浏览器渲染后提取 |

---

## 修复路径

### P0-1：安装 Playwright 系统依赖
```bash
# 需要 root 权限，容器环境受限
apt-get install -y libnspr4 libnss3 libatk1.0-0 libdbus-1-3 \
  libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 \
  libxrandr2 libgbm1 libxkbcommon0 libasound2

# 然后安装 playwright
pip install playwright
playwright install chromium
```

### P0-2：配置商业 API Key
```bash
export SCRAPER_API_KEY="your-scrapingbee-or-scrapingninja-key"
```

### P1：引入备用绕过方案
- 使用 `curl_cffi`（已安装）模拟浏览器指纹
- 使用 `cloudscraper` 专门处理 Cloudflare
- 接入 ScraperAPI / ZenRows 等专业绕过 API

---

## 知识库更新记录

- ✅ `patterns/data-collection/README.md` — 已补充 Fiverr/Indeed 反爬信息
- ✅ `patterns/agent-execution-framework.md` — 3C 分支流程已定义
- ✅ `skills/bypass_scraper.py` — 已实现完整检测→API→浏览器备选链路
- ❌ 浏览器备选失效 — 容器系统依赖缺失（P0）

---

## 待办事项

- [ ] 获取 SCRAPER_API_KEY（ScrapingBee/ScrapingNinja）
- [ ] 在 Docker 构建阶段安装 Playwright 系统依赖
- [ ] 评估 cloudscraper 作为轻量替代
- [ ] 测试有浏览器支持环境下的完整闭环
