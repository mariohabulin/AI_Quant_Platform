import os
import sys
import pytest
import pandas as pd

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
)

from strategies.bollinger_strategy import BollingerStrategy


def test_bollinger_strategy_uses_default_parameters():
    strategy = BollingerStrategy()

    assert strategy.period == 20
    assert strategy.standard_deviations == 2.0


def test_bollinger_strategy_accepts_custom_parameters():
    strategy = BollingerStrategy(
        period=10,
        standard_deviations=2.5,
    )

    assert strategy.period == 10
    assert strategy.standard_deviations == 2.5


def test_bollinger_period_must_be_integer():
    with pytest.raises(
        TypeError,
        match="Bollinger period must be an integer.",
    ):
        BollingerStrategy(
            period="20",
            standard_deviations=2.0,
        )


def test_bollinger_period_must_be_positive():
    with pytest.raises(
        ValueError,
        match="Bollinger period must be greater than zero.",
    ):
        BollingerStrategy(
            period=0,
            standard_deviations=2.0,
        )

    with pytest.raises(
        ValueError,
        match="Bollinger period must be greater than zero.",
    ):
        BollingerStrategy(
            period=-20,
            standard_deviations=2.0,
        )


def test_bollinger_standard_deviations_must_be_number():
    with pytest.raises(
        TypeError,
        match="Bollinger standard deviations must be a number.",
    ):
        BollingerStrategy(
            period=20,
            standard_deviations="2.0",
        )


def test_bollinger_standard_deviations_must_be_positive():
    with pytest.raises(
        ValueError,
        match="Bollinger standard deviations must be greater than zero.",
    ):
        BollingerStrategy(
            period=20,
            standard_deviations=0,
        )

    with pytest.raises(
        ValueError,
        match="Bollinger standard deviations must be greater than zero.",
    ):
        BollingerStrategy(
            period=20,
            standard_deviations=-2.0,
        )


def test_bollinger_strategy_declares_required_features():
    strategy = BollingerStrategy()

    assert strategy.required_features == [
        {
            "name": "BOLLINGER_BANDS",
            "parameters": {
                "period": 20,
                "standard_deviations": 2.0,
            },
        },
    ]


def test_bollinger_strategy_required_features_use_custom_parameters():
    strategy = BollingerStrategy(
        period=10,
        standard_deviations=2.5,
    )

    assert strategy.required_features == [
        {
            "name": "BOLLINGER_BANDS",
            "parameters": {
                "period": 10,
                "standard_deviations": 2.5,
            },
        },
    ]


def test_bollinger_strategy_generates_signal_column():
    strategy = BollingerStrategy()

    data = pd.DataFrame({
        "Close": [100, 95, 105],
        "BOLLINGER_LOWER_20_2.0": [90, 96, 92],
        "BOLLINGER_UPPER_20_2.0": [110, 104, 104],
    })

    result = strategy.generate_signals(data)

    assert isinstance(result, pd.DataFrame)
    assert "Signal" in result.columns


def test_bollinger_strategy_generates_buy_signal():
    strategy = BollingerStrategy()

    data = pd.DataFrame({
        "Close": [100, 95, 94],
        "BOLLINGER_LOWER_20_2.0": [90, 96, 93],
        "BOLLINGER_UPPER_20_2.0": [110, 104, 105],
    })

    result = strategy.generate_signals(data)

    assert result["Signal"].tolist() == [0, 1, 0]


def test_bollinger_strategy_generates_sell_signal():
    strategy = BollingerStrategy()

    data = pd.DataFrame({
        "Close": [100, 105, 104],
        "BOLLINGER_LOWER_20_2.0": [90, 94, 93],
        "BOLLINGER_UPPER_20_2.0": [110, 104, 106],
    })

    result = strategy.generate_signals(data)

    assert result["Signal"].tolist() == [0, -1, 0]


def test_bollinger_strategy_rejects_missing_required_columns():
    strategy = BollingerStrategy()

    data = pd.DataFrame({
        "Close": [100, 101, 102],
    })

    with pytest.raises(
        ValueError,
        match=(
            "Missing required columns: "
            "\\['BOLLINGER_LOWER_20_2.0', "
            "'BOLLINGER_UPPER_20_2.0'\\]"
        ),
    ):
        strategy.generate_signals(data)