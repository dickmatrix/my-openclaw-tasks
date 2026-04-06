# 群消息路由规则

## 触发条件
群内 @我（director）时，根据消息关键字分发到对应 agent 处理，结果由各 bot 直接回群。

## 路由表

| 关键字 | 目标 Agent | Bot 账号 |
|--------|-----------|---------|
| 搜索, 查找, 定位, 在哪, 找, 文件, 函数, 类, 方法, 变量, 模块, 路径, import, require, 调用, 引用, grep, find, locate, search, look up | scout | zhen_cha_yuan |
| 写, 生成, 创建, 实现, 编写, 补全, 初始化, 构造, 新建, 代码, function, class, interface, api, 接口, CRUD, 增删改查 | writer | bian_ji_yuan |
| 审查, 安全, 漏洞, 风险, 攻击, 注入, XSS, SQL, CSRF, 权限, 认证, 加密, 敏感, 泄露, 越权, 绕过, 污点, 威胁, 审计 | censor | shen_cha_yuan |
| 架构, 设计, 模式, 方案, 结构, 模块化, 分层, 微服务, 分布式, 高并发, 可扩展, 解耦, 聚合, SOA, Event-Driven | architect | mei_gu_zuo_kong_win |
| 调试, 问题, 错误, bug, 异常, 崩溃, 卡死, 超时, 失败, 排查, 诊断, 定位, 原因, 修复, fix, crash, issue, error, warning, stack, trace | auditor | shen_ji_yuan |
| 默认 | director | da_jie_tou_win |

## 实现方式
- director 接收消息后分析关键字
- 通过 sessions_send 转发给对应 agent
- 各 agent 处理后直接回复到群（通过各自的 feishu bot 账号）

## 状态
- 规则制定：✅ 完成
- 实现：✅ 已实现（写入 system_prompt.md，作为实际执行指令）
- 测试：待做
