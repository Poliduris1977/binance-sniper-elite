import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

class Visualizer:
    def __init__(self, db_manager):
        self.con = db_manager.get_connection()
        os.makedirs('data/reports', exist_ok=True)

    def plot_event(self, symbol, trade_date):
        print(f"[*] Visualizing {symbol} for {trade_date}...")
        
        df_price = self.con.execute(f"SELECT * FROM candles WHERE symbol='{symbol}' AND CAST(open_time AS DATE) = '{trade_date}' ORDER BY open_time").df()
        
        # Проверяем наличие таблицы и данных в OI
        try:
            df_oi = self.con.execute(f"SELECT * FROM open_interest WHERE symbol='{symbol}' AND CAST(open_time AS DATE) = '{trade_date}' ORDER BY open_time").df()
        except:
            df_oi = pd.DataFrame()

        if df_oi.empty:
            print("[!] No OI data found, plotting price only.")
            fig = go.Figure(data=[go.Candlestick(x=df_price['open_time'], open=df_price['open'], high=df_price['high'], low=df_price['low'], close=df_price['close'])])
        else:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df_price['open_time'], open=df_price['open'], high=df_price['high'], low=df_price['low'], close=df_price['close'], name='Price'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_oi['open_time'], y=df_oi['sum_open_interest'], name='OI', line=dict(color='cyan')), row=2, col=1)

        fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False)
        output = f"data/reports/event_{trade_date}.html"
        fig.write_html(output)
        print(f"[+] Report: {output}")