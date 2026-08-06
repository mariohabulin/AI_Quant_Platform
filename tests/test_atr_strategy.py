import os
import sys

import pandas as pd
import pytest

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
)

from strategies.atr_strategy import ATRStrategy


def test_atr_strategy_uses_default_parameters():
    strategy = ATRStrategy()

    assert strategy.period == 14
    assert strategy.multiplier == 1.0


def test_atr_strategy_accepts_custom_parameters():
    strategy = ATRStrategy(period=20, multiplier=1.5)

    assert strategy.period == 20
    assert strategy.multiplier == 1.5


def test_atr_period_must_be_integer():
    with pytest.raises(TypeError, match="ATR period must be an integer."):
        ATRStrategy(period="14")


def test_atr_period_must_be_positive():
    with pytest.raises(
        ValueError,
        match="ATR period must be greater than zero.",
    ):
        ATRStrategy(period=0)


def test_atr_multiplier_must_be_number():
    with pytest.raises(
        TypeError,
        match="ATR multiplier must be a number.",
    ):
        ATRStrategy(multiplier="1.0")


def test_atr_multiplier_must_be_positive():
    with pytest.raises(
        ValueError,
        match="ATR multiplier must be greater than zero.",
    ):
        ATRStrategy(multiplier=0)


def test_atr_strategy_declares_required_features():
    strategy = ATRStrategy(period=20)

    assert strategy.required_features == [
        {
            "name": "ATR",
            "parameters": {"period": 20},
        },
    ]


def test_atr_strategy_generates_buy_sell_and_neutral_signals():
    strategy = ATRStrategy(period=2, multiplier=1.0)
    data = pd.DataFrame(
        {
            "Close": [100.0, 100.0, 103.0, 100.0, 100.5],
            "ATR_2": [2.0, 2.0, 2.0, 2.0, 2.0],
        }
    )

    result = strategy.generate_signals(data)

    assert result["Signal"].tolist() == [0, 0, 1, -1, 0]


def test_atr_strategy_uses_previous_atr_value():
    strategy = ATRStrategy(period=2, multiplier=1.0)
    data = pd.DataFrame(
        {
            "Close": [100.0, 103.0],
            "ATR_2": [2.0, 10.0],
        }
    )

    result = strategy.generate_signals(data)

    assert result["Signal"].tolist() == [0, 1]


def test_atr_strategy_rejects_missing_required_columns():
    strategy = ATRStrategy(period=14)
    data = pd.DataFrame({"Close": [100, 101, 102]})

    with pytest.raises(
        ValueError,
        match="Missing required columns: \\['ATR_14'\\]",
    ):
        strategy.generate_signals(data)
