import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.getcwd(), 'src'))

from utils.db_manager import DBManager
from ingestion.vision_loader import VisionDownloader
from analytics.event_detector import EventDetector
from analytics.visualizer import Visualizer

def main():
    print("--- STARTING RESEARCH PLATFORM ---")
    db = DBManager()
    loader = VisionDownloader()
    detector = EventDetector(db)
    viz = Visualizer(db)

    # 1. Загрузка
    for i in range(2, 4):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        loader.download_day("BTCUSDT", date_str, db)

    # 2. Поиск аномалий
    events = detector.find_volatility_events(threshold_pct=1.5)

    # 3. Отрисовка первой найденной аномалии
    if not events.empty:
        first_date = events.iloc[0]['trade_date']
        viz.plot_event("BTCUSDT", first_date)

if __name__ == '__main__':
    main()