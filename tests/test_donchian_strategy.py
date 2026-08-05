import os
import sys
import pytest
import pandas as pd

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
)

from strategies.donchian_strategy import DonchianStrategy


def test_donchian_strategy_uses_default_parameters():
    strategy = DonchianStrategy()

    assert strategy.period == 20


def test_donchian_strategy_accepts_custom_period():
    strategy = DonchianStrategy(
        period=55,
    )

    assert strategy.period == 55


def test_donchian_period_must_be_integer():
    with pytest.raises(
        TypeError,
        match="Donchian period must be an integer.",
    ):
        DonchianStrategy(
            period="20",
        )


def test_donchian_period_must_be_positive():
    with pytest.raises(
        ValueError,
        match="Donchian period must be greater than zero.",
    ):
        DonchianStrategy(
            period=0,
        )

    with pytest.raises(
        ValueError,
        match="Donchian period must be greater than zero.",
    ):
        DonchianStrategy(
            period=-20,
        )


def test_donchian_strategy_declares_required_features():
    strategy = DonchianStrategy()

    assert strategy.required_features == [
        {
            "name": "DONCHIAN_CHANNELS",
            "parameters": {
                "period": 20,
            },
        },
    ]


def test_donchian_strategy_required_features_use_custom_period():
    strategy = DonchianStrategy(
        period=55,
    )

    assert strategy.required_features == [
        {
            "name": "DONCHIAN_CHANNELS",
            "parameters": {
                "period": 55,
            },
        },
    ]


def test_donchian_strategy_generates_signal_column():
    strategy = DonchianStrategy()

    data = pd.DataFrame({
        "Close": [100, 105, 95],
        "DONCHIAN_UPPER_20": [110, 104, 108],
        "DONCHIAN_LOWER_20": [90, 92, 96],
    })

    result = strategy.generate_signals(data)

    assert isinstance(result, pd.DataFrame)
    assert "Signal" in result.columns


def test_donchian_strategy_generates_buy_signal():
    strategy = DonchianStrategy()

    data = pd.DataFrame({
        "Close": [100, 105, 106],
        "DONCHIAN_UPPER_20": [110, 104, 108],
        "DONCHIAN_LOWER_20": [90, 92, 93],
    })

    result = strategy.generate_signals(data)

    assert result["Signal"].tolist() == [0, 1, 0]


def test_donchian_strategy_generates_sell_signal():
    strategy = DonchianStrategy()

    data = pd.DataFrame({
        "Close": [100, 95, 96],
        "DONCHIAN_UPPER_20": [110, 108, 109],
        "DONCHIAN_LOWER_20": [90, 96, 94],
    })

    result = strategy.generate_signals(data)

    assert result["Signal"].tolist() == [0, -1, 0]


def test_donchian_strategy_rejects_missing_required_columns():
    strategy = DonchianStrategy()

    data = pd.DataFrame({
        "Close": [100, 101, 102],
    })

    with pytest.raises(
        ValueError,
        match=(
            "Missing required columns: "
            "\\['DONCHIAN_UPPER_20', 'DONCHIAN_LOWER_20'\\]"
        ),
    ):
        strategy.generate_signals(data)

