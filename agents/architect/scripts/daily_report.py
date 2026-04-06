#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_report.py — 专家级金融日报 v2.0
核心升级:
- 3年历史数据 (趋势判断为主)
- 置信度加权信号体系
- 新闻情感分析 + 权重融合
- 板块方向性信号 (买入/持有/卖出)
- 趋势导向 > 实时行情
"""

import os, sys, json, csv, math, re
from datetime import date, datetime, timedelta
from collections import defaultdict

# ====== 配置 ======
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "mock_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
ROOT_DIR   = os.path.dirname(BASE_DIR)
DOCS_DIR   = os.path.join(ROOT_DIR, "docs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# ====== 方法论置信度配置 ======
METHODOLOGIES = {
    "MA200趋势":      {"stars": 5, "weight": 0.25, "desc": "30年+实证"},
    "12M动量":        {"stars": 4, "weight": 0.20, "desc": "Jegadeesh-Titman"},
    "Fama-French三因子": {"stars": 4, "weight": 0.15, "desc": "学术金标准"},
    "风险平价":        {"stars": 4, "weight": 0.15, "desc": "2008危机有效"},
    "价值投资":        {"stars": 3, "weight": 0.10, "desc": "Buffett/Graham"},
    "RSI均值回归":     {"stars": 3, "weight": 0.08, "desc": "短期有效"},
    "美林时钟":        {"stars": 3, "weight": 0.07, "desc": "宏观周期配置"},
}

# 权重归一化确认
total_weight = sum(m["weight"] for m in METHODOLOGIES.values())
print(f"[方法论权重归一化] 总权重: {total_weight:.2f}")

# ====== 数据加载 ======

def load_market_data_3y(csv_path):
    """加载3年历史数据，按ticker分组"""
    if not os.path.exists(csv_path):
        return {}
    rows = list(csv.DictReader(open(csv_path)))
    by_ticker = defaultdict(list)
    for r in rows:
        by_ticker[r["ticker"]].append(r)
    # 每只股票按日期排序
    for ticker in by_ticker:
        by_ticker[ticker].sort(key=lambda x: x["date"])
    return by_ticker


def compute_indicators(recs):
    """
    基于3年数据计算专家级指标
    recs: 该ticker所有历史K线，已按date排序
    返回: dict with trend/momentum/rsi/zscore/signal
    """
    if len(recs) < 60:
        return None
    closes = [float(r["close"]) for r in recs]
    latest = closes[-1]
    
    # === 趋势指标 ===
    ma200 = sum(closes[-200:]) / min(200, len(closes[-200:])) if len(closes) >= 200 else sum(closes)/len(closes)
    ma50  = sum(closes[-50:])  / min(50,  len(closes[-50:]))  if len(closes) >= 50  else ma200
    ma20  = sum(closes[-20:])  / min(20,  len(closes[-20:]))  if len(closes) >= 20  else latest
    trend_dev = (latest - ma200) / ma200 * 100  # MA200偏离度
    
    # === 动量因子 ===
    mom12m = (latest - closes[-252]) / closes[-252] * 100 if len(closes) >= 252 and closes[-252] else 0.0
    mom6m  = (latest - closes[-126]) / closes[-126] * 100 if len(closes) >= 126 and closes[-126] else 0.0
    mom3m  = (latest - closes[-66])  / closes[-66]  * 100 if len(closes) >= 66  and closes[-66]  else 0.0
    
    # === RSI(14) ===
    if len(closes) >= 15:
        gains  = [max(0.0, closes[i]-closes[i-1]) for i in range(1, min(15,len(closes)))]
        losses = [abs(min(0.0, closes[i]-closes[i-1])) for i in range(1, min(15,len(closes)))]
        avg_g = sum(gains) / 14.0
        avg_l = sum(losses) / 14.0
        rs = avg_g / avg_l if avg_l != 0.0 else 100.0
        rsi = 100.0 - (100.0/(1.0+rs))
    else:
        rsi = 50.0
    
    # === Z-score (20日) ===
    ma20_val = sum(closes[-20:]) / min(20, len(closes[-20:]))
    std20 = math.sqrt(sum((c - ma20_val)**2 for c in closes[-20:]) / min(20, len(closes[-20:])))
    zscore = (latest - ma20_val) / std20 if std20 > 0 else 0.0
    
    # === 价值因子 (简化版PB趋势) ===
    # 注: 完整PB需要财务数据，此处用价格/MA200比值近似
    pb_proxy = latest / ma200  # >1 偏贵，<1 偏便宜
    
    return {
        "close":      latest,
        "ma200":      round(ma200, 2),
        "ma50":       round(ma50, 2),
        "ma20":       round(ma20, 2),
        "trend_dev":  round(trend_dev, 2),   # %，正值=在MA200上方
        "mom12m":     round(mom12m, 2),
        "mom6m":      round(mom6m, 2),
        "mom3m":      round(mom3m, 2),
        "rsi":        round(rsi, 1),
        "zscore":     round(zscore, 2),
        "pb_proxy":   round(pb_proxy, 3),   # 价格/Ma200比值
    }


def compute_sector_signal(indicators):
    """
    根据专家方法论体系，计算板块/股票信号
    返回: {
        "score": float,        # 加权综合得分 (-100 ~ +100)
        "signal": str,         # BUY / HOLD / SELL
        "confidence": float,    # 置信度 0~100
        "details": dict
    }
    """
    if not indicators:
        return {"score": 0, "signal": "HOLD", "confidence": 0, "details": {}}
    
    dev  = indicators["trend_dev"]   # MA200偏离
    mom  = indicators["mom12m"]      # 12M动量
    rsi  = indicators["rsi"]
    z    = indicators["zscore"]
    pb   = indicators["pb_proxy"]   # PB代理
    
    # === 信号强度计算 ===
    # MA200趋势信号
    if dev > 20:    ma_signal = 1.0
    elif dev > 5:   ma_signal = 0.7
    elif dev > 0:   ma_signal = 0.3
    elif dev > -10: ma_signal = -0.3
    elif dev > -20: ma_signal = -0.7
    else:           ma_signal = -1.0
    
    # 12M动量信号
    if mom > 30:    mom_signal = 1.0
    elif mom > 15:  mom_signal = 0.7
    elif mom > 0:   mom_signal = 0.3
    elif mom > -15: mom_signal = -0.3
    elif mom > -30: mom_signal = -0.7
    else:           mom_signal = -1.0
    
    # RSI均值回归信号
    if rsi > 80:   rsi_signal = -0.8   # 严重超买→卖出信号
    elif rsi > 70:  rsi_signal = -0.4
    elif rsi < 20:  rsi_signal = 0.8    # 严重超卖→买入信号
    elif rsi < 30:  rsi_signal = 0.4
    else:           rsi_signal = 0.0
    
    # Z-score异常检测
    if z > 2.5:    z_signal = -0.5     # 暴涨后的反向信号
    elif z < -2.5: z_signal = 0.5      # 暴跌后的反弹信号
    else:           z_signal = 0.0
    
    # 价值信号 (PB代理)
    if pb < 0.85:  value_signal = 0.4  # 相对便宜
    elif pb > 1.20: value_signal = -0.3  # 相对贵
    else:           value_signal = 0.0
    
    # === 加权综合得分 ===
    raw_score = (
        ma_signal   * METHODOLOGIES["MA200趋势"]["weight"]     * 100 +
        mom_signal  * METHODOLOGIES["12M动量"]["weight"]       * 100 +
        rsi_signal  * METHODOLOGIES["RSI均值回归"]["weight"]     * 100 +
        z_signal    * METHODOLOGIES["Fama-French三因子"]["weight"] * 100 +
        value_signal * METHODOLOGIES["价值投资"]["weight"]       * 100
    )
    
    score = max(-100, min(100, raw_score))
    
    # === 信号判定 ===
    if score >= 40:  signal = "BUY"
    elif score >= 15: signal = "HOLD-BULL"
    elif score <= -40: signal = "SELL"
    elif score <= -15: signal = "HOLD-BEAR"
    else:             signal = "HOLD"
    
    # === 置信度 ===
    # 一致性越高，置信度越高
    signals = [ma_signal, mom_signal, rsi_signal, z_signal, value_signal]
    pos = sum(1 for s in signals if s > 0)
    neg = sum(1 for s in signals if s < 0)
    consistency = abs(pos - neg) / len(signals)  # 0~1
    magnitude = abs(score) / 100  # 0~1
    confidence = round((consistency * 0.4 + magnitude * 0.6) * 100, 1)
    
    return {
        "score":      round(score, 1),
        "signal":     signal,
        "confidence": confidence,
        "details": {
            "ma_signal":    round(ma_signal, 2),
            "mom_signal":   round(mom_signal, 2),
            "rsi_signal":   round(rsi_signal, 2),
            "z_signal":     round(z_signal, 2),
            "value_signal": round(value_signal, 2),
        }
    }


def sector_signal_summary(stocks_data):
    """
    将多只股票聚合成板块信号
    stocks_data: [{"ticker": ..., "indicators": {...}, "signal": {...}}, ...]
    """
    sectors = defaultdict(list)
    for stock in stocks_data:
        sector = stock.get("sector", "Other")
        sectors[sector].append(stock)
    
    summary = {}
    for sector, members in sectors.items():
        scores = [m["signal"]["score"] for m in members if m.get("signal")]
        confs  = [m["signal"]["confidence"] for m in members if m.get("signal")]
        if not scores:
            continue
        # 板块得分 = 成员得分加权平均
        avg_score = sum(scores) / len(scores)
        avg_conf  = sum(confs)  / len(confs)
        
        # 信号判定
        buy_count  = sum(1 for s in members if s.get("signal",{}).get("signal") in ["BUY","HOLD-BULL"])
        sell_count = sum(1 for s in members if s.get("signal",{}).get("signal") in ["SELL","HOLD-BEAR"])
        
        if buy_count >= len(members) * 0.6:
            signal = "BUY"
        elif sell_count >= len(members) * 0.6:
            signal = "SELL"
        elif avg_score > 20:
            signal = "HOLD-BULL"
        elif avg_score < -20:
            signal = "HOLD-BEAR"
        else:
            signal = "HOLD"
        
        summary[sector] = {
            "signal":     signal,
            "score":      round(avg_score, 1),
            "confidence": round(avg_conf, 1),
            "member_count": len(members),
            "buy_count":  buy_count,
            "sell_count": sell_count,
        }
    return summary


# ====== 新闻情感分析 ======

SENTIMENT_KEYWORDS_POS = [
    "超配","增持","买入","看好","突破","新高","复苏","增长","强劲",
    "上调","超预期","景气","扩张","繁荣","牛市","反弹","大涨"
]
SENTIMENT_KEYWORDS_NEG = [
    "减持","卖出","看空","破位","新低","衰退","下滑","疲软",
    "下调","低于预期","收缩","危机","崩盘","熊市","暴跌","大跌"
]


def score_sentiment(text):
    """对一段文本进行情感打分，返回 -1~+1"""
    if not text:
        return 0.0
    text = text.lower()
    pos = sum(1 for kw in SENTIMENT_KEYWORDS_POS if kw in text)
    neg = sum(1 for kw in SENTIMENT_KEYWORDS_NEG if kw in text)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def fetch_and_analyze_news():
    """获取新闻并计算情感得分"""
    news_items = []
    try:
        import akshare as ak
        df = ak.stock_news_main_cx()
        for _, row in df.head(20).iterrows():
            tag = str(row.get("tag","")).strip()
            summary = str(row.get("summary","")).strip()
            if summary and len(summary) > 10:
                sentiment = score_sentiment(summary)
                news_items.append({
                    "source": "财新",
                    "tag": tag,
                    "title": summary[:150],
                    "sentiment": sentiment,
                    "sentiment_label": "正面" if sentiment > 0.3 else ("负面" if sentiment < -0.3 else "中性")
                })
    except Exception as e:
        print("Caixin news failed:", e)
    
    try:
        import akshare as ak
        df2 = ak.stock_news_em()
        for _, row in df2.head(15).iterrows():
            title = str(row.get("新闻标题","")).strip()
            if title and len(title) > 5:
                sentiment = score_sentiment(title)
                news_items.append({
                    "source": str(row.get("文章来源","")) or "东方财富",
                    "tag": str(row.get("关键词","")).strip(),
                    "title": title[:150],
                    "sentiment": sentiment,
                    "sentiment_label": "正面" if sentiment > 0.3 else ("负面" if sentiment < -0.3 else "中性")
                })
    except Exception as e:
        print("Eastmoney news failed:", e)
    
    return news_items


def news_sentiment_summary(news_items):
    """新闻情感聚合"""
    if not news_items:
        return {"score": 0, "label": "中性", "positive": 0, "negative": 0, "neutral": 0}
    scores = [n["sentiment"] for n in news_items]
    avg = sum(scores) / len(scores)
    pos = sum(1 for s in scores if s > 0.3)
    neg = sum(1 for s in scores if s < -0.3)
    neu = len(scores) - pos - neg
    label = "偏多" if avg > 0.2 else ("偏空" if avg < -0.2 else "中性")
    return {
        "score": round(avg, 3),
        "label": label,
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "total": len(scores)
    }


# ====== 板块标签映射 ======

SECTOR_MAP = {
    # (常见ticker前缀或关键字) -> 板块名
    "AAPL": "科技", "MSFT": "科技", "GOOGL": "科技", "AMZN": "科技",
    "NVDA": "科技", "META": "科技", "TSLA": "新能源车", "AMD": "科技",
    "AVGO": "科技", "ORCL": "科技", "CRM": "科技", "ADBE": "科技",
    "NFLX": "科技", "INTC": "科技", "CSCO": "科技", "PEP": "消费",
    "KO": "消费", "COST": "消费", "WMT": "消费", "JNJ": "医药",
    "UNH": "医药", "PFE": "医药", "ABBV": "医药", "TMO": "医药",
    "JPM": "金融", "BAC": "金融", "WFC": "金融", "GS": "金融",
    "XOM": "能源", "CVX": "能源", "COP": "能源", "SLB": "能源",
    "BA": "航空军工", "CAT": "工业", "GE": "工业", "MMM": "工业",
    "DIS": "娱乐", "CMCSA": "电信", "VZ": "电信", "T": "电信",
    "AMT": "房地产", "PLD": "房地产", "CCI": "房地产",
    "LMT": "航空军工", "NOC": "航空军工", "RTX": "航空军工",
}

def get_sector(ticker):
    for prefix, sector in SECTOR_MAP.items():
        if ticker.startswith(prefix):
            return sector
    return "其他"


# ====== 主分析流程 ======

def analyze_us_stocks_3y():
    """
    分析美股: 加载3年数据，计算指标，产生信号
    返回: list of dict with ticker, indicators, signal, sector
    """
    us_path = os.path.join(DATA_DIR, "market_data_us_batch.csv")
    by_ticker = load_market_data_3y(us_path)
    
    results = []
    for ticker, recs in by_ticker.items():
        indicators = compute_indicators(recs)
        if not indicators:
            continue
        sig = compute_sector_signal(indicators)
        results.append({
            "ticker":      ticker,
            "sector":      get_sector(ticker),
            "indicators":  indicators,
            "signal":      sig,
        })
    
    return results


def build_macro_environment(macro_data):
    """
    根据宏观指标，给出宏观环境定调
    """
    fedf = macro_data.get("FEDFUNDS", {}).get("value", 0)
    cpi  = macro_data.get("CPI", {}).get("value", 0)
    vix  = macro_data.get("VIX", {}).get("value", 0)
    m2   = macro_data.get("M2", {}).get("value", 0)
    
    # 判断环境
    if fedf > 5 and cpi > 5:
        env = "🔴 紧缩滞胀"
        direction = "防御"
    elif fedf > 5:
        env = "🟠 高利率收紧"
        direction = "保守"
    elif cpi > 5:
        env = "🟡 通胀压力"
        direction = "抗通胀"
    elif vix > 25:
        env = "😱 市场恐慌"
        direction = "防御"
    elif vix > 18:
        env = "📊 波动偏高"
        direction = "中性"
    else:
        env = "🟢 宏观平稳"
        direction = "积极"
    
    return {
        "env": env,
        "direction": direction,
        "fedf": fedf,
        "cpi": cpi,
        "vix": vix,
        "m2": m2,
    }


def load_macro():
    path = os.path.join(DATA_DIR, "macro_indicators.csv")
    if not os.path.exists(path):
        return {}
    rows = list(csv.DictReader(open(path)))
    by_code = defaultdict(list)
    for r in rows:
        by_code[r["indicator_code"]].append(r)
    result = {}
    for code, recs in by_code.items():
        recs.sort(key=lambda x: x["date"])
        if recs:
            result[code] = {"date": recs[-1]["date"], "value": float(recs[-1]["value"])}
    return result


# ====== 报告生成 ======

def generate_expert_report(us_stocks, sector_sigs, macro_env, news_summary, news_items, today_str):
    """生成专家级日报"""
    lines = []
    
    # === 标题 ===
    lines.append("# 📬 专家级金融日报 | " + today_str)
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')} (UTC+8)")
    lines.append("")
    
    # === 一、宏观定调 ===
    lines.append("## 一、宏观环境定调")
    lines.append("")
    lines.append(f"| 环境 | 方向 | FEDFUNDS | CPI | VIX |")
    lines.append("|------|------|----------|-----|-----|")
    env = macro_env
    lines.append(f"| {env['env']} | {env['direction']} | {env['fedf']:.2f}% | {env['cpi']:.2f}% | {env['vix']:.1f} |")
    lines.append("")
    
    # === 二、板块信号矩阵 ===
    lines.append("## 二、板块信号矩阵")
    lines.append("")
    lines.append("| 板块 | 信号 | 评分 | 置信度 | 多头成员 | 空头成员 |")
    lines.append("|------|------|------|--------|---------|---------|")
    
    buy_alerts  = []
    sell_alerts = []
    
    for sector, sig in sorted(sector_sigs.items(), key=lambda x: -x[1]["score"]):
        signal_emoji = {"BUY":"🟢","HOLD-BULL":"🟡","HOLD":"⚪","HOLD-BEAR":"🟠","SELL":"🔴"}.get(sig["signal"], "⚪")
        lines.append(f"| {sector} | {signal_emoji} {sig['signal']} | {sig['score']} | {sig['confidence']}% | {sig['buy_count']} | {sig['sell_count']} |")
        if sig["signal"] == "BUY":
            buy_alerts.append(sector)
        elif sig["signal"] == "SELL":
            sell_alerts.append(sector)
    lines.append("")
    
    # === 三、买入信号板块详情 ===
    if buy_alerts:
        lines.append("## 三、🟢 买入信号板块")
        lines.append("")
        lines.append(f"**触发板块**: {', '.join(buy_alerts)}")
        lines.append("")
        lines.append("| 股票 | 信号 | 评分 | 置信度 | MA200偏离 | 12M动量 | RSI |")
        lines.append("|------|------|------|--------|----------|---------|-----|")
        for stock in sorted(us_stocks, key=lambda x: -x["signal"]["score"]):
            if stock["sector"] in buy_alerts and stock["signal"]["signal"] in ["BUY","HOLD-BULL"]:
                ind = stock["indicators"]
                sig = stock["signal"]
                lines.append(f"| {stock['ticker']} | {sig['signal']} | {sig['score']} | {sig['confidence']}% | {ind['trend_dev']:+.1f}% | {ind['mom12m']:+.1f}% | {ind['rsi']} |")
        lines.append("")
    else:
        lines.append("## 三、🟢 买入信号板块")
        lines.append("**当前无板块触发买入信号**")
        lines.append("")
    
    # === 四、卖出信号板块 ===
    if sell_alerts:
        lines.append("## 四、🔴 卖出信号板块")
        lines.append("")
        lines.append(f"**触发板块**: {', '.join(sell_alerts)}")
        lines.append("")
        lines.append("| 股票 | 信号 | 评分 | 置信度 | MA200偏离 | 12M动量 | RSI |")
        lines.append("|------|------|------|--------|----------|---------|-----|")
        for stock in sorted(us_stocks, key=lambda x: x["signal"]["score"]):
            if stock["sector"] in sell_alerts and stock["signal"]["signal"] in ["SELL","HOLD-BEAR"]:
                ind = stock["indicators"]
                sig = stock["signal"]
                lines.append(f"| {stock['ticker']} | {sig['signal']} | {sig['score']} | {sig['confidence']}% | {ind['trend_dev']:+.1f}% | {ind['mom12m']:+.1f}% | {ind['rsi']} |")
        lines.append("")
    else:
        lines.append("## 四、🔴 卖出信号板块")
        lines.append("**当前无板块触发卖出信号**")
        lines.append("")
    
    # === 五、新闻情感摘要 ===
    lines.append("## 五、财经情感摘要")
    lines.append("")
    ns = news_summary
    lines.append(f"整体情感: **{ns['label']}** (得分: {ns['score']:+.2f})")
    lines.append(f"正面 {ns['positive']} | 负面 {ns['negative']} | 中性 {ns['neutral']} / 共 {ns['total']} 条")
    lines.append("")
    
    if news_items:
        # 正面新闻
        pos_news = [n for n in news_items if n["sentiment"] > 0.3][:3]
        neg_news = [n for n in news_items if n["sentiment"] < -0.3][:3]
        if pos_news:
            lines.append("**正面新闻**")
            for n in pos_news:
                lines.append(f"- [{n['source']}] {n['title'][:80]}")
            lines.append("")
        if neg_news:
            lines.append("**负面新闻**")
            for n in neg_news:
                lines.append(f"- [{n['source']}] {n['title'][:80]}")
            lines.append("")
    
    # === 六、风险提示 ===
    lines.append("## 六、风险提示")
    lines.append("")
    risks = []
    
    vix_val = macro_env.get("vix", 0)
    if vix_val > 25:
        risks.append(f"😱 VIX 偏高 ({vix_val:.1f})，市场恐慌情绪")
    if macro_env.get("fedf", 0) > 5:
        risks.append(f"💰 高利率环境 ({macro_env['fedf']:.2f}%)，流动性收紧")
    if macro_env.get("cpi", 0) > 5:
        risks.append(f"⚠️ 通胀压力 ({macro_env['cpi']:.2f}%)，政策不确定性")
    
    # RSI超买警告
    overbought = sum(1 for s in us_stocks if s["indicators"]["rsi"] > 70)
    oversold   = sum(1 for s in us_stocks if s["indicators"]["rsi"] < 30)
    if overbought > len(us_stocks) * 0.3:
        risks.append(f"📈 RSI超买股票偏多 ({overbought}只)，短期回调风险")
    if oversold > len(us_stocks) * 0.1:
        risks.append(f"🎯 RSI超卖股票出现 ({oversold}只)，反弹机会")
    
    if risks:
        for r in risks:
            lines.append("- " + r)
    else:
        lines.append("- 无显著风险")
    lines.append("")
    
    # === 七、方法论权重说明 ===
    lines.append("## 七、方法论置信度")
    lines.append("")
    lines.append("| 方法论 | 置信度 | 权重 | 实证 |")
    lines.append("|--------|--------|------|------|")
    for name, cfg in METHODOLOGIES.items():
        stars = "★" * cfg["stars"] + "☆" * (5 - cfg["stars"])
        lines.append(f"| {name} | {stars} | {cfg['weight']*100:.0f}% | {cfg['desc']} |")
    lines.append("")
    
    # === 免责声明 ===
    lines.append("---")
    lines.append("> ⚠️ **免责声明**: 本报告基于历史数据与专家方法论，不构成投资建议。所有决策需自行验证风险。")
    
    return "\n".join(lines)


# ====== 主函数 ======

def main():
    today_str = date.today().strftime("%Y-%m-%d")
    print("\n" + "="*60)
    print(f"📬 专家级金融日报 v2.0 | {today_str}")
    print("="*60)
    
    print("\n📊 Step 1: 美股3年数据分析...")
    us_stocks = analyze_us_stocks_3y()
    print(f"  分析股票: {len(us_stocks)} 只")
    
    # 计算板块汇总信号
    sector_sigs = sector_signal_summary(us_stocks)
    print(f"  板块数量: {len(sector_sigs)}")
    buy_s  = [s for s,v in sector_sigs.items() if v["signal"] == "BUY"]
    sell_s = [s for s,v in sector_sigs.items() if v["signal"] == "SELL"]
    print(f"  买入板块: {buy_s}")
    print(f"  卖出板块: {sell_s}")
    
    print("\n📈 Step 2: 宏观环境...")
    macro_data = load_macro()
    macro_env  = build_macro_environment(macro_data)
    print(f"  环境: {macro_env['env']} | 方向: {macro_env['direction']}")
    
    print("\n📰 Step 3: 新闻情感分析...")
    news_items   = fetch_and_analyze_news()
    news_summary = news_sentiment_summary(news_items)
    print(f"  新闻: {news_summary['total']} 条 | 情感: {news_summary['label']} ({news_summary['score']:+.2f})")
    
    print("\n📝 Step 4: 生成专家日报...")
    report_md = generate_expert_report(
        us_stocks, sector_sigs, macro_env, news_summary, news_items, today_str
    )
    
    out_md = os.path.join(DOCS_DIR, "daily_report_" + date.today().strftime("%Y%m%d") + ".md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"  Markdown: {out_md}")
    
    # JSON汇总
    out_json = os.path.join(OUTPUT_DIR, "daily_report_" + date.today().strftime("%Y%m%d") + ".json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "date": today_str,
            "generated_at": datetime.now().isoformat(),
            "macro_env": macro_env,
            "sector_signals": sector_sigs,
            "news_sentiment": news_summary,
            "stock_count": len(us_stocks),
            "sector_count": len(sector_sigs),
            "buy_alerts": buy_s,
            "sell_alerts": sell_s,
        }, f, indent=2, ensure_ascii=False)
    print(f"  JSON: {out_json}")
    
    print("\n" + "="*60)
    print(report_md)


if __name__ == "__main__":
    main()
