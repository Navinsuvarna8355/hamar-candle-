import streamlit as st
import pandas as pd
from nsetools import Nse

# --- Setup ---
st.set_page_config(page_title="Hammer Signal Dashboard", layout="wide")
st.title("📊 Live NSE Dashboard: Hammer Candle Strategy")

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
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

data = fetch_live_data(symbol)
if not data:
    st.stop()

df = pd.DataFrame([data])
st.subheader("📌 Latest Candle")
st.dataframe(df)

# --- Strategy Logic ---
def detect_hammer_signal(latest, support, resistance):
    open_price = latest['open']
    high = latest['high']
    low = latest['low']
    close = latest['close']

    body = abs(close - open_price)
    candle_range = high - low
    lower_wick = min(open_price, close) - low
    upper_wick = high - max(open_price, close)

    if candle_range == 0:
        return "Sideways"

    lower_wick_ratio = lower_wick / candle_range
    upper_wick_ratio = upper_wick / candle_range
    body_ratio = body / candle_range

    is_hammer = (
        lower_wick_ratio > 0.5 and
        upper_wick_ratio < 0.2 and
        body_ratio < 0.3
    )

    if is_hammer and close >= support * 0.98:
        return "Buy CE"
    elif is_hammer and close <= resistance * 1.02:
        return "Buy PE"
    else:
        return "Sideways"

# --- Support/Resistance Logic ---
def detect_support_resistance(df):
    support = df['low'].min()
    resistance = df['high'].max()
    return support, resistance

support, resistance = detect_support_resistance(df)
latest = df.iloc[-1]
signal = detect_hammer_signal(latest, support, resistance)

# --- Display Signal ---
st.subheader("📍 Strategy Signal")
st.markdown(f"### {signal}")

with st.expander("Support/Resistance Levels"):
    st.write(f"Support: `{support:.2f}`")
    st.write(f"Resistance: `{resistance:.2f}`")
    st.write(f"Close Price: `{latest['close']:.2f}`")
