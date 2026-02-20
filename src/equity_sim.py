import duckdb
import pandas as pd
import numpy as np

def main():
    con = duckdb.connect('data/db/market.duckdb', read_only=True)
    query = '''
    WITH Metrics AS (
        SELECT 
            h.symbol, h.open_time,
            (MAX(h.high) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 48 PRECEDING AND 1 PRECEDING) - 
             MIN(h.low) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 48 PRECEDING AND 1 PRECEDING)) / NULLIF(h.close, 0) as comp,
            AVG(h.volume) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 12 PRECEDING AND 1 PRECEDING) / 
            NULLIF(AVG(h.volume) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 168 PRECEDING AND 13 PRECEDING), 0) as rvol
        FROM candles_1h h
    ),
    Pumps AS (
        SELECT symbol, open_time, ((high - low)/low)*100 as move FROM candles_daily
    )
    SELECT p.open_time, p.symbol, p.move
    FROM Pumps p
    JOIN Metrics m ON p.symbol = m.symbol AND p.open_time = m.open_time
    WHERE m.comp < 0.04 AND m.rvol BETWEEN 1.5 AND 3.0
    ORDER BY p.open_time
    '''
    df = con.execute(query).df()
    
    capital = 1000.0
    history = []
    
    print(f"{'Date':<12} | {'Symbol':<10} | {'Move %':<8} | {'Equity':<10}")
    print("-" * 50)
    
    for _, row in df.iterrows():
        trade_size = capital * 0.1
        profit = trade_size * (row['move'] / 100) - (trade_size * 0.002)
        capital += profit
        history.append(capital)
        date_str = pd.to_datetime(row['open_time'], unit='ms').strftime('%Y-%m-%d')
        print(f"{date_str:<12} | {row['symbol']:<10} | {row['move']:>7.1f}% | ")

    # Сохраняем для Excel
    pd.DataFrame({'equity': history}).to_csv('data/equity_curve.csv', index=False)
    
    print("\n--- ГРАФИК РОСТА КАПИТАЛА (ASCII) ---")
    min_c = min(history)
    max_c = max(history)
    for val in history:
        bar = "#" * int((val - min_c) / (max_c - min_c) * 40 + 1)
        print(f" {bar}")

    con.close()

if __name__ == '__main__':
    main()