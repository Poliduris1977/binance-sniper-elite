import requests
import pandas as pd
import duckdb
import os
import time
from utils.scanner import get_active_futures_tickers

def main():
    tickers = get_active_futures_tickers()
    all_data = []
    print(f"--- FETCHING DAILY DATA FOR {len(tickers)} TICKERS ---")
    
    for i, symbol in enumerate(tickers):
        if i % 50 == 0: print(f"Progress: {i}/{len(tickers)}...")
        url = "https://fapi.binance.com/fapi/v1/klines"
        # Берем 400 дней, чтобы захватить весь 2025 и начало 2026
        params = {"symbol": symbol, "interval": "1d", "limit": 400}
        try:
            resp = requests.get(url, params=params, timeout=10).json()
            if isinstance(resp, list):
                for k in resp:
                    all_data.append([symbol, k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])])
            time.sleep(0.05) # Защита от бана
        except:
            continue

    if not all_data:
        print("Error: No data fetched!")
        return

    df = pd.DataFrame(all_data, columns=['symbol', 'open_time', 'open', 'high', 'low', 'close', 'volume'])
    
    db_path = 'data/market.duckdb'
    # Подключаемся и сохраняем
    with duckdb.connect(db_path) as con:
        con.execute("DROP TABLE IF EXISTS candles_daily")
        con.execute("CREATE TABLE candles_daily AS SELECT * FROM df")
        
        row_count = con.execute("SELECT count(*) FROM candles_daily").fetchone()[0]
        print(f"\n[+] Saved {row_count} rows to {db_path}")
        
        # Сразу ищем ракеты > 20%
        print("\n--- ROCKETS FOUND (Move Low-High >= 20%) ---")
        report = con.execute('''
            SELECT symbol, 
                   CAST(epoch_ms(open_time) AS DATE) as date, 
                   round(((high - low) / low) * 100, 2) as move_pct,
                   round(volume, 0) as vol
            FROM candles_daily 
            WHERE ((high - low) / low) * 100 >= 20 
            ORDER BY move_pct DESC
        ''').df()
        
        if report.empty:
            print("No 20% moves found in the sampled period.")
        else:
            print(report.to_string(index=False))

if __name__ == '__main__':
    main()