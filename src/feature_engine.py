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