import pandas as pd
import pytest

from src.backtest import BacktestingEngine
from src.paper_broker import PaperBroker
from src.paper_trading import PaperTradingEngine, PaperTradingSession
from src.replay_consistency import ReplayConsistencyValidator
from src.risk_engine import RiskEngine


class LengthSignalStrategy:
    def __init__(self, signals):
        self.signals = tuple(signals)

    def run(self, data):
        result = data.copy()
        result["Signal"] = list(self.signals[:len(result)])
        result["Stop"] = result["Close"] - 2.0
        return result


def data():
    index = pd.date_range("2026-08-01", periods=4, freq="h")
    close = [100.0, 105.0, 110.0, 108.0]
    return pd.DataFrame({
        "Open": close, "High": close, "Low": close, "Close": close,
        "Volume": [1000.0] * 4,
    }, index=index)


def make_validator(signals=(1, 0, -1, 0), commission=0.0, slippage=0.0, spread=0.0):
    risk_backtest = RiskEngine(risk_per_trade=0.01, max_position_fraction=1.0)
    risk_paper = RiskEngine(risk_per_trade=0.01, max_position_fraction=1.0)
    backtest = BacktestingEngine(
        LengthSignalStrategy(signals), risk_engine=risk_backtest,
        commission_rate=commission, slippage_rate=slippage, spread_rate=spread,
    )
    broker = PaperBroker(
        initial_cash=10000.0, commission_rate=commission,
        slippage_rate=slippage, spread_rate=spread,
    )
    paper = PaperTradingEngine(LengthSignalStrategy(signals), risk_paper, broker)
    return ReplayConsistencyValidator(backtest, PaperTradingSession(paper))


def stop(event):
    return float(event.bar["Close"]) - 2.0


def test_requires_backtest_engine():
    session = make_validator().paper_session
    with pytest.raises(ValueError, match="backtest_engine is required"):
        ReplayConsistencyValidator(None, session)


def test_requires_paper_session():
    with pytest.raises(TypeError, match="PaperTradingSession"):
        ReplayConsistencyValidator(object(), object())


def test_rejects_invalid_tolerance():
    validator = make_validator()
    with pytest.raises(TypeError, match="tolerance"):
        ReplayConsistencyValidator(validator.backtest_engine, validator.paper_session, "x")
    with pytest.raises(ValueError, match="cannot be negative"):
        ReplayConsistencyValidator(validator.backtest_engine, validator.paper_session, -1)


def test_rejects_non_dataframe_and_empty_data():
    validator = make_validator()
    with pytest.raises(TypeError, match="pandas DataFrame"):
        validator.run([])
    with pytest.raises(ValueError, match="cannot be empty"):
        validator.run(pd.DataFrame())


def test_equal_zero_cost_paths_are_consistent():
    report = make_validator().run(data(), stop_resolver=stop)
    assert report.status == "CONSISTENT"
    assert report.is_consistent is True
    assert report.differences == ()


def test_signal_sequence_is_compared_bar_by_bar():
    report = make_validator().run(data(), stop_resolver=stop)
    assert report.backtest_signals == (1, 0, -1, 0)
    assert report.replay_signals == (1, 0, -1, 0)


def test_completed_trade_count_is_reported():
    report = make_validator().run(data(), stop_resolver=stop)
    assert report.backtest_trade_count == 1
    assert report.replay_trade_count == 1


def test_execution_cost_paths_are_consistent_when_assumptions_match():
    report = make_validator(commission=0.001, slippage=0.002, spread=0.004).run(
        data(), stop_resolver=stop
    )
    assert report.is_consistent


def test_final_equity_is_compared():
    report = make_validator().run(data(), stop_resolver=stop)
    assert report.backtest_final_equity == pytest.approx(10500.0)
    assert report.replay_final_equity == pytest.approx(10500.0)


def test_detects_execution_assumption_drift_with_diagnostic_field():
    validator = make_validator()
    validator.paper_session.engine.paper_broker.slippage_rate = 0.01
    report = validator.run(data(), stop_resolver=stop)
    assert report.status == "DIVERGENT"
    fields = {difference.field for difference in report.differences}
    assert "trade_1.entry_fill_price" in fields
    assert "final_equity" in fields


def test_open_final_position_exposes_forced_close_semantic_difference():
    report = make_validator(signals=(1, 0, 0, 0)).run(data(), stop_resolver=stop)
    assert report.status == "DIVERGENT"
    fields = {difference.field for difference in report.differences}
    assert "trade_count" in fields
    assert "open_position_state" in fields


def test_validator_requires_fresh_paper_session():
    validator = make_validator()
    validator.paper_session.process(data().iloc[:1], stop_price=98.0)
    with pytest.raises(ValueError, match="must be fresh"):
        validator.run(data(), stop_resolver=stop)
