# Zed 多线程协作：handoff 约定

在 Zed 里开 **3 条独立 Agent 线程**（Research / Implement / Review），用本目录 **交接文件** 同步状态，避免多线程改同一处逻辑。

## 怎么用

1. 复制 `TEMPLATE.md` 为 `active/<任务名>-<日期>.md`（例如 `active/kimi-proxy-20260406.md`）。
2. **Research 线程**：只读与检索，把结论写进该文件的「研究结论」区块。
3. **Implement 线程**：只实现「待办」里列出的改动，改完更新「实现记录」与「给 Review 的检查点」。
4. **Review 线程**：对照检查点审代码与风险，把结果写进「审查结论」，并更新「状态」。

任意线程在 Zed 里用 `@handoff/active/xxx.md` 引用当前任务单。

## 与仓库内其它配置的关系

- 角色分工可与 `config/agent_collaboration.json` 对齐；本目录是 **IDE 内人机协作** 的落地载体，不替代 OpenClaw Gateway。
