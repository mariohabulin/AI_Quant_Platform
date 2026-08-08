import os
import sys
import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from backtest import BacktestingEngine
from risk_engine import RiskEngine


class SignalEngine:
    def run(self, data):
        result = data.copy()
        result["Signal"] = [1, 0, -1]
        return result


def test_risk_engine_defaults_to_one_percent_risk():
    engine = RiskEngine()
    assert engine.risk_per_trade == 0.01
    assert engine.max_position_fraction == 1.0


def test_position_size_is_derived_from_risk_budget_and_stop_distance():
    decision = RiskEngine(risk_per_trade=0.01).assess_long(10000, 100, 98)
    assert decision.status == "ALLOW"
    assert decision.risk_budget == 100
    assert decision.position_size == 50
    assert decision.monetary_risk == 100


def test_exposure_cap_reduces_position():
    decision = RiskEngine(0.02, 0.25).assess_long(10000, 100, 99)
    assert decision.status == "REDUCE"
    assert decision.position_size == 25
    assert decision.position_notional == 2500
    assert decision.monetary_risk == 25


def test_invalid_long_stop_is_rejected_not_sized():
    decision = RiskEngine().assess_long(10000, 100, 100)
    assert decision.status == "REJECT"
    assert decision.position_size == 0


@pytest.mark.parametrize("value", [0, -0.01, 1.01])
def test_invalid_risk_per_trade_is_rejected(value):
    with pytest.raises(ValueError):
        RiskEngine(risk_per_trade=value)


def test_boolean_risk_is_rejected():
    with pytest.raises(TypeError):
        RiskEngine(risk_per_trade=True)


def test_non_positive_equity_is_rejected():
    with pytest.raises(ValueError):
        RiskEngine().assess_long(0, 100, 95)


def test_risk_managed_backtest_uses_partial_position():
    data = pd.DataFrame({
        "Open": [100, 105, 110], "High": [101, 106, 111],
        "Low": [99, 104, 109], "Close": [100, 105, 110],
        "Volume": [1000, 1000, 1000], "Stop": [98, 98, 98],
    })
    engine = BacktestingEngine(SignalEngine(), risk_engine=RiskEngine(0.01))
    engine.run(data)
    trade = engine.trade_history[0]
    assert trade["shares"] == 50
    assert trade["risk_status"] == "ALLOW"
    assert trade["planned_monetary_risk"] == 100
    assert engine.capital == 10500


def test_risk_managed_backtest_requires_stop_column():
    data = pd.DataFrame({
        "Open": [100, 105, 110], "High": [101, 106, 111],
        "Low": [99, 104, 109], "Close": [100, 105, 110],
        "Volume": [1000, 1000, 1000],
    })
    engine = BacktestingEngine(SignalEngine(), risk_engine=RiskEngine())
    with pytest.raises(ValueError, match="requires 'Stop' column"):
        engine.run(data)


def test_rejected_risk_decision_does_not_open_position():
    data = pd.DataFrame({
        "Open": [100, 105, 110], "High": [101, 106, 111],
        "Low": [99, 104, 109], "Close": [100, 105, 110],
        "Volume": [1000, 1000, 1000], "Stop": [100, 100, 100],
    })
    engine = BacktestingEngine(SignalEngine(), risk_engine=RiskEngine())
    engine.run(data)
    assert engine.trade_history == []
    assert engine.capital == 10000


def test_existing_backtester_remains_all_in_without_risk_engine():
    data = pd.DataFrame({
        "Open": [100, 105, 110], "High": [101, 106, 111],
        "Low": [99, 104, 109], "Close": [100, 105, 110],
        "Volume": [1000, 1000, 1000],
    })
    engine = BacktestingEngine(SignalEngine())
    engine.run(data)
    assert engine.capital == 11000
    assert engine.trade_history[0]["shares"] == 100
    assert engine.trade_history[0]["risk_status"] is None
