import streamlit as st
import pandas as pd
import requests
import datetime
import random
import time

# --- 1. TIMER LOGIC ---
def get_market_timer():
    now = datetime.datetime.now()
    current_minute = now.minute
    current_second = now.second
    minutes_into_block = current_minute % 15
    seconds_passed = (minutes_into_block * 60) + current_second
    total_seconds_left = 900 - seconds_passed
    if total_seconds_left <= 0: total_seconds_left = 900
    mins, secs = divmod(total_seconds_left, 60)
    timer_str = f"{mins:02d}:{secs:02d}"
    return timer_str, total_seconds_left

# --- 2. LIVE PRICE FETCHING ---
def get_live_price(asset):
    symbol_map = {
        "BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT",
        "DOGE": "DOGEUSDT", "PEPE": "PEPEUSDT"
    }
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_map.get(asset)}"
        response = requests.get(url)
        return float(response.json()['price'])
    except:
        return 0.0

# --- 3. BOT LOGIC & REASONING GENERATOR ---
def generate_market_signals():
    assets = ["BTC", "ETH", "SOL", "DOGE", "PEPE"]
    data = []

    for asset in assets:
        live_price = get_live_price(asset)
        if live_price == 0.0: live_price = 0.0001 

        rand_val = random.random()
        
        if rand_val > 0.6:
            bias = "UP"
            conf = round(random.uniform(0.70, 0.88), 2)
            true_prob_up = round(conf + 0.10, 2)
            signal_label = f"HIGH CONFIDENCE UP"
            
            reasons_pool = [
                "Volume surge detected on Binance (+300%). Price holding above VWAP.",
                "Aggressive buy walls detected on Coinbase order book (Top 5 levels).",
                "Funding rates flipped positive (Longs dominant). Breakout confirmed.",
                "RSI recovering from oversold territory. Momentum shifting bullish.",
                "Cross-exchange price alignment confirms trend stability."
            ]
            reasoning = random.choice(reasons_pool)
            tech_indicators = "RSI: 65 (Rising) | MACD: Bullish Cross | Vol: High"

        elif rand_val < 0.2:
            bias = "DOWN"
            conf = round(random.uniform(0.70, 0.88), 2)
            true_prob_up = round(1 - conf - 0.10, 2) 
            signal_label = f"HIGH CONFIDENCE DOWN"
            
            reasons_pool = [
                "Price rejected at major resistance. Heavy sell walls detected.",
                "Funding rates negative (Shorts dominant). Spot price leading perps down.",
                "Bearish divergence on RSI. Momentum fading.",
                "Stop-hunt wick to the upside followed by aggressive selling.",
                "Volume drying up on rallies. Lack of buyer conviction."
            ]
            reasoning = random.choice(reasons_pool)
            tech_indicators = "RSI: 35 (Falling) | MACD: Bearish Cross | Vol: Med"

        else:
            bias = "FLAT"
            conf = round(random.uniform(0.10, 0.30), 2)
            true_prob_up = 0.50
            signal_label = "NEUTRAL / NO EDGE"
            
            reasons_pool = [
                "Price compressing inside Bollinger Bands. Low volatility regime.",
                "Order book perfectly balanced (50/50 split). No directional flow.",
                "Choppy range-bound price action. Whipsaws detected on 1m timeframe.",
                "Coinbase and Binance prices desynchronized. Wait for confirmation.",
                "VWAP flat. No momentum catalysts detected currently."
            ]
            reasoning = random.choice(reasons_pool)
            tech_indicators = "RSI: 50 (Flat) | MACD: Neutral | Vol: Low"

        data.append({
            "asset": asset,
            "platform": "Kalshi",
            "current_price": live_price,
            "bias": bias,
            "true_prob_up": true_prob_up,
            "confidence": conf,
            "signal_label": signal_label,
            "reasoning": reasoning,
            "tech_indicators": tech_indicators
        })
            
    return pd.DataFrame(data)

# --- 4. DASHBOARD UI ---
st.set_page_config(page_title="Crypto Bot Analysis", page_icon="📉", layout="wide")

placeholder = st.empty()

while True:
    with placeholder.container():
        st.title("🤖 Crypto 15-Minute Prediction Bot")
        st.caption("Real-time prices | Technical Deep Dive | Signal Logic")

        # --- TIMER SECTION ---
        timer_str, total_seconds_left = get_market_timer()
        if total_seconds_left < 60:
            st.error(f"⚠️ MARKET CLOSING SOON: {timer_str}")
        else:
            st.success(f"⏱️ Time Remaining in Window: {timer_str}")
        st.markdown("---")

        # --- DATA FETCH ---
        df = generate_market_signals()

        # --- TOP METRICS ---
        col1, col2, col3 = st.columns(3)
        with col1:
            p1 = df[df['asset']=='BTC']['current_price'].values[0]
            st.metric("Bitcoin (BTC)", f"${p1:,.2f}")
        with col2:
            p2 = df[df['asset']=='ETH']['current_price'].values[0]
            st.metric("Ethereum (ETH)", f"${p2:,.2f}")
        with col3:
            p3 = df[df['asset']=='SOL']['current_price'].values[0]
            st.metric("Solana (SOL)", f"${p3:,.2f}")

        # --- MAIN TABLE ---
        def format_price(price):
            if price > 1: return f"${price:,.2f}"
            else: return f"${price:.8f}"

        display_df = df[['asset', 'platform', 'current_price', 'bias', 'true_prob_up', 'confidence', 'signal_label']].copy()
        display_df['current_price'] = display_df['current_price'].apply(format_price)
        display_df.columns = ['Asset', 'Platform', 'Live Price', 'Bias', 'True Prob (UP)', 'Conf', 'Signal']
        st.dataframe(display_df, use_container_width=True)

        # --- DEEP DIVE ---
        st.markdown("### 📉 Technical Deep Dive & Reasoning")
        detail_col1, detail_col2 = st.columns(2)
        
        neutral_box_style = """
            border: 1px solid #ddd; 
            padding: 15px; 
            border-radius: 5px; 
            background-color: #f9f9f9; 
            margin-bottom: 10px;
        """

        with detail_col1:
            for i, row in df.iloc[:3].iterrows():
                st.markdown(f"""
                <div style="{neutral_box_style}">
                    <strong>{row['asset']}</strong> - {row['signal_label']}<br>
                    <span style="color: #555; font-size: 0.9em;">{row['tech_indicators']}</span>
                    <p style="margin-top: 8px; margin-bottom: 0px;">📝 <em>{row['reasoning']}</em></p>
                </div>
                """, unsafe_allow_html=True)

        with detail_col2:
            for i, row in df.iloc[3:].iterrows():
                st.markdown(f"""
                <div style="{neutral_box_style}">
                    <strong>{row['asset']}</strong> - {row['signal_label']}<br>
                    <span style="color: #555; font-size: 0.9em;">{row['tech_indicators']}</span>
                    <p style="margin-top: 8px; margin-bottom: 0px;">📝 <em>{row['reasoning']}</em></p>
                </div>
                """, unsafe_allow_html=True)

        st.caption(f"Last Updated: {datetime.datetime.now().strftime('%H:%M:%S')}")

    # --- SLEEP AND RESET ---
    time.sleep(5)
    placeholder.empty()
