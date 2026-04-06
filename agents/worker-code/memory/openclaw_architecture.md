# OpenClaw 架构文档

## 系统架构概览

### 多智能体集群架构
```
┌─────────────────────────────────────────┐
│         Kakashi Controller              │
│     (总监节点 - 全局调度与决策)          │
└─────────┬──────────┬──────────┬────────┘
          │          │          │
    ┌─────▼────┐ ┌───▼────┐ ┌───▼────┐
    │Researcher│ │ Coder  │ │ Doc    │
    │  (研究)   │ │ (开发) │ │ (文案) │
    └──────────┘ └────────┘ └────────┘
```

### 核心组件

#### 1. Kakashi Controller (总监控制器)
- **职责**：任务拆解、意图识别、流程规划
- **工具**：task_dispatch, memory_search, context_compaction
- **通信**：与子节点异步消息队列
- **状态管理**：分布式状态机

#### 2. Agent Manager (智能体管理)
- **注册中心**：Agent Registry
- **健康检查**：心跳机制 (Heartbeat)
- **负载均衡**：动态调度
- **容错机制**：降级与重试

#### 3. Memory System (记忆系统)
- **短期记忆**：工作上下文 (Working Context)
- **长期记忆**：向量数据库 (LanceDB)
- **检索策略**：Embedding + Rerank
- **遗忘机制**：LRU + 重要性评分

#### 4. Tool Ecosystem (工具生态)
- **Web Search**：全网检索
- **Code Interpreter**：代码执行
- **Docker Client**：容器控制
- **File Operations**：文件管理

## 通信协议

### 节点间消息格式
```json
{
  "type": "TASK_DISPATCH",
  "from": "kakashi-controller",
  "to": "worker-code",
  "task_id": "uuid-v4",
  "payload": {
    "action": "docker_deploy",
    "params": {}
  },
  "priority": "P0",
  "deadline": "ISO8601-timestamp"
}
```

### 响应格式
```json
{
  "type": "TASK_RESULT",
  "task_id": "uuid-v4",
  "status": "success|failed|timeout",
  "result": {},
  "metadata": {
    "execution_time": 1234,
    "tokens_used": 5678
  }
}
```

## 部署架构

### Docker Compose 结构
```yaml
services:
  kakashi-controller:
    image: openclaw/controller:latest
    ports:
      - "18789:18789"
    environment:
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379

  worker-research:
    image: openclaw/research:latest
    depends_on:
      - kakashi-controller
    volumes:
      - ./data/research:/app/data

  worker-code:
    image: openclaw/code:latest
    depends_on:
      - kakashi-controller
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

## 配置管理

### 全局配置 (openclaw.json)
- 模型供应商配置
- 智能体列表定义
- 插件系统配置
- 网关端口设置

### 节点配置 (agent.json)
- 模型选择与参数
- 工具白名单
- 知识库路径
- 父节点关系

## 扩展指南

### 新增节点
1. 创建 `agents/{node-name}/` 目录
2. 编写 `agent.json` 和 `system_prompt.md`
3. 配置工具接口脚本
4. 在 `openclaw.json` 注册节点
5. 更新 Kakashi Controller 调度矩阵

### 自定义工具
1. 继承 `BaseTool` 基类
2. 实现 `execute(params)` 方法
3. 注册到工具仓库
4. 在 `agent.json` 声明工具权限
