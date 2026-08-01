import os
import sys

import pandas as pd

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
)

from backtest import BacktestingEngine
from performance_analysis import PerformanceAnalyzer
from strategies.ema_strategy import EMAStrategy
from strategy_engine import StrategyEngine
from strategy_library import StrategyLibrary


def create_market_data():
    close_prices = (
        list(range(100, 121))
        + list(range(120, 89, -1))
        + list(range(90, 121))
    )

    return pd.DataFrame(
        {
            "Open": close_prices,
            "High": [price + 1 for price in close_prices],
            "Low": [price - 1 for price in close_prices],
            "Close": close_prices,
            "Volume": [1000] * len(close_prices),
        }
    )


def execute_pipeline(data, fast_period, slow_period):
    library = StrategyLibrary()

    strategy = EMAStrategy(
        fast_period=fast_period,
        slow_period=slow_period,
    )
    library.register(strategy)

    strategy_engine = StrategyEngine(
        library,
        strategy.name,
    )

    backtesting_engine = BacktestingEngine(
        strategy_engine,
        initial_capital=10000.0,
    )

    result = backtesting_engine.run(data)

    performance_analyzer = PerformanceAnalyzer(
        initial_capital=10000.0,
    )

    metrics = performance_analyzer.calculate(
        backtesting_engine.trade_history,
        backtesting_engine.equity_curve,
    )

    return {
        "result": result,
        "trade_history": backtesting_engine.trade_history,
        "equity_curve": backtesting_engine.equity_curve,
        "metrics": metrics,
    }


def test_parameterized_ema_strategies_execute_complete_pipeline():
    data = create_market_data()

    default_evaluation = execute_pipeline(
        data,
        fast_period=20,
        slow_period=50,
    )

    custom_evaluation = execute_pipeline(
        data,
        fast_period=10,
        slow_period=30,
    )

    default_result = default_evaluation["result"]
    custom_result = custom_evaluation["result"]

    assert "EMA_20" in default_result.columns
    assert "EMA_50" in default_result.columns

    assert "EMA_10" in custom_result.columns
    assert "EMA_30" in custom_result.columns

    assert "EMA_20" not in custom_result.columns
    assert "EMA_50" not in custom_result.columns

    assert "Signal" in default_result.columns
    assert "Signal" in custom_result.columns

    assert set(default_result["Signal"].unique()).issubset(
        {-1, 0, 1}
    )
    assert set(custom_result["Signal"].unique()).issubset(
        {-1, 0, 1}
    )

    assert len(default_evaluation["equity_curve"]) == len(data)
    assert len(custom_evaluation["equity_curve"]) == len(data)

    assert isinstance(default_evaluation["trade_history"], list)
    assert isinstance(custom_evaluation["trade_history"], list)

    assert isinstance(default_evaluation["metrics"], dict)
    assert isinstance(custom_evaluation["metrics"], dict)

    assert "total_return" in default_evaluation["metrics"]
    assert "total_return" in custom_evaluation["metrics"]

    assert "number_of_trades" in default_evaluation["metrics"]
    assert "number_of_trades" in custom_evaluation["metrics"]