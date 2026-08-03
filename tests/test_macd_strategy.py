import os
import sys
import pytest
import pandas as pd

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
)

from strategies.macd_strategy import MACDStrategy


def test_macd_strategy_uses_default_parameters():
    strategy = MACDStrategy()

    assert strategy.fast_period == 12
    assert strategy.slow_period == 26
    assert strategy.signal_period == 9


def test_macd_strategy_accepts_custom_parameters():
    strategy = MACDStrategy(
        fast_period=5,
        slow_period=15,
        signal_period=4,
    )

    assert strategy.fast_period == 5
    assert strategy.slow_period == 15
    assert strategy.signal_period == 4


def test_macd_fast_period_must_be_integer():
    with pytest.raises(
        TypeError,
        match="MACD fast period must be an integer.",
    ):
        MACDStrategy(
            fast_period="12",
            slow_period=26,
            signal_period=9,
        )


def test_macd_slow_period_must_be_integer():
    with pytest.raises(
        TypeError,
        match="MACD slow period must be an integer.",
    ):
        MACDStrategy(
            fast_period=12,
            slow_period="26",
            signal_period=9,
        )


def test_macd_signal_period_must_be_integer():
    with pytest.raises(
        TypeError,
        match="MACD signal period must be an integer.",
    ):
        MACDStrategy(
            fast_period=12,
            slow_period=26,
            signal_period="9",
        )


def test_macd_fast_period_must_be_positive():
    with pytest.raises(
        ValueError,
        match="MACD fast period must be greater than zero.",
    ):
        MACDStrategy(
            fast_period=0,
            slow_period=26,
            signal_period=9,
        )

    with pytest.raises(
        ValueError,
        match="MACD fast period must be greater than zero.",
    ):
        MACDStrategy(
            fast_period=-12,
            slow_period=26,
            signal_period=9,
        )


def test_macd_slow_period_must_be_positive():
    with pytest.raises(
        ValueError,
        match="MACD slow period must be greater than zero.",
    ):
        MACDStrategy(
            fast_period=12,
            slow_period=0,
            signal_period=9,
        )

    with pytest.raises(
        ValueError,
        match="MACD slow period must be greater than zero.",
    ):
        MACDStrategy(
            fast_period=12,
            slow_period=-26,
            signal_period=9,
        )


def test_macd_signal_period_must_be_positive():
    with pytest.raises(
        ValueError,
        match="MACD signal period must be greater than zero.",
    ):
        MACDStrategy(
            fast_period=12,
            slow_period=26,
            signal_period=0,
        )

    with pytest.raises(
        ValueError,
        match="MACD signal period must be greater than zero.",
    ):
        MACDStrategy(
            fast_period=12,
            slow_period=26,
            signal_period=-9,
        )


def test_macd_fast_period_must_be_less_than_slow_period():
    with pytest.raises(
        ValueError,
        match="MACD fast period must be less than slow period.",
    ):
        MACDStrategy(
            fast_period=26,
            slow_period=12,
            signal_period=9,
        )

    with pytest.raises(
        ValueError,
        match="MACD fast period must be less than slow period.",
    ):
        MACDStrategy(
            fast_period=12,
            slow_period=12,
            signal_period=9,
        )


def test_macd_strategy_declares_required_features():
    strategy = MACDStrategy()

    assert strategy.required_features == [
        {
            "name": "MACD",
            "parameters": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
            },
        },
    ]


def test_macd_strategy_required_features_use_custom_parameters():
    strategy = MACDStrategy(
        fast_period=5,
        slow_period=15,
        signal_period=4,
    )

    assert strategy.required_features == [
        {
            "name": "MACD",
            "parameters": {
                "fast_period": 5,
                "slow_period": 15,
                "signal_period": 4,
            },
        },
    ]


def test_macd_strategy_generates_signal_column():
    strategy = MACDStrategy()

    data = pd.DataFrame({
        "MACD_12_26": [0.0, 0.5, 0.2],
        "MACD_SIGNAL_12_26_9": [0.0, 0.3, 0.4],
    })

    result = strategy.generate_signals(data)

    assert isinstance(result, pd.DataFrame)
    assert "Signal" in result.columns


def test_macd_strategy_generates_buy_signal():
    strategy = MACDStrategy()

    data = pd.DataFrame({
        "MACD_12_26": [0.2, 0.4, 0.6],
        "MACD_SIGNAL_12_26_9": [0.3, 0.3, 0.5],
    })

    result = strategy.generate_signals(data)

    assert result["Signal"].tolist() == [0, 1, 0]


def test_macd_strategy_generates_sell_signal():
    strategy = MACDStrategy()

    data = pd.DataFrame({
        "MACD_12_26": [0.4, 0.2, 0.1],
        "MACD_SIGNAL_12_26_9": [0.3, 0.3, 0.2],
    })

    result = strategy.generate_signals(data)

    assert result["Signal"].tolist() == [0, -1, 0]


def test_macd_strategy_rejects_missing_macd_columns():
    strategy = MACDStrategy()

    data = pd.DataFrame({
        "Close": [100, 101, 102],
    })

    with pytest.raises(
        ValueError,
        match=(
            "Missing required columns: "
            "\\['MACD_12_26', 'MACD_SIGNAL_12_26_9'\\]"
        ),
    ):
        strategy.generate_signals(data)