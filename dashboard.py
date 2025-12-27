import streamlit as st
import pandas as pd
import requests
import datetime

# --- 1. TIMER LOGIC ---
def get_market_timer():
    """
    Calculates time remaining in the current 15-minute market window.
    Windows reset at :00, :15, :30, :45.
    """
    now = datetime.datetime.now()
    current_minute = now.minute
    current_second = now.second
    
    # Calculate how many minutes we are into the current 15-min block
    minutes_into_block = current_minute % 15
    
    # Total seconds passed in this block
    seconds_passed = (minutes_into_block * 60) + current_second
    
    # 15 minutes = 900 seconds
    total_seconds_left = 900 - seconds_passed
    
    # Handle edge case where we are exactly at the reset point
    if total_seconds_left <= 0:
        total_seconds_left = 900
        
    # Format to MM:SS
    mins, secs = divmod(total_seconds_left, 60)
    timer_str = f"{mins:02d}:{secs:02d}"
    
    return timer_str, total_seconds_left

# --- 2. LIVE PRICE FETCHING ---
def get_live_price(asset):
    symbol_map = {
        "BTC": "BTCUSDT",
        "ETH": "ETHUSDT",
        "SOL": "SOLUSDT",
        "DOGE": "DOGEUSDT",
        "PEPE": "PEPEUSDT"
    }
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_map.get(asset)}"
        response = requests.get(url)
        return float(response.json()['price'])
    except:
        return 0.0

# --- 3. BOT LOGIC ---
def generate_market_signals():
    assets = ["BTC", "ETH", "SOL", "DOGE", "PEPE"]
    data = []

    for asset in assets:
        live_price = get_live_price(asset)
        if live_price == 0.0: live_price = 0.0001 

        # Simulated Signals (Randomized for demo)
        import random
        rand_val = random.random()
        if rand_val > 0.6:
            bias = "UP"
            conf = random.uniform(0.70, 0.85)
            imp_prob = 0.55
            true_prob = imp_prob + 0.15
            label = f"HIGH CONFIDENCE {bias}"
        elif rand_val < 0.2:
            bias = "DOWN"
            conf = random.uniform(0.70, 0.85)
            imp_prob = 0.45
            true_prob = imp_prob - 0.15
            label = f"HIGH CONFIDENCE {bias}"
        else:
            bias = "FLAT"
            conf = random.uniform(0.10, 0.30)
            imp_prob = 0.50
            true_prob = 0.50
            label = "NEUTRAL / CHOP"

        data.append({
            "asset": asset,
            "platform": "Kalshi",
            "current_price": live_price,
            "bias": bias,
            "true_prob_up": true_prob,
            "confidence": conf,
            "signal_label": label
        })
            
    return pd.DataFrame(data)

# --- 4. DASHBOARD UI (NO WHILE LOOP) ---
st.set_page_config(
    page_title="Crypto 15m Bot",
    page_icon="⏱️",
    layout="wide",
)

st.title("🤖 Crypto 15-Minute Prediction Bot")
st.caption("Real-time prices via Binance | Smooth Updates")

# 1. FETCH TIMER
timer_str, total_seconds_left = get_market_timer()

# 2. DISPLAY TIMER (HEADER)
# If time < 60s, make it red
if total_seconds_left < 60:
    st.error(f"⚠️ MARKET CLOSING SOON: {timer_str}")
else:
    st.success(f"⏱️ Time Remaining in Window: {timer_str}")
    
st.markdown("---") 

# 3. FETCH DATA
df = generate_market_signals()

# 4. TOP METRICS
col1, col2, col3, col4 = st.columns(4)

with col1:
    btc_p = df[df['asset']=='BTC']['current_price'].values[0]
    st.metric("Bitcoin", f"${btc_p:,.2f}")
with col2:
    eth_p = df[df['asset']=='ETH']['current_price'].values[0]
    st.metric("Ethereum", f"${eth_p:,.2f}")
with col3:
    sol_p = df[df['asset']=='SOL']['current_price'].values[0]
    st.metric("Solana", f"${sol_p:,.2f}")
with col4:
    st.metric("Status", "Scanning", delta="Live API")

# 5. MAIN TABLE
display_df = df[['asset', 'platform', 'current_price', 'bias', 'true_prob_up', 'confidence', 'signal_label']].copy()
display_df.columns = ['Asset', 'Platform', 'Live Price', 'Bias', 'True Prob (UP)', 'Conf', 'Signal Label']

def highlight_row(row):
    if "HIGH CONFIDENCE UP" in row['Signal Label']: return ['background-color: #1b4332'] * len(row)
    elif "HIGH CONFIDENCE DOWN" in row['Signal Label']: return ['background-color: #4a0404'] * len(row)
    elif "NEUTRAL" in row['Signal Label']: return ['background-color: #333333'] * len(row)
    else: return ['background-color: #262626'] * len(row)

styled_df = display_df.style.apply(highlight_row, axis=1)
st.dataframe(styled_df, use_container_width=True)

# 6. DETAILS
with st.expander("View Reasoning"):
    for i, row in df.iterrows():
        st.text(f"{row['asset']}: {row['signal_label']} (Confidence: {row['confidence']:.1%})")

st.caption(f"Last Updated: {datetime.datetime.now().strftime('%H:%M:%S')}")

# --- THE FIX: AUTO-RERUN ---
# This tells Streamlit to re-run this script every 5 seconds 
# WITHOUT using a blocking 'while' loop.
st.automatic_rerun(interval=5000)
