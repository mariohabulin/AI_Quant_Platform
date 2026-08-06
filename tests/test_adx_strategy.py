import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from strategies.adx_strategy import ADXStrategy


def test_adx_strategy_uses_default_parameters():
    strategy = ADXStrategy()
    assert strategy.period == 14
    assert strategy.threshold == 25.0


def test_adx_strategy_accepts_custom_parameters():
    strategy = ADXStrategy(period=10, threshold=20)
    assert strategy.period == 10
    assert strategy.threshold == 20

@pytest.mark.parametrize("period,error,message", [("14", TypeError, "ADX period must be an integer."), (0, ValueError, "ADX period must be greater than zero.")])
def test_adx_strategy_rejects_invalid_period(period, error, message):
    with pytest.raises(error, match=message):
        ADXStrategy(period=period)

@pytest.mark.parametrize("threshold,error,message", [("25", TypeError, "ADX threshold must be a number."), (0, ValueError, "ADX threshold must be greater than zero and at most 100."), (101, ValueError, "ADX threshold must be greater than zero and at most 100.")])
def test_adx_strategy_rejects_invalid_threshold(threshold, error, message):
    with pytest.raises(error, match=message):
        ADXStrategy(threshold=threshold)

def test_adx_strategy_declares_required_features():
    assert ADXStrategy(period=10).required_features == [{"name": "ADX", "parameters": {"period": 10}}]

def test_adx_strategy_signals_new_strong_trends_only():
    data = pd.DataFrame({
        "Close": [100, 101, 102, 101, 100, 99],
        "ADX_3": [10, 26, 30, 20, 28, 32],
        "PLUS_DI_3": [20, 30, 35, 22, 15, 12],
        "MINUS_DI_3": [25, 20, 18, 24, 30, 35],
    })
    result = ADXStrategy(period=3, threshold=25).generate_signals(data)
    assert result["Signal"].tolist() == [0, 1, 0, 0, -1, 0]

def test_adx_strategy_rejects_missing_required_columns():
    with pytest.raises(ValueError, match=r"Missing required columns: \['ADX_14', 'PLUS_DI_14', 'MINUS_DI_14'\]"):
        ADXStrategy().generate_signals(pd.DataFrame({"Close": [100]}))
