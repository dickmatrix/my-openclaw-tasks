# OpenClaw 微服务架构

## 核心组件
- **Agent 集群**：多个专业 Agent（architect、coder、validator、tester 等）
- **消息总线**：Agent 间通信（Discord、Feishu、内部消息）
- **知识库**：RAG 系统，支持向量搜索
- **容器编排**：Docker Compose / Kubernetes

## Agent 协作模式

### 1. 顺序流水线
```
architect → coder → validator → tester → executor
```
用于：需求分析 → 代码生成 → 质量检查 → 测试 → 部署

### 2. 并行处理
```
researcher ─┐
            ├→ executor
auditor ────┘
```
用于：多个 Agent 并行处理不同任务

### 3. 反馈循环
```
coder → validator → (有问题) → coder
        ↓
      (通过) → tester
```
用于：迭代改进代码质量

## 数据流
1. **输入**：用户需求 → director agent
2. **分解**：director 分解为子任务
3. **执行**：各 Agent 执行对应任务
4. **聚合**：结果汇总并反馈
5. **学习**：更新知识库

## 通信协议
- **内部**：JSON 消息格式
- **外部**：REST API / WebSocket
- **异步**：消息队列（Redis/RabbitMQ）

## 扩展性
- 新 Agent 通过 agent.json 注册
- 新 Skill 通过 skills/ 目录添加
- 新工具通过 tools/ 目录集成
