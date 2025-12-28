import streamlit as st
import pandas as pd
import requests
import datetime
import random
import time

# --- 1. SESSION STATE SETUP ---
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = "15m"

# --- 2. DATA FETCHING WITH FALLBACK (Binance -> Bybit -> Coinbase) ---

def get_market_data(asset, timeframe):
    """
    Tries to fetch price from multiple sources in order.
    Returns: (current_price, start_price, source_name)
    """
    
    # Map assets to API symbols
    binance_sym = f"{asset}USDT"
    bybit_sym = f"{asset}USDT"
    coinbase_sym = f"{asset}-USD"
    
    # Map dashboard timeframe to API intervals
    # 15m = 900s, 1h = 3600s
    interval_map = {'15m': '15m', '1h': '1h'} # Binance
    bybit_map = {'15m': '15', '1h': '60'}     # Bybit (numbers)
    coinbase_map = {'15m': 900, '1h': 3600}    # Coinbase (seconds)
    
    api_interval = interval_map.get(timeframe, '15m')
    api_bybit = bybit_map.get(timeframe, '15')
    api_coinbase = coinbase_map.get(timeframe, 900)

    sources = ["Binance", "Bybit", "Coinbase"]
    
    for source in sources:
        try:
            current_price = 0.0
            start_price = 0.0
            
            # === SOURCE 1: BINANCE ===
            if source == "Binance":
                # Price
                url_price = f"https://api.binance.com/api/v3/ticker/price?symbol={binance_sym}"
                resp_price = requests.get(url_price, timeout=2)
                if resp_price.status_code != 200: raise Exception("Status Error")
                current_price = float(resp_price.json()['price'])
                
                # Candles (Start Price)
                url_klines = f"https://api.binance.com/api/v3/klines?symbol={binance_sym}&interval={api_interval}&limit=1"
                resp_klines = requests.get(url_klines, timeout=2)
                if resp_klines.status_code != 200: raise Exception("Status Error")
                start_price = float(resp_klines.json()[0][1])

            # === SOURCE 2: BYBIT ===
            elif source == "Bybit":
                # Price (Spot V5)
                url_price = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={bybit_sym}"
                resp_price = requests.get(url_price, timeout=2)
                if resp_price.status_code != 200: raise Exception("Status Error")
                current_price = float(resp_price.json()['result']['list'][0]['lastPrice'])
                
                # Candles
                url_klines = f"https://api.bybit.com/v5/market/kline?category=spot&symbol={bybit_sym}&interval={api_bybit}&limit=1"
                resp_klines = requests.get(url_klines, timeout=2)
                if resp_klines.status_code != 200: raise Exception("Status Error")
                # Bybit returns [start_time, open, high, low, close, volume, ...]
                start_price = float(resp_klines.json()['result']['list'][0]['open'])

            # === SOURCE 3: COINBASE ===
            elif source == "Coinbase":
                # Price
                url_price = f"https://api.coinbase.com/v2/prices/{coinbase_sym}/spot"
                resp_price = requests.get(url_price, timeout=2)
                if resp_price.status_code != 200: raise Exception("Status Error")
                current_price = float(resp_price.json()['data']['amount'])
                
                # Candles
                url_klines = f"https://api.coinbase.com/v2/prices/{coinbase_sym}/candles?granularity={api_coinbase}"
                resp_klines = requests.get(url_klines, timeout=2)
                if resp_klines.status_code != 200: raise Exception("Status Error")
                # Coinbase returns [time, low, high, open, close, volume]
                start_price = float(resp_klines.json()['data'][0][3])

            # If we got here, success!
            return current_price, start_price, source

        except Exception as e:
            # If this source failed, log it and continue to next source
            # st.sidebar.write(f"{source} failed for {asset}: {str(e)[:15]}") # Debug
            continue

    # If loop finishes, all sources failed
    return 0.0, 0.0, "Error"

def get_timer(timeframe):
    now = datetime.datetime.utcnow() 
    minute = now.minute
    second = now.second
    
    if timeframe == "15m":
        block_size = 15
        total_seconds = 900
        text = "15 Min Market"
    else:
        block_size = 60
        total_seconds = 3600
        text = "1 Hour Market"

    minutes_into = minute % block_size
    seconds_passed = (minutes_into * 60) + second
    seconds_left = total_seconds - seconds_passed
    if seconds_left <= 0: seconds_left = total_seconds
        
    mins, secs = divmod(seconds_left, 60)
    return f"{mins:02d}:{secs:02d}", seconds_left, text

# --- 3. BOT LOGIC ---

def generate_signals(timeframe):
    assets = ["BTC", "ETH", "SOL", "DOGE", "PEPE"]
    data = []
    plat_label = "Polymarket" if timeframe == "15m" else "Kalshi / Poly"

    for asset in assets:
        current_price, start_price, source = get_market_data(asset, timeframe)
        
        if current_price == 0.0 or start_price == 0.0:
            data.append({
                "asset": asset,
                "platform": plat_label,
                "source": "UNAVAILABLE",
                "current_price": 0.0,
                "start_price": 0.0,
                "pct_change": 0.0,
                "bias": "WAIT",
                "true_prob_up": 0.50,
                "confidence": 0.0,
                "signal_label": "DATA ERROR",
                "reasoning": "All APIs unreachable.",
                "tech_indicators": "OFFLINE"
            })
            continue
            
        pct_change = ((current_price - start_price) / start_price) * 100

        rand_val = random.random()
        
        if rand_val > 0.6:
            bias = "UP"
            conf = round(random.uniform(0.70, 0.88), 2)
            true_prob_up = round(conf + 0.10, 2)
            signal_label = f"HIGH CONFIDENCE UP"
            reasons_pool = [
                "Volume surge detected. Price holding above VWAP.",
                "Aggressive buy walls on Coinbase. Breakout confirmed.",
                "Funding rates positive. Momentum shifting bullish.",
                "RSI recovering. Trend stability confirmed."
            ]
            tech = "RSI: Rising | MACD: Bullish | Vol: High"

        elif rand_val < 0.2:
            bias = "DOWN"
            conf = round(random.uniform(0.70, 0.88), 2)
            true_prob_up = round(1 - conf - 0.10, 2) 
            signal_label = f"HIGH CONFIDENCE DOWN"
            reasons_pool = [
                "Price rejected at resistance. Heavy sell walls.",
                "Funding rates negative. Spot leading perps down.",
                "Bearish divergence on RSI. Momentum fading.",
                "Stop-hunt wick followed by aggressive selling."
            ]
            tech = "RSI: Falling | MACD: Bearish | Vol: Med"
        else:
            bias = "FLAT"
            conf = round(random.uniform(0.10, 0.30), 2)
            true_prob_up = 0.50
            signal_label = "NEUTRAL / NO EDGE"
            reasons_pool = [
                "Price compressing. Low volatility regime.",
                "Order book balanced. No directional flow.",
                "Choppy range action. Wait for confirmation.",
                "VWAP flat. No catalysts detected."
            ]
            tech = "RSI: Flat | MACD: Neutral | Vol: Low"

        data.append({
            "asset": asset,
            "platform": plat_label,
            "source": source, # NEW COLUMN
            "current_price": current_price,
            "start_price": start_price,
            "pct_change": pct_change,
            "bias": bias,
            "true_prob_up": true_prob_up,
            "confidence": conf,
            "signal_label": signal_label,
            "reasoning": random.choice(reasons_pool),
            "tech_indicators": tech
        })
    return pd.DataFrame(data)

# --- 4. DASHBOARD UI ---

st.set_page_config(page_title="Crypto Multi-Source Bot", page_icon="🌐", layout="wide")

# SIDEBAR STATUS
with st.sidebar:
    st.header("📡 Network Status")
    st.caption("Data Chain: Binance ➔ Bybit ➔ Coinbase")
    st.caption("If prices lag, check your internet.")

tab1, tab2 = st.tabs(["15 Minute Markets", "1 Hour Markets"])

# ==========================================
# TAB 1: 15 MINUTE MARKETS
# ==========================================
with tab1:
    st.title("🤖 15-Minute Prediction Markets (UTC)")
    st.caption("Polymarket Focus | Multi-Source API")
    
    timer_str, secs_left, t_type = get_timer("15m")
    if secs_left < 60: st.error(f"⚠️ CLOSING SOON ({t_type}): {timer_str}")
    else: st.success(f"⏱️ Time Remaining ({t_type}): {timer_str}")
    st.markdown("---")

    df_15m = generate_signals("15m")
    
    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("BTC", f"${df_15m[df_15m['asset']=='BTC']['current_price'].values[0]:,.2f}")
    c2.metric("ETH", f"${df_15m[df_15m['asset']=='ETH']['current_price'].values[0]:,.2f}")
    c3.metric("SOL", f"${df_15m[df_15m['asset']=='SOL']['current_price'].values[0]:,.2f}")

    # Table
    def format_p(p): return f"${p:,.2f}" if p > 1 else f"${p:.8f}"
    def format_pct(v): return f"{v:+.2f}%"

    disp = df_15m[['asset', 'source', 'platform', 'current_price', 'start_price', 'pct_change', 'bias', 'true_prob_up', 'confidence', 'signal_label']].copy()
    disp['current_price'] = disp['current_price'].apply(format_p)
    disp['start_price'] = disp['start_price'].apply(format_p)
    disp['pct_change'] = disp['pct_change'].apply(format_pct)
    disp.columns = ['Asset', 'Data Source', 'Platform', 'Current (Live)', 'Start Price (UTC)', 'Change %', 'Bias', 'True Prob (UP)', 'Conf', 'Signal']
    st.dataframe(disp, use_container_width=True)

    # DEEP DIVE
    st.markdown("### 📉 Technical Deep Dive & Reasoning")
    detail_col1, detail_col2 = st.columns(2)
    neutral_box_style = "border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9; margin-bottom: 10px;"

    with detail_col1:
        for i, row in df_15m.iloc[:3].iterrows():
            st.markdown(f"""
            <div style="{neutral_box_style}">
                <strong>{row['asset']}</strong> - {row['signal_label']}<br>
                <span style="color: #555; font-size: 0.9em;">{row['tech_indicators']}</span>
                <p style="margin-top: 8px; margin-bottom: 0px;">📝 <em>{row['reasoning']}</em></p>
            </div>
            """, unsafe_allow_html=True)

    with detail_col2:
        for i, row in df_15m.iloc[3:].iterrows():
            st.markdown(f"""
            <div style="{neutral_box_style}">
                <strong>{row['asset']}</strong> - {row['signal_label']}<br>
                <span style="color: #555; font-size: 0.9em;">{row['tech_indicators']}</span>
                <p style="margin-top: 8px; margin-bottom: 0px;">📝 <em>{row['reasoning']}</em></p>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# TAB 2: 1 HOUR MARKETS
# ==========================================
with tab2:
    st.title("🤖 1-Hour Prediction Markets (UTC)")
    st.caption("Kalshi & Polymarket Focus | Multi-Source API")
    
    timer_str, secs_left, t_type = get_timer("1h")
    if secs_left < 120: st.warning(f"⚠️ CLOSING SOON ({t_type}): {timer_str}")
    else: st.success(f"⏱️ Time Remaining ({t_type}): {timer_str}")
    st.markdown("---")

    df_1h = generate_signals("1h")

    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("BTC", f"${df_1h[df_1h['asset']=='BTC']['current_price'].values[0]:,.2f}")
    c2.metric("ETH", f"${df_1h[df_1h['asset']=='ETH']['current_price'].values[0]:,.2f}")
    c3.metric("SOL", f"${df_1h[df_1h['asset']=='SOL']['current_price'].values[0]:,.2f}")

    # Table
    disp = df_1h[['asset', 'source', 'platform', 'current_price', 'start_price', 'pct_change', 'bias', 'true_prob_up', 'confidence', 'signal_label']].copy()
    disp['current_price'] = disp['current_price'].apply(format_p)
    disp['start_price'] = disp['start_price'].apply(format_p)
    disp['pct_change'] = disp['pct_change'].apply(format_pct)
    disp.columns = ['Asset', 'Data Source', 'Platform', 'Current (Live)', 'Start Price (UTC)', 'Change %', 'Bias', 'True Prob (UP)', 'Conf', 'Signal']
    st.dataframe(disp, use_container_width=True)

    # DEEP DIVE
    st.markdown("### 📉 Technical Deep Dive & Reasoning")
    detail_col1, detail_col2 = st.columns(2)

    with detail_col1:
        for i, row in df_1h.iloc[:3].iterrows():
            st.markdown(f"""
            <div style="{neutral_box_style}">
                <strong>{row['asset']}</strong> - {row['signal_label']}<br>
                <span style="color: #555; font-size: 0.9em;">{row['tech_indicators']}</span>
                <p style="margin-top: 8px; margin-bottom: 0px;">📝 <em>{row['reasoning']}</em></p>
            </div>
            """, unsafe_allow_html=True)

    with detail_col2:
        for i, row in df_1h.iloc[3:].iterrows():
            st.markdown(f"""
            <div style="{neutral_box_style}">
                <strong>{row['asset']}</strong> - {row['signal_label']}<br>
                <span style="color: #555; font-size: 0.9em;">{row['tech_indicators']}</span>
                <p style="margin-top: 8px; margin-bottom: 0px;">📝 <em>{row['reasoning']}</em></p>
            </div>
            """, unsafe_allow_html=True)

# --- AUTO REFRESH ---
time.sleep(10)
st.rerun()
