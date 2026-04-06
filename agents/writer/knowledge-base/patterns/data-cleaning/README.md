# 数据清洗（Data Cleaning）模式库

> 整理自 GitHub Topics + 主流开源项目调研，2026-03-30

## 目录

- [概述](#概述)
- [去重策略](#去重策略)
- [标准化](#标准化)
- [异常值检测](#异常值检测)
- [字段推断与类型转换](#字段推断与类型转换)
- [参考工具](#参考工具)

---

## 概述

数据清洗是非标工作中最核心的环节。输入数据往往：
- 来源杂（DB/API/文件/爬虫）
- 格式乱（JSON/XML/CSV/Excel/PDF混在一起）
- 边界多（缺失值、格式不一致、噪声数据）

清洗的目标：输出一致、可靠、可直接用于下游的数据。

---

## 去重策略

去重是最常见需求，但"重复"的定义因场景而异：

### 精确去重

```python
# 基于主键/唯一标识符
df.drop_duplicates(subset=["id"], keep="first")

# SQL 风格
DELETE FROM target WHERE id IN (
  SELECT id, MAX(ctid) FROM source GROUP BY id HAVING COUNT(*) > 1
)
```

### 模糊去重（近似重复）

```python
# SimHash / MinHash — 文本相似度去重
from datasketch import MinHash, MinHashLSH

def minhash_dedup(texts, threshold=0.8):
    lsh = MinHashLSH(threshold=threshold, num_perm=128)
    buckets = {}
    for i, text in enumerate(texts):
        m = MinHash()
        for word in text.split():
            m.update(word.encode('utf8'))
        lsh.insert(i, m)
        for j in lsh.query(m):
            if j < i:
                yield (j, i)  # 近似重复对
```

### 指纹去重

```python
# Simpler fingerprint approach
import hashlib

def fingerprint(record):
    # 基于关键字段生成指纹
    raw = f"{record['name']}|{record['phone']}|{record['email']}"
    return hashlib.md5(raw.encode()).hexdigest()

# 全局去重
seen = set()
for record in records:
    fp = fingerprint(record)
    if fp not in seen:
        seen.add(fp)
        yield record
```

### 场景选择建议

| 场景 | 推荐策略 |
|------|---------|
| 数据库主键去重 | 精确匹配（SQL DISTINCT / GROUP BY） |
| 用户数据去重 | 指纹（name+phone+email组合hash） |
| 文本/文章去重 | MinHash / SimHash |
| 图片去重 | pHash（感知哈希）|
| 日志流去重 | 滑动窗口 + 布隆过滤器 |

---

## 标准化

### 日期时间标准化

```python
from dateutil import parser
from zoneinfo import ZoneInfo
import pandas as pd

def parse_date(value, target_tz="UTC"):
    """智能解析各种日期格式并标准化"""
    if pd.isna(value):
        return None
    dt = parser.parse(str(value), fuzzy=True)
    dt = dt.astimezone(ZoneInfo(target_tz))
    return dt.isoformat()

# 示例输入 → 输出
# "2026/03/30"       → "2026-03-30T00:00:00+00:00"
# "Mar 30, 2026"     → "2026-03-30T00:00:00+00:00"
# "2026-03-30T02:45" → "2026-03-30T02:45:00+00:00"
```

### 字符串标准化

```python
import unicodedata
import re

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    # Unicode NFKC 归一化
    text = unicodedata.normalize("NFKC", text)
    # 全角转半角
    text = text.translate(str.maketrans(
        'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ))
    # 去除控制字符
    text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C' or ch in '\n\t')
    # 合并多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_phone(phone):
    """手机号标准化：保留区号+本地号码"""
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) == 11 and digits[0] == '1':
        return f"+86-{digits}"  # 中国手机号
    return digits

def normalize_email(email):
    return normalize_text(email).lower().strip()
```

### 编码处理

```python
def safe_decode(bytes_value, encodings=["utf-8", "gbk", "gb2312", "latin-1"]):
    """尝试多种编码安全解码"""
    for enc in encodings:
        try:
            return bytes_value.decode(enc)
        except (UnicodeDecodeError, AttributeError):
            continue
    return bytes_value.decode("utf-8", errors="replace")
```

---

## 异常值检测

```python
import numpy as np
from scipy import stats

def detect_outliers_iqr(series, factor=1.5):
    """IQR（四分位距）方法，适合非正态分布数据"""
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return series[(series < lower) | (series > upper)]

def detect_outliers_zscore(series, threshold=3):
    """Z-score 方法，适合近似正态分布数据"""
    z = np.abs(stats.zscore(series.dropna()))
    return series[z > threshold]

def detect_outliers_modified_zscore(series, threshold=3.5):
    """Modified Z-score（MAD），对离群值更鲁棒"""
    median = series.median()
    mad = (series - median).abs().median()
    if mad == 0:
        return series * 0  # 全部相同值，无离群点
    modified_z = 0.6745 * (series - median) / mad
    return series[abs(modified_z) > threshold]
```

### 规则驱动检测

```python
RULES = {
    "email": lambda v: bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str(v))),
    "phone_cn": lambda v: bool(re.match(r'^1[3-9]\d{9}$', str(v))),
    "ipv4": lambda v: bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', str(v))),
    "url": lambda v: bool(re.match(r'^https?://', str(v))),
    "positive_int": lambda v: isinstance(v, int) and v > 0,
}

def validate_field(value, field_type):
    """根据类型校验字段合法性"""
    validator = RULES.get(field_type, lambda v: True)
    return validator(value)
```

---

## 字段推断与类型转换

```python
from ast import literal_eval
import json

def infer_and_convert(value):
    """智能推断并转换字段类型"""
    if value is None or value == "" or str(value).lower() in ("null", "none", "na", "n/a"):
        return None, "null"
    
    s = str(value).strip()
    
    # 布尔值
    if s.lower() in ("true", "yes", "1", "on"):
        return True, "boolean"
    if s.lower() in ("false", "no", "0", "off"):
        return False, "boolean"
    
    # 数字
    try:
        if "." in s:
            return float(s), "float"
        return int(s), "integer"
    except ValueError:
        pass
    
    # JSON / 嵌套结构
    if s.startswith(("{", "[")):
        try:
            return literal_eval(s), "object"
        except Exception:
            try:
                return json.loads(s), "object"
            except Exception:
                pass
    
    # 日期（智能解析在标准化章节）
    return s, "string"

def auto_schema(df, sample_size=1000):
    """从 DataFrame 样本自动推断 schema"""
    sample = df.head(sample_size)
    schema = {}
    for col in df.columns:
        types = [infer_and_convert(v)[1] for v in sample[col] if pd.notna(v)]
        majority = max(set(types), default="string")
        schema[col] = majority
    return schema
```

---

## 参考工具

| 工具 | 用途 | 语言 |
|------|------|------|
| [datajuicer/data-juicer](https://github.com/datajuicer/data-juicer) | 大模型数据清洗 pipeline | Python |
| [whylabs/whylogs](https://github.com/whylabs/whylogs) | 数据质量日志，可视化统计 | Python |
| [pandas](https://github.com/pandas-dev/pandas) | 表格数据清洗基础库 | Python |
| [ Apache Arrow / Parquet](https://github.com/apache/arrow) | 列式存储，分析友好 | C++/Python |
| [Ruff](https://github.com/astral-sh/ruff) / [polars](https://github.com/pola-rs/polar) | 高性能 DataFrame | Rust |

---

*维护者：Writer Agent | 更新：2026-03-30*
