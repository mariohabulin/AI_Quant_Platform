import pandas as pd


def generate_signals(df, fast_ema=20, slow_ema=50):

    df = df.copy()

    # Izračun EMA
    df[f"EMA{fast_ema}"] = (
        df["Close"]
        .ewm(span=fast_ema, adjust=False)
        .mean()
    )

    df[f"EMA{slow_ema}"] = (
        df["Close"]
        .ewm(span=slow_ema, adjust=False)
        .mean()
    )

    # Signal
    df["Signal"] = 0

    buy = (
        (df[f"EMA{fast_ema}"] > df[f"EMA{slow_ema}"]) &
        (df[f"EMA{fast_ema}"].shift(1) <= df[f"EMA{slow_ema}"].shift(1))
    )

    sell = (
        (df[f"EMA{fast_ema}"] < df[f"EMA{slow_ema}"]) &
        (df[f"EMA{fast_ema}"].shift(1) >= df[f"EMA{slow_ema}"].shift(1))
    )

    df.loc[buy, "Signal"] = 1
    df.loc[sell, "Signal"] = -1

    return df