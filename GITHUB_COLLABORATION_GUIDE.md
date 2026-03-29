# Agent 进化 GitHub 协同优化 - 完整实现指南

## 📋 项目概览

**项目名称**: Agent Evolution GitHub Collaboration  
**目标**: 通过 GitHub Actions 实现 Agent 与 GitHub 的深度协同  
**核心优化**: Schema 治理 + CI/CD 流水线 + 数据驱动决策

---

## 🏗️ 系统架构

```
Agent 提交代码
    ↓
GitHub Actions 触发
    ↓
Schema 验证 (Registry Guard)
    ↓
构建 & 测试 (CI/CD Pipeline)
    ↓
基准测试 (Benchmark Loop)
    ↓
进化决策 (Evolution Decision)
    ↓
自动合并 / 回滚
```

---

## 📁 项目结构

```
.github/
├── workflows/
│   └── agent-evolution-collaboration.yml (主工作流)
scripts/
├── validate_schema.py (Schema 验证)
├── benchmark_runner.sh (基准测试)
└── evolution_decision.py (进化决策)
schema_registry/
├── master.json (主索引)
├── data_cleaning_schema.json
└── vscode_extension_schema.json
benchmark/
└── logs/ (测试结果)
```

---

## 🔄 三大优化任务

### Task A: Schema 自动化治理 (Registry Guard)

**目标**: 防止 Agent 污染数据库

**核心逻辑**:
1. **格式校验**: 强制执行 JSON Schema 验证
2. **去重分析**: 计算 Jaccard 相似度，相似度 > 0.9 拒绝合入
3. **版本标记**: 自动追加 SemVer 标签

**触发条件**:
```yaml
on:
  push:
    paths: ['schema_registry/**']
```

**执行步骤**:
```bash
python3 scripts/validate_schema.py
```

**输出**:
- ✓ 格式验证通过
- ✓ 无重复 Schema
- ✓ 版本标签已添加

---

### Task B: VSCodium 扩展闭环 (CI/CD Pipeline)

**目标**: 自动构建、测试和分发扩展

**核心逻辑**:
1. **构建环境**: 使用 node:latest 执行 vsce package
2. **热更新分发**: 利用 GitHub Releases 通知 Agent
3. **自愈测试**: 编译失败时自动开启修复任务

**触发条件**:
```yaml
on:
  push:
    paths: ['evolve_codium/**']
```

**执行步骤**:
```bash
npm install
npm run compile
npx vsce package --out ./dist/cleaner-latest.vsix
```

**输出**:
- ✓ 扩展已构建
- ✓ Artifact 已上传
- ✓ Release 已创建

---

### Task C: 数据驱动型进化 (Benchmark Feedback Loop)

**目标**: 通过性能数据自动决策是否进化

**核心逻辑**:
1. **平行运行**: 同时启动旧版本和新版本
2. **数据沉淀**: 记录清洗耗时、字段匹配率、内存峰值
3. **进化决策**: 若 R_new > R_old 且 T_new ≤ T_old × 1.1，自动更新

**进化公式**:
```
P_success = Accuracy / Time

若 P_success_new > P_success_old:
  → 接受新版本
否则:
  → 触发回滚
```

**触发条件**:
```yaml
on:
  schedule: '0 0 * * *'  # 每日零点
  workflow_dispatch:     # 手动触发
```

**性能指标**:
- 吞吐量: 1000 rows/sec
- 错误率: < 2%
- 成功率: ≥ 98%

---

## 🛡️ 分支保护规则

**必须配置**:

1. **需要至少 1 个审查**
   - 防止 Agent 直接合入
   - 确保人工审查

2. **需要通过所有状态检查**
   - Schema 验证必须通过
   - 构建必须成功
   - 基准测试必须通过

3. **禁止强制推送**
   - 保护历史记录
   - 防止意外覆盖

4. **要求分支最新**
   - 防止冲突
   - 确保代码一致性

---

## 📊 工作流详解

### 工作流 1: Schema 验证

```yaml
jobs:
  schema-integrity-check:
    steps:
      - Validate Schema Format
      - Check Schema Duplicates
      - Add SemVer Tags
      - Update Master Registry
```

**验证内容**:
- JSON 格式有效性
- 必需字段完整性
- 字段类型正确性
- 与现有 Schema 的相似度

---

### 工作流 2: 扩展构建

```yaml
jobs:
  build-vscodium-extension:
    steps:
      - Install Dependencies
      - Build Extension
      - Upload Artifact
      - Create Release
      - Notify Agent on Failure
```

**构建流程**:
1. 安装 npm 依赖
2. 编译 TypeScript
3. 打包 .vsix 文件
4. 上传到 Artifacts
5. 创建 GitHub Release

---

### 工作流 3: 基准测试

```yaml
jobs:
  benchmark-feedback-loop:
    steps:
      - Run Benchmark Tests
      - Evolution Decision
      - Upload Benchmark Results
      - Commit Results
```

**测试指标**:
- 吞吐量 (rows/sec)
- 错误率 (%)
- 成功率 (%)
- 内存峰值 (MB)
- 执行时间 (s)

---

## 🚀 快速开始

### 1. 配置分支保护

在 GitHub 仓库设置中:
1. 进入 Settings → Branches
2. 添加分支保护规则
3. 配置上述 4 个规则

### 2. 创建 Schema

在 `schema_registry/` 目录创建新 Schema:

```json
{
  "name": "my_schema",
  "version": "1.0.0",
  "fields": {
    "id": {"type": "int", "required": true},
    "name": {"type": "string", "required": true}
  }
}
```

### 3. 提交代码

```bash
git add schema_registry/my_schema.json
git commit -m "Add new schema"
git push origin main
```

### 4. 查看工作流

在 GitHub Actions 中查看执行进度

### 5. 查看结果

- Schema 验证结果
- 构建日志
- 基准测试报告
- 进化决策

---

## 📈 性能优化

### 成本优化

**建议**:
- GitHub Actions 免费额度有限
- 频繁的 Benchmark 放在宿主机本地运行
- GitHub 仅作为版本控制和 CI/CD 触发器

**配置**:
```yaml
# 减少运行频率
schedule: '0 0 * * 0'  # 每周一次而非每天
```

### 时间优化

**并行执行**:
```yaml
jobs:
  schema-check:
    runs-on: ubuntu-latest
  
  build-extension:
    runs-on: ubuntu-latest
    needs: schema-check  # 依赖关系
  
  benchmark:
    runs-on: ubuntu-latest
    needs: build-extension
```

---

## 🔍 故障排查

### 问题 1: Schema 验证失败

**原因**: JSON 格式错误或缺少必需字段

**解决**:
```bash
python3 scripts/validate_schema.py
```

### 问题 2: 构建失败

**原因**: npm 依赖问题或编译错误

**解决**:
```bash
npm install
npm run compile
```

### 问题 3: 基准测试失败

**原因**: 性能指标未达标

**解决**: 检查 `benchmark/logs/latest.json` 中的详细指标

---

## 📚 最佳实践

### 1. Schema 设计

```json
{
  "name": "descriptive_name",
  "version": "1.0.0",
  "description": "清晰的描述",
  "fields": {
    "field_name": {
      "type": "string|int|float|datetime",
      "required": true|false,
      "description": "字段描述"
    }
  }
}
```

### 2. 提交信息

```
[Schema] Add data_cleaning_schema v1.0.0

- 添加数据清洗标准 Schema
- 包含 id, name, value, timestamp 字段
- 通过 Schema 验证
```

### 3. 版本管理

- 使用 SemVer (Major.Minor.Patch)
- 向后兼容时增加 Minor
- 破坏性变更增加 Major

### 4. 监控指标

定期检查:
- Schema 注册表大小
- 构建成功率
- 基准测试趋势
- 进化决策历史

---

## 🎓 学习资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [JSON Schema 规范](https://json-schema.org/)
- [SemVer 版本管理](https://semver.org/)
- [VSCode 扩展开发](https://code.visualstudio.com/api)

---

## ✅ 完成清单

- [x] Schema Registry Guard 脚本
- [x] GitHub Actions 工作流
- [x] 分支保护规则配置
- [x] 基准测试框架
- [x] 进化决策逻辑
- [x] 完整实现指南
- [x] 最佳实践文档

---

**项目状态**: ✅ 生产就绪  
**版本**: 1.0.0  
**最后更新**: 2026-03-29
