import requests
import zipfile
import io
import pandas as pd
from datetime import datetime

class VisionDownloader:
    BASE_URL = "https://data.binance.vision/data/futures/um/daily"
    API_URL = "https://fapi.binance.com/fapi/v1/openInterestHist"

    def _ensure_tables(self, db_manager):
        con = db_manager.get_connection()
        con.execute("CREATE TABLE IF NOT EXISTS candles (symbol VARCHAR, open_time TIMESTAMP, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE)")
        con.execute("CREATE TABLE IF NOT EXISTS open_interest (symbol VARCHAR, sum_open_interest DOUBLE, sum_open_interest_value DOUBLE, open_time TIMESTAMP)")

    def download_day(self, symbol, date_str, db_manager):
        self._ensure_tables(db_manager)
        self._fetch_and_store(symbol, date_str, f"klines/{symbol}/1m", f"{symbol}-1m-{date_str}", "candles", db_manager)
        
        # Пытаемся взять OI из архива, если 404 - идем в API
        if not self._fetch_and_store(symbol, date_str, "openInterest", f"{symbol}-openInterest-{date_str}", "open_interest", db_manager):
            self._fetch_oi_from_api(symbol, date_str, db_manager)

    def _fetch_and_store(self, symbol, date_str, folder, file_name, table_name, db_manager):
        url = f"{self.BASE_URL}/{folder}/{file_name}.zip"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                    with z.open(f"{file_name}.csv") as f:
                        df = pd.read_csv(f)
                        if table_name == "candles":
                            df = df.iloc[:, :6]
                            df.columns = ['open_time', 'open', 'high', 'low', 'close', 'volume']
                        else:
                            df.columns = ['symbol', 'sum_open_interest', 'sum_open_interest_value', 'open_time']
                        
                        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
                        df['symbol'] = symbol
                        db_manager.get_connection().execute(f"INSERT INTO {table_name} SELECT * FROM df")
                        print(f"[+] Loaded {table_name} from ARCHIVE for {date_str}")
                        return True
            return False
        except:
            return False

    def _fetch_oi_from_api(self, symbol, date_str, db_manager):
        print(f"[*] Trying API Fallback for OI ({date_str})...")
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        start_ts = int(dt_obj.timestamp() * 1000)
        
        params = {"symbol": symbol, "period": "5m", "startTime": start_ts, "limit": 500}
        resp = requests.get(self.API_URL, params=params)
        
        if resp.status_code == 200:
            data = resp.json()
            if data:
                df = pd.DataFrame(data)
                # API возвращает: timestamp, sumOpenInterest, sumOpenInterestValue, symbol
                df = df[['symbol', 'sumOpenInterest', 'sumOpenInterestValue', 'timestamp']]
                df.columns = ['symbol', 'sum_open_interest', 'sum_open_interest_value', 'open_time']
                df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
                
                db_manager.get_connection().execute("INSERT INTO open_interest SELECT * FROM df")
                print(f"[+] Loaded {len(df)} rows from API for {date_str}")