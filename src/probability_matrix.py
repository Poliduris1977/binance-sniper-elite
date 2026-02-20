import duckdb
import pandas as pd
import numpy as np

def main():
    con = duckdb.connect('data/db/market.duckdb', read_only=True)
    
    print("--- GENERATING GLOBAL PROBABILITY MATRIX ---")
    
    # Запрос собирает метрики для ВСЕХ событий в базе
    query = '''
    WITH Metrics AS (
        SELECT 
            h.symbol,
            h.open_time,
            (MAX(h.high) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 48 PRECEDING AND 1 PRECEDING) - 
             MIN(h.low) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 48 PRECEDING AND 1 PRECEDING)) / NULLIF(h.close, 0) as comp,
            AVG(h.volume) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 12 PRECEDING AND 1 PRECEDING) / 
            NULLIF(AVG(h.volume) OVER(PARTITION BY h.symbol ORDER BY h.open_time ROWS BETWEEN 168 PRECEDING AND 13 PRECEDING), 0) as rvol
        FROM candles_1h h
    ),
    Pumps AS (
        SELECT symbol, open_time, ((high - low)/low)*100 as move FROM candles_daily
    )
    SELECT 
        m.comp,
        m.rvol,
        p.move
    FROM Pumps p
    JOIN Metrics m ON p.symbol = m.symbol AND p.open_time = m.open_time
    WHERE m.comp IS NOT NULL AND m.rvol IS NOT NULL
    '''
    
    df = con.execute(query).df()
    
    # Создаем категории для матрицы
    df['comp_group'] = pd.cut(df['comp'], bins=[0, 0.04, 0.08, 0.15, 1], labels=['Extreme (0-4%)', 'Tight (4-8%)', 'Loose (8-15%)', 'None (>15%)'])
    df['rvol_group'] = pd.cut(df['rvol'], bins=[0, 1.5, 3, 5, 100], labels=['Normal (0-1.5x)', 'High (1.5-3x)', 'Strong (3-5x)', 'Insane (>5x)'])

    # 1. Матрица среднего профита
    pivot_gain = df.pivot_table(index='comp_group', columns='rvol_group', values='move', aggfunc='mean')
    
    # 2. Матрица вероятности "Супер-Пампа" (>40%)
    df['is_super'] = df['move'] > 40
    pivot_winrate = df.pivot_table(index='comp_group', columns='rvol_group', values='is_super', aggfunc='mean') * 100

    print("\n[1] AVG PROFIT MATRIX (На сколько в среднем растет монета):")
    print(pivot_gain.round(1))
    
    print("\n[2] SUPER-PUMP PROBABILITY (%) (Шанс увидеть рост >40%):")
    print(pivot_winrate.round(1))

    con.close()

if __name__ == '__main__':
    main()