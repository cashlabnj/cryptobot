import streamlit as st
import pandas as pd
import requests
import datetime
import random
import time

# --- 1. SESSION STATE SETUP ---
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = "15m"

# --- 2. DATA FETCHING (UTC ALIGNED) ---

def get_market_data(asset, timeframe):
    """
    Fetches Live Price (ticker endpoint) and Start Price (klines endpoint).
    Aligns strictly with Binance UTC time.
    """
    symbol_map = {
        "BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT",
        "DOGE": "DOGEUSDT", "PEPE": "PEPEUSDT"
    }
    
    try:
        # 1. Get Current Price (Fastest endpoint)
        url_price = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_map.get(asset)}"
        resp_price = requests.get(url_price)
        current_price = float(resp_price.json()['price'])

        # 2. Get Start Price (Klines endpoint - Candle Open)
        interval_map = {'15m': '15m', '1h': '1h'}
        api_interval = interval_map.get(timeframe, '15m')
        
        url_klines = f"https://api.binance.com/api/v3/klines?symbol={symbol_map.get(asset)}&
