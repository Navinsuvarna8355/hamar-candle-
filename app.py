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
