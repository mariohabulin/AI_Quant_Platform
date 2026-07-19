import pandas as pd


def generate_signals(df, fast_ema=20, slow_ema=50):
    """
    Generate BUY and SELL signals using an EMA crossover strategy.

    Parameters
    ----------
    df : pandas.DataFrame
        Market data containing a Close column.
    fast_ema : int, default 20
        Period used for the fast exponential moving average.
    slow_ema : int, default 50
        Period used for the slow exponential moving average.

    Returns
    -------
    pandas.DataFrame
        Copy of the input DataFrame containing fast EMA, slow EMA,
        and Signal columns.

        Signal values:
        1  = BUY
        0  = no signal
        -1 = SELL

    Raises
    ------
    TypeError
        If df is not a pandas DataFrame.
    ValueError
        If the Close column is missing or EMA periods are invalid.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input data must be a pandas DataFrame.")

    if "Close" not in df.columns:
        raise ValueError("Input DataFrame must contain a 'Close' column.")

    if fast_ema <= 0 or slow_ema <= 0:
        raise ValueError("EMA periods must be positive integers.")

    if fast_ema >= slow_ema:
        raise ValueError("fast_ema must be smaller than slow_ema.")

    df = df.copy()

    fast_column = f"EMA{fast_ema}"
    slow_column = f"EMA{slow_ema}"

    df[fast_column] = (
        df["Close"]
        .ewm(span=fast_ema, adjust=False)
        .mean()
    )

    df[slow_column] = (
        df["Close"]
        .ewm(span=slow_ema, adjust=False)
        .mean()
    )

    df["Signal"] = 0

    buy = (
        (df[fast_column] > df[slow_column])
        & (df[fast_column].shift(1) <= df[slow_column].shift(1))
    )

    sell = (
        (df[fast_column] < df[slow_column])
        & (df[fast_column].shift(1) >= df[slow_column].shift(1))
    )

    df.loc[buy, "Signal"] = 1
    df.loc[sell, "Signal"] = -1

    return df
if __name__ == "__main__":
    df = pd.read_csv("data/AAPL.csv", index_col=0)

    result = generate_signals(df)

    result.to_csv("data/AAPL.csv")

    print(result[["Close", "EMA20", "EMA50", "Signal"]].tail())
    print(result["Signal"].value_counts())