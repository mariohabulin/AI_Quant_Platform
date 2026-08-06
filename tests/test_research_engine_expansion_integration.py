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
from strategies.bollinger_strategy import BollingerStrategy
from strategies.donchian_strategy import DonchianStrategy
from strategies.supertrend_strategy import SupertrendStrategy
from strategies.adx_strategy import ADXStrategy
from strategies.stochastic_strategy import StochasticStrategy


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


def test_bollinger_strategy_executes_complete_research_pipeline():
    data = create_market_data()

    library = StrategyLibrary()

    strategy = BollingerStrategy(
        period=20,
        standard_deviations=2.0,
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

    assert "BOLLINGER_MIDDLE_20" in result.columns
    assert "BOLLINGER_UPPER_20_2.0" in result.columns
    assert "BOLLINGER_LOWER_20_2.0" in result.columns
    assert "Signal" in result.columns

    assert "EMA_20" not in result.columns
    assert "EMA_50" not in result.columns
    assert "RSI_14" not in result.columns
    assert "MACD_12_26" not in result.columns

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


def test_donchian_strategy_executes_complete_research_pipeline():
    data = create_market_data()

    library = StrategyLibrary()

    strategy = DonchianStrategy(
        period=20,
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

    assert "DONCHIAN_UPPER_20" in result.columns
    assert "DONCHIAN_LOWER_20" in result.columns
    assert "DONCHIAN_MIDDLE_20" in result.columns
    assert "Signal" in result.columns

    assert "EMA_20" not in result.columns
    assert "EMA_50" not in result.columns
    assert "RSI_14" not in result.columns
    assert "MACD_12_26" not in result.columns
    assert "BOLLINGER_MIDDLE_20" not in result.columns

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

def test_atr_strategy_executes_complete_research_pipeline():
    from strategies.atr_strategy import ATRStrategy

    data = create_market_data()
    library = StrategyLibrary()
    strategy = ATRStrategy(period=14, multiplier=1.0)
    library.register(strategy)

    strategy_engine = StrategyEngine(library, strategy.name)
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

    assert "ATR_14" in result.columns
    assert "Signal" in result.columns
    assert "EMA_20" not in result.columns
    assert "RSI_14" not in result.columns
    assert "MACD_12_26" not in result.columns
    assert "BOLLINGER_MIDDLE_20" not in result.columns
    assert "DONCHIAN_UPPER_20" not in result.columns
    assert set(result["Signal"].unique()).issubset({-1, 0, 1})
    assert len(backtesting_engine.equity_curve) == len(data)
    assert isinstance(backtesting_engine.trade_history, list)
    assert isinstance(metrics, dict)
    assert "total_return" in metrics
    assert "number_of_trades" in metrics
    assert "max_drawdown" in metrics
    assert "sharpe_ratio" in metrics


def test_supertrend_strategy_executes_complete_research_pipeline():
    data = create_market_data()
    library = StrategyLibrary()
    strategy = SupertrendStrategy(period=10, multiplier=3.0)
    library.register(strategy)

    strategy_engine = StrategyEngine(library, strategy.name)
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

    assert "ATR_10" in result.columns
    assert "SUPERTREND_10_3.0" in result.columns
    assert "SUPERTREND_DIRECTION_10_3.0" in result.columns
    assert "Signal" in result.columns
    assert "EMA_20" not in result.columns
    assert "RSI_14" not in result.columns
    assert "MACD_12_26" not in result.columns
    assert "BOLLINGER_MIDDLE_20" not in result.columns
    assert "DONCHIAN_UPPER_20" not in result.columns
    assert set(result["Signal"].unique()).issubset({-1, 0, 1})
    assert len(backtesting_engine.equity_curve) == len(data)
    assert isinstance(backtesting_engine.trade_history, list)
    assert isinstance(metrics, dict)
    assert "total_return" in metrics
    assert "number_of_trades" in metrics
    assert "max_drawdown" in metrics
    assert "sharpe_ratio" in metrics


def test_adx_strategy_executes_complete_research_pipeline():
    data = create_market_data()
    library = StrategyLibrary()
    strategy = ADXStrategy(period=14, threshold=25.0)
    library.register(strategy)
    strategy_engine = StrategyEngine(library, strategy.name)
    backtesting_engine = BacktestingEngine(strategy_engine, initial_capital=10000.0)
    result = backtesting_engine.run(data)
    performance_analyzer = PerformanceAnalyzer(initial_capital=10000.0)
    metrics = performance_analyzer.calculate(backtesting_engine.trade_history, backtesting_engine.equity_curve)
    assert "ADX_14" in result.columns
    assert "PLUS_DI_14" in result.columns
    assert "MINUS_DI_14" in result.columns
    assert "Signal" in result.columns
    assert "EMA_20" not in result.columns
    assert set(result["Signal"].unique()).issubset({-1, 0, 1})
    assert len(backtesting_engine.equity_curve) == len(data)
    assert isinstance(metrics, dict)
    assert "total_return" in metrics


def test_stochastic_strategy_executes_complete_research_pipeline():
    data = create_market_data()
    library = StrategyLibrary()
    strategy = StochasticStrategy(
        k_period=14,
        d_period=3,
        oversold=20.0,
        overbought=80.0,
    )
    library.register(strategy)
    strategy_engine = StrategyEngine(library, strategy.name)
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

    assert "STOCHASTIC_K_14" in result.columns
    assert "STOCHASTIC_D_14_3" in result.columns
    assert "Signal" in result.columns
    assert "EMA_20" not in result.columns
    assert set(result["Signal"].unique()).issubset({-1, 0, 1})
    assert len(backtesting_engine.equity_curve) == len(data)
    assert isinstance(metrics, dict)
    assert "total_return" in metrics
