import pandas as pd

from backtest import BacktestingEngine
from benchmark import BuyAndHoldBenchmark, compare_strategy_to_benchmark
from performance_analysis import PerformanceAnalyzer


class ChronologicalDataSplitter:
    """Split time-ordered market data into in-sample and out-of-sample sets."""

    def __init__(self, in_sample_fraction=0.70):
        if not isinstance(in_sample_fraction, (int, float)) or isinstance(
            in_sample_fraction, bool
        ):
            raise TypeError("In-sample fraction must be a number.")

        self.in_sample_fraction = float(in_sample_fraction)

        if not 0.0 < self.in_sample_fraction < 1.0:
            raise ValueError("In-sample fraction must be between 0 and 1.")

    @staticmethod
    def _validate_data(data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        if data.empty:
            raise ValueError("Input DataFrame cannot be empty.")

        if len(data) < 2:
            raise ValueError(
                "Out-of-sample validation requires at least two rows."
            )

        if not data.index.is_monotonic_increasing:
            raise ValueError(
                "Input data index must be monotonic increasing for chronological validation."
            )

    def split(self, data):
        """Return independent chronological in-sample and out-of-sample copies."""
        self._validate_data(data)

        split_position = int(len(data) * self.in_sample_fraction)
        split_position = min(max(split_position, 1), len(data) - 1)

        in_sample = data.iloc[:split_position].copy()
        out_of_sample = data.iloc[split_position:].copy()

        return {
            "in_sample": in_sample,
            "out_of_sample": out_of_sample,
            "split_position": split_position,
            "in_sample_rows": len(in_sample),
            "out_of_sample_rows": len(out_of_sample),
            "in_sample_start": in_sample.index[0],
            "in_sample_end": in_sample.index[-1],
            "out_of_sample_start": out_of_sample.index[0],
            "out_of_sample_end": out_of_sample.index[-1],
        }


class OutOfSampleValidator:
    """Run identical strategy and benchmark validation on chronological IS/OOS data."""

    def __init__(
        self,
        strategy_engine,
        in_sample_fraction=0.70,
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0,
        spread_rate=0.0,
        execution_timing=BacktestingEngine.SAME_BAR_CLOSE,
    ):
        self.strategy_engine = strategy_engine
        self.splitter = ChronologicalDataSplitter(in_sample_fraction)
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.spread_rate = spread_rate
        # Reuse existing engines as validation authorities for configuration.
        validated_backtester = BacktestingEngine(
            strategy_engine,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
            spread_rate=spread_rate,
            execution_timing=execution_timing,
        )
        self.execution_timing = validated_backtester.execution_timing

    def _evaluate_partition(self, data):
        backtester = BacktestingEngine(
            self.strategy_engine,
            initial_capital=self.initial_capital,
            commission_rate=self.commission_rate,
            slippage_rate=self.slippage_rate,
            spread_rate=self.spread_rate,
            execution_timing=self.execution_timing,
        )
        backtester.run(data)

        analyzer = PerformanceAnalyzer(backtester.initial_capital)
        metrics = analyzer.calculate(
            backtester.trade_history,
            backtester.equity_curve,
        )

        benchmark = BuyAndHoldBenchmark(
            initial_capital=backtester.initial_capital,
            commission_rate=self.commission_rate,
            slippage_rate=self.slippage_rate,
            spread_rate=self.spread_rate,
            entry_price_column=(
                "Open"
                if self.execution_timing == BacktestingEngine.NEXT_BAR_OPEN
                else "Close"
            ),
        ).run(data)

        comparison = compare_strategy_to_benchmark(
            backtester.capital,
            benchmark,
        )

        return {
            "initial_capital": backtester.initial_capital,
            "execution_timing": backtester.execution_timing,
            "final_capital": backtester.capital,
            "trade_history": list(backtester.trade_history),
            "equity_curve": list(backtester.equity_curve),
            "performance": metrics,
            "benchmark": benchmark,
            "comparison": comparison,
        }

    def run(self, data):
        """Evaluate the same strategy independently on IS and unseen OOS data."""
        split = self.splitter.split(data)

        in_sample_result = self._evaluate_partition(split["in_sample"])
        out_of_sample_result = self._evaluate_partition(
            split["out_of_sample"]
        )

        return {
            "split": {
                key: value
                for key, value in split.items()
                if key not in {"in_sample", "out_of_sample"}
            },
            "in_sample": in_sample_result,
            "out_of_sample": out_of_sample_result,
            "generalization": {
                "in_sample_strategy_return": in_sample_result["comparison"][
                    "strategy_return"
                ],
                "out_of_sample_strategy_return": out_of_sample_result[
                    "comparison"
                ]["strategy_return"],
                "in_sample_excess_return": in_sample_result["comparison"][
                    "excess_return"
                ],
                "out_of_sample_excess_return": out_of_sample_result[
                    "comparison"
                ]["excess_return"],
            },
        }
