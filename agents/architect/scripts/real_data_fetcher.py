#!/usr/bin/env python3
"""
real_data_fetcher.py
真实数据源接入（适配国内网络环境）

数据源优先级:
1. Nasdaq API    → 美股历史行情 (AAPL/MSFT/NVDA/TSLA/GOOGL/META/AMZN)
2. Eastmoney API → 港股历史行情 (0700.HK/3690.HK/9988.HK/1810.HK/2382.HK)
                 → A股/港股/美股指数实时
3. World Bank API → 全球宏观 (GDP/人口/贸易数据，年频，需网络支持)
4. FRED          → 海外用户使用，国内可能超时

注意: FRED 在国内网络可能不可达，若超时自动跳过，不阻塞其他数据源。

用法:
  python3 real_data_fetcher.py --type all --days 30
  python3 real_data_fetcher.py --type us_stocks --days 365
  python3 real_data_fetcher.py --type hk_stocks --days 90
  python3 real_data_fetcher.py --type indices          # 更新指数数据
"""

import urllib.request
import json
import csv
import os
import sys
import argparse
import time
from datetime import date, datetime, timedelta

# ========== 配置 ==========

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "mock_data")
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "Nasdaq":    {"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    "Eastmoney": {"User-Agent": "Mozilla/5.0"},
    "WorldBank": {"User-Agent": "Mozilla/5.0"},
    "FRED":      {"User-Agent": "Mozilla/5.0"},
}

US_TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN"]

HK_TICKERS_SECID = {
    "0700.HK": ("116", "00700", "腾讯控股"),
    "3690.HK": ("116", "03690", "美团"),
    "9988.HK": ("116", "09988", "阿里巴巴"),
    "1810.HK": ("116", "01810", "小米"),
    "2382.HK": ("116", "02382", "舜宇光学"),
}

# Eastmoney A股/指数 secid
CN_INDICES = {
    "SHIndex":   ("1", "000001", "上证指数"),
    "SZIndex":   ("0", "399001", "深证成指"),
    "CSI300":    ("1", "000300", "沪深300"),
    "GEM":       ("0", "399006", "创业板"),
}

# Eastmoney 海外指数 secid
GLOBAL_INDICES = {
    "NDX":    ("100", "NDX",     "纳斯达克100"),
    "SPX":    ("100", "SPX",     "标普500"),
    "DJI":    ("100", "DJIA",    "道琼斯"),
    "HSI":    ("116", "HSI",     "恒生指数"),  # 注: Eastmoney历史k线暂不支持恒生指数，用Sina实时替代
    "VIX":    ("100", "VIX",     "VIX恐慌指数"),
}

# ========== 工具函数 ==========

def http_get(url, source, timeout=15):
    headers = HEADERS.get(source, {"User-Agent": "Mozilla/5.0"})
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"    ⚠ [{source}] {str(e)[:60]}")
        return None

def write_csv(path, rows, header):
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerows(rows)

# ========== 1. 美股历史行情 (Nasdaq API) ==========

def fetch_us_stock(ticker, days=365):
    end_dt   = date.today()
    start_dt = end_dt - timedelta(days=days)
    url = (
        f"https://api.nasdaq.com/api/quote/{ticker}/historical"
        f"?assetclass=stocks&fromdate={start_dt.strftime('%Y-%m-%d')}"
        f"&todate={end_dt.strftime('%Y-%m-%d')}&limit=400"
    )
    print(f"  {ticker}: ", end="", flush=True)
    text = http_get(url, "Nasdaq")
    if not text:
        return []
    try:
        data = json.loads(text)
        rows = data["data"]["tradesTable"]["rows"]
    except (KeyError, json.JSONDecodeError):
        return []

    records = []
    for r in rows:
        try:
            records.append((
                datetime.strptime(r["date"], "%m/%d/%Y").strftime("%Y-%m-%d"),
                ticker,
                float(r["open"].replace("$","").replace(",","")),
                float(r["high"].replace("$","").replace(",","")),
                float(r["low"].replace("$","").replace(",","")),
                float(r["close"].replace("$","").replace(",","")),
                int(r["volume"].replace(",","")),
            ))
        except (ValueError, KeyError):
            continue
    print(f"{len(records)} 条", flush=True)
    return records

# ========== 2. 港股历史行情 (Eastmoney) ==========

def fetch_hk_stock(secid, code, days=365):
    end_dt   = date.today()
    start_dt = end_dt - timedelta(days=days)
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?secid={secid}.{code}&fields1=f1,f2,f3,f4,f5"
        f"&fields2=f51,f52,f53,f54,f55&klt=101&fqt=1"
        f"&beg={start_dt.strftime('%Y%m%d')}&end={end_dt.strftime('%Y%m%d')}"
    )
    print(f"  {code}: ", end="", flush=True)
    text = http_get(url, "Eastmoney", timeout=10)
    if not text:
        return []
    try:
        klines = json.loads(text).get("data", {}).get("klines", [])
    except json.JSONDecodeError:
        return []

    records = []
    for kl in klines:
        fields = kl.split(",")
        if len(fields) < 5:
            continue
        try:
            # Eastmoney 日k格式: date, open, close, high, low (基本无成交量)
            records.append((
                fields[0],            # date
                f"{secid}.{code}",   # ticker
                float(fields[1]),     # open
                float(fields[3]),     # high
                float(fields[4]),     # low
                float(fields[2]),     # close
                int(fields[5]) if len(fields) > 5 and fields[5] else 0,
            ))
        except ValueError:
            continue
    print(f"{len(records)} 条", flush=True)
    return records

# ========== 3. 指数实时数据 (Eastmoney) ==========

def fetch_index_realtime(ticker_name, secid=None, market=None, days=30):
    """获取指数历史行情"""
    from datetime import timedelta
    end_dt   = date.today()
    start_dt = end_dt - timedelta(days=days)
    if secid and market:
        url = (
            f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
            f"?secid={secid}.{market}&fields1=f1,f2,f3,f4,f5"
            f"&fields2=f51,f52,f53,f54,f55&klt=101&fqt=1"
            f"&beg={start_dt.strftime('%Y%m%d')}&end={end_dt.strftime('%Y%m%d')}"
        )
    else:
        return []
    print(f"  {ticker_name}: ", end="", flush=True)
    text = http_get(url, "Eastmoney", timeout=10)
    if not text:
        return []
    try:
        resp_data = json.loads(text)
        data_obj = resp_data.get("data") if resp_data else None
        klines = data_obj.get("klines", []) if data_obj else []
    except (json.JSONDecodeError, AttributeError):
        return []

    records = []
    for kl in klines:
        fields = kl.split(",")
        if len(fields) < 5:
            continue
        try:
            # Eastmoney 格式: date, open, close, high, low
            records.append((
                fields[0],       # date
                ticker_name,     # ticker
                float(fields[1]),  # open
                float(fields[3]),  # high
                float(fields[4]),  # low
                float(fields[2]),  # close
                int(fields[5]) if len(fields) > 5 and fields[5] else 0,
            ))
        except ValueError:
            continue
    print(f"{len(records)} 条", flush=True)
    return records

# ========== 4. 宏观数据 (World Bank API) ==========

def fetch_worldbank_indicator(country, indicator, years="2020:2025"):
    """World Bank 年频宏观指标"""
    url = (
        f"http://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        f"?format=json&date={years}&per_page=20"
    )
    text = http_get(url, "WorldBank", timeout=10)
    if not text:
        return []
    try:
        data = json.loads(text)
        records = data[1] if len(data) > 1 else []
        result = []
        for r in records:
            if r.get("value") is not None:
                result.append((
                    f"{r['date']}-12-31",
                    f"{indicator}",
                    r["value"],
                    country,
                ))
        return result
    except (json.JSONDecodeError, IndexError):
        return []

def fetch_macro_indicators(days=365):
    """
    宏观指标合集 (FRED优先，不可用则用WorldBank/其他)
    注意：国内网络FRED可能超时，建议在 --type macro 时单独测试
    """
    all_records = []
    end_dt   = date.today()
    start_dt = end_dt - timedelta(days=days)

    # FRED 系列 (注意：国内可能不通)
    fred_series = {
        "FEDFUNDS": "FEDFUNDS",    # 联邦基金利率
        "CPI":      "CPIAUCSL",     # CPI同比
        "M2":       "M2SL",         # M2
        "SP500":    "SP500",         # 标普500
        "VIX":      "VIXCLS",       # VIX
        "OIL":      "DCOILWTICO",   # WTI原油
    }

    for code, fred_id in fred_series.items():
        url = (
            f"https://fred.stlouisfed.org/graph/fredgraph.csv"
            f"?id={fred_id}&vintage_date={end_dt.strftime('%Y-%m-%d')}"
        )
        print(f"  FRED {code}: ", end="", flush=True)
        text = http_get(url, "FRED", timeout=8)
        if text:
            lines = text.strip().split("\n")
            count = 0
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or "observation_date" in line:
                    continue
                parts = line.split(",")
                if len(parts) >= 2 and start_dt.strftime("%Y-%m-%d") <= parts[0] <= end_dt.strftime("%Y-%m-%d"):
                    try:
                        all_records.append((parts[0], code, float(parts[1]), "US"))
                        count += 1
                    except ValueError:
                        continue
            print(f"{count} 条 (FRED OK)", flush=True)
        else:
            print("超时/失败 (跳过)", flush=True)
        time.sleep(0.3)  # 避免过快请求

    return all_records

# ========== 主函数 ==========

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", default="all",
                        choices=["all","us_stocks","hk_stocks","indices","macro"])
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"📡 真实数据接入 | type={args.type} | days={args.days}")
    print(f"{'='*55}")

    # --- 美股 ---
    if args.type in ("all", "us_stocks"):
        print("\n📊 美股 (Nasdaq API)")
        for ticker in US_TICKERS:
            records = fetch_us_stock(ticker, days=args.days)
            if records:
                write_csv(
                    os.path.join(DATA_DIR, "market_data_us.csv"),
                    records,
                    ["date","ticker","open","high","low","close","volume"]
                )

    # --- 港股 ---
    if args.type in ("all", "hk_stocks"):
        print("\n📊 港股 (Eastmoney)")
        for ticker, (secid, code, name) in HK_TICKERS_SECID.items():
            records = fetch_hk_stock(secid, code, days=args.days)
            if records:
                write_csv(
                    os.path.join(DATA_DIR, "market_data_hk.csv"),
                    records,
                    ["date","ticker","open","high","low","close","volume"]
                )

    # --- 指数 ---
    if args.type in ("all", "indices"):
        print("\n📈 市场指数 (Eastmoney)")
        all_index_records = []

        # A股/港股指数 (美股指数用Nasdaq已覆盖)
        for name, (mkt, code, label) in {**CN_INDICES, **GLOBAL_INDICES}.items():
            recs = fetch_index_realtime(label, secid=mkt, market=code)
            all_index_records.extend(recs)

        if all_index_records:
            write_csv(
                os.path.join(DATA_DIR, "market_data_indices.csv"),
                all_index_records,
                ["date","ticker","open","high","low","close","volume"]
            )

    # --- 宏观 ---
    if args.type in ("all", "macro"):
        print("\n📉 宏观指标 (FRED + WorldBank)")
        # 尝试 FRED
        fred_records = fetch_macro_indicators(days=args.days)
        if fred_records:
            write_csv(
                os.path.join(DATA_DIR, "macro_indicators_fred.csv"),
                fred_records,
                ["date","indicator_code","value","country"]
            )
        # WorldBank 补充
        wb_indicators = [
            ("US", "NY.GDP.MKTP.CD", "GDP_US"),
            ("CN", "NY.GDP.MKTP.CD", "GDP_CN"),
        ]
        for country, indicator, label in wb_indicators:
            print(f"  WB {label}: ", end="", flush=True)
            recs = fetch_worldbank_indicator(country, indicator)
            if recs:
                write_csv(
                    os.path.join(DATA_DIR, "macro_indicators_wb.csv"),
                    recs,
                    ["date","indicator_code","value","country"]
                )
                print(f"{len(recs)} 条")
            else:
                print("无数据或超时")
            time.sleep(0.5)

    print("\n✅ 数据接入完成！")
    print(f"   输出目录: {DATA_DIR}")
    for fname in os.listdir(DATA_DIR):
        fpath = os.path.join(DATA_DIR, fname)
        size = os.path.getsize(fpath)
        print(f"   {fname}: {size/1024:.0f} KB")

if __name__ == "__main__":
    main()
