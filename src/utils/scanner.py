import requests

def get_active_futures_tickers():
    try:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        resp = requests.get(url, timeout=10).json()
        tickers = [s['symbol'] for s in resp['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
        print(f"[+] Found {len(tickers)} active USDT-M futures")
        return tickers
    except Exception as e:
        print(f"[!] Error fetching tickers: {e}")
        return ["BTCUSDT", "ETHUSDT"] # Fallback