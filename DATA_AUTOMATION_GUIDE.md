# 自动化数据采集与清洗闭环 - 完整实现指南

## 📋 项目概览

**项目名称**: Data Collection & Cleaning Automation System  
**目标**: 构建自动化的数据采集、清洗和验证闭环  
**核心组件**: Scout (数据猎人) + Writer (代码生成) + Auditor (自动验证)

---

## 🏗️ 系统架构

```
GitHub Issues (数据任务)
    ↓
Scout (数据猎人)
    ↓ #SCOUT_READY
Writer (代码生成)
    ↓ #WRITER_PATCHED
Auditor-Code (自动验证)
    ↓ #AUDIT_PASS
Vector DB (知识沉淀)
```

---

## 📁 项目结构

```
/Users/mac/Documents/龙虾相关/my_openclaw/
├── data_hunter/
│   ├── scripts/
│   │   └── data_hunter.py (数据猎人脚本)
│   ├── templates/
│   │   ├── data_validator.py (验证装饰器)
│   │   └── cleaning_rules.json (清洗规则)
│   ├── config/
│   │   └── workflow.json (工作流配置)
│   ├── logs/ (日志)
│   └── results/ (结果)
├── .github/
│   ├── workflows/
│   │   └── data_automation.yml (GitHub Actions)
│   └── ISSUE_TEMPLATE/
│       └── data_cleaning.md (Issue 模板)
└── vector_db/
    └── data_cleaning/ (知识库)
```

---

## 🚀 快速开始

### 1. 配置环境变量

```bash
export GITHUB_TOKEN=your_github_token
export OPENCLAW_WORKSPACE=/Users/mac/Documents/龙虾相关/my_openclaw
```

### 2. 运行数据猎人

```bash
python3 /Users/mac/Documents/龙虾相关/my_openclaw/data_hunter/scripts/data_hunter.py
```

### 3. 查看侦察报告

```bash
cat /Users/mac/Documents/龙虾相关/my_openclaw/data_hunter/results/scout_report_*.md
```

---

## 🔄 工作流程详解

### Phase 1: Scout 侦察 (#SCOUT_READY)

**职责**: 从 GitHub 发现数据采集和清洗任务

**执行步骤**:
1. 搜索 GitHub Issues (标签: data-cleaning, web-scraping, data-collection)
2. 分析任务类型和复杂度
3. 识别所需工具 (pandas, regex, requests 等)
4. 生成侦察报告

**输出**: `scout_report.md`

**示例**:
```
## 任务 #123: 清洗电商数据

- **类型**: data_cleaning
- **复杂度**: medium
- **所需工具**: pandas, regex
- **预计时间**: 1-2 hours
```

---

### Phase 2: Writer 代码生成 (#WRITER_PATCHED)

**职责**: 根据任务生成清洗脚本

**强制约束**:
1. 必须使用 `@validate_schema` 装饰器
2. 必须包含异常值处理 (`@handle_outliers`)
3. 必须定义数据 Schema

**生成的代码示例**:
```python
from data_validator import validate_schema, handle_outliers
import pandas as pd

@validate_schema({
    'id': 'int',
    'name': 'str',
    'price': 'float'
})
@handle_outliers(method='drop')
def clean_ecommerce_data(df: pd.DataFrame) -> pd.DataFrame:
    # 移除重复行
    df = df.drop_duplicates()
    
    # 文本规范化
    df['name'] = df['name'].str.lower().str.strip()
    
    # 价格验证
    df = df[df['price'] > 0]
    
    return df
```

---

### Phase 3: Auditor 自动验证 (#AUDIT_PASS)

**职责**: 在沙箱中执行和验证代码

**验证项目**:
1. ✅ 语法检查 (Python 编译)
2. ✅ Schema 验证 (数据结构)
3. ✅ 输出验证 (CSV/JSON 有效性)
4. ✅ 性能检查 (成功率 ≥ 95%)

**成功标准**:
```json
{
  "tests_pass": true,
  "schema_valid": true,
  "output_exists": true,
  "success_rate": 0.95
}
```

---

### Phase 4: 知识沉淀

**职责**: 将清洗规则保存到向量库

**保存内容**:
- 正则表达式模板
- 反爬策略
- 清洗规则
- 异常处理逻辑

**存储位置**: `/Users/mac/Documents/龙虾相关/my_openclaw/vector_db/data_cleaning/`

---

## 🔧 配置详解

### workflow.json

```json
{
  "stages": [
    {
      "name": "Scout Hunting",
      "agent": "Scout",
      "trigger": "schedule:daily:09:00",
      "success_marker": "#SCOUT_READY"
    },
    {
      "name": "Code Generation",
      "agent": "Writer",
      "constraints": [
        "must_use_data_validator",
        "must_include_schema_check",
        "must_handle_outliers"
      ],
      "success_marker": "#WRITER_PATCHED"
    },
    {
      "name": "Automated Testing",
      "agent": "Auditor-Code",
      "success_criteria": {
        "tests_pass": true,
        "success_rate": 0.95
      },
      "success_marker": "#AUDIT_PASS"
    }
  ],
  "parallelization": {
    "enabled": false,
    "max_concurrent": 1,
    "reason": "防止爬虫 IP 被封禁"
  }
}
```

---

## 📊 GitHub Actions 工作流

### 自动化触发

**时间表**: 每天 09:00 UTC

**执行步骤**:
1. 检出代码
2. 安装 Python 依赖
3. 运行数据猎人
4. 上传侦察报告
5. 提交结果到 GitHub

### 手动触发

```bash
# 在 GitHub Actions 中手动运行
# 或使用 CLI:
gh workflow run data_automation.yml
```

---

## 📝 创建数据清洗任务

### 使用 GitHub Issue 模板

1. 访问 GitHub 仓库
2. 点击 "Issues" → "New Issue"
3. 选择 "Data Cleaning Task" 模板
4. 填写任务信息

### Issue 模板字段

```markdown
## 任务描述
清洗电商平台的产品数据

## 数据源
https://example.com/products.csv

## 清洗需求
- [x] 移除重复行
- [x] 处理缺失值
- [x] 文本规范化
- [x] 异常值处理

## 预期输出格式
CSV

## 优先级
High
```

---

## 🎯 使用示例

### 示例 1: 清洗 CSV 数据

**Issue**:
```
标题: [Data Cleaning] 清洗销售数据
标签: data-cleaning
```

**Scout 发现** → **Writer 生成**:
```python
@validate_schema({
    'date': 'str',
    'product': 'str',
    'quantity': 'int',
    'price': 'float'
})
@handle_outliers(method='drop')
def clean_sales_data(df):
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['quantity'] > 0]
    df = df[df['price'] > 0]
    return df
```

**Auditor 验证** → **成功** ✅

---

### 示例 2: 网页爬取和清洗

**Issue**:
```
标题: [Data Cleaning] 爬取并清洗新闻数据
标签: web-scraping, data-cleaning
```

**Scout 发现** → **Writer 生成**:
```python
import requests
from bs4 import BeautifulSoup
import pandas as pd

@validate_schema({
    'title': 'str',
    'url': 'str',
    'date': 'str'
})
def scrape_and_clean_news():
    # 爬取逻辑
    # 清洗逻辑
    return df
```

**Auditor 验证** → **成功** ✅

---

## 🔍 监控和调试

### 查看日志

```bash
# Scout 日志
tail -f /Users/mac/Documents/龙虾相关/my_openclaw/data_hunter/logs/hunt_*.log

# GitHub Actions 日志
gh run view --log
```

### 查看结果

```bash
# 侦察报告
ls -la /Users/mac/Documents/龙虾相关/my_openclaw/data_hunter/results/

# 向量库
ls -la /Users/mac/Documents/龙虾相关/my_openclaw/vector_db/data_cleaning/
```

---

## 📈 性能指标

### 目标

- **成功率**: ≥ 95%
- **平均处理时间**: < 2 小时
- **知识库规模**: > 100 条规则

### 监控

```bash
# 查看统计信息
python3 -c "
import json
import os

results_dir = '/Users/mac/Documents/龙虾相关/my_openclaw/data_hunter/results'
reports = [f for f in os.listdir(results_dir) if f.endswith('.md')]
print(f'总报告数: {len(reports)}')
"
```

---

## 🛠️ 故障排查

### 问题 1: Scout 找不到任务

**原因**: GitHub Token 无效或权限不足

**解决**:
```bash
gh auth logout
gh auth login
export GITHUB_TOKEN=$(gh auth token)
```

### 问题 2: Writer 生成的代码有错误

**原因**: 约束条件未满足

**检查**:
- 是否使用了 `@validate_schema`?
- 是否包含了 `@handle_outliers`?
- Schema 定义是否正确?

### 问题 3: Auditor 验证失败

**原因**: 数据格式不符合预期

**调试**:
```bash
# 查看详细错误
python3 cleaning_script.py --debug

# 检查输出文件
head -20 output.csv
```

---

## 📚 最佳实践

### 1. 定义清晰的 Schema

```python
schema = {
    'id': 'int',           # 主键
    'name': 'str',         # 产品名称
    'price': 'float',      # 价格
    'created_at': 'str'    # 创建时间
}
```

### 2. 使用装饰器强制验证

```python
@validate_schema(schema)
@handle_outliers(method='drop')
def clean_data(df):
    return df
```

### 3. 记录清洗步骤

```python
def clean_data(df):
    print(f"原始数据: {len(df)} 行")
    df = df.drop_duplicates()
    print(f"去重后: {len(df)} 行")
    df = df.dropna()
    print(f"去空值后: {len(df)} 行")
    return df
```

### 4. 定期审查知识库

```bash
# 查看已保存的规则
ls -la /Users/mac/Documents/龙虾相关/my_openclaw/vector_db/data_cleaning/
```

---

## 🎓 学习资源

- [Pandas 文档](https://pandas.pydata.org/docs/)
- [正则表达式教程](https://regex101.com/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [OpenClaw 文档](https://openclaw.dev/)

---

## 📞 支持

遇到问题？

1. 查看本指南的故障排查部分
2. 检查日志文件
3. 查看 GitHub Issues
4. 联系技术支持

---

**最后更新**: 2026-03-29  
**版本**: 1.0.0  
**状态**: ✅ 生产就绪
