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


def test_drawdown_guard_latches_kill_switch():
    engine = RiskEngine(max_drawdown_fraction=0.10)
    assert engine.observe_equity(10000, "2026-01-05").status == "ALLOW"
    decision = engine.observe_equity(9000, "2026-01-06")
    assert decision.status == "REJECT"
    assert decision.kill_switch_active is True
    assert decision.drawdown == pytest.approx(0.10)
    assert engine.observe_equity(9500, "2026-01-07").status == "REJECT"


def test_new_equity_high_updates_drawdown_peak():
    engine = RiskEngine(max_drawdown_fraction=0.10)
    engine.observe_equity(10000, "2026-01-05")
    engine.observe_equity(12000, "2026-01-06")
    decision = engine.observe_equity(11000, "2026-01-07")
    assert decision.status == "ALLOW"
    assert decision.drawdown == pytest.approx(1 / 12)


def test_daily_loss_guard_resets_on_new_day():
    engine = RiskEngine(daily_loss_limit=0.02)
    engine.observe_equity(10000, "2026-01-05 09:00")
    assert engine.observe_equity(9800, "2026-01-05 15:00").status == "REJECT"
    assert engine.observe_equity(9800, "2026-01-06 09:00").status == "ALLOW"


def test_weekly_loss_guard_resets_on_new_iso_week():
    engine = RiskEngine(weekly_loss_limit=0.05)
    engine.observe_equity(10000, "2026-01-05")
    assert engine.observe_equity(9500, "2026-01-09").status == "REJECT"
    assert engine.observe_equity(9500, "2026-01-12").status == "ALLOW"


def test_invalid_protection_limits_are_rejected():
    with pytest.raises(ValueError):
        RiskEngine(max_drawdown_fraction=0)
    with pytest.raises(ValueError):
        RiskEngine(daily_loss_limit=1.1)
    with pytest.raises(TypeError):
        RiskEngine(weekly_loss_limit=True)


def test_protection_guards_require_datetime_index_when_enabled():
    with pytest.raises(TypeError, match="datetime-like"):
        RiskEngine(max_drawdown_fraction=0.1).observe_equity(10000, object())


def test_disabled_protection_does_not_require_datetime_index():
    decision = RiskEngine().observe_equity(10000, object())
    assert decision.status == "ALLOW"


class TwoTradeSignalEngine:
    def run(self, data):
        result = data.copy()
        result["Signal"] = [1, -1, 1, -1]
        return result


def test_backtester_blocks_new_trade_after_drawdown_kill_switch():
    data = pd.DataFrame({
        "Open": [100, 90, 90, 95], "High": [101, 91, 91, 96],
        "Low": [99, 89, 89, 94], "Close": [100, 90, 90, 95],
        "Volume": [1000] * 4, "Stop": [98, 88, 88, 93],
    }, index=pd.to_datetime(["2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08"]))
    risk = RiskEngine(risk_per_trade=0.10, max_drawdown_fraction=0.05)
    engine = BacktestingEngine(TwoTradeSignalEngine(), risk_engine=risk)
    engine.run(data)
    assert len(engine.trade_history) == 1
    assert risk.kill_switch_active is True


def test_protection_state_resets_between_backtest_runs():
    risk = RiskEngine(max_drawdown_fraction=0.05)
    risk.observe_equity(10000, "2026-01-05")
    risk.observe_equity(9000, "2026-01-06")
    assert risk.kill_switch_active is True
    data = pd.DataFrame({
        "Open": [100, 105, 110], "High": [101, 106, 111],
        "Low": [99, 104, 109], "Close": [100, 105, 110],
        "Volume": [1000] * 3, "Stop": [98, 98, 98],
    }, index=pd.to_datetime(["2026-02-02", "2026-02-03", "2026-02-04"]))
    engine = BacktestingEngine(SignalEngine(), risk_engine=risk)
    engine.run(data)
    assert risk.kill_switch_active is False
    assert len(engine.trade_history) == 1
