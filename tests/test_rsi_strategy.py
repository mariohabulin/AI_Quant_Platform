import os
import sys

import pandas as pd
import pytest

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
)

from strategies.rsi_strategy import RSIStrategy


def test_rsi_strategy_uses_default_parameters():
    strategy = RSIStrategy()

    assert strategy.period == 14
    assert strategy.oversold == 30
    assert strategy.overbought == 70

def test_rsi_strategy_accepts_custom_parameters():
    strategy = RSIStrategy(
        period=10,
        oversold=25,
        overbought=75,
    )

    assert strategy.period == 10
    assert strategy.oversold == 25
    assert strategy.overbought == 75

def test_rsi_period_must_be_integer():
    with pytest.raises(
        TypeError,
        match="RSI period must be an integer.",
    ):
        RSIStrategy(
            period="14",
            oversold=30,
            overbought=70,
        )

def test_rsi_period_must_be_positive():
    with pytest.raises(
        ValueError,
        match="RSI period must be greater than zero.",
    ):
        RSIStrategy(period=0)

    with pytest.raises(
        ValueError,
        match="RSI period must be greater than zero.",
    ):
        RSIStrategy(period=-14)

def test_rsi_oversold_must_be_number():
    with pytest.raises(
        TypeError,
        match="RSI oversold threshold must be a number.",
    ):
        RSIStrategy(
            oversold="30",
        )

def test_rsi_overbought_must_be_number():
    with pytest.raises(
        TypeError,
        match="RSI overbought threshold must be a number.",
    ):
        RSIStrategy(
            overbought="70",
        )

def test_rsi_oversold_must_be_between_zero_and_one_hundred():
    with pytest.raises(
        ValueError,
        match="RSI oversold threshold must be between 0 and 100.",
    ):
        RSIStrategy(
            oversold=0,
        )

    with pytest.raises(
        ValueError,
        match="RSI oversold threshold must be between 0 and 100.",
    ):
        RSIStrategy(
            oversold=100,
        )

def test_rsi_overbought_must_be_between_zero_and_one_hundred():
    with pytest.raises(
        ValueError,
        match="RSI overbought threshold must be between 0 and 100.",
    ):
        RSIStrategy(
            overbought=0,
        )

    with pytest.raises(
        ValueError,
        match="RSI overbought threshold must be between 0 and 100.",
    ):
        RSIStrategy(
            overbought=100,
        )

def test_rsi_oversold_must_be_less_than_overbought():
    with pytest.raises(
        ValueError,
        match="RSI oversold threshold must be less than overbought threshold.",
    ):
        RSIStrategy(
            oversold=70,
            overbought=30,
        )

    with pytest.raises(
        ValueError,
        match="RSI oversold threshold must be less than overbought threshold.",
    ):
        RSIStrategy(
            oversold=50,
            overbought=50,
        )

def test_rsi_strategy_declares_required_features():
    strategy = RSIStrategy()

    assert strategy.required_features == [
        {
            "name": "RSI",
            "parameters": {
                "period": 14,
            },
        },
    ]

def test_rsi_strategy_required_features_use_custom_period():
    strategy = RSIStrategy(period=21)

    assert strategy.required_features == [
        {
            "name": "RSI",
            "parameters": {
                "period": 21,
            },
        },
    ]

def test_rsi_strategy_generates_signal_column():
    strategy = RSIStrategy()

    data = pd.DataFrame({
        "RSI_14": [25, 35, 75],
    })

    result = strategy.generate_signals(data)

    assert isinstance(result, pd.DataFrame)
    assert "Signal" in result.columns

def test_rsi_strategy_generates_buy_signal():
    strategy = RSIStrategy(
        period=14,
        oversold=30,
        overbought=70,
    )

    data = pd.DataFrame({
        "RSI_14": [35, 25, 20],
    })

    result = strategy.generate_signals(data)

    assert result["Signal"].tolist() == [0, 1, 1]

def test_rsi_strategy_generates_sell_signal():
    strategy = RSIStrategy(
        period=14,
        oversold=30,
        overbought=70,
    )

    data = pd.DataFrame({
        "RSI_14": [65, 75, 80],
    })

    result = strategy.generate_signals(data)

    assert result["Signal"].tolist() == [0, -1, -1]

def test_rsi_strategy_rejects_missing_rsi_column():
    strategy = RSIStrategy()

    data = pd.DataFrame({
        "Close": [100, 101, 102],
    })

    with pytest.raises(
        ValueError,
        match="Missing required columns: \\['RSI_14'\\]",
    ):
        strategy.generate_signals(data)