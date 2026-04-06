#!/usr/bin/env python3
"""
daily_strategy.py
阶段三：每日08:00策略报告生成
- 读取当前状态向量
- 在历史向量库中检索相似周期
- 计算科技/资源板块置信度
- 输出策略清单到 output/daily_strategy_YYYYMMDD.json
用法: python3 daily_strategy.py
"""

import json
import os
import math
import random
import sys
from datetime import date, datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "mock_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
STATE_FILE = os.path.join(OUTPUT_DIR, "current_state.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)

VECTOR_DIM = 64

random.seed()

# ========== 模拟标的池 ==========

US_STOCKS = [
    {"ticker": "NVDA",  "sector": "tech",     "base_price": 135},
    {"ticker": "TSLA",  "sector": "tech",     "base_price": 250},
    {"ticker": "AAPL",  "sector": "tech",     "base_price": 220},
    {"ticker": "MSFT",  "sector": "tech",     "base_price": 415},
    {"ticker": "AMZN",  "sector": "tech",     "base_price": 195},
    {"ticker": "GOLD",  "sector": "resource", "base_price": 2300},
    {"ticker": "COPX",  "sector": "resource", "base_price": 95},   # 铜ETF
    {"ticker": "SLV",   "sector": "resource", "base_price": 28},   # 银ETF
]

HK_STOCKS = [
    {"ticker": "2382.HK", "sector": "tech",    "base_price": 15},
    {"ticker": "1810.HK", "sector": "tech",    "base_price": 12},
    {"ticker": "0700.HK", "sector": "tech",    "base_price": 380},
    {"ticker": "3690.HK", "sector": "tech",    "base_price": 45},
]

ALL_STOCKS = US_STOCKS + HK_STOCKS

# ========== 工具函数 ==========

def cosine_similarity(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    norm_a = math.sqrt(sum(x*x for x in a) + 1e-9)
    norm_b = math.sqrt(sum(x*x for x in b) + 1e-9)
    return dot / (norm_a * norm_b)

def embedding_to_vector(*args):
    seed = int(sum(abs(v)*1000 for v in args)) % (2**31)
    rng = random.Random(seed)
    return [rng.gauss(0, 1) for _ in range(VECTOR_DIM)]

def load_cycle_vectors():
    path = os.path.join(DATA_DIR, "cycle_vectors.json")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)["vectors"]

def load_current_state():
    if not os.path.exists(STATE_FILE):
        # 兜底：生成一个默认状态
        now = datetime.now()
        return {
            "updated_at": now.isoformat(),
            "macro_snapshot": {"FEDFUNDS": 5.25, "GOLD": 2300},
            "market_snapshot": {"NVDA": 135},
            "feature_vector": embedding_to_vector(5.25, 135)
        }
    with open(STATE_FILE) as f:
        return json.load(f)

def historical_win_rate(similarity, sector):
    """
    基于相似度模拟历史胜率。
    真实场景：查询 strategy_decisions 历史库中相似节点后30天涨跌概率。
    """
    # 相似度 > 0.9 → 高置信度；< 0.6 → 拒绝输出
    if similarity < 0.6:
        return None  # 无法获取
    
    # 科技板块弹性更高，资源板块趋势更稳定
    base = 0.52 if sector == "tech" else 0.55
    # 相似度加权
    confidence = min(0.95, base + (similarity - 0.6) * 0.8)
    return round(confidence * 100)

def generate_trigger_condition(ticker, sector, current_price):
    """生成触发条件"""
    if sector == "tech":
        threshold_pct = random.uniform(1.5, 4.0)
    else:
        threshold_pct = random.uniform(1.0, 2.5)
    trigger_up   = round(current_price * (1 + threshold_pct/100), 2)
    trigger_down = round(current_price * (1 - threshold_pct/100), 2)
    return {
        "direction": "long",
        "entry_condition": f"price > {trigger_up}",
        "stop_condition":  f"price < {trigger_down}",
        " Boolean": True
    }

def estimate_return(similarity, sector):
    """估算预期收益率上限"""
    if similarity < 0.6:
        return None
    if sector == "tech":
        # 高波动板块：历史相似度0.8+ → 预期上限8-20%
        base = 8 + (similarity - 0.6) * 40
    else:
        # 资源板块：历史相似度0.8+ → 预期上限5-12%
        base = 5 + (similarity - 0.6) * 25
    return round(min(base, 25), 2)

# ========== 主函数 ==========

def main():
    today_str = date.today().strftime("%Y-%m-%d")
    now = datetime.now()
    
    print(f"\n{'='*60}")
    print(f"阶段三：每日策略报告生成 | {today_str} {now.hour}:{now.minute:02d}")
    print(f"{'='*60}")
    
    # 1. 加载当前状态
    state = load_current_state()
    current_vec = state["feature_vector"]
    macro = state.get("macro_snapshot", {})
    market = state.get("market_snapshot", {})
    print(f"\n📋 当前宏观状态:")
    for k, v in list(macro.items())[:4]:
        print(f"   {k}: {v}")
    
    # 2. 检索历史相似周期
    vectors = load_cycle_vectors()
    if not vectors:
        print("⚠ 无历史向量库，执行冷启动策略（无历史相似度参考）")
        top_matches = []
    else:
        similarities = []
        for v in vectors:
            sim = cosine_similarity(current_vec, v["vector"])
            similarities.append((sim, v))
        similarities.sort(key=lambda x: -x[0])
        top_matches = similarities[:5]
    
    # 取最高相似度
    best_sim = top_matches[0][0] if top_matches else 0.0
    best_label = top_matches[0][1]["label"] if top_matches else "无历史匹配"
    
    print(f"\n🔍 最相似历史周期: [{best_sim:.3f}] {best_label}")
    for sim, v in top_matches[1:]:
        print(f"   [{sim:.3f}] {v['date']} - {v['label']}")
    
    # 3. 决定是否输出（容错机制）
    if best_sim < 0.6:
        print("\n⛔ 最高相似度 < 60%，策略置信度不足，拒绝输出买卖建议。")
        decision = {
            "date": today_str,
            "confidence_status": "UNABLE_TO_ESTIMATE",
            "best_similarity": round(best_sim, 4),
            "reason": "历史相似度低于60%阈值，无法输出有效策略",
            "us_pool": [],
            "hk_pool": [],
            "generated_at": now.isoformat()
        }
    else:
        print(f"\n✅ 置信度检验通过，开始生成操作池...")
        
        us_pool = []
        hk_pool = []
        
        for stock in US_STOCKS:
            conf = historical_win_rate(best_sim, stock["sector"])
            curr_price = market.get(stock["ticker"], stock["base_price"])
            trigger = generate_trigger_condition(stock["ticker"], stock["sector"], curr_price)
            exp_ret = estimate_return(best_sim, stock["sector"])
            us_pool.append({
                "ticker": stock["ticker"],
                "sector": stock["sector"],
                "current_price": curr_price,
                "trigger_condition": trigger,
                "expected_return上限": f"{exp_ret}%" if exp_ret else "无法获取",
                "confidence": conf if conf else "无法获取",
                "source_similarity": round(best_sim, 4),
                "historical_match": best_label
            })
        
        for stock in HK_STOCKS:
            conf = historical_win_rate(best_sim, stock["sector"])
            curr_price = market.get(stock["ticker"], stock["base_price"])
            trigger = generate_trigger_condition(stock["ticker"], stock["sector"], curr_price)
            exp_ret = estimate_return(best_sim, stock["sector"])
            hk_pool.append({
                "ticker": stock["ticker"],
                "sector": stock["sector"],
                "current_price": curr_price,
                "trigger_condition": trigger,
                "expected_return上限": f"{exp_ret}%" if exp_ret else "无法获取",
                "confidence": conf if conf else "无法获取",
                "source_similarity": round(best_sim, 4),
                "historical_match": best_label
            })
        
        decision = {
            "date": today_str,
            "confidence_status": "CONFIDENT" if best_sim >= 0.85 else "PARTIAL",
            "best_similarity": round(best_sim, 4),
            "macro_snapshot": macro,
            "us_pool": us_pool,
            "hk_pool": hk_pool,
            "generated_at": now.isoformat()
        }
    
    # 4. 输出报告
    out_file = os.path.join(OUTPUT_DIR, f"daily_strategy_{date.today().strftime('%Y%m%d')}.json")
    with open(out_file, "w") as f:
        json.dump(decision, f, indent=2, ensure_ascii=False)
    
    # 5. 打印摘要
    print(f"\n{'='*60}")
    print(f"📤 策略报告已生成: {out_file}")
    print(f"{'='*60}")
    
    print(f"\n[宏观参数]")
    for k, v in list(macro.items())[:5]:
        print(f"  {k}: {v}")
    
    print(f"\n[回溯匹配]")
    print(f"  历史相似周期: {best_label}")
    print(f"  相似度: {best_sim:.3f}")
    print(f"  置信度状态: {decision['confidence_status']}")
    
    if decision["us_pool"]:
        print(f"\n[US操作池] ({len(decision['us_pool'])} 只)")
        for s in decision["us_pool"]:
            print(f"  {s['ticker']} ({s['sector']}) | 置信度: {s['confidence']}% | 预期上限: {s['expected_return上限']} | 触发: {s['trigger_condition']['entry_condition']}")
    
    if decision["hk_pool"]:
        print(f"\n[HK操作池] ({len(decision['hk_pool'])} 只)")
        for s in decision["hk_pool"]:
            print(f"  {s['ticker']} ({s['sector']}) | 置信度: {s['confidence']}% | 预期上限: {s['expected_return上限']} | 触发: {s['trigger_condition']['entry_condition']}")
    
    if not decision["us_pool"] and not decision["hk_pool"]:
        print(f"\n⛔ 无操作池 (相似度不足)")
    
    print(f"\n✅ 每日策略报告完毕！")

if __name__ == "__main__":
    main()
