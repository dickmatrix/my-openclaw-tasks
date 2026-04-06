# Python 最佳实践指南

## 项目结构
```
project/
├── src/              # 源代码
├── tests/            # 测试
├── docs/             # 文档
├── requirements.txt  # 依赖
└── setup.py          # 包配置
```

## 类型提示
- 所有函数必须有类型提示
- 使用 `from typing import` 导入类型
- 使用 `Optional[T]` 表示可选类型
- 使用 `Union[T1, T2]` 表示多种类型

## 代码风格
- 遵循 PEP 8 规范
- 使用 black 格式化代码
- 使用 flake8 检查代码质量
- 使用 mypy 进行类型检查

## 数据结构
- 使用 dataclass 定义数据结构
- 使用 pydantic 进行数据验证
- 避免使用全局变量
- 使用 enum 定义常量

## 异步编程
- 使用 async/await 处理 I/O 密集任务
- 使用 asyncio 管理异步任务
- 使用 aiohttp 进行异步 HTTP 请求
- 避免在异步函数中进行阻塞操作

## 测试
- 使用 pytest 作为测试框架
- 单元测试覆盖率 > 80%
- 使用 pytest-mock 进行 mock
- 使用 pytest-asyncio 测试异步代码

## 依赖管理
- 使用 requirements.txt 或 poetry
- 定期更新依赖
- 使用虚拟环境隔离项目
- 避免依赖冲突
