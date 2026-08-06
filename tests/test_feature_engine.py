import os
import sys

import pandas as pd
import pytest

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
)

from feature_engine import (
    generate_bollinger_bands,
    generate_ema,
    generate_features,
    generate_macd,
    generate_rsi,
    generate_donchian_channels
)


def test_generate_features():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    result = generate_features(data)

    assert isinstance(result, pd.DataFrame)

    expected_columns = {
        "EMA_20",
        "EMA_50",
        "RETURN_1",
        "VOLATILITY_20",
        "RSI_14",
        "VOLUME_MA_20",
    }

    assert expected_columns.issubset(result.columns)


def test_generate_dynamic_ema_feature():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    from feature_engine import generate_ema

    result = generate_ema(data, period=10)

    assert "EMA_10" in result.columns

    expected = data["Close"].ewm(
        span=10,
        adjust=False,
    ).mean()

    pd.testing.assert_series_equal(
        result["EMA_10"],
        expected,
        check_names=False,
    )


def test_generate_dynamic_ema_invalid_type():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    from feature_engine import generate_ema

    with pytest.raises(TypeError, match="EMA period must be an integer."):
        generate_ema(data, period="10")


def test_generate_dynamic_ema_invalid_period():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    from feature_engine import generate_ema

    with pytest.raises(
        ValueError,
        match="EMA period must be greater than zero.",
    ):
        generate_ema(data, period=0)

    with pytest.raises(
        ValueError,
        match="EMA period must be greater than zero.",
    ):
        generate_ema(data, period=-10)


def test_generate_dynamic_ema_does_not_modify_original_dataframe():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    original_data = data.copy(deep=True)

    from feature_engine import generate_ema

    result = generate_ema(data, period=10)

    pd.testing.assert_frame_equal(data, original_data)

    assert "EMA_10" in result.columns
    assert "EMA_10" not in data.columns


def test_generate_features_generates_only_required_ema_features():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    required_features = [
        {
            "name": "EMA",
            "parameters": {
                "period": 10,
            },
        },
        {
            "name": "EMA",
            "parameters": {
                "period": 30,
            },
        },
    ]

    result = generate_features(
        data,
        required_features=required_features,
    )

    assert "EMA_10" in result.columns
    assert "EMA_30" in result.columns

    assert "EMA_20" not in result.columns
    assert "EMA_50" not in result.columns
    assert "RSI_14" not in result.columns
    assert "VOLATILITY_20" not in result.columns
    assert "VOLUME_MA_20" not in result.columns


def test_generate_features_rejects_unknown_feature():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    required_features = [
        {
            "name": "UNKNOWN_FEATURE",
            "parameters": {},
        },
    ]

    with pytest.raises(
        ValueError,
        match="Unsupported feature: UNKNOWN_FEATURE",
    ):
        generate_features(
            data,
            required_features=required_features,
        )


def test_generate_features_rejects_non_list_required_features():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        TypeError,
        match="required_features must be a list.",
    ):
        generate_features(
            data,
            required_features="EMA",
        )


def test_generate_features_rejects_non_dictionary_feature_requirement():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        TypeError,
        match="Each feature requirement must be a dictionary.",
    ):
        generate_features(
            data,
            required_features=["EMA"],
        )


def test_generate_features_rejects_missing_feature_name():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    required_features = [
        {
            "parameters": {
                "period": 10,
            },
        },
    ]

    with pytest.raises(
        ValueError,
        match="Feature requirement must include 'name'.",
    ):
        generate_features(
            data,
            required_features=required_features,
        )


def test_generate_features_rejects_missing_feature_parameters():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    required_features = [
        {
            "name": "EMA",
        },
    ]

    with pytest.raises(
        ValueError,
        match="Feature requirement must include 'parameters'.",
    ):
        generate_features(
            data,
            required_features=required_features,
        )


def test_generate_dynamic_rsi_feature():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102, 103],
        "High": [101, 102, 103, 104, 105],
        "Low": [98, 99, 100, 101, 102],
        "Close": [100, 101, 102, 101, 103],
        "Volume": [1000, 1100, 1200, 1300, 1400],
    })

    from feature_engine import generate_rsi

    result = generate_rsi(data, period=3)

    assert "RSI_3" in result.columns


def test_generate_features_generates_required_rsi_feature():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102, 103],
        "High": [101, 102, 103, 104, 105],
        "Low": [98, 99, 100, 101, 102],
        "Close": [100, 101, 102, 101, 103],
        "Volume": [1000, 1100, 1200, 1300, 1400],
    })

    required_features = [
        {
            "name": "RSI",
            "parameters": {
                "period": 3,
            },
        },
    ]

    result = generate_features(
        data,
        required_features=required_features,
    )

    assert "RSI_3" in result.columns

    assert "EMA_20" not in result.columns
    assert "EMA_50" not in result.columns
    assert "RSI_14" not in result.columns

def test_generate_dynamic_macd_feature():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102, 103],
        "High": [101, 102, 103, 104, 105],
        "Low": [98, 99, 100, 101, 102],
        "Close": [100, 101, 103, 102, 105],
        "Volume": [1000, 1100, 1200, 1300, 1400],
    })

    from feature_engine import generate_macd

    result = generate_macd(
        data,
        fast_period=2,
        slow_period=3,
        signal_period=2,
    )

    assert "MACD_2_3" in result.columns
    assert "MACD_SIGNAL_2_3_2" in result.columns
    assert "MACD_HISTOGRAM_2_3_2" in result.columns


def test_generate_macd_fast_period_must_be_integer():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        TypeError,
        match="MACD fast period must be an integer.",
    ):
        generate_macd(
            data,
            fast_period="12",
            slow_period=26,
            signal_period=9,
        )


def test_generate_macd_slow_period_must_be_integer():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        TypeError,
        match="MACD slow period must be an integer.",
    ):
        generate_macd(
            data,
            fast_period=12,
            slow_period="26",
            signal_period=9,
        )


def test_generate_macd_signal_period_must_be_integer():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        TypeError,
        match="MACD signal period must be an integer.",
    ):
        generate_macd(
            data,
            fast_period=12,
            slow_period=26,
            signal_period="9",
        )


def test_generate_macd_fast_period_must_be_positive():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        ValueError,
        match="MACD fast period must be greater than zero.",
    ):
        generate_macd(
            data,
            fast_period=0,
            slow_period=26,
            signal_period=9,
        )


def test_generate_macd_slow_period_must_be_positive():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        ValueError,
        match="MACD slow period must be greater than zero.",
    ):
        generate_macd(
            data,
            fast_period=12,
            slow_period=0,
            signal_period=9,
        )


def test_generate_macd_signal_period_must_be_positive():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        ValueError,
        match="MACD signal period must be greater than zero.",
    ):
        generate_macd(
            data,
            fast_period=12,
            slow_period=26,
            signal_period=0,
        )


def test_generate_macd_fast_period_must_be_less_than_slow_period():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        ValueError,
        match="MACD fast period must be less than slow period.",
    ):
        generate_macd(
            data,
            fast_period=26,
            slow_period=12,
            signal_period=9,
        )

    with pytest.raises(
        ValueError,
        match="MACD fast period must be less than slow period.",
    ):
        generate_macd(
            data,
            fast_period=12,
            slow_period=12,
            signal_period=9,
        )


def test_generate_macd_does_not_modify_original_dataframe():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102, 103],
        "High": [101, 102, 103, 104, 105],
        "Low": [98, 99, 100, 101, 102],
        "Close": [100, 101, 103, 102, 105],
        "Volume": [1000, 1100, 1200, 1300, 1400],
    })

    original_data = data.copy(deep=True)

    result = generate_macd(
        data,
        fast_period=2,
        slow_period=3,
        signal_period=2,
    )

    pd.testing.assert_frame_equal(data, original_data)

    assert "MACD_2_3" in result.columns
    assert "MACD_2_3" not in data.columns


def test_generate_features_generates_required_macd_feature():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102, 103],
        "High": [101, 102, 103, 104, 105],
        "Low": [98, 99, 100, 101, 102],
        "Close": [100, 101, 103, 102, 105],
        "Volume": [1000, 1100, 1200, 1300, 1400],
    })

    required_features = [
        {
            "name": "MACD",
            "parameters": {
                "fast_period": 2,
                "slow_period": 3,
                "signal_period": 2,
            },
        },
    ]

    result = generate_features(
        data,
        required_features=required_features,
    )

    assert "MACD_2_3" in result.columns
    assert "MACD_SIGNAL_2_3_2" in result.columns
    assert "MACD_HISTOGRAM_2_3_2" in result.columns

    assert "EMA_20" not in result.columns
    assert "EMA_50" not in result.columns
    assert "RSI_14" not in result.columns


def test_generate_macd_calculates_expected_values():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102, 103],
        "High": [101, 102, 103, 104, 105],
        "Low": [98, 99, 100, 101, 102],
        "Close": [100, 101, 103, 102, 105],
        "Volume": [1000, 1100, 1200, 1300, 1400],
    })

    result = generate_macd(
        data,
        fast_period=2,
        slow_period=3,
        signal_period=2,
    )

    expected_fast_ema = data["Close"].ewm(
        span=2,
        adjust=False,
    ).mean()

    expected_slow_ema = data["Close"].ewm(
        span=3,
        adjust=False,
    ).mean()

    expected_macd = expected_fast_ema - expected_slow_ema

    expected_signal = expected_macd.ewm(
        span=2,
        adjust=False,
    ).mean()

    expected_histogram = expected_macd - expected_signal

    pd.testing.assert_series_equal(
        result["MACD_2_3"],
        expected_macd,
        check_names=False,
    )

    pd.testing.assert_series_equal(
        result["MACD_SIGNAL_2_3_2"],
        expected_signal,
        check_names=False,
    )

    pd.testing.assert_series_equal(
        result["MACD_HISTOGRAM_2_3_2"],
        expected_histogram,
        check_names=False,
    )


def test_generate_dynamic_bollinger_feature():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102, 103],
        "High": [101, 102, 103, 104, 105],
        "Low": [98, 99, 100, 101, 102],
        "Close": [100, 101, 103, 102, 105],
        "Volume": [1000, 1100, 1200, 1300, 1400],
    })

    result = generate_bollinger_bands(
        data,
        period=3,
        standard_deviations=2.0,
    )

    assert "BOLLINGER_MIDDLE_3" in result.columns
    assert "BOLLINGER_UPPER_3_2.0" in result.columns
    assert "BOLLINGER_LOWER_3_2.0" in result.columns


def test_generate_bollinger_period_must_be_integer():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        TypeError,
        match="Bollinger period must be an integer.",
    ):
        generate_bollinger_bands(
            data,
            period="20",
            standard_deviations=2.0,
        )


def test_generate_bollinger_period_must_be_positive():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        ValueError,
        match="Bollinger period must be greater than zero.",
    ):
        generate_bollinger_bands(
            data,
            period=0,
            standard_deviations=2.0,
        )

    with pytest.raises(
        ValueError,
        match="Bollinger period must be greater than zero.",
    ):
        generate_bollinger_bands(
            data,
            period=-20,
            standard_deviations=2.0,
        )


def test_generate_bollinger_standard_deviations_must_be_number():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        TypeError,
        match="Bollinger standard deviations must be a number.",
    ):
        generate_bollinger_bands(
            data,
            period=20,
            standard_deviations="2.0",
        )


def test_generate_bollinger_standard_deviations_must_be_positive():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        ValueError,
        match="Bollinger standard deviations must be greater than zero.",
    ):
        generate_bollinger_bands(
            data,
            period=20,
            standard_deviations=0,
        )

    with pytest.raises(
        ValueError,
        match="Bollinger standard deviations must be greater than zero.",
    ):
        generate_bollinger_bands(
            data,
            period=20,
            standard_deviations=-2.0,
        )


def test_generate_bollinger_does_not_modify_original_dataframe():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102, 103],
        "High": [101, 102, 103, 104, 105],
        "Low": [98, 99, 100, 101, 102],
        "Close": [100, 101, 103, 102, 105],
        "Volume": [1000, 1100, 1200, 1300, 1400],
    })

    original_data = data.copy(deep=True)

    result = generate_bollinger_bands(
        data,
        period=3,
        standard_deviations=2.0,
    )

    pd.testing.assert_frame_equal(data, original_data)

    assert "BOLLINGER_MIDDLE_3" in result.columns
    assert "BOLLINGER_MIDDLE_3" not in data.columns


def test_generate_bollinger_calculates_expected_values():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102, 103],
        "High": [101, 102, 103, 104, 105],
        "Low": [98, 99, 100, 101, 102],
        "Close": [100, 101, 103, 102, 105],
        "Volume": [1000, 1100, 1200, 1300, 1400],
    })

    result = generate_bollinger_bands(
        data,
        period=3,
        standard_deviations=2.0,
    )

    expected_middle = data["Close"].rolling(
        window=3,
    ).mean()

    expected_std = data["Close"].rolling(
        window=3,
    ).std()

    expected_upper = expected_middle + 2.0 * expected_std
    expected_lower = expected_middle - 2.0 * expected_std

    pd.testing.assert_series_equal(
        result["BOLLINGER_MIDDLE_3"],
        expected_middle,
        check_names=False,
    )

    pd.testing.assert_series_equal(
        result["BOLLINGER_UPPER_3_2.0"],
        expected_upper,
        check_names=False,
    )

    pd.testing.assert_series_equal(
        result["BOLLINGER_LOWER_3_2.0"],
        expected_lower,
        check_names=False,
    )


def test_generate_features_generates_required_bollinger_feature():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102, 103],
        "High": [101, 102, 103, 104, 105],
        "Low": [98, 99, 100, 101, 102],
        "Close": [100, 101, 103, 102, 105],
        "Volume": [1000, 1100, 1200, 1300, 1400],
    })

    required_features = [
        {
            "name": "BOLLINGER_BANDS",
            "parameters": {
                "period": 3,
                "standard_deviations": 2.0,
            },
        },
    ]

    result = generate_features(
        data,
        required_features=required_features,
    )

    assert "BOLLINGER_MIDDLE_3" in result.columns
    assert "BOLLINGER_UPPER_3_2.0" in result.columns
    assert "BOLLINGER_LOWER_3_2.0" in result.columns

    assert "EMA_20" not in result.columns
    assert "EMA_50" not in result.columns
    assert "RSI_14" not in result.columns


def test_generate_dynamic_donchian_feature():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    result = generate_donchian_channels(
        data,
        period=20,
    )

    assert "DONCHIAN_UPPER_20" in result.columns
    assert "DONCHIAN_LOWER_20" in result.columns
    assert "DONCHIAN_MIDDLE_20" in result.columns


def test_generate_donchian_period_must_be_integer():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        TypeError,
        match="Donchian period must be an integer.",
    ):
        generate_donchian_channels(
            data,
            period="20",
        )


def test_generate_donchian_period_must_be_positive():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    with pytest.raises(
        ValueError,
        match="Donchian period must be greater than zero.",
    ):
        generate_donchian_channels(
            data,
            period=0,
        )

    with pytest.raises(
        ValueError,
        match="Donchian period must be greater than zero.",
    ):
        generate_donchian_channels(
            data,
            period=-20,
        )


def test_generate_donchian_does_not_modify_original_dataframe():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    original_data = data.copy(deep=True)

    result = generate_donchian_channels(
        data,
        period=2,
    )

    pd.testing.assert_frame_equal(data, original_data)

    assert "DONCHIAN_UPPER_2" in result.columns
    assert "DONCHIAN_UPPER_2" not in data.columns


def test_generate_donchian_calculates_expected_values():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102],
        "High": [101, 103, 102, 105],
        "Low": [98, 99, 97, 100],
        "Close": [100, 102, 101, 104],
        "Volume": [1000, 1100, 1200, 1300],
    })

    result = generate_donchian_channels(
        data,
        period=2,
    )

    expected_upper = data["High"].rolling(
        window=2,
    ).max().shift(1)

    expected_lower = data["Low"].rolling(
        window=2,
    ).min().shift(1)

    expected_middle = (
        expected_upper + expected_lower
    ) / 2

    pd.testing.assert_series_equal(
        result["DONCHIAN_UPPER_2"],
        expected_upper,
        check_names=False,
    )

    pd.testing.assert_series_equal(
        result["DONCHIAN_LOWER_2"],
        expected_lower,
        check_names=False,
    )

    pd.testing.assert_series_equal(
        result["DONCHIAN_MIDDLE_2"],
        expected_middle,
        check_names=False,
    )


def test_generate_features_generates_required_donchian_feature():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102],
        "High": [101, 103, 102, 105],
        "Low": [98, 99, 97, 100],
        "Close": [100, 102, 101, 104],
        "Volume": [1000, 1100, 1200, 1300],
    })

    required_features = [
        {
            "name": "DONCHIAN_CHANNELS",
            "parameters": {
                "period": 2,
            },
        },
    ]

    result = generate_features(
        data,
        required_features=required_features,
    )

    assert "DONCHIAN_UPPER_2" in result.columns
    assert "DONCHIAN_LOWER_2" in result.columns
    assert "DONCHIAN_MIDDLE_2" in result.columns

    assert "EMA_20" not in result.columns
    assert "EMA_50" not in result.columns
    assert "RSI_14" not in result.columns
    assert "MACD_12_26" not in result.columns
    assert "BOLLINGER_MIDDLE_20" not in result.columns


def test_generate_donchian_uses_previous_candles_only():
    data = pd.DataFrame({
        "Open": [99, 100, 101, 102],
        "High": [101, 103, 102, 105],
        "Low": [98, 99, 97, 100],
        "Close": [100, 102, 101, 104],
        "Volume": [1000, 1100, 1200, 1300],
    })

    result = generate_donchian_channels(
        data,
        period=2,
    )

    expected_upper = data["High"].rolling(
        window=2,
    ).max().shift(1)

    expected_lower = data["Low"].rolling(
        window=2,
    ).min().shift(1)

    expected_middle = (
        expected_upper + expected_lower
    ) / 2

    pd.testing.assert_series_equal(
        result["DONCHIAN_UPPER_2"],
        expected_upper,
        check_names=False,
    )

    pd.testing.assert_series_equal(
        result["DONCHIAN_LOWER_2"],
        expected_lower,
        check_names=False,
    )

    pd.testing.assert_series_equal(
        result["DONCHIAN_MIDDLE_2"],
        expected_middle,
        check_names=False,
    )

def test_generate_atr_adds_requested_feature():
    from feature_engine import generate_atr

    data = pd.DataFrame({
        "Open": [100, 101, 105, 104],
        "High": [102, 106, 107, 108],
        "Low": [99, 100, 103, 102],
        "Close": [101, 105, 104, 107],
        "Volume": [1000, 1000, 1000, 1000],
    })

    result = generate_atr(data, period=2)

    assert "ATR_2" in result.columns
    assert "ATR_2" not in data.columns


def test_generate_atr_uses_true_range_and_wilder_smoothing():
    from feature_engine import generate_atr

    data = pd.DataFrame({
        "Open": [100, 101, 105, 104],
        "High": [102, 106, 107, 108],
        "Low": [99, 100, 103, 102],
        "Close": [101, 105, 104, 107],
        "Volume": [1000, 1000, 1000, 1000],
    })

    result = generate_atr(data, period=2)

    expected = pd.Series([float("nan"), 4.5, 4.25, 5.125])
    pd.testing.assert_series_equal(
        result["ATR_2"].reset_index(drop=True),
        expected,
        check_names=False,
    )


def test_generate_atr_rejects_invalid_period_type():
    from feature_engine import generate_atr

    data = pd.DataFrame({
        "Open": [100],
        "High": [101],
        "Low": [99],
        "Close": [100],
        "Volume": [1000],
    })

    with pytest.raises(TypeError, match="ATR period must be an integer."):
        generate_atr(data, period="14")


def test_generate_atr_rejects_non_positive_period():
    from feature_engine import generate_atr

    data = pd.DataFrame({
        "Open": [100],
        "High": [101],
        "Low": [99],
        "Close": [100],
        "Volume": [1000],
    })

    with pytest.raises(
        ValueError,
        match="ATR period must be greater than zero.",
    ):
        generate_atr(data, period=0)


def test_generate_features_supports_atr_requirement():
    data = pd.DataFrame({
        "Open": [100, 101, 102],
        "High": [102, 103, 104],
        "Low": [99, 100, 101],
        "Close": [101, 102, 103],
        "Volume": [1000, 1000, 1000],
    })

    result = generate_features(
        data,
        required_features=[
            {
                "name": "ATR",
                "parameters": {"period": 2},
            },
        ],
    )

    assert "ATR_2" in result.columns
    assert "EMA_20" not in result.columns


def test_generate_supertrend_adds_line_direction_and_atr_features():
    from feature_engine import generate_supertrend

    data = pd.DataFrame({
        "Open": [100, 101, 102, 103, 104],
        "High": [102, 103, 104, 105, 106],
        "Low": [99, 100, 101, 102, 103],
        "Close": [101, 102, 103, 104, 105],
        "Volume": [1000] * 5,
    })

    result = generate_supertrend(data, period=2, multiplier=1.0)

    assert "ATR_2" in result.columns
    assert "SUPERTREND_2_1.0" in result.columns
    assert "SUPERTREND_DIRECTION_2_1.0" in result.columns
    assert "SUPERTREND_2_1.0" not in data.columns


def test_generate_supertrend_direction_is_bounded():
    from feature_engine import generate_supertrend

    close = [100, 102, 104, 106, 103, 100, 97, 100, 104]
    data = pd.DataFrame({
        "Open": close,
        "High": [value + 1 for value in close],
        "Low": [value - 1 for value in close],
        "Close": close,
        "Volume": [1000] * len(close),
    })

    result = generate_supertrend(data, period=2, multiplier=1.0)

    assert set(
        result["SUPERTREND_DIRECTION_2_1.0"].unique()
    ).issubset({-1, 0, 1})
    assert result["SUPERTREND_DIRECTION_2_1.0"].eq(1).any()
    assert result["SUPERTREND_DIRECTION_2_1.0"].eq(-1).any()


def test_generate_supertrend_rejects_invalid_parameters():
    from feature_engine import generate_supertrend

    data = pd.DataFrame({
        "Open": [100],
        "High": [101],
        "Low": [99],
        "Close": [100],
        "Volume": [1000],
    })

    with pytest.raises(
        TypeError,
        match="Supertrend period must be an integer.",
    ):
        generate_supertrend(data, period="10", multiplier=3.0)

    with pytest.raises(
        ValueError,
        match="Supertrend period must be greater than zero.",
    ):
        generate_supertrend(data, period=0, multiplier=3.0)

    with pytest.raises(
        TypeError,
        match="Supertrend multiplier must be a number.",
    ):
        generate_supertrend(data, period=10, multiplier="3.0")

    with pytest.raises(
        ValueError,
        match="Supertrend multiplier must be greater than zero.",
    ):
        generate_supertrend(data, period=10, multiplier=0)


def test_generate_features_supports_supertrend_requirement():
    data = pd.DataFrame({
        "Open": [100, 101, 102, 103],
        "High": [102, 103, 104, 105],
        "Low": [99, 100, 101, 102],
        "Close": [101, 102, 103, 104],
        "Volume": [1000] * 4,
    })

    result = generate_features(
        data,
        required_features=[
            {
                "name": "SUPERTREND",
                "parameters": {
                    "period": 2,
                    "multiplier": 1.0,
                },
            },
        ],
    )

    assert "SUPERTREND_2_1.0" in result.columns
    assert "SUPERTREND_DIRECTION_2_1.0" in result.columns
    assert "EMA_20" not in result.columns


def test_generate_adx_adds_directional_and_strength_features():
    from feature_engine import generate_adx
    close = [100, 102, 104, 106, 108, 106, 104, 102, 100, 98]
    data = pd.DataFrame({
        "Open": close, "High": [v + 1 for v in close],
        "Low": [v - 1 for v in close], "Close": close,
        "Volume": [1000] * len(close),
    })
    result = generate_adx(data, period=3)
    assert "PLUS_DI_3" in result.columns
    assert "MINUS_DI_3" in result.columns
    assert "ADX_3" in result.columns
    assert result["ADX_3"].dropna().between(0, 100).all()
    assert "ADX_3" not in data.columns


def test_generate_adx_rejects_invalid_period():
    from feature_engine import generate_adx
    data = pd.DataFrame({"Open": [100], "High": [101], "Low": [99], "Close": [100], "Volume": [1000]})
    with pytest.raises(TypeError, match="ADX period must be an integer."):
        generate_adx(data, period="14")
    with pytest.raises(ValueError, match="ADX period must be greater than zero."):
        generate_adx(data, period=0)


def test_generate_features_supports_adx_requirement():
    data = pd.DataFrame({
        "Open": [100, 101, 102, 103, 104, 105],
        "High": [102, 103, 104, 105, 106, 107],
        "Low": [99, 100, 101, 102, 103, 104],
        "Close": [101, 102, 103, 104, 105, 106],
        "Volume": [1000] * 6,
    })
    result = generate_features(data, required_features=[{"name": "ADX", "parameters": {"period": 2}}])
    assert "ADX_2" in result.columns
    assert "PLUS_DI_2" in result.columns
    assert "MINUS_DI_2" in result.columns
    assert "EMA_20" not in result.columns


def test_generate_stochastic_adds_k_and_d_features():
    from feature_engine import generate_stochastic

    data = pd.DataFrame({
        "Open": [10, 11, 12, 13, 14, 15],
        "High": [12, 13, 14, 15, 16, 17],
        "Low": [8, 9, 10, 11, 12, 13],
        "Close": [11, 12, 13, 14, 15, 16],
        "Volume": [1000] * 6,
    })

    result = generate_stochastic(data, k_period=3, d_period=2)

    assert "STOCHASTIC_K_3" in result.columns
    assert "STOCHASTIC_D_3_2" in result.columns
    assert result["STOCHASTIC_K_3"].dropna().between(0, 100).all()
    assert "STOCHASTIC_K_3" not in data.columns


def test_generate_stochastic_rejects_invalid_periods():
    from feature_engine import generate_stochastic

    data = pd.DataFrame({
        "Open": [100],
        "High": [101],
        "Low": [99],
        "Close": [100],
        "Volume": [1000],
    })

    with pytest.raises(
        TypeError,
        match="Stochastic %K period must be an integer.",
    ):
        generate_stochastic(data, k_period="14", d_period=3)

    with pytest.raises(
        ValueError,
        match="Stochastic %K period must be greater than zero.",
    ):
        generate_stochastic(data, k_period=0, d_period=3)

    with pytest.raises(
        TypeError,
        match="Stochastic %D period must be an integer.",
    ):
        generate_stochastic(data, k_period=14, d_period="3")

    with pytest.raises(
        ValueError,
        match="Stochastic %D period must be greater than zero.",
    ):
        generate_stochastic(data, k_period=14, d_period=0)


def test_generate_features_supports_stochastic_requirement():
    data = pd.DataFrame({
        "Open": [10, 11, 12, 13, 14, 15],
        "High": [12, 13, 14, 15, 16, 17],
        "Low": [8, 9, 10, 11, 12, 13],
        "Close": [11, 12, 13, 14, 15, 16],
        "Volume": [1000] * 6,
    })

    result = generate_features(
        data,
        required_features=[{
            "name": "STOCHASTIC",
            "parameters": {
                "k_period": 3,
                "d_period": 2,
            },
        }],
    )

    assert "STOCHASTIC_K_3" in result.columns
    assert "STOCHASTIC_D_3_2" in result.columns
    assert "EMA_20" not in result.columns
