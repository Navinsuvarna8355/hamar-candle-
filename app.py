import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import time
import plotly.graph_objects as go

# --- Utility Functions ---
SYMBOL_MAP = {
    "Nifty": "NIFTY",
    "Bank Nifty": "BANKNIFTY",
    "Sensex": "SENSEX"
}

@st.cache_data(ttl=60)
def fetch_option_chain(symbol_key, current_time_key):
    symbol_name = SYMBOL_MAP.get(symbol_key)
    if not symbol_name:
        st.error("Invalid symbol selected.")
        return None

    nse_oc_url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol_name}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        resp = session.get(nse_oc_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        return {
            "records_data": data["records"]["data"],
            "underlying_value": data["records"]["underlyingValue"],
            "expiry_dates": data["records"]["expiryDates"],
            "fetch_time": datetime.now().strftime('%H:%M:%S')
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for {symbol_key}: {e}")
        return None

def detect_decay(oc_data, underlying, decay_range=150):
    atm_strikes = [d for d in oc_data if abs(d["strikePrice"] - underlying) <= decay_range and "CE" in d and "PE" in d]
    details = []
    for strike_data in atm_strikes:
        ce_data = strike_data["CE"]
        pe_data = strike_data["PE"]

        ce_theta = ce_data.get("theta", 0)
        pe_theta = pe_data.get("theta", 0)
        ce_chg = ce_data.get("change", 0)
        pe_chg = pe_data.get("change", 0)

        decay_side = "Both"
        if ce_theta != 0 and pe_theta != 0:
            if abs(ce_theta) > abs(pe_theta) and ce_chg < 0:
                decay_side = "CE"
            elif abs(pe_theta) > abs(ce_theta) and pe_chg < 0:
                decay_side = "PE"
        elif ce_chg < 0 and pe_chg < 0:
            if abs(ce_chg) > abs(pe_chg):
                decay_side = "CE"
            elif abs(pe_chg) > abs(ce_chg):
                decay_side = "PE"

        details.append({
            "strikePrice": strike_data["strikePrice"],
            "CE_theta": ce_theta,
            "PE_theta": pe_theta,
            "CE_Change": ce_chg,
            "PE_Change": pe_chg,
            "Decay_Side": decay_side
        })
    
    df = pd.DataFrame(details).sort_values(by="strikePrice")
    ce_count = df[df['Decay_Side'] == 'CE'].shape[0]
    pe_count = df[df['Decay_Side'] == 'PE'].shape[0]
    
    overall_decay_side = "Both Sides Decay"
    if ce_count > pe_count:
        overall_decay_side = "CE Decay Active"
    elif pe_count > ce_count:
        overall_decay_side = "PE Decay Active"

    return overall_decay_side, df

def create_decay_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['strikePrice'],
        y=df['CE_theta'].abs(),
        name='CE Theta (Abs)',
        marker_color='#FF5733'
    ))
    fig.add_trace(go.Bar(
        x=df['strikePrice'],
        y=df['PE_theta'].abs(),
        name='PE Theta (Abs)',
        marker_color='#0080FF'
    ))
    fig.update_layout(
        title='Absolute Theta Values by Strike Price',
        xaxis_title='Strike Price',
        yaxis_title='Absolute Theta Value',
        barmode='group',
        legend_title='Option Side'
    )
    return fig

# --- Streamlit UI ---
st.set_page_config(page_title="Decay + Directional Bias", layout="wide", page_icon="📈")
st.title("📊 Decay + Directional Bias Detector")

# Init session state
if "data_container" not in st.session_state:
    st.session_state.data_container = None
    st.session_state.selected_symbol = "Bank Nifty"
if "last_fetch_time" not in st.session_state:
    st.session_state.last_fetch_time = 0

# --- Settings Sidebar ---
col1, col2 = st.columns([1, 2])
with col1:
    st.header("Settings")
    selected_symbol = st.selectbox(
        "Select an Index",
        ["Bank Nifty", "Nifty", "Sensex"],
        index=["Bank Nifty", "Nifty", "Sensex"].index(st.session_state.selected_symbol)
    )
    auto_refresh = st.checkbox("Auto-Refresh Data", value=True)
    refresh_rate = st.slider("Refresh Rate (seconds)", 30, 120, 60, step=15)
    fetch_button = st.button("Manual Fetch")

# --- Auto-refresh fetch BEFORE UI render ---
current_time = time.time()
if auto_refresh and (current_time - st.session_state.last_fetch_time >= refresh_rate):
    with st.spinner(f"Auto-refreshing data for {st.session_state.selected_symbol}..."):
        data_dict = fetch_option_chain(st.session_state.selected_symbol, datetime.now())
        if data_dict:
            st.session_state.data_container = data_dict
            st.session_state.last_fetch_time = current_time

# --- Manual fetch ---
if fetch_button or st.session_state.data_container is None or selected_symbol != st.session_state.selected_symbol:
    st.session_state.selected_symbol = selected_symbol
    with st.spinner(f"Fetching live data for {selected_symbol}..."):
        data_dict = fetch_option_chain(selected_symbol, datetime.now())
        if data_dict:
            st.session_state.data_container = data_dict
            st.session_state.last_fetch_time = time.time()

# --- Left Column UI ---
with col1:
    if st.session_state.data_container:
        st.metric(f"{st.session_state.selected_symbol} Value", st.session_state.data_container["underlying_value"])
        selected_expiry = st.selectbox(
            "Select Expiry Date",
            st.session_state.data_container["expiry_dates"],
            format_func=lambda d: datetime.strptime(d, '%d-%b-%Y').strftime('%d %b, %Y')
        )
        filtered_oc_data = [d for d in st.session_state.data_container["records_data"] if d.get("expiryDate") == selected_expiry]
        decay_side, df = detect_decay(filtered_oc_data, st.session_state.data_container["underlying_value"])
        st.metric("Decay Side", decay_side)
        st.caption(f"Last updated: {st.session_state.data_container['fetch_time']}")
    else:
        st.warning("Please fetch data to get started.")

# --- Right Column UI ---
with col2:
    st.header("Live Analysis")
    if st.session_state.data_container:
        tab1, tab2 = st.tabs(["Data Table", "Theta Chart"])
        with tab1:
            st.dataframe(df, use_container_width=True)
        with tab2:
            chart_fig = create_decay_chart(df)
            st.plotly_chart(chart_fig, use_container_width=True)
    else:
        st.info("Live analysis will appear here after fetching data.")

# --- Recommendations ---
st.divider()
st.header("Trading Recommendations")
if st.session_state.data_container:
    decay_side, _ = detect_decay(st.session_state.data_container["records_data"], st.session_state.data_container["underlying_value"])
    st.info("Note: These are trading ideas based on the decay analysis. Always combine with other market analysis.")
    if decay_side == "CE Decay Active":
        st.subheader("Market Bias: Bearish (Downside)")
        st.markdown("""
        **Recommended Strategies:**
        * Sell Call Options (Short Call)
        * Buy Put Options (Long Put)
        * Bear Put Spread
        """)
    elif decay_side == "PE Decay Active":
        st.subheader("Market Bias: Bullish (Upside)")
        st.markdown("""
        **Recommended Strategies:**
        * Sell Put Options (Short Put)
        * Buy Call Options (Long Call)
        * Bull Call Spread
        """)
    else:
        st.subheader("Market Bias: Neutral/Range-bound")
        st.markdown("""
        **Recommended Strategies:**
        * Sell Straddle or Strangle
        * Iron Condor
        """)
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

    if is_hammer and close <= support * 1.02:
        return "Buy CE"
    elif is_hammer and close >= resistance * 0.98:
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
