# TypeScript 最佳实践指南

## 项目配置
- 启用 strict 模式
- 禁用 `any` 类型
- 设置 `noImplicitAny: true`
- 设置 `strictNullChecks: true`

## 类型定义
- 使用 interface 定义对象结构
- 使用 type 定义联合类型和元组
- 避免使用 `any`，使用 `unknown` 代替
- 使用 generics 提高代码复用性

## 函数设计
- 所有函数必须有返回类型注解
- 使用函数重载处理多种参数类型
- 使用可选参数而非函数重载
- 避免使用 `arguments` 对象

## React 组件
- 使用函数组件和 hooks
- 使用 `React.FC<Props>` 定义组件类型
- 使用 `useCallback` 优化性能
- 使用 `useMemo` 缓存计算结果

## 异步编程
- 使用 async/await 处理异步操作
- 使用 Promise 链式调用
- 使用 try/catch 处理错误
- 避免回调地狱

## 测试
- 使用 Jest 作为测试框架
- 使用 React Testing Library 测试组件
- 单元测试覆盖率 > 80%
- 使用 mock 隔离外部依赖

## 代码质量
- 使用 ESLint 检查代码质量
- 使用 Prettier 格式化代码
- 使用 husky 进行 git hooks
- 使用 commitlint 规范提交信息
