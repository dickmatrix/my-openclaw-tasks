# Test Case 2: Semi-Fuzzy Input

**Input**: "我的代码有问题"

## Intent Recognition

| 维度 | 结果 |
|------|------|
| **意图类型** | Check (检查类) |
| **置信度** | High |
| **隐含实体** | [代码: 未指定路径] |
| **隐含意图** | Bug诊断 / 性能检查 / 功能验证 |
| **处理策略** | 1. 检测当前目录代码<br>2. 询问具体问题类型 |

## Task Decomposition

### Plan
```
├── Task 1: 扫描当前目录代码 → 识别项目类型和文件
├── Task 2: 诊断问题类型 → 询问用户具体问题
├── Task 3: 定位问题文件 → 根据问题类型筛选
└── Task 4: 分析问题 → 提供解决方案
```

## Execution

### Step 1: Scan Current Directory Code
- Status: ⏳ Executing

### Step 2: Ask User About Specific Issue
- Question: 具体是什么问题?
  - 运行时错误?
  - 性能问题?
  - 逻辑错误?
  - 其他?

## Evaluation

- [ ] 意图识别正确: ⏳ Pending
- [ ] 任务分解合理: ⏳ Pending
- [ ] 执行流程顺畅: ⏳ Pending
- [ ] 问题定位准确: ⏳ Pending

---

*Test Case 2 - 2026-03-29T08:25:00Z*
