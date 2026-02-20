import duckdb
import pandas as pd

class EventDetector:
    def __init__(self, db_manager):
        self.con = db_manager.get_connection()

    def find_volatility_events(self, threshold_pct=2.0):
        print(f"[*] Searching for events with volatility > {threshold_pct}%...")
        
        query = f"""
        WITH daily_metrics AS (
            SELECT 
                CAST(open_time AS DATE) as trade_date,
                MIN(low) as day_low,
                MAX(high) as day_high,
                SUM(volume) as total_volume
            FROM candles
            GROUP BY 1
        )
        SELECT * FROM daily_metrics 
        WHERE ((day_high - day_low) / day_low) * 100 > {threshold_pct}
        """
        
        events = self.con.execute(query).df()
        if not events.empty:
            print(f"[!] Found {len(events)} anomalous days!")
            print(events)
        else:
            print("[.] No anomalies found for this period.")
        return events