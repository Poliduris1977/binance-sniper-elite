import duckdb
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
    TrapStats AS (
        SELECT 
            ((d.low - d.open) / d.open) * 100 as drawdown
        FROM Metrics m
        JOIN candles_daily d ON m.symbol = d.symbol AND m.open_time = d.open_time
        WHERE m.comp BETWEEN 0.04 AND 0.08 AND m.rvol BETWEEN 3.0 AND 5.0
    )
    SELECT 
        AVG(drawdown) as avg_trap_drop,
        MIN(drawdown) as max_trap_crash
    FROM TrapStats
    '''
    res = con.execute(query).df()
    print("\n--- TRAP DOWNSIDE ANALYSIS ---")
    print(res.to_string(index=False))
    con.close()
if __name__ == '__main__':
    main()