import duckdb
import pandas as pd

def main():
    con = duckdb.connect('data/db/market.duckdb', read_only=True)
    
    print("--- GENERATING CLUSTER MAP ---")
    
    query = '''
    WITH CoinStats AS (
        SELECT 
            symbol,
            AVG(volume * close) as daily_usd_volume, -- Ликвидность в USD
            COUNT(*) as age_hours,                   -- Возраст (кол-во свечей)
            AVG(((high - low)/low)*100) as avg_volatility -- Средняя "болтанка"
        FROM candles_1h
        GROUP BY symbol
    )
    SELECT 
        symbol,
        CASE 
            WHEN age_hours < 720 THEN 'Fresh Meat'       -- Меньше месяца на бирже
            WHEN daily_usd_volume > 10000000 THEN 'Mainstream' -- Топ по ликвидности
            ELSE 'Zombies'                                -- Всё остальное (старое и тихое)
        END as cluster,
        ROUND(daily_usd_volume/1000000, 2) as vol_mln_usd,
        ROUND(avg_volatility, 2) as volatility_pct
    FROM CoinStats
    ORDER BY cluster, daily_usd_volume DESC
    '''
    
    df = con.execute(query).df()
    
    # Считаем "Профиль" каждого кластера
    profile = df.groupby('cluster').agg({
        'symbol': 'count',
        'volatility_pct': 'mean',
        'vol_mln_usd': 'mean'
    }).rename(columns={'symbol': 'coin_count'})
    
    print("\n[ КАРТА КЛАСТЕРОВ ]")
    print(profile.round(2))
    
    # Сохраняем список, чтобы знать, кто где
    df.to_csv('data/coin_clusters.csv', index=False)
    print("\n[+] Список монет с распределением по кластерам сохранен в data/coin_clusters.csv")
    
    con.close()

if __name__ == '__main__':
    main()