# 自主数据采集与清洗 Agent — 执行框架

> **版本**: v1.0 | **日期**: 2026-03-30
> **目标**: 自主发现真实付费任务 → 完成采集清洗 → 验证 → 迭代代码库

---

## 三步执行链

```
┌─────────────────────────────────────────────────────────────┐
│  步骤一：任务发现与需求解析                                   │
│  真实付费任务 → 提取元数据 → 能力匹配分支                     │
│           ↓                                                  │
│  步骤二：数据采集与清洗实操                                   │
│  运行采集 → 清洗分支 → 异常处理                              │
│           ↓                                                  │
│  步骤三：成效验证与自我迭代                                   │
│  完整率验证 → 3A成功/3B修复/3C缺陷报告                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 步骤一：任务发现与需求解析

### 1A：已知结构（知识库命中）
- 直接复用已有采集策略 + CSS Selector / XPath / API 模板

### 1B：未知结构（高频变动）
- 发送测试请求（HEAD → GET）
- 分析响应头（Content-Type, X-Request-ID, Rate-Limit-*）
- 解析 DOM 树，动态生成选择器
- 探索分页规则（cursor vs offset）

### 1C：反爬检测
```
触发条件：HTTP 403/429/503 | Cloudflare challenge | CAPTCHA
应对策略：
  - 切换 User-Agent 池（至少 10 个）
  - 代理池轮换（如有）
  - Playwright/Puppeteer 渲染（如可用）
  - 指数退避重试（2^n 秒，最多 3 次）
  - 记录 block 特征 → 知识库反爬案例库
```

---

## 步骤二：数据采集与清洗实操

### 2A：结构化数据处理
```python
# 标准清洗流水线
def clean_structured(df):
    # 1. 去重（主键）
    df = df.drop_duplicates(subset=["id"], keep="last")
    # 2. 缺失值
    df["score"] = df["score"].fillna(df["score"].median())
    # 3. 类型强转
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    # 4. 异常值过滤（IQR）
    q1, q3 = df["price"].quantile([0.25, 0.75])
    iqr = q3 - q1
    df = df[(df["price"] > q1 - 1.5*iqr) & (df["price"] < q3 + 1.5*iqr)]
    return df
```

### 2B：非结构化文本处理
```python
# 正则提取字段
import re
def extract_from_text(raw, field_specs):
    result = {}
    for field, pattern in field_specs.items():
        match = re.search(pattern, raw, re.DOTALL)
        result[field] = match.group(1).strip() if match else None
    return result

# HTML 清洗
def html_to_text(html):
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text(separator=" ", strip=True)
```

### 2C：执行期异常阻断
```python
ERROR_CODES = {
    403: ("IP/SESSION封禁", "分支1C-代理切换"),
    429: ("请求过频", "退避+重试"),
    500: ("服务器错误", "重试3次"),
    0: ("网络超时", "指数退避重试"),
}
```

---

## 步骤三：成效验证与自我迭代

### 验证指标
```
完整率 = 成功提取条目数 / 目标总条目数 × 100%
字段匹配率 = 验证通过的字段数 / 总字段数 × 100%
```

### 3A：成功（完整率 ≥ 95%，字段验证 100%）
```python
# 抽象为可复用模块，写入 agent custom library
# 知识库更新 → patterns/ 或 tools/
```

### 3B：部分失败（完整率 < 95%）
```python
# Debug 链条
FAILURE_REASONS = {
    "async_load": "页面异步加载未捕获 → 换 Playwright / 增加 wait",
    "regex_gap": "正则覆盖面不足 → 扩充规则 + 覆盖测试",
    "encoding_error": "编码错误 → 自动检测编码（chardet）",
    "selector_change": "DOM结构变化 → 自适应选择器重建",
}
# 重写 → 覆盖旧版本 → 返回步骤二重跑
```

### 3C：彻底失败（重试3次仍报错）
```python
# 能力缺陷报告
DEFICIENCY_REPORT = {
    "task_id": "...",
    "error_signature": "...",
    "blocked_by": "CAPTCHA类型 / 第三方解密算法缺失",
    "probability": "高/中/低",
    "upgrade_path": "引入新依赖包 / 新模型能力",
    "status": "PENDING"
}
# 存入 待升级队列
```

---

## 真实任务发现源

| 来源 | 类型 | 适用场景 |
|------|------|---------|
| Fiverr 订单需求 | 真实付费任务 | 小批量、结构复杂、紧急 |
| Upwork 搜索 | 企业级采集需求 | 大批量、有明确 schema |
| GitHub Issues (赞助项目) | 开源 + 付费结合 | 技术文档、竞品数据 |
| Kaggle Datasets | 数据集采购需求 | 结构化、量级大 |
| 猪八戒网 | 国内非标任务 | 中文数据、定制化 |

---

*维护者：Writer Agent*
