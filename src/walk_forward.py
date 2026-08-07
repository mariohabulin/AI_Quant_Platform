import pandas as pd

from out_of_sample import OutOfSampleValidator


class WalkForwardSplitter:
    """Create deterministic chronological train/test windows without leakage."""

    def __init__(self, train_size, test_size, step_size=None, expanding=True):
        for value, name in ((train_size, "Train size"), (test_size, "Test size")):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{name} must be an integer.")
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")
        if step_size is None:
            step_size = test_size
        if not isinstance(step_size, int) or isinstance(step_size, bool):
            raise TypeError("Step size must be an integer.")
        if step_size <= 0:
            raise ValueError("Step size must be greater than zero.")
        if not isinstance(expanding, bool):
            raise TypeError("Expanding must be a boolean.")

        self.train_size = train_size
        self.test_size = test_size
        self.step_size = step_size
        self.expanding = expanding

    @staticmethod
    def _validate_data(data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")
        if data.empty:
            raise ValueError("Input DataFrame cannot be empty.")
        if not data.index.is_monotonic_increasing:
            raise ValueError("Input data index must be monotonic increasing for walk-forward validation.")
        if data.index.has_duplicates:
            raise ValueError("Input data index must not contain duplicates for walk-forward validation.")

    def split(self, data):
        self._validate_data(data)
        minimum_rows = self.train_size + self.test_size
        if len(data) < minimum_rows:
            raise ValueError(
                f"Walk-forward validation requires at least {minimum_rows} rows."
            )

        windows = []
        test_start = self.train_size
        window_number = 1

        while test_start + self.test_size <= len(data):
            train_start = 0 if self.expanding else test_start - self.train_size
            train_end = test_start
            test_end = test_start + self.test_size

            train = data.iloc[train_start:train_end].copy()
            test = data.iloc[test_start:test_end].copy()
            windows.append(
                {
                    "window": window_number,
                    "train": train,
                    "test": test,
                    "train_start": train.index[0],
                    "train_end": train.index[-1],
                    "test_start": test.index[0],
                    "test_end": test.index[-1],
                    "train_rows": len(train),
                    "test_rows": len(test),
                }
            )
            window_number += 1
            test_start += self.step_size

        return windows


class WalkForwardValidator:
    """Evaluate a fixed strategy repeatedly across chronological walk-forward windows."""

    def __init__(
        self,
        strategy_engine,
        train_size,
        test_size,
        step_size=None,
        expanding=True,
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0,
        spread_rate=0.0,
    ):
        self.strategy_engine = strategy_engine
        self.splitter = WalkForwardSplitter(train_size, test_size, step_size, expanding)
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.spread_rate = spread_rate

        # Reuse the existing OOS validator as the authority for execution configuration.
        self._partition_validator = OutOfSampleValidator(
            strategy_engine,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
            spread_rate=spread_rate,
        )

    def _evaluate(self, data):
        return self._partition_validator._evaluate_partition(data)

    def run(self, data):
        windows = self.splitter.split(data)
        results = []

        for window in windows:
            train_result = self._evaluate(window["train"])
            test_result = self._evaluate(window["test"])
            results.append(
                {
                    "window": window["window"],
                    "train_start": window["train_start"],
                    "train_end": window["train_end"],
                    "test_start": window["test_start"],
                    "test_end": window["test_end"],
                    "train_rows": window["train_rows"],
                    "test_rows": window["test_rows"],
                    "train": train_result,
                    "test": test_result,
                }
            )

        test_returns = [item["test"]["comparison"]["strategy_return"] for item in results]
        test_excess = [item["test"]["comparison"]["excess_return"] for item in results]
        positive_return_windows = sum(value > 0 for value in test_returns)
        positive_excess_windows = sum(value > 0 for value in test_excess)

        return {
            "configuration": {
                "train_size": self.splitter.train_size,
                "test_size": self.splitter.test_size,
                "step_size": self.splitter.step_size,
                "expanding": self.splitter.expanding,
            },
            "windows": results,
            "summary": {
                "window_count": len(results),
                "mean_test_strategy_return": sum(test_returns) / len(test_returns),
                "mean_test_excess_return": sum(test_excess) / len(test_excess),
                "positive_test_return_windows": positive_return_windows,
                "positive_test_excess_windows": positive_excess_windows,
                "positive_test_return_rate": positive_return_windows / len(results),
                "positive_test_excess_rate": positive_excess_windows / len(results),
            },
        }
