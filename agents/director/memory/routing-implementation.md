# 路由实现说明

## 当前架构

```
用户 @director → director 接收 → 关键字匹配 → sessions_send 给目标 agent
                                                 ↓
                                            目标 agent 处理 → 返回结果给 director
                                                 ↓
                                            director 统一回复到群

模型分层：
- 简单问题 → MiniMax-M2.7-highspeed（默认）
- 复杂问题 → heavy_track（多步推理/架构/安全/调试类问题）
```

## 路由触发条件
- 群内 @director（da_jie_tou_win）时触发路由流程
- 未 @ 时 director 不处理群消息

## 模型分层规则
- 简单问题：快速问答、简单操作、一句话可答 → 默认模型
- 复杂问题：多步推理、bug调试、架构设计、安全审计、异常分析 → heavy_track

## 各 Bot 对应关系（供参考）

| Agent | Bot 账号 | 飞书 App |
|-------|---------|---------|
| auditor | shen_ji_yuan | 审计员 |
| censor | shen_cha_yuan | 审查员 |
| writer | bian_ji_yuan | 编辑员 |
| scout | zhen_cha_yuan | 侦查员 |
| architect | mei_gu_zuo_kong_win | 架构师 |

## 测试方法

群里发消息测试：
- `@大肥助手 调试这段代码：function test() { return 1 }` → 应路由到 auditor
- `@大肥助手 写一个排序算法` → 应路由到 writer
- `@大肥助手 搜索 userService 在哪里` → 应路由到 scout

## 待优化

如果需要真正实现"各 bot 直接回群"而非"director 转发"，需要：
1. 用户 @特定 bot 发消息
2. OpenClaw 根据 feishu 账号路由到对应 agent
3. 那个 bot 直接回群

目前是"透明中转"模式。
