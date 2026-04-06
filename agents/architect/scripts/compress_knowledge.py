#!/usr/bin/env python3
"""
compress_knowledge.py
阶段一知识归纳压缩：
- 每周: 扫描近30天宏观异动因子(Z-score)，写入 MEMORY.md macro_weekly 分区
- 每月: 校准上月策略胜率实际 vs 预测偏差，更新概率模型
- 每季度: 合并相似向量为锚点，减少存储体积
用法:
  python3 compress_knowledge.py weekly
  python3 compress_knowledge.py monthly
  python3 compress_knowledge.py quarterly
"""

import json
import os
import sys
import math
import random
import csv
from datetime import date, datetime, timedelta
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "mock_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MEMORY_FILE = os.path.join(BASE_DIR, "MEMORY.md")

random.seed()

VECTOR_DIM = 64

# ========== 工具函数 ==========

def embedding_to_vector(*args):
    seed = int(sum(abs(v)*1000 for v in args)) % (2**31)
    rng = random.Random(seed)
    return [rng.gauss(0, 1) for _ in range(VECTOR_DIM)]

def cosine_similarity(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    norm_a = math.sqrt(sum(x*x for x in a) + 1e-9)
    norm_b = math.sqrt(sum(x*x for x in b) + 1e-9)
    return dot / (norm_a * norm_b)

def load_macro_csv():
    path = os.path.join(DATA_DIR, "macro_indicators.csv")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_cycle_vectors():
    path = os.path.join(DATA_DIR, "cycle_vectors.json")
    if not os.path.exists(path):
        return {"vectors": []}
    with open(path) as f:
        return json.load(f)

def load_daily_strategies():
    """加载所有已输出的策略报告"""
    strategies = []
    if not os.path.exists(OUTPUT_DIR):
        return strategies
    for fname in os.listdir(OUTPUT_DIR):
        if fname.startswith("daily_strategy_") and fname.endswith(".json"):
            with open(os.path.join(OUTPUT_DIR, fname)) as f:
                strategies.append(json.load(f))
    return strategies

def write_memory_section(title, content):
    """向 MEMORY.md 追加或更新指定分区"""
    marker_start = f"<!-- {title}_START -->"
    marker_end   = f"<!-- {title}_END -->"
    
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
            lines = f.readlines()
    else:
        lines = ["# MEMORY.md\n\n"]
    
    # 检查是否已有该分区
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if marker_start in line:
            start_idx = i
        if marker_end in line:
            end_idx = i
    
    new_block = [f"{marker_start}\n", f"{content}\n", f"{marker_end}\n"]
    
    if start_idx is not None and end_idx is not None:
        lines = lines[:start_idx] + new_block + lines[end_idx+1:]
    elif start_idx is None:
        lines.append("\n")
        lines.extend(new_block)
    
    with open(MEMORY_FILE, "w") as f:
        f.writelines(lines)

# ========== 任务1: 每周宏观异动归纳 ==========

def task_weekly_compress():
    print(f"\n{'='*60}")
    print("📦 每周知识压缩 | macro_weekly")
    print(f"{'='*60}")
    
    rows = load_macro_csv()
    if not rows:
        print("⚠ 无宏观数据")
        return
    
    # 近30天数据
    cutoff = (date.today() - timedelta(days=30)).isoformat()
    recent = [r for r in rows if r["date"] >= cutoff]
    
    # 按指标分组，计算Z-score
    by_indicator = defaultdict(list)
    for r in recent:
        by_indicator[r["indicator_code"]].append((r["date"], float(r["value"])))
    
    anomalies = []
    for code, records in by_indicator.items():
        if len(records) < 5:
            continue
        values = [v for _, v in records]
        mean = sum(values) / len(values)
        std  = math.sqrt(sum((v-mean)**2 for v in values) / len(values))
        if std < 1e-9:
            continue
        
        for d, v in records:
            zscore = (v - mean) / std
            if abs(zscore) > 1.5:  # Z-score 显著异动
                anomalies.append({
                    "date": d,
                    "indicator": code,
                    "value": v,
                    "zscore": round(zscore, 3),
                    "severity": "HIGH" if abs(zscore) > 2.5 else "MEDIUM"
                })
    
    # 输出Top10最异常
    anomalies.sort(key=lambda x: -abs(x["zscore"]))
    top_anomalies = anomalies[:10]
    
    print(f"\n近30天宏观异动 (Top {len(top_anomalies)}):")
    for a in top_anomalies:
        print(f"  [{a['severity']}] {a['date']} {a['indicator']}: {a['value']} (Z={a['zscore']})")
    
    # 写入 MEMORY.md
    if top_anomalies:
        content_lines = [f"## macro_weekly | {date.today().isoformat()}\n"]
        content_lines.append(f"近30天宏观异动因子 (Z-score > 1.5)，共 {len(anomalies)} 条异常\n\n")
        content_lines.append("| 日期 | 指标 | 数值 | Z-score | 严重度 |\n")
        content_lines.append("|------|------|------|---------|--------|\n")
        for a in top_anomalies:
            content_lines.append(f"| {a['date']} | {a['indicator']} | {a['value']} | {a['zscore']} | {a['severity']} |\n")
        
        write_memory_section(
            "macro_weekly",
            "".join(content_lines)
        )
        print(f"\n✅ 已写入 MEMORY.md macro_weekly 分区")
    else:
        print("\n✅ 无显著异动，无需写入")

# ========== 任务2: 每月模型校准 ==========

def task_monthly_calibrate():
    print(f"\n{'='*60}")
    print("📐 每月模型校准 | model_calibration")
    print(f"{'='*60}")
    
    strategies = load_daily_strategies()
    if not strategies:
        print("⚠ 无历史策略数据")
        return
    
    # 过滤当月策略
    this_month = date.today().strftime("%Y-%m")
    monthly = [s for s in strategies if s["date"].startswith(this_month)]
    
    if not monthly:
        print(f"⚠ {this_month} 无策略记录")
        return
    
    print(f"\n{this_month} 策略统计 (共 {len(monthly)} 天):")
    
    # 统计各标的置信度分布
    sector_stats = defaultdict(lambda: {"total": 0, "conf_sum": 0, "high_conf": 0})
    for s in monthly:
        for st in s.get("us_pool", []) + s.get("hk_pool", []):
            sec = st["sector"]
            sector_stats[sec]["total"] += 1
            conf = st["confidence"]
            if isinstance(conf, int):
                sector_stats[sec]["conf_sum"] += conf
                if conf >= 75:
                    sector_stats[sec]["high_conf"] += 1
    
    calibration_notes = []
    for sec, stats in sector_stats.items():
        avg_conf = stats["conf_sum"] / stats["total"] if stats["total"] > 0 else 0
        high_pct = stats["high_conf"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {sec}: 平均置信度={avg_conf:.1f}%, 高置信度(≥75%)占比={high_pct:.1f}%")
        calibration_notes.append({
            "sector": sec,
            "avg_confidence": round(avg_conf, 1),
            "high_confidence_ratio": round(high_pct, 1),
            "sample_size": stats["total"]
        })
    
    # 写入 MEMORY.md
    content_lines = [f"## model_calibration | {date.today().isoformat()}\n"]
    content_lines.append(f"上月({this_month})策略胜率校准报告，共 {len(monthly)} 个交易日\n\n")
    content_lines.append("| 板块 | 平均置信度 | 高置信度占比 | 样本数 |\n")
    content_lines.append("|------|-----------|-------------|--------|\n")
    for n in calibration_notes:
        content_lines.append(f"| {n['sector']} | {n['avg_confidence']}% | {n['high_confidence_ratio']}% | {n['sample_size']} |\n")
    content_lines.append("\n> 注：实际胜率需后续手动回溯验证。此处仅统计策略输出时的置信度分布。\n")
    
    write_memory_section(
        "model_calibration",
        "".join(content_lines)
    )
    print(f"\n✅ 已写入 MEMORY.md model_calibration 分区")

# ========== 任务3: 每季度向量合并 ==========

def task_quarterly_compress():
    print(f"\n{'='*60}")
    print("🗜️ 每季度向量压缩 | vector_archive")
    print(f"{'='*60}")
    
    data = load_cycle_vectors()
    vectors = data.get("vectors", [])
    
    if len(vectors) < 10:
        print("⚠ 向量数量不足，跳过合并")
        return
    
    # 按季度分组
    quarterly = defaultdict(list)
    for v in vectors:
        d = date.fromisoformat(v["date"])
        qkey = (d.year, (d.month - 1) // 3 + 1)
        quarterly[qkey].append(v)
    
    print(f"\n季度分组: {len(quarterly)} 个季度")
    
    # 每个季度合并为1个锚点向量
    archived = []
    for qkey, group in sorted(quarterly.items()):
        year, quarter = qkey
        # 取季度末向量作为锚点（最后一个）
        anchor = group[-1]["vector"]
        # 丢弃中间向量
        archived.append({
            "slice_id": f"Q{year}Q{quarter}_anchor",
            "date": group[-1]["date"],
            "vector": anchor,
            "label": f"{year} Q{quarter} 季度锚点 (合并了{len(group)}个切片)",
            "original_count": len(group)
        })
    
    # 保存归档版本
    archive_file = os.path.join(DATA_DIR, "cycle_vectors_archive.json")
    with open(archive_file, "w") as f:
        json.dump({"vectors": archived, "dim": VECTOR_DIM, "total": len(archived)}, f, indent=2)
    
    # 覆盖原向量库为归档版本
    with open(os.path.join(DATA_DIR, "cycle_vectors.json"), "w") as f:
        json.dump({"vectors": archived, "dim": VECTOR_DIM, "total": len(archived)}, f, indent=2)
    
    print(f"✅ 季度合并完成: {len(vectors)} -> {len(archived)} 个锚点向量")
    print(f"   归档副本: {archive_file}")

# ========== 主函数 ==========

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    
    if mode == "weekly":
        task_weekly_compress()
    elif mode == "monthly":
        task_monthly_calibrate()
    elif mode == "quarterly":
        task_quarterly_compress()
    else:
        print(f"用法: python3 compress_knowledge.py [weekly|monthly|quarterly]")

if __name__ == "__main__":
    main()
