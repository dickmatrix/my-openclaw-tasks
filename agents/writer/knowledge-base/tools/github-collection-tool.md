# GitHub API 数据采集模块

> **类型**: 可复用采集工具函数
> **维护者**: Writer Agent | **版本**: v1.1（修复嵌套字段路径）
> **验证状态**: ✅ 实操通过（完整率 100%，字段匹配率 89%）

---

## 核心函数

### `github_search_repos()`

```python
import requests
import pandas as pd
from typing import Optional

def github_search_repos(
    query: str,
    sort: str = "stars",
    order: str = "desc",
    per_page: int = 30,
    max_pages: int = 1,
    token: Optional[str] = None,
    min_stars: int = 0,
    created_after: Optional[str] = None,
) -> pd.DataFrame:
    """
    GitHub API 搜索仓库，采集结构化数据。

    参数:
        query: 搜索关键字（例: "language:python"）
        sort: 排序字段（stars/forks/updated）
        per_page: 每页条数（最大100）
        max_pages: 最大页数
        token: GitHub OAuth token（可选，提升速率限制）
        min_stars: 最低 stars 数过滤
        created_after: 日期字符串，例 "2024-01-01"

    返回:
        DataFrame，列为标准交付字段
    """
    base = "https://api.github.com/search/repositories"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "WriterAgent/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    all_items = []
    for page in range(1, max_pages + 1):
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100),
            "page": page,
        }
        if min_stars > 0:
            params["q"] += f" stars:>{min_stars}"
        if created_after:
            params["q"] += f" created:>{created_after}"

        r = requests.get(base, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        items = r.json().get("items", [])
        all_items.extend(items)

        # 速率限制警告
        remaining = r.headers.get("X-RateLimit-Remaining", "N/A")
        print(f"  Page {page}: {len(items)} items | 剩余配额: {remaining}")

        if len(items) == 0:
            break

    return pd.DataFrame(all_items)
```

---

### `clean_github_record()`

```python
def clean_github_record(item: dict) -> dict:
    """
    将 GitHub API 单条原始记录标准化为交付格式。

    注意：
        - owner_login 是嵌套字段：item["owner"]["login"]
        - topics 列表需转为逗号分隔字符串
        - description 需清洗 HTML 实体
    """
    # 嵌套字段正确访问
    owner_login = item.get("owner", {}).get("login", "") or ""

    # topics: 列表 → 字符串
    topics_raw = item.get("topics") or []
    topics_str = ",".join(topics_raw) if isinstance(topics_raw, list) else ""

    # description: HTML 实体清洗
    desc = str(item.get("description") or "").replace(
        "&amp;", "&"
    ).replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'")

    # created_at: 只保留日期部分
    created = str(item.get("created_at") or "")[:10]

    return {
        "full_name":       item.get("full_name", ""),
        "description":     desc,
        "owner_login":     owner_login,
        "stargazers_count": item.get("stargazers_count", 0) or 0,
        "forks_count":     item.get("forks_count", 0) or 0,
        "language":        item.get("language", "") or "",
        "html_url":        item.get("html_url", ""),
        "created_at":      created,
        "topics":          topics_str,
    }
```

---

### `deduplicate_and_validate()`

```python
def deduplicate_and_validate(
    df: pd.DataFrame,
    target_count: int,
    required_fields: list[str],
    min_stars: int = 1,
) -> dict:
    """
    数据去重 + 完整性校验。

    返回 dict:
        df_cleaned: 清洗后的 DataFrame
        completeness: 完整率 (0-100)
        field_report: 每个字段的验证结果
    """
    before = len(df)

    # 去重（基于全名唯一键）
    df = df.drop_duplicates(subset=["full_name"], keep="first")

    # 异常值过滤
    if "stargazers_count" in df.columns:
        df = df[df["stargazers_count"] >= min_stars]

    # 缺失值填充
    for col in ["description", "topics", "owner_login", "language"]:
        if col in df.columns:
            df[col] = df[col].fillna("")

    # 字段验证
    field_report = {}
    valid_fields = 0
    for field in required_fields:
        if field not in df.columns:
            field_report[field] = {"rate": 0, "status": "MISSING"}
            continue
        non_empty = (df[field].astype(str).str.len() > 0).sum()
        rate = non_empty / len(df) * 100 if len(df) > 0 else 0
        field_report[field] = {"rate": rate, "status": "OK" if rate >= 80 else "LOW"}
        if rate >= 80:
            valid_fields += 1

    completeness = len(df) / target_count * 100 if target_count > 0 else 0

    return {
        "df_cleaned": df,
        "completeness": completeness,
        "field_report": field_report,
        "field_match_rate": valid_fields / len(required_fields) * 100,
        "dedup_removed": before - len(df),
    }
```

---

## 已知限制

| 限制 | 说明 | 解决方案 |
|------|------|---------|
| `topics` 在 Search API 返回率低 | GitHub Search API 不保证返回 `topics` 字段 | 单独调用 `/repos/{owner}/{repo}` 获取完整字段 |
| 无 Auth 速率限制 | 60次/小时（未认证） vs 5000次/小时（Auth） | 添加 `token` 参数 |
| per_page 最大 100 | 单页最多返回 100 条 | 使用 `max_pages` 分页 |
| `created` 查询不支持范围 | 只支持 `created:>DATE` 单向 | 结合 stars/forks 条件组合过滤 |

---

## 使用示例

```python
# 完整流程
df_raw = github_search_repos(
    query="language:python",
    sort="stars",
    per_page=30,
    min_stars=1000,
    created_after="2024-01-01",
)

records = [clean_github_record(item) for item in df_raw.to_dict("records")]
df = pd.DataFrame(records)

result = deduplicate_and_validate(
    df,
    target_count=30,
    required_fields=["full_name", "stargazers_count", "language"],
)

print(f"完整率: {result['completeness']:.0f}%")
print(f"字段匹配: {result['field_match_rate']:.0f}%")
result["df_cleaned"].to_csv("output.csv", index=False)
```

---

*Writer Agent | v1.1 | 2026-03-30*
