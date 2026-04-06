#!/usr/bin/env python3
"""
batch_download.py
全量美股并行下载 — S&P 500 成分股 (约500只)
使用 AKShare stock_us_daily + ThreadPoolExecutor

单只耗时: ~3-5秒
500只 × 8线程 ≈ 4-6分钟

用法:
  python3 batch_download.py --sp500 --days 365 --workers 8
  python3 batch_download.py --tickers AAPL MSFT --days 30
"""

import os
import sys
import csv
import time
import argparse
import warnings
import threading
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "mock_data")
os.makedirs(DATA_DIR, exist_ok=True)

# ========== S&P 500 成分股列表 ==========
SP500_TICKERS = sorted(set([
    "MMM","AOS","ABT","ABBV","ABNB","ACN","ADBE","AEP","AES","AFL","A","APD",
    "AKAM","ALB","ARE","ALGN","ALLE","LNT","ALL","GOOGL","GOOG","MO","AMZN",
    "AMGN","APH","ADI","ANSS","AAPL","AMAT","APTV","ACA","AR","ADM","AJG",
    "AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","AXON","BALL","BAC",
    "BKNG","BAX","BDX","BBY","BIIB","BLK","BA","BMY","BRO","AVGO","BF.B",
    "BOX","BXP","BSX","BUR","CDW","CARR","CTVA","CAT","CBOE","CB","CDNS",
    "CPT","CE","CHD","CNP","CINF","CTAS","CSCO","C","CF","SCHW","CSGP",
    "CVS","CVX","CME","CMS","KO","CL","CMCSA","CMA","CAG","COP","ED","STZ",
    "COO","CPRT","GLW","CTVA","CSRA","CVE","CI","CLX","CNC","COF","CAH",
    "KSU","K","KMB","KIM","KMI","KLAC","LHX","LRCX","LW","LEG","LEN","LLY",
    "LNC","LIN","LYB","MTD","MKC","MCD","MCK","MDT","MRK","META","MET",
    "MAA","MMC","MLM","MAS","MTB","MCO","MS","MOS","MSI","MSCI","NDAQ",
    "NTAP","NTRS","NDSN","NKE","NI","NSC","NOC","NUE","NVDA","NVR","NXPI",
    "ORLY","OXY","ODFL","OMC","ON","OKE","ORCL","PCAR","PKG","PARA","PH",
    "PAYX","PAYC","PYPL","PNR","QCOM","DGX","RTX","RE","RF","RSG","RMD",
    "RVTY","RHI","ROK","ROP","RCL","SPGI","SBAC","CRM","SLB","STX","SRE",
    "SHW","SPG","SWKS","SJM","SNA","SO","LUV","SWK","SBUX","STT","STLD",
    "SYK","SYY","TMUS","TGT","TFC","TJX","TSCO","TT","TPR","TXN","TXT",
    "TMO","TRV","TSN","USB","UDR","ULTA","UNP","UAL","UPS","URI","UNH",
    "VLO","V","VRSK","VMC","VRSN","VRTX","VZ","VTRS","VICI","WMT","WBA",
    "WFC","WELL","WMB","WST","WDC","WU","WM","WYNN","XEL","XYL","YUM",
    "ZBH","ZBRA","ZTS","AAL","APLS","AMT","BKR","CBOE","CB","CHTR","CME",
    "CPRT","DAL","DFS","DG","DHI","DHR","DLR","DOC","DOV","DOW","DXC",
    "EA","ECL","EFX","EIX","EMN","EMR","ENPH","EQR","ES","ETN","ETR",
    "EVRG","EXC","EXPE","EXR","F","FANG","FAST","FCX","FDS","FDX","FITB",
    "FRC","FSLR","FTNT","GD","GE","GILD","GIS","GM","GNRC","GS","GWW",
    "HAL","HAS","HBAN","HCA","HES","HII","HLT","HPE","HPQ","HRL","HSY",
    "HUM","HWM","ICLR","IDXX","IEX","IFF","ILMN","INCY","INGR","INTU",
    "INVH","IQV","IR","IRM","IT","ITW","IVZ","J","JBHT","JCI","JKHY",
    "JNJ","JPM","KEY","KEYS","KHC","KR","L","LDOS","LH","LKQ","LLY",
    "LMT","LOGI","LOW","LYB","MA","MAR","MASI","MAT","MCD","MCK","MCO",
    "MDLA","MDT","MFC","MHK","MLM","MNST","MOS","MPC","MSCI","MSFT",
    "MTCH","MTD","MU","NDAQ","NEE","NEM","NFLX","NOC","NOV","NRG","NSC",
    "NTAP","NUE","NWL","O","ODFL","OFC","OMC","ON","ORCL","ORLY","OTIS",
    "OXY","PAYC","PCAR","PCG","PEAK","PEG","PGR","PH","PKG","PKI","PLD",
    "PM","PNC","PNW","PPG","PPL","PRU","PSA","PTC","PWR","PXD","QCOM",
    "RCL","RE","RF","RMD","ROK","ROL","ROST","RSG","RTX","SBAC","SBUX",
    "SCHW","SEDG","SHW","SJM","SLB","SNPS","SO","SPG","SPGI","SRE","STE",
    "STZ","SWK","SWKS","SYY","T","TAP","TDG","TEL","TGT","TJX","TMO",
    "TPR","TRGP","TROW","TT","TTWO","TXN","UAL","UBER","UDR","UNH","UNP",
    "USB","V","VLO","VRSK","VRTX","WAB","WAT","WBA","WDAY","WDC","WEC",
    "WFC","WM","WRB","WTW","WY","WYNN","XEL","XOM","XRAY","ZION","ZTS"
]))

print(f"S&P 500 tickers: {len(SP500_TICKERS)}")

# ========== 全局锁 + 计数器 ==========
write_lock = threading.Lock()
counter_lock = threading.Lock()
done_count = [0]

def write_rows(path, rows, header):
    with write_lock:
        file_exists = os.path.exists(path)
        with open(path, "a", newline="") as f:
            w = csv.writer(f)
            if not file_exists:
                w.writerow(header)
            w.writerows(rows)

def fetch_one(ticker, days, output_path, header):
    import akshare as ak
    try:
        end_dt   = date.today()
        start_dt = end_dt - timedelta(days=days)
        start_s  = start_dt.strftime("%Y-%m-%d")
        end_s    = end_dt.strftime("%Y-%m-%d")

        df = ak.stock_us_daily(symbol=ticker, adjust="qfq")
        df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
        df = df[(df["date_str"] >= start_s) & (df["date_str"] <= end_s)]

        rows = []
        for _, row in df.iterrows():
            rows.append((
                row["date_str"], ticker,
                float(row["open"]), float(row["high"]),
                float(row["low"]), float(row["close"]),
                int(row["volume"]),
            ))

        write_rows(output_path, rows, header)

        with counter_lock:
            done_count[0] += 1
            print(f"  ✅ [{done_count[0]}/{total_tickers}] {ticker}: {len(rows)} 条", flush=True)
        return True

    except Exception as e:
        with counter_lock:
            done_count[0] += 1
            print(f"  ❌ [{done_count[0]}/{total_tickers}] {ticker}: {e}", flush=True)
        return False

# ========== 主函数 ==========

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="+", default=None)
    parser.add_argument("--sp500", action="store_true")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    global total_tickers
    if args.tickers:
        tickers = args.tickers
    elif args.sp500:
        tickers = SP500_TICKERS
    else:
        print("用法: --sp500 或 --tickers AAPL MSFT NVDA")
        sys.exit(1)

    total_tickers = len(tickers)
    output_path = os.path.join(DATA_DIR, "market_data_us_batch.csv")
    header = ["date","ticker","open","high","low","close","volume"]

    # 清空旧文件
    if os.path.exists(output_path):
        os.remove(output_path)

    print(f"\n{'='*55}")
    print(f"📡 全量下载 | {total_tickers} 只 | {args.days}天 | {args.workers}线程")
    print(f"{'='*55}")

    t0 = time.time()
    success = 0
    fail = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(fetch_one, t, args.days, output_path, header): t
            for t in tickers
        }
        for f in as_completed(futures):
            if f.result():
                success += 1
            else:
                fail += 1

    elapsed = time.time() - t0
    print(f"\n✅ 完成！耗时: {elapsed:.0f}秒 | 成功: {success} | 失败: {fail}")
    if os.path.exists(output_path):
        sz = os.path.getsize(output_path)
        print(f"   文件: {output_path} ({sz/1024:.0f} KB)")

if __name__ == "__main__":
    main()
