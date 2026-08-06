import os
import sys

import pandas as pd
import pytest

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
)

from strategies.stochastic_strategy import StochasticStrategy


def test_stochastic_strategy_uses_default_parameters():
    strategy = StochasticStrategy()

    assert strategy.k_period == 14
    assert strategy.d_period == 3
    assert strategy.oversold == 20.0
    assert strategy.overbought == 80.0


def test_stochastic_strategy_accepts_custom_parameters():
    strategy = StochasticStrategy(
        k_period=10,
        d_period=4,
        oversold=25,
        overbought=75,
    )

    assert strategy.k_period == 10
    assert strategy.d_period == 4
    assert strategy.oversold == 25
    assert strategy.overbought == 75


@pytest.mark.parametrize(
    "parameter,value,error,message",
    [
        ("k_period", "14", TypeError, "Stochastic %K period must be an integer."),
        ("k_period", 0, ValueError, "Stochastic %K period must be greater than zero."),
        ("d_period", "3", TypeError, "Stochastic %D period must be an integer."),
        ("d_period", 0, ValueError, "Stochastic %D period must be greater than zero."),
    ],
)
def test_stochastic_strategy_rejects_invalid_periods(
    parameter,
    value,
    error,
    message,
):
    with pytest.raises(error, match=message):
        StochasticStrategy(**{parameter: value})


@pytest.mark.parametrize(
    "parameter,value,error,message",
    [
        (
            "oversold",
            "20",
            TypeError,
            "Stochastic oversold threshold must be a number.",
        ),
        (
            "oversold",
            -1,
            ValueError,
            "Stochastic oversold threshold must be between 0 and 100.",
        ),
        (
            "overbought",
            "80",
            TypeError,
            "Stochastic overbought threshold must be a number.",
        ),
        (
            "overbought",
            101,
            ValueError,
            "Stochastic overbought threshold must be between 0 and 100.",
        ),
    ],
)
def test_stochastic_strategy_rejects_invalid_thresholds(
    parameter,
    value,
    error,
    message,
):
    with pytest.raises(error, match=message):
        StochasticStrategy(**{parameter: value})


def test_stochastic_strategy_rejects_inverted_thresholds():
    with pytest.raises(
        ValueError,
        match=(
            "Stochastic oversold threshold must be less than "
            "overbought threshold."
        ),
    ):
        StochasticStrategy(oversold=80, overbought=20)


def test_stochastic_strategy_declares_required_features():
    strategy = StochasticStrategy(k_period=10, d_period=4)

    assert strategy.required_features == [{
        "name": "STOCHASTIC",
        "parameters": {
            "k_period": 10,
            "d_period": 4,
        },
    }]


def test_stochastic_strategy_generates_crossovers_in_extreme_zones():
    data = pd.DataFrame({
        "STOCHASTIC_K_3": [10, 15, 25, 90, 85, 75],
        "STOCHASTIC_D_3_2": [12, 18, 20, 88, 82, 80],
    })

    result = StochasticStrategy(
        k_period=3,
        d_period=2,
        oversold=20,
        overbought=80,
    ).generate_signals(data)

    assert result["Signal"].tolist() == [0, 0, 1, 0, 0, -1]


def test_stochastic_strategy_holds_crossovers_outside_extreme_zones():
    data = pd.DataFrame({
        "STOCHASTIC_K_3": [40, 45, 55, 60],
        "STOCHASTIC_D_3_2": [42, 48, 50, 58],
    })

    result = StochasticStrategy(
        k_period=3,
        d_period=2,
    ).generate_signals(data)

    assert result["Signal"].eq(0).all()


def test_stochastic_strategy_preserves_input_data():
    data = pd.DataFrame({
        "STOCHASTIC_K_3": [10, 15, 25],
        "STOCHASTIC_D_3_2": [12, 18, 20],
    })

    StochasticStrategy(k_period=3, d_period=2).generate_signals(data)

    assert "Signal" not in data.columns


def test_stochastic_strategy_rejects_non_dataframe_input():
    with pytest.raises(
        TypeError,
        match="Input data must be a pandas DataFrame.",
    ):
        StochasticStrategy().generate_signals([])


def test_stochastic_strategy_rejects_missing_required_columns():
    with pytest.raises(
        ValueError,
        match=(
            r"Missing required columns: \['STOCHASTIC_K_14', "
            r"'STOCHASTIC_D_14_3'\]"
        ),
    ):
        StochasticStrategy().generate_signals(
            pd.DataFrame({"Close": [100]})
        )
