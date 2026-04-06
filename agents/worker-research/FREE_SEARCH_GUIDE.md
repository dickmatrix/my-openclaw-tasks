# OpenClaw 免费搜索方案集成指南

## 概述

已为 OpenClaw 集成了两个完全免费的搜索方案，无需付费 API：

| 方案 | 提供商 | 成本 | 特点 |
|------|--------|------|------|
| **方案 A** | DuckDuckGo | 完全免费 | 无需 API Key，开箱即用 |
| **方案 B** | Google Gemini | 1000/天免费 | 高质量 Google 搜索结果 |
| **路由器** | 自动降级 | 免费 | 优先 DuckDuckGo，失败自动降级 |

---

## 快速开始

### 1. DuckDuckGo 搜索（推荐）

**完全免费，无需配置**

```python
from agents.worker_research.skills.duckduckgo_search import search_free

# 执行搜索
result = search_free("白银价格走势 2024", top_k=10)
print(result)
```

**输出格式：**
```json
{
  "status": "success",
  "provider": "DuckDuckGo (Free)",
  "query": "白银价格走势 2024",
  "count": 10,
  "results": [
    {
      "title": "...",
      "url": "...",
      "snippet": "...",
      "source": "DuckDuckGo",
      "confidence": "95.0%"
    }
  ]
}
```

### 2. Google Gemini Grounding 搜索

**需要 Gemini API Key（免费额度：1000/天）**

#### 获取 API Key

1. 访问 https://ai.google.dev
2. 点击 "Get API Key"
3. 创建新项目或选择现有项目
4. 复制 API Key

#### 配置

```bash
# 方式 1：环境变量
export GEMINI_API_KEY="your-api-key-here"

# 方式 2：.env 文件
echo "GEMINI_API_KEY=your-api-key-here" >> .env
```

#### 使用

```python
from agents.worker_research.skills.gemini_grounding_search import search_gemini
import os

api_key = os.getenv("GEMINI_API_KEY")
result = search_gemini("白银价格走势 2024", api_key=api_key, top_k=10)
print(result)
```

### 3. 自动路由器（推荐用于生产）

**自动选择最佳方案，失败时自动降级**

```python
from agents.worker_research.skills.search_router import search

# 自动使用 DuckDuckGo（完全免费）
result = search("白银价格走势 2024", provider="auto")

# 或显式指定提供商
result = search("白银价格走势 2024", provider="duckduckgo")
result = search("白银价格走势 2024", provider="gemini", gemini_api_key="...")
```

---

## 在 OpenClaw Agent 中使用

### 注册 Skill

已在 `agents/worker-research/agent.json` 中注册了新的 skills：

```json
{
  "skills": {
    "duckduckgoSearch": "./agents/worker-research/skills/duckduckgo_search.py",
    "geminiGroundingSearch": "./agents/worker-research/skills/gemini_grounding_search.py",
    "searchRouter": "./agents/worker-research/skills/search_router.py"
  }
}
```

### 在 Agent 中调用

```python
# 在 agent 的 system_prompt 或代码中
from skills.search_router import search

# 执行搜索
results = search(query="用户查询", provider="auto")

# 处理结果
for result in results["results"]:
    print(f"{result['title']}: {result['url']}")
```

---

## 依赖安装

### 宿主机安装（推荐）

```bash
# 安装所有依赖
pip install duckduckgo-search google-generativeai httpx

# 或使用脚本
bash agents/worker-research/install_search_deps.sh
```

### 容器内使用

由于容器镜像限制，建议在宿主机上运行 Python 脚本，然后通过 HTTP API 调用 OpenClaw。

---

## 性能对比

| 指标 | DuckDuckGo | Gemini | 说明 |
|------|-----------|--------|------|
| 速度 | 快 | 中等 | DuckDuckGo 更快 |
| 准确度 | 中等 | 高 | Gemini 使用 Google 搜索 |
| 成本 | 免费 | 1000/天免费 | 都是免费的 |
| 配置 | 无需 | 需要 API Key | DuckDuckGo 开箱即用 |
| 稳定性 | 高 | 高 | 都很稳定 |

---

## 故障排除

### DuckDuckGo 搜索失败

```
ModuleNotFoundError: No module named 'duckduckgo_search'
```

**解决：**
```bash
pip install duckduckgo-search
```

### Gemini 搜索失败

```
Error: Gemini API Key required
```

**解决：**
```bash
export GEMINI_API_KEY="your-key"
# 或在代码中传递
search(query, api_key="your-key")
```

### 搜索结果为空

- 检查网络连接
- 尝试更换搜索关键词
- 检查 API 配额（Gemini 1000/天）

---

## 最佳实践

1. **优先使用 DuckDuckGo**
   - 完全免费，无需配置
   - 速度快，适合大多数场景

2. **Gemini 用于高质量需求**
   - 需要 Google 搜索结果时
   - 有 API Key 配额时

3. **使用自动路由器**
   - 生产环境推荐
   - 自动降级，提高可靠性

4. **批量搜索**
   ```python
   from skills.search_router import batch_search
   
   queries = ["查询1", "查询2", "查询3"]
   results = batch_search(queries, provider="auto")
   ```

---

## 文件清单

- `duckduckgo_search.py` - DuckDuckGo 搜索实现
- `gemini_grounding_search.py` - Gemini Grounding 搜索实现
- `search_router.py` - 统一搜索路由器
- `install_search_deps.sh` - 依赖安装脚本
- `requirements.txt` - 已更新依赖列表

---

## 参考资源

- DuckDuckGo Search: https://github.com/deedy5/duckduckgo_search
- Google Gemini API: https://ai.google.dev
- OpenClaw Skills: https://github.com/openclaw/openclaw
