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

def test_repeated_runs_reset_backtesting_state():
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

    first_capital = engine.capital
    first_trade_history = engine.trade_history.copy()
    first_equity_curve = engine.equity_curve.copy()

    engine.run(data)

    assert engine.capital == first_capital
    assert engine.trade_history == first_trade_history
    assert engine.equity_curve == first_equity_curve



def test_backtesting_engine_accepts_execution_cost_configuration():
    engine = BacktestingEngine(
        DummyStrategyEngine(),
        commission_rate=0.001,
        slippage_rate=0.002,
        spread_rate=0.004,
    )

    assert engine.commission_rate == 0.001
    assert engine.slippage_rate == 0.002
    assert engine.spread_rate == 0.004


@pytest.mark.parametrize(
    "parameter_name",
    ["commission_rate", "slippage_rate", "spread_rate"],
)
def test_backtesting_engine_rejects_negative_execution_cost_rates(parameter_name):
    kwargs = {parameter_name: -0.001}

    with pytest.raises(ValueError, match="cannot be negative"):
        BacktestingEngine(DummyStrategyEngine(), **kwargs)


@pytest.mark.parametrize(
    "parameter_name",
    ["commission_rate", "slippage_rate", "spread_rate"],
)
def test_backtesting_engine_rejects_execution_cost_rates_at_or_above_one(parameter_name):
    kwargs = {parameter_name: 1.0}

    with pytest.raises(ValueError, match="must be less than 1.0"):
        BacktestingEngine(DummyStrategyEngine(), **kwargs)


def test_execution_price_applies_slippage_and_half_spread_by_side():
    engine = BacktestingEngine(
        DummyStrategyEngine(),
        slippage_rate=0.01,
        spread_rate=0.02,
    )

    assert engine._calculate_execution_price(100.0, "buy") == pytest.approx(102.0)
    assert engine._calculate_execution_price(100.0, "sell") == pytest.approx(98.0)


def test_buy_reserves_commission_without_negative_capital():
    engine = BacktestingEngine(
        DummyStrategyEngine(),
        initial_capital=10000.0,
        commission_rate=0.01,
    )

    engine._buy(100.0, 0)

    assert engine.capital == pytest.approx(0.0)
    assert engine.shares == pytest.approx(10000.0 / 101.0)
    assert engine.entry_commission == pytest.approx(
        engine.shares * 100.0 * 0.01
    )


def test_trade_history_records_realistic_execution_cost_breakdown():
    engine = BacktestingEngine(
        DummyStrategyEngine(),
        initial_capital=10000.0,
        commission_rate=0.001,
        slippage_rate=0.002,
        spread_rate=0.004,
    )

    engine._buy(100.0, 0)
    engine._sell(110.0, 1)

    trade = engine.trade_history[0]

    assert trade["entry_market_price"] == 100.0
    assert trade["exit_market_price"] == 110.0
    assert trade["entry_price"] == pytest.approx(100.4)
    assert trade["exit_price"] == pytest.approx(109.56)
    assert trade["total_commission"] > 0.0
    assert trade["execution_cost"] > 0.0
    assert trade["total_costs"] == pytest.approx(
        trade["total_commission"] + trade["execution_cost"]
    )
    assert trade["profit_loss"] == pytest.approx(
        trade["gross_profit_loss"] - trade["total_costs"]
    )


def test_realistic_execution_costs_reduce_final_capital():
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

    zero_cost_engine = BacktestingEngine(SignalStrategyEngine())
    realistic_engine = BacktestingEngine(
        SignalStrategyEngine(),
        commission_rate=0.001,
        slippage_rate=0.001,
        spread_rate=0.002,
    )

    zero_cost_engine.run(data)
    realistic_engine.run(data)

    assert realistic_engine.capital < zero_cost_engine.capital
    assert realistic_engine.trade_history[0]["total_costs"] > 0.0


def test_zero_cost_configuration_preserves_legacy_trade_results():
    engine = BacktestingEngine(DummyStrategyEngine())

    engine._buy(100.0, 0)
    engine._sell(110.0, 1)

    trade = engine.trade_history[0]

    assert engine.capital == pytest.approx(11000.0)
    assert trade["entry_price"] == 100.0
    assert trade["exit_price"] == 110.0
    assert trade["gross_profit_loss"] == pytest.approx(1000.0)
    assert trade["total_costs"] == pytest.approx(0.0)
    assert trade["profit_loss"] == pytest.approx(1000.0)


def test_default_execution_timing_preserves_same_bar_close_semantics():
    class SignalStrategyEngine:
        def run(self, data):
            result = data.copy()
            result["Signal"] = [1, 0, -1, 0]
            return result

    data = pd.DataFrame(
        {
            "Open": [100.0, 110.0, 80.0, 90.0],
            "High": [106.0, 116.0, 86.0, 96.0],
            "Low": [99.0, 109.0, 79.0, 89.0],
            "Close": [105.0, 115.0, 85.0, 95.0],
            "Volume": [1000.0] * 4,
        }
    )

    engine = BacktestingEngine(SignalStrategyEngine())
    engine.run(data)

    trade = engine.trade_history[0]
    assert trade["execution_timing"] == "same_bar_close"
    assert trade["entry_index"] == trade["entry_signal_index"] == 0
    assert trade["exit_index"] == trade["exit_signal_index"] == 2
    assert trade["entry_market_price"] == 105.0
    assert trade["exit_market_price"] == 85.0


def test_next_bar_open_executes_only_after_the_signal_bar_closes():
    class SignalStrategyEngine:
        def run(self, data):
            result = data.copy()
            result["Signal"] = [1, 0, -1, 0]
            return result

    data = pd.DataFrame(
        {
            "Open": [100.0, 110.0, 80.0, 90.0],
            "High": [106.0, 116.0, 86.0, 96.0],
            "Low": [99.0, 109.0, 79.0, 89.0],
            "Close": [105.0, 115.0, 85.0, 95.0],
            "Volume": [1000.0] * 4,
        }
    )

    engine = BacktestingEngine(
        SignalStrategyEngine(),
        execution_timing=BacktestingEngine.NEXT_BAR_OPEN,
    )
    engine.run(data)

    trade = engine.trade_history[0]
    assert trade["execution_timing"] == "next_bar_open"
    assert trade["entry_signal_index"] == 0
    assert trade["entry_index"] == 1
    assert trade["entry_market_price"] == 110.0
    assert trade["exit_signal_index"] == 2
    assert trade["exit_index"] == 3
    assert trade["exit_market_price"] == 90.0
    assert engine.capital == pytest.approx(10000.0 * 90.0 / 110.0)


def test_next_bar_open_never_executes_a_signal_from_the_final_bar():
    class FinalBarSignalEngine:
        def run(self, data):
            result = data.copy()
            result["Signal"] = [0, 1]
            return result

    data = pd.DataFrame(
        {
            "Open": [100.0, 110.0],
            "Close": [105.0, 115.0],
        }
    )
    engine = BacktestingEngine(
        FinalBarSignalEngine(),
        execution_timing=BacktestingEngine.NEXT_BAR_OPEN,
    )

    engine.run(data)

    assert engine.trade_history == []
    assert engine.position == 0
    assert engine.capital == 10000.0


def test_next_bar_open_forced_close_records_no_synthetic_exit_signal():
    class OpenPositionEngine:
        def run(self, data):
            result = data.copy()
            result["Signal"] = [1, 0, 0]
            return result

    data = pd.DataFrame(
        {
            "Open": [100.0, 110.0, 120.0],
            "Close": [105.0, 115.0, 125.0],
        }
    )
    engine = BacktestingEngine(
        OpenPositionEngine(),
        execution_timing=BacktestingEngine.NEXT_BAR_OPEN,
    )

    engine.run(data)

    trade = engine.trade_history[0]
    assert trade["entry_signal_index"] == 0
    assert trade["entry_index"] == 1
    assert trade["exit_signal_index"] is None
    assert trade["exit_index"] == 2
    assert trade["exit_market_price"] == 125.0


@pytest.mark.parametrize(
    "execution_timing, error",
    [(42, TypeError), ("future_close", ValueError)],
)
def test_backtesting_engine_rejects_invalid_execution_timing(
    execution_timing,
    error,
):
    with pytest.raises(error, match="Execution timing"):
        BacktestingEngine(
            DummyStrategyEngine(),
            execution_timing=execution_timing,
        )


@pytest.mark.parametrize(
    "data",
    [
        pd.DataFrame({"Close": [100.0, 101.0]}),
        pd.DataFrame({"Open": [100.0, 0.0], "Close": [100.0, 101.0]}),
        pd.DataFrame({"Open": [100.0, "bad"], "Close": [100.0, 101.0]}),
    ],
)
def test_next_bar_open_requires_positive_numeric_open_prices(data):
    engine = BacktestingEngine(
        DummyStrategyEngine(),
        execution_timing=BacktestingEngine.NEXT_BAR_OPEN,
    )

    with pytest.raises(ValueError, match="Open"):
        engine.run(data)
