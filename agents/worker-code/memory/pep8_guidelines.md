# PEP 8 - Python 代码风格指南摘要

## 代码布局

### 缩进
- 使用 4 个空格缩进
- 行长度限制 79 字符（标准库强制）
- 多行结构：垂直对齐、悬挂缩进、4空格缩进

### 空行
- 顶级定义间两行空行
- 方法定义间一行空行
- 函数内逻辑段落间可空行分隔

### 导入
- 导入独占一行
- 分组顺序：标准库 > 第三方 > 本地
- 绝对导入优先，避免通配符导入

## 命名约定

### 变量与函数
- **函数/变量**：`lowercase_with_underscores`
- **类名**：`CapWords` (驼峰式)
- **常量**：`UPPERCASE_WITH_UNDERSCORES`

### 类属性
- `_protected`：单下划线前缀
- `__private`：双下划线前缀（名称改写）
- `__special__`：双下划线前后缀（魔术方法）

## 类型注解
```python
def func(arg1: Type1, arg2: Type2) -> ReturnType:
    pass

class Example:
    attr: int = 0
```

## 字符串引号
- 单引号优先：`'string'`
- 避免转义：`"This is a 'test'"`
- 三引号用于文档字符串

## 表达式与语句
- 避免显式 `== True`：`if is_valid:` 而非 `if is_valid == True:`
- 使用 `is not` 而非 `not ... is`：`if x is not None:`
- 否定成员测试：`if key not in d:` 而非 `if not key in d:`

## 注释规范
```python
# 单行注释：# 后空格
def complex_function():
    """多行文档字符串。
    
    Args:
        param1: 参数描述
        
    Returns:
        返回值描述
    """
    pass
```

## 自动化工具
- **flake8**：代码检查（Lint）
- **black**：代码格式化
- **isort**：导入排序
- **mypy**：类型检查
