import os
import sys
import pandas as pd
import pytest

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from backtest import BacktestingEngine


class DummyStrategyEngine:
    def run(self, data):
        result = data.copy()
        result["Signal"] = 0
        return result


def test_backtesting_engine_runs_strategy():
    data = pd.DataFrame({
        "Close": [100, 101, 102],
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Volume": [1000, 1000, 1000],
    })

    engine = BacktestingEngine(DummyStrategyEngine())

    result = engine.run(data)

    assert isinstance(result, pd.DataFrame)
    assert "Signal" in result.columns

def test_backtesting_engine_rejects_non_dataframe_input():
    engine = BacktestingEngine(DummyStrategyEngine())

    with pytest.raises(
        TypeError,
        match="Input data must be a pandas DataFrame.",
    ):
        engine.run([100, 101, 102])

def test_backtesting_engine_rejects_empty_dataframe():
    engine = BacktestingEngine(DummyStrategyEngine())

    empty_data = pd.DataFrame()

    with pytest.raises(
        ValueError,
        match="Input DataFrame cannot be empty.",
    ):
        engine.run(empty_data)

def test_backtesting_engine_initial_state():
    engine = BacktestingEngine(DummyStrategyEngine())

    assert engine.initial_capital == 10000.0
    assert engine.capital == 10000.0
    assert engine.shares == 0.0
    assert engine.position == 0
    assert engine.entry_price == 0.0

def test_buy_opens_position():
    engine = BacktestingEngine(DummyStrategyEngine())

    engine._buy(100.0, 0)

    assert engine.capital == 0.0
    assert engine.position == 1
    assert engine.entry_price == 100.0
    assert engine.shares == 100.0

def test_sell_closes_position():
    engine = BacktestingEngine(DummyStrategyEngine())

    engine._buy(100.0, 0)
    engine._sell(110.0, 1)

    assert engine.capital == 11000.0
    assert engine.shares == 0.0
    assert engine.position == 0
    assert engine.entry_price == 0.0
    assert engine.entry_index is None

def test_run_processes_buy_and_sell_signals():
    class SignalStrategyEngine:
        def run(self, data):
            result = data.copy()
            result["Signal"] = [1, 0, -1]
            return result

    data = pd.DataFrame({
        "Close": [100, 105, 110],
        "Open": [100, 105, 110],
        "High": [100, 105, 110],
        "Low": [100, 105, 110],
        "Volume": [1000, 1000, 1000],
    })

    engine = BacktestingEngine(SignalStrategyEngine())

    engine.run(data)

    assert engine.position == 0
    assert engine.shares == 0.0
    assert engine.capital == 11000.0

def test_run_records_equity_after_each_candle():
    class SignalStrategyEngine:
        def run(self, data):
            result = data.copy()
            result["Signal"] = [1, 0, -1]
            return result

    data = pd.DataFrame({
        "Close": [100, 105, 110],
        "Open": [100, 105, 110],
        "High": [100, 105, 110],
        "Low": [100, 105, 110],
        "Volume": [1000, 1000, 1000],
    })

    engine = BacktestingEngine(SignalStrategyEngine())

    engine.run(data)

    assert len(engine.equity_curve) == 3
    assert engine.equity_curve[0]["equity"] == 10000.0
    assert engine.equity_curve[1]["equity"] == 10500.0
    assert engine.equity_curve[2]["equity"] == 11000.0

    assert engine.equity_curve[0]["index"] == 0
    assert engine.equity_curve[1]["index"] == 1
    assert engine.equity_curve[2]["index"] == 2

def test_equity_curve_tracks_unrealized_loss():
    class SignalStrategyEngine:
        def run(self, data):
            result = data.copy()
            result["Signal"] = [1, 0, 0, 0]
            return result

    data = pd.DataFrame({
        "Close": [100, 95, 90, 85],
        "Open": [100, 95, 90, 85],
        "High": [100, 95, 90, 85],
        "Low": [100, 95, 90, 85],
        "Volume": [1000, 1000, 1000, 1000],
    })

    engine = BacktestingEngine(SignalStrategyEngine())

    engine.run(data)

    assert len(engine.equity_curve) == 4
    assert engine.equity_curve[0]["equity"] == 10000.0
    assert engine.equity_curve[1]["equity"] == 9500.0
    assert engine.equity_curve[2]["equity"] == 9000.0
    assert engine.equity_curve[3]["equity"] == 8500.0

def test_trade_history_is_empty_on_initialization():
    engine = BacktestingEngine(DummyStrategyEngine())

    assert engine.trade_history == []

def test_equity_curve_is_empty_on_initialization():
    engine = BacktestingEngine(DummyStrategyEngine())

    assert engine.equity_curve == []

def test_calculate_equity_without_open_position():
    engine = BacktestingEngine(DummyStrategyEngine())

    equity = engine._calculate_equity(100.0)

    assert equity == 10000.0

def test_calculate_equity_with_open_position():
    engine = BacktestingEngine(DummyStrategyEngine())

    engine._buy(100.0, 0)

    equity = engine._calculate_equity(110.0)

    assert equity == 11000.0

def test_record_equity():
    engine = BacktestingEngine(DummyStrategyEngine())

    engine._record_equity(100.0, 0)

    assert len(engine.equity_curve) == 1

    record = engine.equity_curve[0]

    assert record["index"] == 0
    assert record["equity"] == 10000.0

def test_sell_records_trade_history():
    engine = BacktestingEngine(DummyStrategyEngine())

    engine._buy(100.0, 0)
    engine._sell(110.0, 1)

    assert len(engine.trade_history) == 1

    trade = engine.trade_history[0]

    assert trade["entry_price"] == 100.0
    assert trade["exit_price"] == 110.0
    assert trade["profit_loss"] == 1000.0
    assert trade["entry_index"] == 0
    assert trade["exit_index"] == 1

def test_close_open_position_at_end_of_backtest():
    class SignalStrategyEngine:
        def run(self, data):
            result = data.copy()
            result["Signal"] = [1, 0, 0]
            return result

    data = pd.DataFrame({
        "Close": [100, 105, 110],
        "Open": [100, 105, 110],
        "High": [100, 105, 110],
        "Low": [100, 105, 110],
        "Volume": [1000, 1000, 1000],
    })

    engine = BacktestingEngine(SignalStrategyEngine())

    engine.run(data)

    assert engine.position == 0
    assert engine.shares == 0.0
    assert engine.capital == 11000.0
    assert engine.entry_price == 0.0
    assert engine.entry_index is None

def test_close_open_position_records_final_trade():
    class SignalStrategyEngine:
        def run(self, data):
            result = data.copy()
            result["Signal"] = [1, 0, 0]
            return result

    data = pd.DataFrame({
        "Close": [100, 105, 110],
        "Open": [100, 105, 110],
        "High": [100, 105, 110],
        "Low": [100, 105, 110],
        "Volume": [1000, 1000, 1000],
    })

    engine = BacktestingEngine(SignalStrategyEngine())

    engine.run(data)

    assert len(engine.trade_history) == 1

    trade = engine.trade_history[0]

    assert trade["entry_index"] == 0
    assert trade["exit_index"] == 2
    assert trade["entry_price"] == 100.0
    assert trade["exit_price"] == 110.0
    assert trade["profit_loss"] == 1000.0

def test_end_of_backtest_does_not_create_duplicate_trade():
    class SignalStrategyEngine:
        def run(self, data):
            result = data.copy()
            result["Signal"] = [1, 0, -1]
            return result

    data = pd.DataFrame({
        "Close": [100, 105, 110],
        "Open": [100, 105, 110],
        "High": [100, 105, 110],
        "Low": [100, 105, 110],
        "Volume": [1000, 1000, 1000],
    })

    engine = BacktestingEngine(SignalStrategyEngine())

    engine.run(data)

    assert len(engine.trade_history) == 1

