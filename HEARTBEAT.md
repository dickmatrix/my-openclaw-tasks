# HEARTBEAT.md - 每日优化检查清单

> 每次心跳轮询时，按照以下清单进行检查。不要每次都只回复 HEARTBEAT_OK，要主动完成有意义的工作。

## 每日检查 (Daily - 2-3 次/天)

- [ ] **Cursor 索引状态** - 是否需要重新索引？(Cmd+Shift+J)
- [ ] **Chat 历史** - 是否有超过 50 条消息的对话需要重置？(Cmd+N)
- [ ] **Token 消耗** - 今日消耗是否超过预期？
- [ ] **代码质量** - 是否有新的 Linter 错误需要修复？

## 周期性回顾 (Weekly - 每周一)

- [ ] **统计本周数据**
  - Chat 总数
  - 平均消息长度
  - 模型使用分布 (Haiku vs Sonnet)
  - 总 Token 消耗

- [ ] **分析优化机会**
  - 哪些任务类型消耗 Token 最多？
  - 是否有重复的对话模式可以优化？
  - .cursorrules 是否需要更新？

- [ ] **更新文档**
  - 将本周发现写入 `memory/YYYY-MM-DD.md`
  - 更新 `MEMORY.md` 中的优化心得
  - 更新 `CURSOR_OPTIMIZATION.md` 中的成本基准

## 月度审视 (Monthly - 每月 1 号)

- [ ] **成本趋势分析**
  - 对比上月数据
  - 评估优化效果
  - 调整模型分级策略

- [ ] **规则更新**
  - 审视 .cursorrules 是否与项目演进一致
  - 检查 .cursorignore 是否需要新增过滤规则
  - 更新快捷键使用习惯

- [ ] **长期记忆维护**
  - 回顾本月所有日志
  - 提炼关键经验到 MEMORY.md
  - 删除过时的优化建议

## 快速参考

### 当前配置
- **项目规则:** `.cursorrules` ✅
- **索引过滤:** `.cursorignore` ✅
- **优化指南:** `CURSOR_OPTIMIZATION.md` ✅
- **日志系统:** `memory/YYYY-MM-DD.md` ✅

### 常用快捷键
- Cmd+L - 打开 Chat
- Cmd+N - 新建 Chat（重置上下文）
- Cmd+K - 精准修复（选中代码）
- Cmd+Shift+R - 快速重构（选中方法名）
- Cmd+Shift+J - 重新索引 + 修复 Linter 错误

### 模型选择指南
- **Haiku** - UI、单测、文档（成本低）
- **Sonnet** - 架构、复杂逻辑（准确度高）
- **Small** - Bug 修复、快速迭代（平衡）

---

**最后更新:** 2026-03-29
**下一次检查:** 2026-03-30
