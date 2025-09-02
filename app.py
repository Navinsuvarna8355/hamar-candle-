import streamlit as st
from nsetools import Nse
import pandas as pd
import time

# --- Setup ---
st.set_page_config(page_title="Live NSE Hammer Signal", layout="wide")
st.title("📈 Live NSE Signal Dashboard")

nse = Nse()
symbol_map = {
    "NIFTY": "NIFTY 50",
    "BANKNIFTY": "NIFTY BANK",
    "SENSEX": "S&P BSE SENSEX"
}

selected_index = st.selectbox("Choose Index", list(symbol_map.keys()))
symbol = symbol_map[selected_index]

# --- Fetch Live Data ---
def fetch_live_data(symbol):
    try:
        quote = nse.get_index_quote(symbol)
        return {
            "open": float(quote["open"]),
            "high": float(quote["dayHigh"]),
            "low": float(quote["dayLow"]),
            "close": float(quote["lastPrice"]),
            "volume": float(quote["quantityTraded"])
        }
    except:
        return None

data = fetch_live_data(symbol)
if not data:
    st.error("Failed to fetch live data. Try again later.")
    st.stop()

df = pd.DataFrame([data])
st.subheader("🔍 Latest Candle")
st.dataframe(df)

# --- Strategy Logic ---
def is_weak_hammer(candle):
    body = abs(candle['close'] - candle['open'])
    lower_wick = min(candle['open'], candle['close']) - candle['low']
    upper_wick = candle['high'] - max(candle['open'], candle['close'])
    return lower_wick > 2 * body and upper_wick < body

def detect_support_resistance(df):
    support = df['low'].min()
    resistance = df['high'].max()
    return support, resistance

support, resistance = detect_support_resistance(df)
latest = df.iloc[-1]

if is_weak_hammer(latest):
    if latest['close'] <= support * 1.02:
        signal = "🟢 Buy CE"
    elif latest['close'] >= resistance * 0.98:
        signal = "🔴 Buy PE"
    else:
        signal = "⚪ No Signal (Hammer not near zone)"
else:
    signal = "⚪ No Signal (Not a weak hammer)"

# --- Display Signal ---
st.subheader("📍 Strategy Signal")
st.markdown(f"### {signal}")

with st.expander("Support/Resistance Levels"):
    st.write(f"Support: `{support:.2f}`")
    st.write(f"Resistance: `{resistance:.2f}`")
    st.write(f"Close Price: `{latest['close']:.2f}`")

