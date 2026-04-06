# Go 最佳实践指南

## 项目结构
```
project/
├── cmd/              # 可执行程序入口
├── internal/         # 内部包（不对外暴露）
├── pkg/              # 公共包
├── api/              # API 定义（protobuf/openapi）
├── config/           # 配置管理
├── migrations/       # 数据库迁移
└── tests/            # 测试文件
```

## 错误处理
- 显式检查错误，不使用 panic（生产环境）
- 使用 `errors.Is()` 和 `errors.As()` 进行错误判断
- 自定义错误类型时实现 `Error()` 方法
- 使用 `fmt.Errorf()` 添加上下文信息

## 接口设计
- 使用小接口（1-3 个方法）
- 接口定义在使用方，不在实现方
- 优先使用组合而非继承

## 并发模式
- 使用 goroutine 处理 I/O 密集任务
- 使用 channel 进行 goroutine 间通信
- 使用 sync.WaitGroup 等待 goroutine 完成
- 使用 context 控制超时和取消

## 性能优化
- 避免频繁的内存分配，使用对象池
- 使用 sync.Pool 缓存临时对象
- 避免在热路径中进行反射操作
- 使用 pprof 进行性能分析

## 测试
- 单元测试覆盖率 > 80%
- 使用 table-driven tests
- 使用 testify/assert 简化断言
- 使用 mock 隔离外部依赖

## 依赖管理
- 使用 go.mod 管理版本
- 定期运行 `go mod tidy`
- 避免循环依赖
- 使用 vendor 目录锁定依赖版本
