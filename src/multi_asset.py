
import pandas as pd

from backtest import BacktestingEngine
from validation_pipeline import StrategyValidationPipeline, ValidationPolicy


class MultiAssetValidationPolicy:
    """Aggregate asset-level validation without hiding cross-market dispersion."""

    def __init__(self, min_assets=2, min_validated_asset_rate=0.60, max_rejected_asset_rate=0.20):
        if not isinstance(min_assets, int) or isinstance(min_assets, bool):
            raise TypeError("Minimum assets must be an integer.")
        if min_assets < 2:
            raise ValueError("Minimum assets must be at least 2 for multi-asset validation.")
        for value, name in (
            (min_validated_asset_rate, "Minimum validated asset rate"),
            (max_rejected_asset_rate, "Maximum rejected asset rate"),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be a number.")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1.")
        self.min_assets = min_assets
        self.min_validated_asset_rate = float(min_validated_asset_rate)
        self.max_rejected_asset_rate = float(max_rejected_asset_rate)

    def classify(self, asset_results):
        total = len(asset_results)
        if total < self.min_assets:
            raise ValueError(f"Multi-asset validation requires at least {self.min_assets} assets.")
        statuses = [r["classification"]["status"] for r in asset_results.values()]
        counts = {status: statuses.count(status) for status in (
            ValidationPolicy.VALIDATED, ValidationPolicy.CONDITIONAL, ValidationPolicy.REJECTED
        )}
        rates = {key.lower(): value / total for key, value in counts.items()}
        gates = {
            "validated_asset_rate": rates["validated"] >= self.min_validated_asset_rate,
            "rejected_asset_rate": rates["rejected"] <= self.max_rejected_asset_rate,
        }
        if rates["rejected"] > 0.50:
            status = ValidationPolicy.REJECTED
        elif all(gates.values()):
            status = ValidationPolicy.VALIDATED
        else:
            status = ValidationPolicy.CONDITIONAL
        return {
            "status": status,
            "counts": counts,
            "rates": rates,
            "gates": gates,
            "thresholds": {
                "min_assets": self.min_assets,
                "min_validated_asset_rate": self.min_validated_asset_rate,
                "max_rejected_asset_rate": self.max_rejected_asset_rate,
            },
        }


class MultiAssetValidator:
    """Run one frozen strategy through the same validation pipeline on many assets."""

    def __init__(
        self,
        strategy_engine,
        train_size,
        test_size,
        step_size=None,
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
        self.pipeline_kwargs = dict(
            train_size=train_size, test_size=test_size, step_size=step_size,
            expanding=expanding, in_sample_fraction=in_sample_fraction,
            initial_capital=initial_capital, commission_rate=commission_rate,
            slippage_rate=slippage_rate, spread_rate=spread_rate,
            simulations=simulations, confidence_level=confidence_level,
            random_seed=random_seed,
            min_positive_walk_forward_excess_rate=min_positive_walk_forward_excess_rate,
            execution_timing=execution_timing,
        )
        self.policy = MultiAssetValidationPolicy(
            min_assets=min_assets,
            min_validated_asset_rate=min_validated_asset_rate,
            max_rejected_asset_rate=max_rejected_asset_rate,
        )

    @staticmethod
    def _validate_assets(assets):
        if not isinstance(assets, dict):
            raise TypeError("Assets must be a dictionary mapping asset names to DataFrames.")
        if not assets:
            raise ValueError("Assets cannot be empty.")
        for name, data in assets.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Every asset must have a non-empty string name.")
            if not isinstance(data, pd.DataFrame):
                raise TypeError(f"Asset '{name}' data must be a pandas DataFrame.")

    @staticmethod
    def _mean(values):
        return sum(values) / len(values)

    def run(self, assets):
        self._validate_assets(assets)
        if len(assets) < self.policy.min_assets:
            raise ValueError(f"Multi-asset validation requires at least {self.policy.min_assets} assets.")

        results = {}
        for asset_name in sorted(assets):
            pipeline = StrategyValidationPipeline(self.strategy_engine, **self.pipeline_kwargs)
            results[asset_name] = pipeline.run(assets[asset_name])

        oos_returns = [r["out_of_sample"]["out_of_sample"]["comparison"]["strategy_return"] for r in results.values()]
        oos_excess = [r["out_of_sample"]["out_of_sample"]["comparison"]["excess_return"] for r in results.values()]
        persistence = [r["walk_forward"]["summary"]["positive_test_excess_rate"] for r in results.values()]
        classification = self.policy.classify(results)

        return {
            "strategy": StrategyValidationPipeline._strategy_name(self.strategy_engine),
            "asset_count": len(results),
            "assets": results,
            "summary": {
                "mean_oos_strategy_return": self._mean(oos_returns),
                "mean_oos_excess_return": self._mean(oos_excess),
                "positive_oos_excess_asset_rate": sum(v > 0.0 for v in oos_excess) / len(oos_excess),
                "mean_walk_forward_positive_excess_rate": self._mean(persistence),
            },
            "classification": classification,
        }
