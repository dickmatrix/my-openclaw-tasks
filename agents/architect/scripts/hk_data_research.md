# 港股历史数据方案调研

## 问题
Eastmoney 接口在国内被封，无法获取港股历史K线数据。

## 目标
找到可用的港股历史数据源，替代 Eastmoney。

## 方案对比

| 方案 | 来源 | 优点 | 缺点 |
|------|------|------|------|
| Sina 实时行情 | hq.sinajs.cn | 实时+免费 | 只有当日，无法获取历史 |
| Yahoo Finance | finance.yahoo.com | 港股覆盖全，免费 | 国内可能受限 |
| AKShare HK股票 | akshare stock_hk | Python集成 | 底层仍是Eastmoney |
| Tushare | tushare.pro | 数据全面 | 需要积分/注册 |
| 聚合数据 | juhe.cn | 国内可用 | 收费 |
| 炒饭社区 | moneyflow.streast.com | 免费 | 数据有限 |

## Yahoo Finance (yfinance)
- 港股代码: 0700.HK (腾讯)
- 支持多年历史日线数据
- Python: `yfinance` 库
- 国内访问: 可能需要代理

## 验证思路
```python
import yfinance as yf
data = yf.download("0700.HK", start="2023-01-01", end="2024-01-01")
```
