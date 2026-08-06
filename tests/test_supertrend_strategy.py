import os
import sys

import pandas as pd
import pytest

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
)

from strategies.supertrend_strategy import SupertrendStrategy


def test_supertrend_strategy_uses_default_parameters():
    strategy = SupertrendStrategy()

    assert strategy.period == 10
    assert strategy.multiplier == 3.0


def test_supertrend_strategy_accepts_custom_parameters():
    strategy = SupertrendStrategy(period=14, multiplier=2.5)

    assert strategy.period == 14
    assert strategy.multiplier == 2.5


def test_supertrend_period_must_be_integer():
    with pytest.raises(
        TypeError,
        match="Supertrend period must be an integer.",
    ):
        SupertrendStrategy(period="10")


def test_supertrend_period_must_be_positive():
    with pytest.raises(
        ValueError,
        match="Supertrend period must be greater than zero.",
    ):
        SupertrendStrategy(period=0)


def test_supertrend_multiplier_must_be_number():
    with pytest.raises(
        TypeError,
        match="Supertrend multiplier must be a number.",
    ):
        SupertrendStrategy(multiplier="3.0")


def test_supertrend_multiplier_must_be_positive():
    with pytest.raises(
        ValueError,
        match="Supertrend multiplier must be greater than zero.",
    ):
        SupertrendStrategy(multiplier=0)


def test_supertrend_strategy_declares_required_features():
    strategy = SupertrendStrategy(period=14, multiplier=2.5)

    assert strategy.required_features == [
        {
            "name": "SUPERTREND",
            "parameters": {
                "period": 14,
                "multiplier": 2.5,
            },
        },
    ]


def test_supertrend_strategy_signals_only_direction_changes():
    strategy = SupertrendStrategy(period=2, multiplier=1.0)
    data = pd.DataFrame(
        {
            "Close": [100, 101, 102, 99, 98, 103],
            "SUPERTREND_DIRECTION_2_1.0": [0, 1, 1, -1, -1, 1],
        }
    )

    result = strategy.generate_signals(data)

    assert result["Signal"].tolist() == [0, 0, 0, -1, 0, 1]


def test_supertrend_strategy_rejects_missing_required_columns():
    strategy = SupertrendStrategy()
    data = pd.DataFrame({"Close": [100, 101, 102]})

    with pytest.raises(
        ValueError,
        match=(
            r"Missing required columns: "
            r"\['SUPERTREND_DIRECTION_10_3\.0'\]"
        ),
    ):
        strategy.generate_signals(data)
