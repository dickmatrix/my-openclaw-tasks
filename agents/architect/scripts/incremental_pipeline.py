#!/usr/bin/env python3
"""
incremental_pipeline.py — 阶段二：增量数据与特征向量生成
- 读取真实行情 CSV (AKShare + Eastmoney)
- 读取真实宏观 CSV
- 计算当前特征向量
- 与历史向量库做余弦相似度检索
用法: python3 incremental_pipeline.py
"""

import json
import csv
import os
import math
import sys
from datetime import date, datetime, timedelta
from collections import defaultdict

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "mock_data")
STATE_FILE  = os.path.join(BASE_DIR, "output", "current_state.json")
os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)

VECTOR_DIM = 64

# ========== 工具函数 ==========

def embedding_to_vector(*args):
    """基于输入特征生成确定性向量（模拟降维）"""
    seed = int(sum(abs(float(v)) * 1000 for v in args)) % (2**31)
    rng = __import__("random").Random(seed)
    return [rng.gauss(0, 1) for _ in range(VECTOR_DIM)]

def cosine_similarity(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    norm_a = math.sqrt(sum(x*x for x in a) + 1e-9)
    norm_b = math.sqrt(sum(x*x for x in b) + 1e-9)
    return dot / (norm_a * norm_b)

def load_csv(path):
    """加载 CSV 返回 list of dicts"""
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return list(csv.DictReader(f))

def latest_date_value(csv_path, date_col, val_col):
    """取 CSV 中最新一条记录的日期和数值"""
    rows = load_csv(csv_path)
    if not rows:
        return None, None
    rows.sort(key=lambda r: r.get(date_col, ""))
    latest = rows[-1]
    return latest.get(date_col, ""), latest.get(val_col, "")

def get_latest_prices(csv_path, ticker_col, close_col):
    """取各 ticker 最新收盘价"""
    rows = load_csv(csv_path)
    if not rows:
        return {}
    # 按 ticker 分组，取每只股票最新一条
    by_ticker = defaultdict(list)
    for r in rows:
        by_ticker[r.get(ticker_col, "")].append(r)
    result = {}
    for ticker, recs in by_ticker.items():
        recs.sort(key=lambda r: r.get("date", ""))
        if recs:
            result[ticker] = float(recs[-1].get(close_col, 0))
    return result

# ========== 1. 读取真实行情数据 ==========

def load_real_market():
    """从真实 CSV 读取最新行情快照"""
    us_prices = get_latest_prices(
        os.path.join(DATA_DIR, "market_data_us.csv"),
        "ticker", "close"
    )
    hk_prices = get_latest_prices(
        os.path.join(DATA_DIR, "market_data_hk.csv"),
        "ticker", "close"
    )
    return {**us_prices, **hk_prices}

# ========== 2. 读取真实宏观数据 ==========

def load_real_macro():
    """从真实 CSV 读取最新宏观快照"""
    rows = load_csv(os.path.join(DATA_DIR, "macro_indicators.csv"))
    if not rows:
        return {}
    # 取每个 indicator 最新一条
    by_code = defaultdict(list)
    for r in rows:
        by_code[r.get("indicator_code", "")].append(r)
    result = {}
    for code, recs in by_code.items():
        recs.sort(key=lambda r: r.get("date", ""))
        if recs:
            result[code] = float(recs[-1].get("value", 0))
    return result

# ========== 3. 计算当前特征向量 ==========

def compute_feature_vector(market_prices, macro_values):
    """基于真实价格和宏观指标计算当前状态向量"""
    # 用标的价格生成确定性向量
    all_prices = sorted(market_prices.values())
    tech_prices = [v for k, v in market_prices.items()
                   if not str(k).endswith(".HK")]
    hk_prices   = [v for k, v in market_prices.items()
                    if str(k).endswith(".HK")]

    # 宏观特征
    fedf  = macro_values.get("FEDFUNDS", 0)
    cpi   = macro_values.get("CPI", macro_values.get("CPI_CN", 0))
    m2    = macro_values.get("M2", 0)

    vec = embedding_to_vector(
        # 市场宽基
        sum(all_prices) / max(len(all_prices), 1),
        max(all_prices) if all_prices else 0,
        min(all_prices) if all_prices else 0,
        # 科技板块
        sum(tech_prices) / max(len(tech_prices), 1) if tech_prices else 0,
        # 港股
        sum(hk_prices) / max(len(hk_prices), 1) if hk_prices else 0,
        # 宏观
        fedf, cpi, m2,
        # 时间
        datetime.now().hour,
    )
    return vec

# ========== 4. 相似度检索 ==========

def search_similar_cycles(current_vector, top_k=5):
    """在历史向量库中检索相似周期"""
    path = os.path.join(DATA_DIR, "cycle_vectors.json")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    vectors = data.get("vectors", [])
    if not vectors:
        return []

    results = []
    for v in vectors:
        sim = cosine_similarity(current_vector, v["vector"])
        results.append((sim, v))
    results.sort(key=lambda x: -x[0])
    return results[:top_k]

# ========== 5. 更新当前状态 ==========

def save_state(market_prices, macro_values, feature_vector, similar_cycles):
    now = datetime.now()
    state = {
        "updated_at": now.isoformat(),
        "source": "real_data",
        "market_snapshot": market_prices,
        "macro_snapshot":  macro_values,
        "feature_vector": feature_vector,
        "similar_cycles": [
            {"sim": round(sim, 4), "date": v["date"], "label": v["label"]}
            for sim, v in similar_cycles
        ],
        "best_similarity": similar_cycles[0][0] if similar_cycles else 0,
        "confidence": calc_confidence(similar_cycles[0][0] if similar_cycles else 0)
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    return state

def calc_confidence(sim):
    """基于相似度计算置信度"""
    if sim < 0.6:
        return "无法获取"
    if sim >= 0.85:
        return "高置信度"
    return "部分置信"

# ========== 主函数 ==========

def main():
    print(f"\n{'='*60}")
    print(f"阶段二：增量数据管道 | 真实数据模式")
    print(f"{'='*60}")

    # Step 1: 读行情
    market_prices = load_real_market()
    print(f"\n📊 行情快照 ({len(market_prices)} 只):")
    for ticker, price in sorted(market_prices.items())[:8]:
        print(f"   {ticker}: {price:.2f}")
    if len(market_prices) > 8:
        print(f"   ... +{len(market_prices)-8} 只")

    # Step 2: 读宏观
    macro_values = load_real_macro()
    print(f"\n📈 宏观快照 ({len(macro_values)} 指标):")
    for code, val in list(macro_values.items())[:6]:
        print(f"   {code}: {val:.4f}")

    # Step 3: 计算特征向量
    feature_vec = compute_feature_vector(market_prices, macro_values)
    print(f"\n🔢 当前特征向量: [{feature_vec[0]:.4f}, {feature_vec[1]:.4f}, ...]")

    # Step 4: 相似度检索
    similar = search_similar_cycles(feature_vec)
    print(f"\n🔍 历史相似周期 Top {len(similar)}:")
    for sim, v in similar:
        bar = "█" * int(sim * 20)
        print(f"   [{sim:.3f}] {bar} {v['date']} — {v['label']}")

    # Step 5: 保存状态
    state = save_state(market_prices, macro_values, feature_vec, similar)
    print(f"\n🔄 状态已更新: {state['updated_at']}")
    print(f"   最佳相似度: {state['best_similarity']:.4f}")
    print(f"   置信度: {state['confidence']}")

    # Step 6: 输出文件
    print(f"\n✅ 增量管道完毕！")
    print(f"   状态文件: {STATE_FILE}")

if __name__ == "__main__":
    main()
