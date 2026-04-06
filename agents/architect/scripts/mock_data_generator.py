#!/usr/bin/env python3
"""
mock_data_generator.py
阶段一：生成30年历史基准数据 (1995-01-01 ~ 2025-03-31)
- macro_indicators.csv  : 全球宏观基准
- market_data.csv      : 美股/港股历史行情
- cycle_vectors.json   : 历史特征向量库
输出目录: mock_data/
"""

import json
import csv
import os
import math
import random
from datetime import date, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "mock_data")
os.makedirs(DATA_DIR, exist_ok=True)

random.seed(42)  # 固定种子，保证可复现

# ========== 配置 ==========
START_DATE = date(1995, 1, 1)
END_DATE   = date(2025, 3, 31)
VECTOR_DIM = 64  # 简化：64维向量（真实场景1536维）

US_TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN"]
HK_TICKERS = ["0700.HK", "3690.HK", "9988.HK", "1810.HK", "2382.HK"]
INDICATORS = [
    ("FEDFUNDS",   "US"),   # 联邦基金利率
    ("CPI",        "US"),   # 消费者物价指数
    ("M2",         "US"),   # 货币供应量M2
    ("GOLD",       "GLD"),  # 黄金现货价
    ("OIL",        "OIL"),  # 原油
    ("COPPER",     "CPR"),  # 铜
    ("EURUSD",     "EU"),   # 欧元汇率
    ("HIBOR",      "HK"),   # 港币HIBOR
]

# ========== 工具函数 ==========

def date_range(start, end):
    days = []
    d = start
    while d <= end:
        days.append(d)
        d += timedelta(days=1)
    return days

def random_walk(start_val, volatility, trend=0, min_val=None, max_val=None):
    """生成随机游走序列"""
    val = start_val
    values = []
    for _ in range(total_days()):
        val = val + random.gauss(trend, volatility)
        if min_val is not None:
            val = max(min_val, val)
        if max_val is not None:
            val = min(max_val, val)
        values.append(val)
    return values

def total_days():
    return (END_DATE - START_DATE).days + 1

def biz_days_between(start, end):
    """返回范围内的交易日（周一~周五）"""
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days

def embedding_to_vector(*args):
    """将多个标量特征压缩为一个随机种子，再扩展为向量"""
    seed = int(sum(abs(v) * 1000 for v in args)) % (2**31)
    rng = random.Random(seed)
    return [rng.gauss(0, 1) for _ in range(VECTOR_DIM)]

# ========== 1. 生成宏观指标 ==========

def generate_macro_indicators():
    """生成30年宏观指标日频数据"""
    cal = date_range(START_DATE, END_DATE)
    
    # 用少量关键时间节点做随机游走锚点，避免每天完全随机
    anchor_count = 120  # 大约每3个月一个锚点
    anchor_step = total_days() // anchor_count
    
    # 全局参数游走
    fed_funds  = 5.0
    cpi_val    = 2.5
    m2_val     = 11000
    gold_val   = 400
    oil_val    = 50
    copper_val = 3000
    eur_usd    = 0.85
    hibor_val  = 2.0
    
    records = []
    prev_year = None
    
    for i, d in enumerate(cal):
        year = d.year
        
        # 每年重新设定趋势（模拟经济周期）
        if year != prev_year:
            if 1995 <= year <= 2000: trend_mult = 0.8
            elif 2001 <= year <= 2008: trend_mult = 1.0
            elif 2009 <= year <= 2011: trend_mult = -1.5  #金融危机
            elif 2012 <= year <= 2019: trend_mult = 0.9
            elif 2020 <= year <= 2021: trend_mult = -1.0  #COVID
            elif 2022 <= year <= 2025: trend_mult = 1.2   #加息周期
            else: trend_mult = 0.5
            prev_year = year
        
        # 季度末更新锚点
        if d.month in [3,6,9,12] and d.day == 30:
            fed_funds  = max(0.0, fed_funds  + random.gauss(0.05, 0.3)  * trend_mult)
            cpi_val    = max(0.1, cpi_val    + random.gauss(0.1,  0.2)  * trend_mult)
            m2_val     = max(5000, m2_val    + random.gauss(200,  100)  * trend_mult)
            gold_val   = max(200, gold_val   + random.gauss(5,   15)    * trend_mult)
            oil_val    = max(20,  oil_val    + random.gauss(1,    5)    * trend_mult)
            copper_val = max(1500, copper_val+ random.gauss(20,   50)   * trend_mult)
            eur_usd    = max(0.6, eur_usd    + random.gauss(0.005, 0.02)* trend_mult)
            hibor_val  = max(0.1, hibor_val  + random.gauss(0.03,  0.15)* trend_mult)
        
        # 日内微扰
        noise = 0.02
        records.append((d.isoformat(), "FEDFUNDS",   round(fed_funds  + random.gauss(0, 0.05),  4), "US"))
        records.append((d.isoformat(), "CPI",        round(cpi_val    + random.gauss(0, 0.02),  4), "US"))
        records.append((d.isoformat(), "M2",         round(m2_val     + random.gauss(0, 50),    2), "US"))
        records.append((d.isoformat(), "GOLD",        round(gold_val   + random.gauss(0, 2),     2), "GLD"))
        records.append((d.isoformat(), "OIL",        round(oil_val    + random.gauss(0, 0.8),   2), "OIL"))
        records.append((d.isoformat(), "COPPER",      round(copper_val + random.gauss(0, 5),     2), "CPR"))
        records.append((d.isoformat(), "EURUSD",      round(eur_usd    + random.gauss(0, 0.002), 6), "EU"))
        records.append((d.isoformat(), "HIBOR",       round(hibor_val  + random.gauss(0, 0.01),  4), "HK"))
    
    # 写入CSV
    path = os.path.join(DATA_DIR, "macro_indicators.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "indicator_code", "value", "country"])
        for r in records:
            writer.writerow(r)
    print(f"✓ macro_indicators.csv: {len(records)} 条记录 -> {path}")
    return path

# ========== 2. 生成行情数据 ==========

def _generate_stock_random_walk(start_price, annual_trend, annual_vol):
    """单只股票随机游走（年化趋势+波动率）"""
    daily_trend = annual_trend / 252
    daily_vol   = annual_vol   / math.sqrt(252)
    price = start_price
    prices = []
    for _ in range(total_days()):
        price = price * math.exp(random.gauss(daily_trend, daily_vol))
        prices.append(price)
    return prices

def generate_market_data():
    """生成美股/港股历史行情（日频）"""
    cal = date_range(START_DATE, END_DATE)
    
    # 每只股票的起始价格、年化趋势、年化波动率
    stock_cfg = {
        "AAPL":    (50,   0.18, 0.35),
        "MSFT":    (50,   0.15, 0.30),
        "GOOGL":   (100,  0.20, 0.32),
        "TSLA":    (20,   0.30, 0.65),
        "NVDA":    (10,   0.35, 0.55),
        "META":    (80,   0.22, 0.40),
        "AMZN":    (50,   0.20, 0.35),
        "0700.HK": (250,  0.18, 0.35),
        "3690.HK": (30,   0.22, 0.40),
        "9988.HK": (80,   0.15, 0.30),
        "1810.HK": (8,    0.25, 0.50),
        "2382.HK": (10,   0.20, 0.38),
    }
    
    # 先生成每只股票每日收盘价
    close_prices = {}
    for ticker, (start, trend, vol) in stock_cfg.items():
        close_prices[ticker] = _generate_stock_random_walk(start, trend, vol)
    
    records = []
    for i, d in enumerate(cal):
        date_str = d.isoformat()
        for ticker, (start, trend, vol) in stock_cfg.items():
            close = close_prices[ticker][i]
            high  = close * (1 + abs(random.gauss(0, 0.01)))
            low   = close * (1 - abs(random.gauss(0, 0.01)))
            open_ = low + (high - low) * random.random()
            vol_amt = int(random.gauss(5e6, 2e6))
            # 港股成交量偏小
            if ticker.endswith(".HK"):
                vol_amt = int(vol_amt * 0.3)
            records.append((date_str, ticker, round(open_,2), round(high,2),
                            round(low,2), round(close,2), max(0, vol_amt)))
    
    path = os.path.join(DATA_DIR, "market_data.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date","ticker","open","high","low","close","volume"])
        for r in records:
            writer.writerow(r)
    print(f"✓ market_data.csv: {len(records)} 条记录 -> {path}")
    return path

# ========== 3. 生成历史周期向量库 ==========

def generate_cycle_vectors():
    """
    将每年末+每个宏观异动事件作为一个时间切片，生成特征向量。
    真实场景用模型降维，这里用模拟。
    """
    # 每年12月31日作为一个切片，加上重要宏观事件日期
    slices = []
    
    # 关键历史节点
    major_events = [
        (date(1997, 10, 1),  "亚洲金融危机"),
        (date(2000,  4, 1), "科网泡沫"),
        (date(2001,  9, 1), "911事件"),
        (date(2008,  9, 1), "雷曼危机"),
        (date(2009,  3, 1), "QE1启动"),
        (date(2010,  4, 1), "欧债危机"),
        (date(2011,  8, 1), "美股崩盘"),
        (date(2015,  8, 1), "人民币汇改"),
        (date(2018, 12, 1), "中美贸易战"),
        (date(2020,  3, 1), "COVID崩盘"),
        (date(2022,  3, 1), "加息周期启动"),
        (date(2023,  1, 1), "AI浪潮"),
    ]
    
    slice_id = 0
    vectors = []
    
    for year in range(1995, 2026):
        d = date(year, 12, 31)
        
        # 收集当年12月31日的宏观指标（从macro_indicators中抽取对应值）
        # 这里直接模拟
        vec = embedding_to_vector(year, year*0.01, math.sin(year*0.5))
        label = f"{year}年末宏观切片"
        
        vectors.append({
            "slice_id": f"slice_{slice_id:04d}",
            "date": d.isoformat(),
            "vector": vec,
            "label": label
        })
        slice_id += 1
    
    for evt_date, evt_label in major_events:
        if evt_date >= START_DATE and evt_date <= END_DATE:
            vec = embedding_to_vector(evt_date.year, evt_date.month, hash(evt_label) % 1000)
            vectors.append({
                "slice_id": f"slice_{slice_id:04d}",
                "date": evt_date.isoformat(),
                "vector": vec,
                "label": evt_label
            })
            slice_id += 1
    
    # 按日期排序
    vectors.sort(key=lambda x: x["date"])
    
    path = os.path.join(DATA_DIR, "cycle_vectors.json")
    with open(path, "w") as f:
        json.dump({"vectors": vectors, "dim": VECTOR_DIM, "total": len(vectors)}, f, indent=2)
    print(f"✓ cycle_vectors.json: {len(vectors)} 个切片 -> {path}")
    return path

# ========== 主函数 ==========

def main():
    print("=" * 60)
    print("阶段一：30年历史数据基准建立")
    print("=" * 60)
    
    p1 = generate_macro_indicators()
    p2 = generate_market_data()
    p3 = generate_cycle_vectors()
    
    # 统计摘要
    print("\n📊 数据摘要:")
    print(f"  时间范围: {START_DATE} ~ {END_DATE}")
    print(f"  总天数: {total_days():,}")
    print(f"  宏观指标: {len(INDICATORS)} 种 (日频)")
    print(f"  美股: {len([t for t in US_TICKERS])} 只 | 港股: {len([t for t in HK_TICKERS])} 只")
    print(f"  历史切片: 每年末 + {len([e[1] for e in [(date(1997,10,1),'亚洲金融危机')]])} 个重大事件节点")
    print("\n✅ 初始建库完成！")

if __name__ == "__main__":
    main()
