import duckdb
import pandas as pd

def main():
    con = duckdb.connect('data/db/market.duckdb', read_only=True)
    
    print("--- SCANNING FOR GOLDEN PATTERNS (TOP 20) ---")
    
    query = '''
    WITH RawStep AS (
        SELECT 
            h.symbol,
            h.open_time,
            h.high,
            h.low,
            h.close,
            h.volume,
            -- Шаг 1: Считаем рост low относительно предыдущего (внутренний слой)
            CASE WHEN h.low > LAG(h.low) OVER(PARTITION BY h.symbol ORDER BY h.open_time) THEN 1 ELSE 0 END as is_higher
        FROM candles_1h h
    ),
    PrePumpMetrics AS (
        SELECT 
            s.symbol,
            s.open_time,
            -- Индекс сжатия: (Max-Min)/Close за 48 часов
            (MAX(s.high) OVER(PARTITION BY s.symbol ORDER BY s.open_time ROWS BETWEEN 48 PRECEDING AND 1 PRECEDING) - 
             MIN(s.low) OVER(PARTITION BY s.symbol ORDER BY s.open_time ROWS BETWEEN 48 PRECEDING AND 1 PRECEDING)) 
             / NULLIF(s.close, 0) as compression,
            
            -- RVOL: Средний объем за 12ч против средней недели (168ч)
            AVG(s.volume) OVER(PARTITION BY s.symbol ORDER BY s.open_time ROWS BETWEEN 12 PRECEDING AND 1 PRECEDING) / 
            NULLIF(AVG(s.volume) OVER(PARTITION BY s.symbol ORDER BY s.open_time ROWS BETWEEN 168 PRECEDING AND 13 PRECEDING), 0) as rvol,
            
            -- Шаг 2: Суммируем лесенку (внешний слой)
            SUM(is_higher) OVER(PARTITION BY s.symbol ORDER BY s.open_time ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING) as ladder_score
        FROM RawStep s
    ),
    Pumps AS (
        SELECT symbol, open_time, ((high - low)/low)*100 as move 
        FROM candles_daily WHERE move >= 20
    )
    SELECT 
        p.symbol,
        CAST(epoch_ms(p.open_time) AS DATE) as date,
        ROUND(m.compression, 4) as comp_idx,
        ROUND(m.rvol, 2) as rvol_idx,
        m.ladder_score,
        ROUND(p.move, 1) as result_move
    FROM Pumps p
    JOIN PrePumpMetrics m ON p.symbol = m.symbol AND p.open_time = m.open_time
    WHERE m.compression < 0.08 
      AND m.rvol > 2.0
    ORDER BY p.move DESC
    LIMIT 20
    '''
    
    try:
        df = con.execute(query).df()
        if not df.empty:
            print("\nSUCCESS! FOUND TOP 20 MATCHES:")
            print(df.to_string(index=False))
            df.to_csv('data/top_20_matches.csv', index=False)
            print("\n[+] Report saved to: data/top_20_matches.csv")
        else:
            print("\n[-] No matches found. Try loosening filters.")
    except Exception as e:
        print(f"\n[!] SQL Error: {e}")
    finally:
        con.close()

if __name__ == '__main__':
    main()