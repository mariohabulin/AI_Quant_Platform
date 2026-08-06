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
    

def generate_ema(data: pd.DataFrame, period: int) -> pd.DataFrame:
    """
    Generate a single EMA feature for the requested period.

    Parameters:
        data (pd.DataFrame): Validated OHLCV market data.
        period (int): EMA period.

    Returns:
        pd.DataFrame: Original market data with the generated EMA feature.
    """
    validate_input(data)

    if isinstance(period, bool) or not isinstance(period, int):
        raise TypeError("EMA period must be an integer.")

    if period <= 0:
        raise ValueError("EMA period must be greater than zero.")

    feature_data = data.copy()

    column_name = f"EMA_{period}"

    feature_data[column_name] = feature_data["Close"].ewm(
        span=period,
        adjust=False,
    ).mean()

    return feature_data


def generate_rsi(data: pd.DataFrame, period: int) -> pd.DataFrame:
    """
    Generate a single RSI feature for the requested period.

    Parameters:
        data (pd.DataFrame): Validated OHLCV market data.
        period (int): RSI period.

    Returns:
        pd.DataFrame: Original market data with the generated RSI feature.
    """
    validate_input(data)

    if isinstance(period, bool) or not isinstance(period, int):
        raise TypeError("RSI period must be an integer.")

    if period <= 0:
        raise ValueError("RSI period must be greater than zero.")

    feature_data = data.copy()

    price_change = feature_data["Close"].diff()

    gains = price_change.clip(lower=0)
    losses = -price_change.clip(upper=0)

    average_gain = gains.rolling(window=period).mean()
    average_loss = losses.rolling(window=period).mean()

    relative_strength = average_gain / average_loss

    column_name = f"RSI_{period}"

    feature_data[column_name] = (
        100 - (100 / (1 + relative_strength))
    )

    return feature_data


def generate_macd(
    data: pd.DataFrame,
    fast_period: int,
    slow_period: int,
    signal_period: int,
) -> pd.DataFrame:
    """
    Generate MACD line, signal line, and histogram.

    Parameters:
        data (pd.DataFrame): Validated OHLCV market data.
        fast_period (int): Fast EMA period.
        slow_period (int): Slow EMA period.
        signal_period (int): Signal EMA period.

    Returns:
        pd.DataFrame: Original market data with MACD features.
    """
    validate_input(data)

    if isinstance(fast_period, bool) or not isinstance(fast_period, int):
        raise TypeError("MACD fast period must be an integer.")

    if fast_period <= 0:
        raise ValueError(
            "MACD fast period must be greater than zero."
        )

    if isinstance(slow_period, bool) or not isinstance(slow_period, int):
        raise TypeError("MACD slow period must be an integer.")

    if slow_period <= 0:
        raise ValueError(
            "MACD slow period must be greater than zero."
        )

    if (
        isinstance(signal_period, bool)
        or not isinstance(signal_period, int)
    ):
        raise TypeError(
            "MACD signal period must be an integer."
       )

    if signal_period <= 0:
        raise ValueError(
            "MACD signal period must be greater than zero."
        )

    if fast_period >= slow_period:
        raise ValueError(
            "MACD fast period must be less than slow period."
        )

    feature_data = data.copy()

    fast_ema = feature_data["Close"].ewm(
        span=fast_period,
        adjust=False,
    ).mean()

    slow_ema = feature_data["Close"].ewm(
        span=slow_period,
        adjust=False,
    ).mean()

    macd_column = f"MACD_{fast_period}_{slow_period}"
    signal_column = (
        f"MACD_SIGNAL_{fast_period}_{slow_period}_{signal_period}"
    )
    histogram_column = (
        f"MACD_HISTOGRAM_{fast_period}_{slow_period}_{signal_period}"
    )

    feature_data[macd_column] = fast_ema - slow_ema

    feature_data[signal_column] = feature_data[macd_column].ewm(
        span=signal_period,
        adjust=False,
    ).mean()

    feature_data[histogram_column] = (
        feature_data[macd_column]
        - feature_data[signal_column]
    )

    return feature_data


def generate_bollinger_bands(
    data: pd.DataFrame,
    period: int,
    standard_deviations: float,
) -> pd.DataFrame:
    """
    Generate Bollinger Bands features.

    Parameters:
        data (pd.DataFrame): Validated OHLCV market data.
        period (int): Rolling window period.
        standard_deviations (float): Number of standard deviations.

    Returns:
        pd.DataFrame: Original market data with Bollinger Bands features.
    """
    validate_input(data)

    if isinstance(period, bool) or not isinstance(period, int):
        raise TypeError(
            "Bollinger period must be an integer."
        )

    if period <= 0:
        raise ValueError(
            "Bollinger period must be greater than zero."
        )

    if (
        isinstance(standard_deviations, bool)
        or not isinstance(standard_deviations, (int, float))
    ):
        raise TypeError(
            "Bollinger standard deviations must be a number."
        )

    if standard_deviations <= 0:
        raise ValueError(
            "Bollinger standard deviations must be greater than zero."
        )

    feature_data = data.copy()

    middle_column = f"BOLLINGER_MIDDLE_{period}"
    upper_column = (
        f"BOLLINGER_UPPER_{period}_{standard_deviations}"
    )
    lower_column = (
        f"BOLLINGER_LOWER_{period}_{standard_deviations}"
    )

    middle_band = feature_data["Close"].rolling(
        window=period,
    ).mean()

    rolling_std = feature_data["Close"].rolling(
        window=period,
    ).std()

    feature_data[middle_column] = middle_band

    feature_data[upper_column] = (
        middle_band
        + standard_deviations * rolling_std
    )

    feature_data[lower_column] = (
        middle_band
        - standard_deviations * rolling_std
    )

    return feature_data


def generate_donchian_channels(
    data: pd.DataFrame,
    period: int,
) -> pd.DataFrame:
    """
    Generate Donchian Channel features.

    Parameters:
        data (pd.DataFrame): Validated OHLCV market data.
        period (int): Rolling window period.

    Returns:
        pd.DataFrame: Original market data with Donchian Channel features.
    """
    validate_input(data)

    if isinstance(period, bool) or not isinstance(period, int):
        raise TypeError(
            "Donchian period must be an integer."
        )

    if period <= 0:
        raise ValueError(
            "Donchian period must be greater than zero."
        )

    feature_data = data.copy()

    upper_column = f"DONCHIAN_UPPER_{period}"
    lower_column = f"DONCHIAN_LOWER_{period}"
    middle_column = f"DONCHIAN_MIDDLE_{period}"

    feature_data[upper_column] = (
        feature_data["High"]
        .rolling(window=period)
        .max()
        .shift(1)
    )

    feature_data[lower_column] = (
        feature_data["Low"]
        .rolling(window=period)
        .min()
        .shift(1)
    )

    feature_data[middle_column] = (
        feature_data[upper_column]
        + feature_data[lower_column]
    ) / 2

    return feature_data



def generate_atr(
    data: pd.DataFrame,
    period: int,
) -> pd.DataFrame:
    """
    Generate Average True Range using Wilder smoothing.

    Parameters:
        data (pd.DataFrame): Validated OHLCV market data.
        period (int): ATR smoothing period.

    Returns:
        pd.DataFrame: Original market data with the ATR feature.
    """
    validate_input(data)

    if isinstance(period, bool) or not isinstance(period, int):
        raise TypeError("ATR period must be an integer.")

    if period <= 0:
        raise ValueError("ATR period must be greater than zero.")

    feature_data = data.copy()
    previous_close = feature_data["Close"].shift(1)

    true_range = pd.concat(
        [
            feature_data["High"] - feature_data["Low"],
            (feature_data["High"] - previous_close).abs(),
            (feature_data["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    column_name = f"ATR_{period}"
    feature_data[column_name] = true_range.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    return feature_data


def generate_supertrend(
    data: pd.DataFrame,
    period: int,
    multiplier: float,
) -> pd.DataFrame:
    """Generate Supertrend line and direction features."""
    validate_input(data)

    if isinstance(period, bool) or not isinstance(period, int):
        raise TypeError("Supertrend period must be an integer.")

    if period <= 0:
        raise ValueError("Supertrend period must be greater than zero.")

    if (
        isinstance(multiplier, bool)
        or not isinstance(multiplier, (int, float))
    ):
        raise TypeError("Supertrend multiplier must be a number.")

    if multiplier <= 0:
        raise ValueError(
            "Supertrend multiplier must be greater than zero."
        )

    feature_data = generate_atr(data, period=period)
    atr_column = f"ATR_{period}"
    suffix = f"{period}_{multiplier}"
    line_column = f"SUPERTREND_{suffix}"
    direction_column = f"SUPERTREND_DIRECTION_{suffix}"

    midpoint = (feature_data["High"] + feature_data["Low"]) / 2
    basic_upper = midpoint + multiplier * feature_data[atr_column]
    basic_lower = midpoint - multiplier * feature_data[atr_column]

    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    supertrend = pd.Series(index=feature_data.index, dtype=float)
    direction = pd.Series(0, index=feature_data.index, dtype=int)

    for position in range(len(feature_data)):
        if pd.isna(feature_data[atr_column].iloc[position]):
            continue

        if position > 0:
            previous_close = feature_data["Close"].iloc[position - 1]

            if (
                pd.isna(final_upper.iloc[position - 1])
                or basic_upper.iloc[position] < final_upper.iloc[position - 1]
                or previous_close > final_upper.iloc[position - 1]
            ):
                final_upper.iloc[position] = basic_upper.iloc[position]
            else:
                final_upper.iloc[position] = final_upper.iloc[position - 1]

            if (
                pd.isna(final_lower.iloc[position - 1])
                or basic_lower.iloc[position] > final_lower.iloc[position - 1]
                or previous_close < final_lower.iloc[position - 1]
            ):
                final_lower.iloc[position] = basic_lower.iloc[position]
            else:
                final_lower.iloc[position] = final_lower.iloc[position - 1]

        if position == 0 or direction.iloc[position - 1] == 0:
            direction.iloc[position] = (
                1
                if feature_data["Close"].iloc[position]
                >= final_lower.iloc[position]
                else -1
            )
        elif direction.iloc[position - 1] == 1:
            direction.iloc[position] = (
                -1
                if feature_data["Close"].iloc[position]
                < final_lower.iloc[position]
                else 1
            )
        else:
            direction.iloc[position] = (
                1
                if feature_data["Close"].iloc[position]
                > final_upper.iloc[position]
                else -1
            )

        supertrend.iloc[position] = (
            final_lower.iloc[position]
            if direction.iloc[position] == 1
            else final_upper.iloc[position]
        )

    feature_data[line_column] = supertrend
    feature_data[direction_column] = direction

    return feature_data


def generate_adx(
    data: pd.DataFrame,
    period: int,
) -> pd.DataFrame:
    """Generate +DI, -DI, and ADX using Wilder smoothing."""
    validate_input(data)

    if isinstance(period, bool) or not isinstance(period, int):
        raise TypeError("ADX period must be an integer.")

    if period <= 0:
        raise ValueError("ADX period must be greater than zero.")

    feature_data = data.copy()
    previous_close = feature_data["Close"].shift(1)
    high_change = feature_data["High"].diff()
    low_change = -feature_data["Low"].diff()

    positive_dm = high_change.where(
        (high_change > low_change) & (high_change > 0),
        0.0,
    )
    negative_dm = low_change.where(
        (low_change > high_change) & (low_change > 0),
        0.0,
    )

    true_range = pd.concat(
        [
            feature_data["High"] - feature_data["Low"],
            (feature_data["High"] - previous_close).abs(),
            (feature_data["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    smoothed_tr = true_range.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()
    smoothed_positive_dm = positive_dm.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()
    smoothed_negative_dm = negative_dm.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    positive_di = 100 * smoothed_positive_dm / smoothed_tr
    negative_di = 100 * smoothed_negative_dm / smoothed_tr
    denominator = positive_di + negative_di
    dx = 100 * (positive_di - negative_di).abs() / denominator
    dx = dx.where(denominator != 0, 0.0)

    feature_data[f"PLUS_DI_{period}"] = positive_di
    feature_data[f"MINUS_DI_{period}"] = negative_di
    feature_data[f"ADX_{period}"] = dx.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    return feature_data


def _validate_required_features(
    required_features: list[dict],
) -> None:
    """
    Validate the structure of required feature requests.

    Parameters:
        required_features (list[dict]):
            Feature requirements to validate.

    Raises:
        TypeError: If required_features is not a list or if a feature
            requirement is not a dictionary.
        ValueError: If a feature requirement is missing a required key.
    """
    if not isinstance(required_features, list):
        raise TypeError("required_features must be a list.")

    for feature_requirement in required_features:
        if not isinstance(feature_requirement, dict):
            raise TypeError(
                "Each feature requirement must be a dictionary."
            )

        if "name" not in feature_requirement:
            raise ValueError(
                "Feature requirement must include 'name'."
            )

        if "parameters" not in feature_requirement:
            raise ValueError(
                "Feature requirement must include 'parameters'."
            )


def generate_features(
    data: pd.DataFrame,
    required_features: list[dict] | None = None,
) -> pd.DataFrame:
    """
    Generate market features from validated OHLCV market data.

    When required_features is not provided, generate the default
    feature set for backward compatibility.

    Parameters:
        data (pd.DataFrame): Validated OHLCV market data.
        required_features (list[dict] | None):
            Optional feature requirements.

    Returns:
        pd.DataFrame: Original market data with generated features.
    """
    validate_input(data)

    feature_data = data.copy()

    if required_features is not None:
        _validate_required_features(required_features)

        for feature_requirement in required_features:
            feature_name = feature_requirement["name"]
            parameters = feature_requirement["parameters"]

            if feature_name == "EMA":
                feature_data = generate_ema(
                    feature_data,
                    period=parameters["period"],
                )

            elif feature_name == "RSI":
                feature_data = generate_rsi(
                    feature_data,
                    period=parameters["period"],
                )

            elif feature_name == "MACD":
                feature_data = generate_macd(
                    feature_data,
                    fast_period=parameters["fast_period"],
                    slow_period=parameters["slow_period"],
                    signal_period=parameters["signal_period"],
                )

            elif feature_name == "BOLLINGER_BANDS":
                feature_data = generate_bollinger_bands(
                    feature_data,
                    period=parameters["period"],
                    standard_deviations=parameters[
                        "standard_deviations"
                    ],
                )

            elif feature_name == "DONCHIAN_CHANNELS":
                feature_data = generate_donchian_channels(
                    feature_data,
                    period=parameters["period"],
                )

            elif feature_name == "ATR":
                feature_data = generate_atr(
                    feature_data,
                    period=parameters["period"],
                )

            elif feature_name == "SUPERTREND":
                feature_data = generate_supertrend(
                    feature_data,
                    period=parameters["period"],
                    multiplier=parameters["multiplier"],
                )

            elif feature_name == "ADX":
                feature_data = generate_adx(
                    feature_data,
                    period=parameters["period"],
                )

            else:
                raise ValueError(
                    f"Unsupported feature: {feature_name}"
                )

        return feature_data

    feature_data = generate_ema(feature_data, period=20)
    feature_data = generate_ema(feature_data, period=50)

    feature_data["RETURN_1"] = feature_data["Close"].pct_change()

    feature_data["VOLATILITY_20"] = (
        feature_data["RETURN_1"]
        .rolling(window=20)
        .std()
    )

    feature_data = generate_rsi(
        feature_data,
        period=14,
    )

    feature_data["VOLUME_MA_20"] = (
        feature_data["Volume"]
        .rolling(window=20)
        .mean()
    )

    return feature_data