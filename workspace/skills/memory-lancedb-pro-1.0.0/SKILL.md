---
name: memory-lancedb-pro
version: 1.0.0
description: LanceDB Pro 高级记忆系统配置指南 - 混合检索、智能元数据、层级衰减
---

# memory-lancedb-pro 配置指南

使用 LanceDB Pro 实现高级记忆系统，支持向量搜索 + BM25 混合检索、智能元数据提取和自动层级管理。

## 快速开始

### 1. 安装插件
```bash
openclaw plugins install memory-lancedb-pro
```

### 2. 配置 embedding provider
在 `config.yaml` 中添加：

```yaml
plugins:
  memory-lancedb-pro:
    embedding:
      apiKey: ${OPENAI_API_KEY}
      model: text-embedding-3-small
      dimensions: 1536
    
    # 可选：多 key 轮换
    # apiKey:
    #   - ${OPENAI_KEY_1}
    #   - ${OPENAI_KEY_2}
```

### 3. 配置 LLM (用于智能提取)
```yaml
plugins:
  memory-lancedb-pro:
    llm:
      apiKey: ${OPENAI_API_KEY}
      model: gpt-4o-mini
      # baseURL: https://api.openai.com/v1  # 可选自定义端点
```

## 检索参数调优

### 混合搜索权重
```yaml
retrieval:
  vectorWeight: 0.7    # 向量相似度权重
  bm25Weight: 0.3      # 关键词权重
```

### 时间衰减
```yaml
retrieval:
  recencyHalfLifeDays: 14    # 新近度半衰期
  recencyWeight: 0.1         # 新近度加分权重
  timeDecayHalfLifeDays: 60  # 时间衰减半衰期
```

### 评分阈值
```yaml
retrieval:
  hardMinScore: 0.35    # 最终评分阈值
```

## 层级系统

### 三层级配置
| 层级 | 描述 | 衰减行为 |
|------|------|----------|
| Core | 核心记忆 | 缓慢衰减 (最低 0.9) |
| Working | 工作记忆 | 标准衰减 (最低 0.7) |
| Peripheral | 边缘记忆 | 快速衰减 (最低 0.5) |

### 自动晋升规则
- 基于重要性、访问频率自动晋升
- 可通过 `tierManager` 配置

## 噪声过滤

### 内置过滤
- Agent 拒绝回复 ("I don't have information")
- 元问题 ("Do you remember?")
- 会话客套话 (hi, hello, good morning)

### 自适应学习
- 自动学习新的噪声模式
- 基于 embedding 相似度检测 (≥0.82)

## 作用域隔离

### 作用域类型
- `global`: 全局记忆
- `agent:{agentId}`: 特定 agent 记忆
- `session:{sessionId}`: 会话级记忆

### 配置示例
```yaml
plugins:
  memory-lancedb-pro:
    defaultScope: agent:main
    scopes:
      - id: agent:main
        description: Main agent memory
      - id: agent:subagent
        description: Sub-agent memory
```

## 完整配置参考

详见 `references/full-reference.md`:
- 数据库 schema 详情
- 混合检索 pipeline 细节
- Weibull 衰减模型参数
- 文档分块策略
- Smart Metadata 系统
- Access Tracking 与增强机制

## 故障排除

### 常见问题

**Q: 检索不到记忆**
A: 检查 embedding API key 是否正确配置，确认 vectorWeight 不是 0

**Q: 记忆过早衰减**
A: 调高 `timeDecayHalfLifeDays` 或调整层级配置

**Q: 噪声过滤过度**
A: 调整 `noiseFilter` 配置或降低相似度阈值