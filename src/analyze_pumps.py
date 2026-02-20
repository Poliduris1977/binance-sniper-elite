import duckdb
import pandas as pd
import numpy as np

def main():
    # ПОДКЛЮЧАЕМСЯ В READ_ONLY, чтобы не мешать скачиванию
    con = duckdb.connect('data/db/market.duckdb', read_only=True)
    
    print("--- STARTING CORRELATION ANALYSIS ---")
    
    # SQL-запрос для вычисления RVOL и Momentum перед каждым пампом
    query = '''
    WITH PrePumpData AS (
        SELECT 
            h.symbol,
            h.open_time,
            h.close,
            h.volume,
            -- Базовый объем (среднее за 168 часов / 1 неделю до события)
            AVG(h.volume) OVER (PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 168 PRECEDING AND 25 PRECEDING) as base_vol,
            -- Базовая цена (для расчета моментума)
            LAG(h.close, 5) OVER (PARTITION BY h.symbol ORDER BY h.open_time) as price_5h_ago
        FROM candles_1h h
    ),
    PumpEvents AS (
        SELECT 
            symbol, 
            open_time as pump_time,
            ((high - low) / low) * 100 as day_move
        FROM candles_daily
        WHERE day_move >= 20
    )
    SELECT 
        p.symbol,
        CAST(epoch_ms(p.pump_time) AS DATE) as date,
        EXTRACT(HOUR FROM epoch_ms(p.pump_time)) as start_hour_utc,
        ROUND(d.volume / NULLIF(d.base_vol, 0), 2) as rvol_1h_before,
        ROUND(((d.close - d.price_5h_ago) / d.price_5h_ago) * 100, 2) as momentum_5h
    FROM PumpEvents p
    JOIN PrePumpData d ON p.symbol = d.symbol AND d.open_time = p.pump_time - 3600000 -- ровно за час до
    WHERE d.base_vol > 0
    ORDER BY rvol_1h_before DESC
    '''
    
    try:
        df = con.execute(query).df()
        
        if df.empty:
            print("Not enough data in candles_1h yet. Keep fetching...")
            return

        print(f"\nAnalyzed {len(df)} pump signatures.")
        
        # 1. Средний всплеск объема
        avg_rvol = df['rvol_1h_before'].median()
        print(f"Median RVOL 1h before pump: {avg_rvol}x")
        
        # 2. Моментум
        positive_momentum = len(df[df['momentum_5h'] > 1]) / len(df) * 100
        print(f"Pumps with positive momentum (+1%+) 5h before: {round(positive_momentum, 2)}%")
        
        # 3. Топ часы
        top_hours = df['start_hour_utc'].value_counts().head(3)
        print("\nTop UTC hours for pumps:")
        print(top_hours)

        # Сохраняем для детального изучения
        df.to_csv('data/pump_signatures.csv', index=False)
        print("\n[!] Full signature report saved to data/pump_signatures.csv")

    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        con.close()

if __name__ == '__main__':
    main()