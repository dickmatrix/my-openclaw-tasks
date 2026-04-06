# 数据采集（Data Collection）模式库

> 整理自 GitHub Topics + 主流开源项目调研，2026-03-30

## 目录

- [概述](#概述)
- [场景分类](#场景分类)
- [核心技术栈](#核心技术栈)
- [采集模式](#采集模式)
- [反爬与容错](#反爬与容错)
- [参考项目](#参考项目)

---

## 概述

数据采集分为三大类：
1. **主动采集** — 主动请求数据源（API / HTTP爬虫 / 数据库直连）
2. **被动采集** — 监听数据流（CDC / Webhook / 消息队列）
3. **文件采集** — 批量处理静态文件（CSV / Excel / PDF /parquet）

---

## 场景分类

| 场景 | 工具/框架 | 语言 |
|------|----------|------|
| 通用网页爬虫 | Scrapy, Crawlee, Firecrawl, Scrapling | Python/TS |
| 浏览器自动化 | SeleniumBase, Playwright, Puppeteer | Python/JS |
| API聚合ETL | Airbyte, Airflow, Dagster, Pathway | Python |
| 增量CDC | Debezium, Flink CDC | Java/Scala |
| 流式摄取 | Vector, Memphis, Redpanda Connect | Rust/Go |
| 无代码爬取 | Maxun, changedetection.io | TS/Python |
| AI数据提取 | ScrapeGraphAI, Data-Juicer | Python |
| 数据库迁移 | Ingestr, CloudQuery, Steampipe | Go/Python |

---

## 核心技术栈

### Python 生态
- **Scrapy** — 最成熟的通用爬虫框架，支持异步、分布式（Scrapy-Redis）
- **Scrapling** — 自适应爬取，自动处理动态/静态页面
- **Playwright / SeleniumBase** — 浏览器自动化，处理 JS 渲染
- **Airflow / Dagster / Mage** — 工作流编排，ETL 调度
- **Pathway** — 实时流处理 ETL，专为 LLM/RAG 设计
- **Data-Juicer** — 面向大模型的数据处理清洗

### Go 生态
- **Crawlee-Python** 对应 **go-streams** — 轻量流处理
- **Rudder-server** — 隐私优先的事件采集
- **Memphis** — 高性能消息队列 + 摄取层
- **CloudQuery** — 云配置 / SaaS 数据导出
- **Redpanda Connect** — 现代 Kafka 替代品，连接器丰富

### TypeScript 生态
- **Crawlee** — Node.js 端爬虫框架，支持 Puppeteer/Playwright/Cheerio
- **Firecrawl** — 整站转 LLM-ready markdown / 结构化数据
- **Maxun** — 无代码爬取平台，开源

---

## 采集模式

### 1. 增量采集（Incremental）
```python
# 伪代码：基于时间戳/版本号的增量判断
last_run = get_last_run_timestamp()
new_records = query(f"SELECT * FROM source WHERE updated_at > {last_run}")
upsert_to_target(new_records)
update_last_run_timestamp(now)
```

### 2. CDC（Change Data Capture）
```java
// Debezium 监听 MySQL binlog
// Debeziumconnector → Kafka → Flink CDC → Target
// 优势：近实时、零侵入、支持全量+增量
```

### 3. 爬虫分类
```
┌─────────────────────────────────────────────┐
│           深度优先（DFS）爬取                │
│  适用：sitemap 已知、层级明确                │
├─────────────────────────────────────────────┤
│           广度优先（BFS）爬取                │
│  适用：发现新页面、链接结构未知              │
├─────────────────────────────────────────────┤
│           聚焦爬取（Focused Crawling）       │
│  适用：只采集特定主题/域名的页面             │
└─────────────────────────────────────────────┘
```

### 4. API 采集策略
```
限流应对：指数退避 + 令牌桶
认证方式：API Key / OAuth2 / JWT
分页处理：cursor-based > offset-based（稳定性更高）
错误处理：4xx → 停；5xx → 重试；429 → 降速
```

---

## 反爬与容错

### 常见反爬机制及应对

| 反爬类型 | 应对策略 |
|---------|---------|
| IP 限流 | 代理池轮换（ScrapingAnt, Oxylabs） |
| UA 检测 | 随机 UA + 真实浏览器指纹 |
| 验证码 | 第三方打码平台 / 机器学习识别 |
| 动态 JS 渲染 | Playwright/Selenium 模拟浏览器 |
| 请求频率限制 | 令牌桶 + 指数退避 |
| 登录墙 | Cookie 复用 / Session 维持 |

### 容错设计
```python
class ResilientFetcher:
    def fetch(self, url, retries=3):
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response
            except (Timeout, ConnectionError) as e:
                wait = 2 ** attempt + random.uniform(0, 1)
                time.sleep(wait)
            except HTTPError as e:
                if e.response.status_code < 500:
                    raise  # 客户端错误不重试
                wait = 2 ** attempt
                time.sleep(wait)
        raise MaxRetriesExceeded(url)
```

---

## 参考项目

### 采集框架
| 项目 | Stars | 特点 |
|------|-------|------|
| [scrapy/scrapy](https://github.com/scrapy/scrapy) | 55k+ | Python 爬虫工业标准 |
| [apify/crawlee](https://github.com/apify/crawlee) | 15k+ | Node.js 全能爬虫，支持浏览器自动化 |
| [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | 20k+ | 整站 LLM-ready markdown 提取 |
| [scrapy/scrapling](https://github.com/D4Vinci/Scrapling) | 1k+ | 自适应爬取，handle 各种页面结构 |
| [scrapegraphai/scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai) | 15k+ | AI 驱动爬虫，用 LLM 理解页面结构 |

### ETL / 数据管道
| 项目 | Stars | 特点 |
|------|-------|------|
| [airbytehq/airbyte](https://github.com/airbytehq/airbyte) | 25k+ | 开源 ETL 平台，连接器最全 |
| [dagster-io/dagster](https://github.com/dagster-io/dagster) | 15k+ | 数据资产编排，可观测性强 |
| [vectordotdev/vector](https://github.com/vectordotdev/vector) | 20k+ | Rust 实现高性能日志/指标管道 |
| [pathwaycom/pathway](https://github.com/pathwaycom/pathway) | 10k+ | Python 实时 ETL，专为 LLM/RAG 设计 |
| [redpanda-data/connect](https://github.com/redpanda-data/connect) | 5k+ | 流处理，BentoML 生态集成 |
| [cloudquery/cloudquery](https://github.com/cloudquery/cloudquery) | 15k+ | 云配置/SaaS 数据导出，Go 实现 |

### 数据质量
| 项目 | Stars | 特点 |
|------|-------|------|
| [whylabs/whylogs](https://github.com/whylabs/whylogs) | 5k+ | 数据日志/质量监控，ML 友好 |
| [elementary-data/elementary](https://github.com/elementary-data/elementary) | 5k+ | dbt 原生数据可观测性 |
| [datajuicer/data-juicer](https://github.com/datajuicer/data-juicer) | 5k+ | 大模型数据处理清洗 |

---

*维护者：Writer Agent | 更新：2026-03-30*
