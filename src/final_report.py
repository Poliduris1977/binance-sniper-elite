import duckdb
import pandas as pd

def main():
    con = duckdb.connect('data/db/market.duckdb', read_only=True)
    
    # 1. Сначала классифицируем монеты (как в прошлом шаге)
    # 2. Затем считаем метрики "Снайпера" для каждой сделки
    query = '''
    WITH Clusters AS (
        SELECT 
            symbol,
            CASE 
                WHEN COUNT(*) < 720 THEN 'Fresh Meat'
                WHEN AVG(volume * close) > 10000000 THEN 'Mainstream'
                ELSE 'Zombies'
            END as cluster
        FROM candles_1h GROUP BY symbol
    ),
    Metrics AS (
        SELECT 
            h.symbol, h.open_time,
            (MAX(h.high) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 48 PRECEDING AND 1 PRECEDING) - 
             MIN(h.low) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 48 PRECEDING AND 1 PRECEDING)) / NULLIF(h.close, 0) as comp,
            AVG(h.volume) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 12 PRECEDING AND 1 PRECEDING) / 
            NULLIF(AVG(h.volume) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 168 PRECEDING AND 13 PRECEDING), 0) as rvol
        FROM candles_1h h
    ),
    FinalData AS (
        SELECT 
            c.cluster,
            ((d.high - d.open) / d.open) * 100 as potential_move
        FROM candles_daily d
        JOIN Metrics m ON d.symbol = m.symbol AND d.open_time = m.open_time
        JOIN Clusters c ON d.symbol = c.symbol
        WHERE m.comp < 0.05 AND m.rvol BETWEEN 1.5 AND 5.0 -- Параметры Снайпера
    )
    SELECT 
        cluster,
        COUNT(*) as total_signals,
        ROUND(AVG(potential_move), 2) as avg_gain,
        ROUND(COUNT(CASE WHEN potential_move > 15 THEN 1 END) * 100.0 / COUNT(*), 1) as win_rate_15pct
    FROM FinalData
    GROUP BY cluster
    '''
    
    df = con.execute(query).df()
    print("\n--- СРАВНИТЕЛЬНЫЙ ОТЧЕТ ПО КЛАСТЕРАМ ---")
    print(df.to_string(index=False))
    con.close()

if __name__ == '__main__':
    main()