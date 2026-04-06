#!/usr/bin/env python3
"""
data_fetcher.py — Quant_Analyst 数据获取层 v2.0
基于 AKShare(美股) + Tencent Finance API(港股)

更新 (2026-04-04):
- 港股改用 Tencent Finance API (web.ifzq.gtimg.cn) 替代被封的 Eastmoney
- 支持 3年+ 历史港股K线数据
- 港股代码映射 Sina realtime -> Tencent format

已知限制:
- AKShare 宏观数据多数依赖 Eastmoney，仅部分可用
- FRED 在国内网络不通

用法:
  python3 data_fetcher.py --type us_stocks --days 365
  python3 data_fetcher.py --type hk_stocks --days 1095   # 3年
  python3 data_fetcher.py --type hk_stocks --days 730    # 2年
  python3 data_fetcher.py --type all --days 1095
"""

import os, sys, csv, json, argparse, warnings, re
from datetime import date, timedelta

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "mock_data")
os.makedirs(DATA_DIR, exist_ok=True)

try:
    import akshare as ak
    AKSHARE_OK = True
except Exception:
    AKSHARE_OK = False

# ========== 配置 ==========

US_TICKERS = [
    "AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","AVGO",
    "ORCL","CRM","ADBE","CSCO","INTC","AMD","PEP","KO","COST",
    "WMT","JNJ","UNH","PFE","ABBV","TMO","JPM","BAC","WFC",
    "GS","XOM","CVX","COP","BA","CAT","GE","MMM","DIS","CMCSA",
    "VZ","T","AMT","PLD","CCI","LMT","NOC","RTX","NFLX","QCOM"
]

# 港股 ticker 映射: (Sina代码, Tencent代码)
# Sina代码用于实时行情，Tencent代码用于历史K线
HK_TICKERS = [
    ("0700.HK", "00700", "腾讯"),
    ("3690.HK", "03690", "美团"),
    ("9988.HK", "09988", "阿里巴巴"),
    ("1810.HK", "01810", "小米"),
    ("2382.HK", "02382", "舜宇光学"),
    ("9618.HK", "09618", "京东"),
    ("9633.HK", "09633", "农夫山泉"),
    ("2333.HK", "02333", "长城汽车"),
    ("3968.HK", "03968", "招商银行"),
    ("3988.HK", "03988", "中国银行"),
    ("1398.HK", "01398", "工商银行"),
    ("0939.HK", "00939", "建设银行"),
    ("2628.HK", "02628", "中国人寿"),
    ("2319.HK", "02319", "蒙牛乳业"),
    ("0941.HK", "00941", "中国移动"),
    ("0668.HK", "00668", "中国海外"),
    ("1658.HK", "01658", "邮储银行"),
    ("1109.HK", "01109", "华润置地"),
    ("2270.HK", "02270", "金斯瑞"),
    ("0175.HK", "00175", "吉利汽车"),
    ("6618.HK", "06618", "微盟"),
    ("3333.HK", "03333", "中国恒大"),
    ("3888.HK", "03888", "金山软件"),
    ("2899.HK", "02899", "紫金矿业"),
    ("9999.HK", "09999", "网易"),
    ("0772.HK", "00772", "联想"),
    ("2269.HK", "02269", "京东健康"),
    ("2689.HK", "02689", "永升服务"),
    ("6969.HK", "06969", "融创中国"),
    ("6888.HK", "06888", "微盟集团"),
    ("0011.HK", "00011", "中国平安"),
    ("0388.HK", "00388", "港交所"),
]


def write_csv(path, rows, header):
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(header)
        w.writerows(rows)


# ========== 1. 美股 (AKShare) ==========

def fetch_us_stocks(days=365):
    records = []
    end_dt   = date.today()
    start_dt = end_dt - timedelta(days=days)
    start_s  = start_dt.strftime("%Y-%m-%d")
    end_s    = end_dt.strftime("%Y-%m-%d")

    for ticker in US_TICKERS:
        print(f"  {ticker}: ", end="", flush=True)
        try:
            df = ak.stock_us_daily(symbol=ticker, adjust="qfq")
            df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
            df = df[(df["date_str"] >= start_s) & (df["date_str"] <= end_s)]
            for _, row in df.iterrows():
                records.append((
                    row["date_str"], ticker,
                    float(row["open"]), float(row["high"]),
                    float(row["low"]),  float(row["close"]),
                    int(row["volume"]),
                ))
            print(f"{len(df)} 条", flush=True)
        except Exception as e:
            print(f"失败: {e}", flush=True)
    return records


# ========== 2. 港股 (Tencent Finance API) ==========
# Eastmoney 被封，改用 Tencent Finance API
# API: https://web.ifzq.gtimg.cn/appstock/app/fqkline/get
# 支持 3年+ 历史数据，回调格式

def fetch_hk_stocks(days=1095):
    """
    使用 Tencent Finance API 获取港股历史K线
    days: 获取多少天的历史数据 (默认3年=1095天)
    """
    import urllib.request
    records = []
    end_dt   = date.today()
    start_dt = end_dt - timedelta(days=days)
    start_s  = start_dt.strftime("%Y-%m-%d")
    end_s    = end_dt.strftime("%Y-%m-%d")
    headers  = {"User-Agent": "Mozilla/5.0"}

    for sina_code, tencent_code, name in HK_TICKERS:
        print(f"  {sina_code}({name}): ", end="", flush=True)
        # Tencent Finance API - 历史K线
        # 注意: 最多获取约2000条记录，但需要分多次请求获取更长区间
        url = (
            f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            f"?_var=kline_dayhfq"
            f"&param=hk{tencent_code},day,{start_s},{end_s},{days},qfq"
        )
        try:
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=15)
            raw = resp.read().decode("utf-8")

            # 解析 JSONP 格式: kline_dayhfq={...}
            m = re.match(r'kline_dayhfq=(.+)', raw)
            if not m:
                print("解析失败", flush=True)
                continue

            j = json.loads(m.group(1))
            stock_data = j.get("data", {}).get(f"hk{tencent_code}", {}).get("day", [])
            count = 0
            for entry in stock_data:
                # 格式: ["2025-06-13","510.500","510.000","515.500","506.000","19085310.000",{...}]
                try:
                    d      = entry[0]
                    open_  = float(entry[1])
                    close  = float(entry[2])
                    high   = float(entry[3])
                    low    = float(entry[4])
                    vol    = int(float(entry[5])) if len(entry) > 5 else 0
                    if start_s <= d <= end_s:
                        records.append((d, sina_code, open_, high, low, close, vol))
                        count += 1
                except (ValueError, IndexError):
                    continue
            print(f"{count} 条", flush=True)
        except Exception as e:
            print(f"失败: {e}", flush=True)
    return records


# ========== 3. 港股实时快照 (Sina) — 保留用于趋势参考 ==========

def fetch_hk_snapshot():
    """获取港股实时快照 (Sina realtime API)"""
    import urllib.request
    codes = []
    ticker_map = {}
    for sina_code, tencent_code, name in HK_TICKERS:
        code = "hk" + tencent_code.zfill(5)
        codes.append(code)
        ticker_map[code] = sina_code

    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"}
    url = "https://hq.sinajs.cn/list=" + ",".join(codes)
    records = {}

    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode("gbk", errors="ignore")
        today_s = date.today().strftime("%Y-%m-%d")

        for line in raw.strip().split("\n"):
            if "=" not in line:
                continue
            parts0 = line.split("hq_str_")
            if len(parts0) < 2:
                continue
            ticker_code = parts0[1].split("=")[0]
            ticker_hk = ticker_map.get(ticker_code, ticker_code + ".HK")
            data_part = line.split('="')[1].split('"')[0]
            fields = data_part.split(",")
            if len(fields) < 5 or not fields[0]:
                continue
            close = float(fields[3]) if fields[3] else 0.0
            prev  = float(fields[4]) if (len(fields) > 4 and fields[4]) else close
            chg   = (close - prev) / prev * 100 if prev else 0.0
            records[ticker_hk] = {
                "date": today_s, "ticker": ticker_hk,
                "name": fields[0], "close": close, "change_pct": round(chg, 2)
            }
    except Exception as e:
        print(f"  Sina realtime failed: {e}")

    return records


# ========== 4. 宏观 (AKShare — 测试可用的) ==========

def fetch_macro(days=365):
    records = []
    end_dt   = date.today()
    start_dt = end_dt - timedelta(days=days)
    start_s  = start_dt.strftime("%Y-%m-%d")
    end_s    = end_dt.strftime("%Y-%m-%d")

    # 美联储利率 (FRED)
    print(f"  联邦基金利率: ", end="", flush=True)
    try:
        df = ak.fred_md()
        df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
        df = df[(df["date_str"] >= start_s) & (df["date_str"] <= end_s)]
        for _, row in df.iterrows():
            records.append((str(row["date_str"])[:10], "FEDFUNDS", float(row["value"]), "US"))
        print(f"{len(df)} 条", flush=True)
    except Exception as e:
        print(f"失败: {e}", flush=True)

    # VIX
    print(f"  VIX: ", end="", flush=True)
    try:
        df = ak.vix()
        date_col = [c for c in df.columns if "date" in c.lower()][0]
        val_col  = [c for c in df.columns if c != date_col][0]
        df["date_str"] = df[date_col].astype(str).str[:10]
        df = df[(df["date_str"] >= start_s) & (df["date_str"] <= end_s)]
        for _, row in df.iterrows():
            records.append((str(row["date_str"])[:10], "VIX", float(row[val_col]), "US"))
        print(f"{len(df)} 条", flush=True)
    except Exception as e:
        print(f"失败: {e}", flush=True)

    return records


# ========== 主函数 ==========

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", default="all",
                        choices=["all","us_stocks","hk_stocks","macro"])
    parser.add_argument("--days", type=int, default=1095)  # 默认3年
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"📡 数据获取 v2.0 | type={args.type} | days={args.days}")
    print(f"   AKShare: {'✅ ' + ak.__version__ if AKSHARE_OK else '❌ 未安装'}")
    print(f"   港股数据源: Tencent Finance API (替代Eastmoney)")
    print(f"{'='*55}")

    if args.type in ("all", "us_stocks"):
        print("\n📊 美股 (AKShare)")
        recs = fetch_us_stocks(days=args.days)
        if recs:
            path = os.path.join(DATA_DIR, "market_data_us_batch.csv")
            write_csv(path, recs, ["date","ticker","open","high","low","close","volume"])
            print(f"  → 追加写入 {path}")

    if args.type in ("all", "hk_stocks"):
        print("\n📊 港股 (Tencent Finance API — 3年历史)")
        recs = fetch_hk_stocks(days=args.days)
        if recs:
            path = os.path.join(DATA_DIR, "market_data_hk.csv")
            write_csv(path, recs, ["date","ticker","open","high","low","close","volume"])
            print(f"  → 追加写入 {path}")

    if args.type in ("all", "macro"):
        print("\n📉 宏观 (AKShare)")
        recs = fetch_macro(days=args.days)
        if recs:
            path = os.path.join(DATA_DIR, "macro_indicators.csv")
            write_csv(path, recs, ["date","indicator_code","value","country"])
            print(f"  → 追加写入 {path}")

    print("\n✅ 完成！")
    for fname in sorted(os.listdir(DATA_DIR)):
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.isfile(fpath) and not fname.startswith("."):
            sz = os.path.getsize(fpath)
            print(f"   {fname}: {sz/1024:.0f} KB")


if __name__ == "__main__":
    main()
