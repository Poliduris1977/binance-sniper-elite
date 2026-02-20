import duckdb
import os

class DBManager:
    def __init__(self, db_path='data/db/market.duckdb'):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.con = duckdb.connect(db_path)
        self.con.execute('''
            CREATE TABLE IF NOT EXISTS candles (
                open_time TIMESTAMP,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume DOUBLE,
                symbol VARCHAR
            )
        ''')

    def get_connection(self):
        return self.con