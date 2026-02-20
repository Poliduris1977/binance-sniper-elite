import duckdb

def update_schema(db_path='data/market.duckdb'):
    con = duckdb.connect(db_path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS open_interest (
            symbol VARCHAR,
            open_time TIMESTAMP,
            sum_open_interest DOUBLE,
            sum_open_interest_value DOUBLE,
            PRIMARY KEY (symbol, open_time)
        )
    """)
    con.close()
    print("[+] Database schema updated with OI table.")

if __name__ == "__main__":
    update_schema()