import streamlit as st
import pandas as pd
import time
import random

# --- BOT LOGIC SIMULATION ---
def generate_market_signals():
    """
    Simulates the bot analyzing 15-minute markets across Kalshi and Polymarket.
    Generates data for BTC, ETH, SOL, and others based on the defined framework.
    """
    # Define assets and base parameters
    data = [
        {
            "asset": "BTC",
            "platform": "Kalshi",
            "current_price": 64235.50,
            "bias": "UP",
            "imp_prob_up": 0.58,
            "true_prob_up": 0.74,
            "confidence": 0.78,
            "reasoning": "Price broke resistance at $64,200 with 4x volume spike on Coinbase/Binance. Funding rates flipped positive (+0.01%). Order books show thin asks above $64,300. No wicks on break."
        },
        {
            "asset": "SOL",
            "platform": "Polymarket",
            "current_price": 145.20,
            "bias": "DOWN",
            "imp_prob_up": 0.45,
            "true_prob_up": 0.32, # True Prob for DOWN is 68%
            "confidence": 0.71,
            "reasoning": "Price aggressively rejected at $148. 5m momentum negative. Heavy sell walls on Binance. Bearish engulfing pattern on 1m candle. Time decay favors sellers."
        },
        {
            "asset": "ETH",
            "platform": "Kalshi",
            "current_price": 3450.10,
            "bias": "FLAT",
            "imp_prob_up": 0.51,
            "true_prob_up": 0.50,
            "confidence": 0.15,
            "reasoning": "Price is compressing near VWAP with decreasing volume. 1m candles show equal wicks (indecision). Coinbase lagging Binance by 2 ticks. No edge detected."
        },
        {
            "asset": "DOGE",
            "platform": "Polymarket",
            "current_price": 0.12,
            "bias": "MIXED",
            "imp_prob_up": 0.52,
            "true_prob_up": 0.48,
            "confidence": 0.05,
            "reasoning": "Abnormal volatility spike detected. Order books fragmented across exchanges. High risk of stop-hunt. Avoid."
        },
        {
            "asset": "PEPE",
            "platform": "Kalshi",
            "current_price": 0.0000042,
            "bias": "UP",
            "imp_prob_up": 0.56,
            "true_prob_up": 0.60,
            "confidence": 0.55,
            "reasoning": "Slight upward momentum, but liquidity is thin on Kraken. Signal not confirmed by secondary feeds. Low confidence."
        }
    ]
    
    # Determine Label based on Confidence and Bias
    for d in data:
        conf = d['confidence']
        bias = d['bias']
        
        if conf >= 0.70:
            d['signal_label'] = f"HIGH CONFIDENCE {bias}"
        elif bias == "FLAT" or bias == "MIXED" or conf < 0.20:
            d['signal_label'] = "AVOID / NEUTRAL"
        else:
            d['signal_label'] = f"LOW CONFIDENCE {bias}"
            
    return pd.DataFrame(data)

# --- DASHBOARD UI CONFIGURATION ---
st.set_page_config(
    page_title="Crypto 15m Prediction Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .big-font { font-size:20px !important; }
    .metric-card { background-color: #1E1E1E; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- MAIN APP LOOP ---
st.title("🤖 Crypto 15-Minute Prediction Bot")
st.markdown("Real-time analysis for **Kalshi** & **Polymarket** direction markets.")

# Auto-refresh placeholder
placeholder = st.empty()

# Logic loop to simulate live updates
for n in range(100):
    with placeholder.container():
        
        # 1. GENERATE / FETCH DATA
        df = generate_market_signals()
        
        # 2. HEADER METRICS
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate Summary Stats
        high_conf_count = len(df[df['confidence'] >= 0.70])
        neutral_count = len(df[df['signal_label'] == "AVOID / NEUTRAL"])
        avg_conf = df['confidence'].mean()
        
        with col1:
            st.metric("Total Markets", len(df), delta="Scanning...")
        with col2:
            st.metric("High Confidence Signals", high_conf_count, delta_color="normal")
        with col3:
            st.metric("Neutral / Chop", neutral_count, delta="Wait")
        with col4:
            st.metric("Avg Model Confidence", f"{avg_conf:.2%}")

        st.markdown("---") # Divider

        # 3. MAIN TABLE (THE SIGNAL FEED)
        st.subheader("Active Market Signals")
        
        # Formatting for display
        display_df = df[['asset', 'platform', 'current_price', 'bias', 'true_prob_up', 'confidence', 'signal_label']].copy()
        
        # Rename columns for readability
        display_df.columns = ['Asset', 'Platform', 'Spot Price', 'Bias', 'True Prob (UP)', 'Conf', 'Signal Label']
        
        # Helper to color the rows based on signal
        def highlight_row(row):
            if "HIGH CONFIDENCE UP" in row['Signal Label']:
                return ['background-color: #1b4332'] * len(row) # Dark Green
            elif "HIGH CONFIDENCE DOWN" in row['Signal Label']:
                return ['background-color: #4a0404'] * len(row) # Dark Red
            elif "AVOID" in row['Signal Label']:
                return ['background-color: #333333'] * len(row) # Dark Grey
            else:
                return ['background-color: #262626'] * len(row) # Standard Dark
        
        # Apply styling (Note: Streamlit styles require pandas Styler object)
        styled_df = display_df.style.apply(highlight_row, axis=1)
        
        # Display
        st.dataframe(styled_df, use_container_width=True, height=300)

        # 4. DETAILED ANALYSIS SECTION (Expandable)
        st.subheader("📉 Deep Dive & Reasoning")
        
        # Create columns for the details
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            for i, row in df.iloc[:3].iterrows():
                with st.expander(f"**{row['asset']} ({row['platform']}) - {row['signal_label']}**"):
                    st.write(f"**Current Price:** ${row['current_price']}")
                    st.write(f"**Implied vs True Prob:** {row['imp_prob_up']:.0%} ➔ {row['true_prob_up']:.0%} (UP)")
                    st.write(f"**Confidence Score:** {row['confidence']*100:.0f}/100")
                    st.info(f"**Reasoning:** {row['reasoning']}")

        with detail_col2:
            for i, row in df.iloc[3:].iterrows():
                with st.expander(f"**{row['asset']} ({row['platform']}) - {row['signal_label']}**"):
                    st.write(f"**Current Price:** ${row['current_price']}")
                    st.write(f"**Implied vs True Prob:** {row['imp_prob_up']:.0%} ➔ {row['true_prob_up']:.0%} (UP)")
                    st.write(f"**Confidence Score:** {row['confidence']*100:.0f}/100")
                    st.warning(f"**Reasoning:** {row['reasoning']}")
        
        # Footer Status
        st.caption(f"Bot Status: Running | Last Updated: {time.strftime('%H:%M:%S')} | Data Source: Simulated Feed")

    # Refresh every 5 seconds (simulating real-time tick)
    time.sleep(5)
    placeholder.empty()
