# GitHub 开源量化资源调研

> 更新时间: 2026-04-03

---

## 一、数据源类 (Data Acquisition)

### 1. AKShare ⭐⭐⭐⭐⭐
**地址**: https://github.com/akfamily/akshare
**语言**: Python 3.9+
**安装**: `pip install akshare --upgrade`
**镜像**: `pip install akshare -i http://mirrors.aliyun.com/pypi/simple/`
**特点**:
- 中文圈最流行的开源财经数据接口库
- 支持 A股/港股/美股/期货/期权/宏观 等全品类
- 一行代码获取数据，API 简洁优雅
- 示例: `ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date="20231022")`
- 示例: `ak.stock_us_daily(symbol="AAPL", adjust="qfq")`
- Docker: `docker run -it registry.cn-shanghai.aliyuncs.com/akfamily/aktools:jupyter python`
- 数据仅供学术研究，不构成投资建议

**覆盖范围**:
- A股: 日线/周线/月线/分钟线，支持复权
- 港股: 实时/历史行情
- 美股: 历史行情(复权)
- 宏观: CPI/PPI/M2/社融等
- 期货/期权/债券/外汇/贵金属

**适用场景**: 替换当前 `real_data_fetcher.py`，大幅简化数据获取逻辑

### 2. yfinance ⭐⭐⭐⭐
**地址**: https://github.com/ranaroussi/yfinance
**安装**: `pip install yfinance`
**特点**:
- Yahoo Finance 官方推荐 Python 库
- 覆盖全球主要股票/指数/ETF/期货
- 免费，无需 API Key
- 在国内网络可能需要 VPN 或代理

### 3. Qlib (微软) ⭐⭐⭐⭐
**地址**: https://github.com/microsoft/qlib
**语言**: Python
**安装**: `pip install pyqlib`
**特点**:
- 微软 AI 量化投资平台
- 支持监督学习/市场动态建模/强化学习多种范式
- 内置 RD-Agent: LLM驱动的自动化因子挖掘和模型优化
- 支持完整量化投研流程: 数据->因子->模型->回测->风控
- 提供了大量预训练模型和因子库
- 文档完善: https://qlib.readthedocs.io

**适用场景**: 如果后续需要 AI 因子挖掘或机器学习选股策略，可深度集成

### 4. OpenBB ⭐⭐⭐⭐
**地址**: https://github.com/OpenBB-finance/OpenBB
**安装**: `pip install openbb`
**特点**:
- 金融数据平台，面向分析师/量化/AI Agent
- "connect once, consume everywhere" 架构
- 支持 MCP Server (AI Agent 接入)
- 示例: `obb.equity.price.historical("AAPL")`
- 有商业版 OpenBB Workspace (企业级 UI)

**适用场景**: 如果需要 AI Agent 原生接入金融数据，OpenBB 的 MCP 支持值得关注

### 5. TA-Lib ⭐⭐⭐
**地址**: https://github.com/ta-lib/ta-lib-python (非官方 Python 封装)
**安装**: `pip install TA-Lib` (需先安装 C library)
**特点**:
- 技术分析指标工业标准库
- 200+ 技术指标 (MACD/RSI/布林带等)
- 计算性能高(Cython)

**适用场景**: 行情数据拿到后，技术面特征计算

---

## 二、框架/回测类

### 6. Backtrader ⭐⭐⭐⭐
**地址**: https://github.com/mementum/backtrader
**特点**: Python 量化回测老牌框架，文档丰富

### 7. Zipline (Quantopian) ⭐⭐⭐⭐
**地址**: https://github.com/stefan-jansen/zipline-reloaded (维护分支)
**特点**: Quantopian 开源的回测框架，支持美股

### 8. AkQuant ⭐⭐⭐⭐
**地址**: https://github.com/akfamily/akquant (AKFamily 出品)
**特点**:
- Rust 构建的极速撮合内核
- Python 链接数据与 AI 生态
- 高性能量化回测框架

---

## 三、学习资源

### awesome-quant (WilsonFreitas)
**地址**: https://github.com/wilsonfreitas/awesome-quant
**特点**: 量化资源大全，包含书单/论文/工具/策略

### financial-machine-learning (FirmAI)
**地址**: https://github.com/firmai/financial-machine-learning
**特点**: 金融机器学习实战资源集合

### Quantitative-Notebooks
**地址**: https://github.com/LongOnly/Quantitative-Notebooks
**特点**: 1.3k stars，量化金融教育笔记本

---

## 四、新闻数据源

### 1. stock_news_main_cx ⭐⭐⭐⭐⭐
**来源**: 财新 (Caixin)
**函数**: `ak.stock_news_main_cx()`
**返回**: 100条财经要闻 (tag/summary/url)
**字段**: tag(标签) / summary(摘要) / url(链接)
**耗时**: ~1秒
**覆盖**: 市场动态、华尔街原声、数据图解、行业分析

### 2. stock_news_em ⭐⭐⭐⭐
**来源**: 东方财富
**函数**: `ak.stock_news_em()`
**返回**: 10条个股新闻 (关键词/新闻标题/发布时间/文章来源)
**耗时**: ~1秒

### 3. news_economic_baidu ⭐⭐
**来源**: 百度经济新闻
**函数**: `ak.news_economic_baidu()`
**注意**: 需要 BAIDUID cookies，国内环境可能失效

### 4. 新浪财经新闻 ⭐⭐⭐
**来源**: 新浪财经
**方式**: `urllib` 直连 `hq.sinajs.cn`
**覆盖**: 实时行情附带新闻标题

**综合建议**: 优先使用 `stock_news_main_cx` (财新) + `stock_news_em` (东方财富)，两者互补，覆盖市场动态+个股新闻。

---

## 五、对本项目的建议

### 数据层 (短期优先级)
1. **优先接入 AKShare** — 替换当前 `real_data_fetcher.py`，大幅减少代码量
   - AKShare 的 `stock_zh_a_hist` / `stock_us_daily` / `stock_hk_spot` 等接口可直接覆盖港股/美股/A股
   - `macro_china` 系列接口可获取中国宏观数据

2. **保留 Eastmoney 作为备用** — 当 AKShare 不可用时的降级方案

### 分析层 (中期优先级)
3. **引入 TA-Lib** — 计算技术指标(Z-score/RSI/MACD等)
4. **Qlib RD-Agent** — 如果需要 AI 因子挖掘再用

### 架构层 (长期)
5. **OpenBB MCP** — 如果 OpenClaw 后续要接入 AI Agent 金融助手，OpenBB 的 MCP Server 是最好的桥接层

---

## 五、AKShare 快速接入计划

```python
# 替代 real_data_fetcher.py 的简化方案
import akshare as ak

# 美股历史
df_us = ak.stock_us_daily(symbol="AAPL", adjust="qfq")

# 港股历史
df_hk = ak.stock_hk_spot()  # 实时
df_hk_hist = ak.stock_hk_hist(symbol="00700", period="daily", start_date="20260301", end_date="20260403")

# A股宏观
df_cpi = ak.macro_china_cpi()  # 中国CPI
df_m2 = ak.macro_china_m2()    # M2

# 指数
df_index = ak.stock_zh_index_hist(symbol="000001", period="daily", start_date="20260301", end_date="20260403")
```

> 注意: AKShare 依赖网络状况，国内可能需要使用镜像源或备用数据源
