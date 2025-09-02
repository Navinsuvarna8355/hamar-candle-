def detect_hammer_signal(latest, support, resistance):
    """
    Detects hammer candle and returns trading signal.

    Parameters:
    - latest: dict with keys 'open', 'high', 'low', 'close'
    - support: float
    - resistance: float

    Returns:
    - str: 'Buy CE', 'Buy PE', or 'Sideways'
    """
    open_price = latest['open']
    high = latest['high']
    low = latest['low']
    close = latest['close']

    body = abs(close - open_price)
    candle_range = high - low
    lower_wick = min(open_price, close) - low
    upper_wick = high - max(open_price, close)

    # Avoid division by zero
    if candle_range == 0:
        return "Sideways"

    lower_wick_ratio = lower_wick / candle_range
    upper_wick_ratio = upper_wick / candle_range
    body_ratio = body / candle_range

    # Define hammer characteristics
    is_hammer = (
        lower_wick_ratio > 0.5 and
        upper_wick_ratio < 0.2 and
        body_ratio < 0.3
    )

    # Signal logic
    if is_hammer and close >= support * 0.98:
        return "Buy CE"
    elif is_hammer and close <= resistance * 1.02:
        return "Buy PE"
    else:
        return "Sideways"


# 🔍 Sample usage
if __name__ == "__main__":
    latest_candle = {
        'open': 19500,
        'high': 19600,
        'low': 19400,
        'close': 19520
    }

    support = 19450
    resistance = 19650

    signal = detect_hammer_signal(latest_candle, support, resistance)
    print("Signal:", signal)
