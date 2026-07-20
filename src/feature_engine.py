import pandas as pd


REQUIRED_COLUMNS = {"Open", "High", "Low", "Close", "Volume"}


def validate_input(data: pd.DataFrame) -> None:
    """
    Validate input market data before feature generation.

    Parameters:
        data (pd.DataFrame): Market data to validate.

    Raises:
        TypeError: If data is not a pandas DataFrame.
        ValueError: If data is empty or required columns are missing.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Input data must be a pandas DataFrame.")

    if data.empty:
        raise ValueError("Input DataFrame cannot be empty.")

    missing_columns = REQUIRED_COLUMNS.difference(data.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")


def generate_features(data: pd.DataFrame) -> pd.DataFrame:
    """
    Generate market features from validated OHLCV market data.

    Parameters:
        data (pd.DataFrame): Validated OHLCV market data.

    Returns:
        pd.DataFrame: Original market data with generated features.
    """
    validate_input(data)

    feature_data = data.copy()

    feature_data["EMA_20"] = feature_data["Close"].ewm(
        span=20,
        adjust=False,
    ).mean()

    feature_data["EMA_50"] = feature_data["Close"].ewm(
        span=50,
        adjust=False,
    ).mean()

    feature_data["RETURN_1"] = feature_data["Close"].pct_change()

    feature_data["VOLATILITY_20"] = (
        feature_data["RETURN_1"]
        .rolling(window=20)
        .std()
    )

    price_change = feature_data["Close"].diff()

    gains = price_change.clip(lower=0)
    losses = -price_change.clip(upper=0)

    average_gain = gains.rolling(window=14).mean()
    average_loss = losses.rolling(window=14).mean()

    relative_strength = average_gain / average_loss

    feature_data["RSI_14"] = (
        100 - (100 / (1 + relative_strength))
    )

    feature_data["VOLUME_MA_20"] = (
        feature_data["Volume"]
        .rolling(window=20)
        .mean()
    )

    return feature_data