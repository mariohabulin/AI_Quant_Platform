import os
import sys
import pytest

import pandas as pd

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from strategies.ema_strategy import EMAStrategy


def test_ema_strategy_accepts_custom_periods():
    strategy = EMAStrategy(
        fast_period=10,
        slow_period=30,
    )

    assert strategy.fast_period == 10
    assert strategy.slow_period == 30

def test_ema_strategy_uses_default_periods():
    strategy = EMAStrategy()

    assert strategy.fast_period == 20
    assert strategy.slow_period == 50

def test_fast_period_must_be_integer():
    with pytest.raises(
        TypeError,
        match="Fast period must be an integer.",
    ):
        EMAStrategy(
            fast_period="10",
            slow_period=30,
        )

def test_slow_period_must_be_integer():
    with pytest.raises(
        TypeError,
        match="Slow period must be an integer.",
    ):
        EMAStrategy(
            fast_period=10,
            slow_period="30",
        )

def test_fast_period_must_be_positive():
    with pytest.raises(
        ValueError,
        match="Fast period must be greater than zero.",
    ):
        EMAStrategy(
            fast_period=0,
            slow_period=30,
        )

def test_slow_period_must_be_positive():
    with pytest.raises(
        ValueError,
        match="Slow period must be greater than zero.",
    ):
        EMAStrategy(
            fast_period=10,
            slow_period=0,
        )

def test_fast_period_must_be_less_than_slow_period():
    with pytest.raises(
        ValueError,
        match="Fast period must be less than slow period.",
    ):
        EMAStrategy(
            fast_period=50,
            slow_period=20,
        )

def test_generate_signals_uses_custom_ema_columns():
    strategy = EMAStrategy(
        fast_period=10,
        slow_period=30,
    )

    df = pd.DataFrame(
        {
            "EMA_10": [10, 11],
            "EMA_30": [11, 10],
        }
    )

    result = strategy.generate_signals(df)

    assert result.loc[1, "Signal"] == 1

import pytest


def test_ema_strategy_declares_required_features():
    strategy = EMAStrategy(
        fast_period=10,
        slow_period=30,
    )

    assert strategy.required_features == [
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

