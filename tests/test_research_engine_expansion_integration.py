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
from strategies.rsi_strategy import RSIStrategy
from strategy_engine import StrategyEngine
from strategy_library import StrategyLibrary
from strategies.macd_strategy import MACDStrategy


def create_market_data():
    close_prices = (
        list(range(100, 111))
        + list(range(110, 89, -1))
        + list(range(90, 111))
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


def test_rsi_strategy_executes_complete_research_pipeline():
    data = create_market_data()

    library = StrategyLibrary()

    strategy = RSIStrategy(
        period=14,
        oversold=30,
        overbought=70,
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

    assert "RSI_14" in result.columns
    assert "Signal" in result.columns

    assert "EMA_20" not in result.columns
    assert "EMA_50" not in result.columns

    assert set(result["Signal"].unique()).issubset(
        {-1, 0, 1}
    )

    assert len(backtesting_engine.equity_curve) == len(data)
    assert isinstance(
        backtesting_engine.trade_history,
        list,
    )

    assert isinstance(metrics, dict)
    assert "total_return" in metrics
    assert "number_of_trades" in metrics
    assert "max_drawdown" in metrics
    assert "sharpe_ratio" in metrics


def test_macd_strategy_executes_complete_research_pipeline():
    data = create_market_data()

    library = StrategyLibrary()

    strategy = MACDStrategy(
        fast_period=12,
        slow_period=26,
        signal_period=9,
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

    assert "MACD_12_26" in result.columns
    assert "MACD_SIGNAL_12_26_9" in result.columns
    assert "MACD_HISTOGRAM_12_26_9" in result.columns
    assert "Signal" in result.columns

    assert "EMA_20" not in result.columns
    assert "EMA_50" not in result.columns
    assert "RSI_14" not in result.columns

    assert set(result["Signal"].unique()).issubset(
        {-1, 0, 1}
    )

    assert len(backtesting_engine.equity_curve) == len(data)
    assert isinstance(
        backtesting_engine.trade_history,
        list,
    )

    assert isinstance(metrics, dict)
    assert "total_return" in metrics
    assert "number_of_trades" in metrics
    assert "max_drawdown" in metrics
    assert "sharpe_ratio" in metrics