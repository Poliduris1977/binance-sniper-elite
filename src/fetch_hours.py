import requests
import pandas as pd
import duckdb
from datetime import datetime, timedelta
import time

def main():
    db_path = 'data/db/market.duckdb'
    con = duckdb.connect(db_path)
    
    # Создаем таблицу, если её нет
    con.execute("CREATE TABLE IF NOT EXISTS candles_1h (symbol VARCHAR, open_time BIGINT, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE)")

    # 1. Получаем ВЕСЬ список событий
    print("--- PREPARING FULL EVENT LIST ---")
    targets = con.execute('''
        WITH FirstDays AS (SELECT symbol, MIN(open_time) as ft FROM candles_daily GROUP BY symbol)
        SELECT c.symbol, c.open_time as event_ts, CAST(epoch_ms(c.open_time) AS DATE) as date
        FROM candles_daily c 
        JOIN FirstDays f ON c.symbol = f.symbol
        WHERE c.open_time > f.ft 
          AND ((c.high - c.low) / c.low) * 100 >= 20 
          AND (c.volume * c.close) >= 10000000
        ORDER BY c.open_time DESC
    ''').fetchall()
    
    total = len(targets)
    print(f"Total events to process: {total}")

    for i, (symbol, event_ts, t_date) in enumerate(targets):
        # Окно: -10 дней и +5 дней
        start_ts = int(event_ts - (10 * 24 * 60 * 60 * 1000))
        end_ts = int(event_ts + (5 * 24 * 60 * 60 * 1000))

        # Проверяем, есть ли уже данные за этот период для этой монеты в нашей базе
        # Проверяем наличие хотя бы 80% данных в этом диапазоне, чтобы не качать лишнее
        existing_count = con.execute('''
            SELECT count(*) FROM candles_1h 
            WHERE symbol = ? AND open_time BETWEEN ? AND ?
        ''', [symbol, start_ts, end_ts]).fetchone()[0]

        if existing_count > 300: # Примерно 12-13 дней данных уже есть
            print(f"[{i+1}/{total}] Skipping {symbol} {t_date} (Data already exists)")
            continue

        print(f"[{i+1}/{total}] Fetching {symbol} for {t_date}...")
        
        all_klines = []
        current_ts = start_ts
        while current_ts < end_ts:
            url = "https://fapi.binance.com/fapi/v1/klines"
            params = {"symbol": symbol, "interval": "1h", "startTime": current_ts, "limit": 1000}
            try:
                resp = requests.get(url, params=params, timeout=10).json()
                if not resp or 'code' in resp: break
                for k in resp:
                    if k[0] >= end_ts: break
                    all_klines.append([symbol, k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])])
                current_ts = resp[-1][0] + 3600000
                if len(resp) < 1000: break
            except:
                time.sleep(1)
                continue
        
        if all_klines:
            df = pd.DataFrame(all_klines, columns=['symbol', 'open_time', 'open', 'high', 'low', 'close', 'volume'])
            # Используем INSERT OR IGNORE логику через временную таблицу, чтобы избежать дублей
            con.execute("CREATE TEMP TABLE temp_h AS SELECT * FROM df")
            con.execute('''
                INSERT INTO candles_1h 
                SELECT t.* FROM temp_h t
                LEFT JOIN candles_1h c ON t.symbol = c.symbol AND t.open_time = c.open_time
                WHERE c.open_time IS NULL
            ''')
            con.execute("DROP TABLE temp_h")
        
        # Чтобы Binance не забанил за агрессивный парсинг
        if i % 10 == 0: time.sleep(0.5)

    con.close()
    print("--- ALL DATA LOADED SUCCESSFULLY ---")

if __name__ == '__main__':
    main()