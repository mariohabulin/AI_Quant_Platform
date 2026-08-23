"""Calendar-bound validation for provider-observed market data with gaps."""

import pandas as pd

try:
    from backtest import BacktestingEngine
    from falsification import StatisticalFalsificationEngine
    from multi_asset import MultiAssetValidationPolicy
    from out_of_sample import OutOfSampleValidator
    from validation_pipeline import StrategyValidationPipeline, ValidationPolicy
except ImportError:  # package import when src is not placed directly on sys.path
    from src.backtest import BacktestingEngine
    from src.falsification import StatisticalFalsificationEngine
    from src.multi_asset import MultiAssetValidationPolicy
    from src.out_of_sample import OutOfSampleValidator
    from src.validation_pipeline import StrategyValidationPipeline, ValidationPolicy


CALENDAR_WINDOWING = "CALENDAR_TIME_WITH_EXPLICIT_GAPS"


def _utc_timestamp(value, name):
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        raise ValueError(f"{name} must be a valid timestamp.")
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp


def _validated_positive_integer(value, name):
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer.")
    if value <= 0:
        raise ValueError(f"{name} must be positive.")
    return value


class _CalendarDataBoundary:
    def __init__(self, calendar_start, calendar_end, granularity_seconds):
        self.calendar_start = _utc_timestamp(calendar_start, "Calendar start")
        self.calendar_end = _utc_timestamp(calendar_end, "Calendar end")
        self.granularity_seconds = _validated_positive_integer(
            granularity_seconds,
            "Granularity seconds",
        )
        self.step = pd.Timedelta(seconds=self.granularity_seconds)
        if self.calendar_end <= self.calendar_start:
            raise ValueError("Calendar end must be after calendar start.")
        if (
            self.calendar_start.floor(self.step) != self.calendar_start
            or self.calendar_end.floor(self.step) != self.calendar_end
        ):
            raise ValueError("Calendar boundaries must align to granularity.")
        self.expected_rows = int(
            (self.calendar_end - self.calendar_start) / self.step
        )

    def validate_data(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")
        if data.empty:
            raise ValueError("Input DataFrame cannot be empty.")
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Input data must use a DatetimeIndex.")
        if data.index.tz is None:
            raise ValueError("Input data index must be timezone-aware.")
        if not data.index.is_monotonic_increasing:
            raise ValueError("Input data index must be monotonic increasing.")
        if data.index.has_duplicates:
            raise ValueError("Input data index must not contain duplicates.")
        normalized = data.index.tz_convert("UTC")
        if normalized[0] < self.calendar_start or normalized[-1] >= self.calendar_end:
            raise ValueError("Input data falls outside the calendar boundary.")
        if not (normalized == normalized.floor(self.step)).all():
            raise ValueError("Input data index must align to calendar granularity.")

    def interval(self, data, start, end):
        index = data.index.tz_convert("UTC")
        return data.loc[(index >= start) & (index < end)].copy()

    def expected_interval_rows(self, start, end):
        return int((end - start) / self.step)


class CalendarChronologicalDataSplitter:
    """Split at a frozen expected-grid timestamp, independent of missing rows."""

    def __init__(
        self,
        calendar_start,
        calendar_end,
        granularity_seconds,
        in_sample_fraction=0.70,
    ):
        if not isinstance(in_sample_fraction, (int, float)) or isinstance(
            in_sample_fraction, bool
        ):
            raise TypeError("In-sample fraction must be a number.")
        self.in_sample_fraction = float(in_sample_fraction)
        if not 0.0 < self.in_sample_fraction < 1.0:
            raise ValueError("In-sample fraction must be between 0 and 1.")
        self.boundary = _CalendarDataBoundary(
            calendar_start,
            calendar_end,
            granularity_seconds,
        )
        self.split_position = int(
            self.boundary.expected_rows * self.in_sample_fraction
        )
        self.split_boundary = (
            self.boundary.calendar_start
            + self.split_position * self.boundary.step
        )

    def split(self, data):
        self.boundary.validate_data(data)
        in_sample = self.boundary.interval(
            data,
            self.boundary.calendar_start,
            self.split_boundary,
        )
        out_of_sample = self.boundary.interval(
            data,
            self.split_boundary,
            self.boundary.calendar_end,
        )
        if in_sample.empty or out_of_sample.empty:
            raise ValueError("Calendar OOS split produced an empty partition.")
        in_expected = self.split_position
        out_expected = self.boundary.expected_rows - self.split_position
        return {
            "in_sample": in_sample,
            "out_of_sample": out_of_sample,
            "windowing": CALENDAR_WINDOWING,
            "split_position": self.split_position,
            "split_boundary": self.split_boundary,
            "calendar_start": self.boundary.calendar_start,
            "calendar_end_exclusive": self.boundary.calendar_end,
            "in_sample_rows": len(in_sample),
            "out_of_sample_rows": len(out_of_sample),
            "in_sample_expected_rows": in_expected,
            "out_of_sample_expected_rows": out_expected,
            "in_sample_missing_rows": in_expected - len(in_sample),
            "out_of_sample_missing_rows": out_expected - len(out_of_sample),
            "in_sample_start": in_sample.index[0],
            "in_sample_end": in_sample.index[-1],
            "out_of_sample_start": out_of_sample.index[0],
            "out_of_sample_end": out_of_sample.index[-1],
        }


class CalendarWalkForwardSplitter:
    """Create exact calendar windows while retaining only observed market rows."""

    def __init__(
        self,
        train_size,
        test_size,
        step_size,
        expanding,
        calendar_start,
        calendar_end,
        granularity_seconds,
    ):
        self.train_size = _validated_positive_integer(train_size, "Train size")
        self.test_size = _validated_positive_integer(test_size, "Test size")
        self.step_size = _validated_positive_integer(step_size, "Step size")
        if self.step_size < self.test_size:
            raise ValueError("Calendar test windows must not overlap.")
        if not isinstance(expanding, bool):
            raise TypeError("Expanding must be a boolean.")
        self.expanding = expanding
        self.boundary = _CalendarDataBoundary(
            calendar_start,
            calendar_end,
            granularity_seconds,
        )
        if self.train_size + self.test_size > self.boundary.expected_rows:
            raise ValueError("Calendar walk-forward range is too short.")

    def split(self, data):
        self.boundary.validate_data(data)
        train_duration = self.train_size * self.boundary.step
        test_duration = self.test_size * self.boundary.step
        step_duration = self.step_size * self.boundary.step
        test_start = self.boundary.calendar_start + train_duration
        windows = []
        window_number = 1

        while test_start + test_duration <= self.boundary.calendar_end:
            train_start = (
                self.boundary.calendar_start
                if self.expanding
                else test_start - train_duration
            )
            train_end = test_start
            test_end = test_start + test_duration
            train = self.boundary.interval(data, train_start, train_end)
            test = self.boundary.interval(data, test_start, test_end)
            if train.empty or test.empty:
                raise ValueError("Calendar walk-forward produced an empty partition.")
            train_expected = self.boundary.expected_interval_rows(
                train_start,
                train_end,
            )
            test_expected = self.boundary.expected_interval_rows(
                test_start,
                test_end,
            )
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
                    "train_expected_rows": train_expected,
                    "test_expected_rows": test_expected,
                    "train_missing_rows": train_expected - len(train),
                    "test_missing_rows": test_expected - len(test),
                    "calendar_train_start": train_start,
                    "calendar_train_end_exclusive": train_end,
                    "calendar_test_start": test_start,
                    "calendar_test_end_exclusive": test_end,
                }
            )
            window_number += 1
            test_start += step_duration
        return windows


class CalendarOutOfSampleValidator:
    def __init__(
        self,
        strategy_engine,
        calendar_start,
        calendar_end,
        granularity_seconds,
        in_sample_fraction=0.70,
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0,
        spread_rate=0.0,
        execution_timing=BacktestingEngine.SAME_BAR_CLOSE,
    ):
        self.splitter = CalendarChronologicalDataSplitter(
            calendar_start,
            calendar_end,
            granularity_seconds,
            in_sample_fraction,
        )
        self._partition_validator = OutOfSampleValidator(
            strategy_engine,
            in_sample_fraction=in_sample_fraction,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
            spread_rate=spread_rate,
            execution_timing=execution_timing,
        )

    def run(self, data):
        split = self.splitter.split(data)
        in_sample = self._partition_validator._evaluate_partition(
            split["in_sample"]
        )
        out_of_sample = self._partition_validator._evaluate_partition(
            split["out_of_sample"]
        )
        return {
            "split": {
                key: value
                for key, value in split.items()
                if key not in {"in_sample", "out_of_sample"}
            },
            "in_sample": in_sample,
            "out_of_sample": out_of_sample,
            "generalization": {
                "in_sample_strategy_return": in_sample["comparison"][
                    "strategy_return"
                ],
                "out_of_sample_strategy_return": out_of_sample["comparison"][
                    "strategy_return"
                ],
                "in_sample_excess_return": in_sample["comparison"][
                    "excess_return"
                ],
                "out_of_sample_excess_return": out_of_sample["comparison"][
                    "excess_return"
                ],
            },
        }


class CalendarWalkForwardValidator:
    def __init__(
        self,
        strategy_engine,
        train_size,
        test_size,
        step_size,
        calendar_start,
        calendar_end,
        granularity_seconds,
        expanding=True,
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0,
        spread_rate=0.0,
        execution_timing=BacktestingEngine.SAME_BAR_CLOSE,
    ):
        self.splitter = CalendarWalkForwardSplitter(
            train_size,
            test_size,
            step_size,
            expanding,
            calendar_start,
            calendar_end,
            granularity_seconds,
        )
        self._partition_validator = OutOfSampleValidator(
            strategy_engine,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
            spread_rate=spread_rate,
            execution_timing=execution_timing,
        )

    def run(self, data):
        windows = self.splitter.split(data)
        results = []
        for window in windows:
            train_result = self._partition_validator._evaluate_partition(
                window["train"]
            )
            test_result = self._partition_validator._evaluate_partition(
                window["test"]
            )
            results.append(
                {
                    key: value
                    for key, value in window.items()
                    if key not in {"train", "test"}
                }
                | {"train": train_result, "test": test_result}
            )

        test_returns = [
            item["test"]["comparison"]["strategy_return"] for item in results
        ]
        test_excess = [
            item["test"]["comparison"]["excess_return"] for item in results
        ]
        positive_return = sum(value > 0.0 for value in test_returns)
        positive_excess = sum(value > 0.0 for value in test_excess)
        return {
            "configuration": {
                "windowing": CALENDAR_WINDOWING,
                "train_size": self.splitter.train_size,
                "test_size": self.splitter.test_size,
                "step_size": self.splitter.step_size,
                "expanding": self.splitter.expanding,
                "calendar_start": self.splitter.boundary.calendar_start,
                "calendar_end_exclusive": self.splitter.boundary.calendar_end,
                "granularity_seconds": self.splitter.boundary.granularity_seconds,
            },
            "windows": results,
            "summary": {
                "window_count": len(results),
                "mean_test_strategy_return": sum(test_returns) / len(results),
                "mean_test_excess_return": sum(test_excess) / len(results),
                "positive_test_return_windows": positive_return,
                "positive_test_excess_windows": positive_excess,
                "positive_test_return_rate": positive_return / len(results),
                "positive_test_excess_rate": positive_excess / len(results),
            },
        }


class CalendarStrategyValidationPipeline:
    def __init__(
        self,
        strategy_engine,
        train_size,
        test_size,
        step_size,
        expanding,
        calendar_start,
        calendar_end,
        granularity_seconds,
        in_sample_fraction=0.70,
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0,
        spread_rate=0.0,
        simulations=1000,
        confidence_level=0.95,
        random_seed=42,
        min_positive_walk_forward_excess_rate=0.60,
        execution_timing=BacktestingEngine.SAME_BAR_CLOSE,
    ):
        self.strategy_engine = strategy_engine
        common = {
            "calendar_start": calendar_start,
            "calendar_end": calendar_end,
            "granularity_seconds": granularity_seconds,
            "initial_capital": initial_capital,
            "commission_rate": commission_rate,
            "slippage_rate": slippage_rate,
            "spread_rate": spread_rate,
            "execution_timing": execution_timing,
        }
        self.oos_validator = CalendarOutOfSampleValidator(
            strategy_engine,
            in_sample_fraction=in_sample_fraction,
            **common,
        )
        self.walk_forward_validator = CalendarWalkForwardValidator(
            strategy_engine,
            train_size=train_size,
            test_size=test_size,
            step_size=step_size,
            expanding=expanding,
            **common,
        )
        self.falsification_engine = StatisticalFalsificationEngine(
            simulations=simulations,
            confidence_level=confidence_level,
            random_seed=random_seed,
        )
        self.policy = ValidationPolicy(min_positive_walk_forward_excess_rate)

    def run(self, data):
        oos = self.oos_validator.run(data)
        walk_forward = self.walk_forward_validator.run(data)
        unseen_trades = []
        for window in walk_forward["windows"]:
            unseen_trades.extend(window["test"]["trade_history"])
        falsification = self.falsification_engine.analyze(unseen_trades)
        classification = self.policy.classify(oos, walk_forward, falsification)
        return {
            "strategy": StrategyValidationPipeline._strategy_name(
                self.strategy_engine
            ),
            "out_of_sample": oos,
            "walk_forward": walk_forward,
            "falsification": falsification,
            "classification": classification,
        }


class CalendarMultiAssetValidator:
    """Run one strategy on sparse assets with identical calendar boundaries."""

    def __init__(
        self,
        strategy_engine,
        train_size,
        test_size,
        step_size,
        calendar_start,
        calendar_end,
        granularity_seconds,
        expanding=True,
        in_sample_fraction=0.70,
        initial_capital=10000.0,
        commission_rate=0.0,
        slippage_rate=0.0,
        spread_rate=0.0,
        simulations=1000,
        confidence_level=0.95,
        random_seed=42,
        min_positive_walk_forward_excess_rate=0.60,
        min_assets=2,
        min_validated_asset_rate=0.60,
        max_rejected_asset_rate=0.20,
        execution_timing=BacktestingEngine.SAME_BAR_CLOSE,
    ):
        self.strategy_engine = strategy_engine
        self.pipeline_kwargs = {
            "train_size": train_size,
            "test_size": test_size,
            "step_size": step_size,
            "expanding": expanding,
            "calendar_start": calendar_start,
            "calendar_end": calendar_end,
            "granularity_seconds": granularity_seconds,
            "in_sample_fraction": in_sample_fraction,
            "initial_capital": initial_capital,
            "commission_rate": commission_rate,
            "slippage_rate": slippage_rate,
            "spread_rate": spread_rate,
            "simulations": simulations,
            "confidence_level": confidence_level,
            "random_seed": random_seed,
            "min_positive_walk_forward_excess_rate": (
                min_positive_walk_forward_excess_rate
            ),
            "execution_timing": execution_timing,
        }
        self.policy = MultiAssetValidationPolicy(
            min_assets=min_assets,
            min_validated_asset_rate=min_validated_asset_rate,
            max_rejected_asset_rate=max_rejected_asset_rate,
        )

    def run(self, assets):
        if not isinstance(assets, dict):
            raise TypeError("Assets must be a dictionary mapping names to DataFrames.")
        if not assets:
            raise ValueError("Assets cannot be empty.")
        if len(assets) < self.policy.min_assets:
            raise ValueError(
                "Multi-asset validation requires at least "
                f"{self.policy.min_assets} assets."
            )
        results = {}
        for asset_name in sorted(assets):
            if not isinstance(asset_name, str) or not asset_name.strip():
                raise ValueError("Every asset must have a non-empty string name.")
            if not isinstance(assets[asset_name], pd.DataFrame):
                raise TypeError(f"Asset '{asset_name}' data must be a DataFrame.")
            pipeline = CalendarStrategyValidationPipeline(
                self.strategy_engine,
                **self.pipeline_kwargs,
            )
            results[asset_name] = pipeline.run(assets[asset_name])

        oos_returns = [
            item["out_of_sample"]["out_of_sample"]["comparison"][
                "strategy_return"
            ]
            for item in results.values()
        ]
        oos_excess = [
            item["out_of_sample"]["out_of_sample"]["comparison"][
                "excess_return"
            ]
            for item in results.values()
        ]
        persistence = [
            item["walk_forward"]["summary"]["positive_test_excess_rate"]
            for item in results.values()
        ]
        count = len(results)
        return {
            "strategy": StrategyValidationPipeline._strategy_name(
                self.strategy_engine
            ),
            "windowing": CALENDAR_WINDOWING,
            "asset_count": count,
            "assets": results,
            "summary": {
                "mean_oos_strategy_return": sum(oos_returns) / count,
                "mean_oos_excess_return": sum(oos_excess) / count,
                "positive_oos_excess_asset_rate": (
                    sum(value > 0.0 for value in oos_excess) / count
                ),
                "mean_walk_forward_positive_excess_rate": (
                    sum(persistence) / count
                ),
            },
            "classification": self.policy.classify(results),
        }
